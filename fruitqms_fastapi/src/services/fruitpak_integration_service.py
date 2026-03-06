"""
FruitPak integration service.

Communicates with FruitPak's API to:
  1. Authenticate via JWT (login + token refresh)
  2. Search/fetch batch (GRN) data for intake inspections
  3. Sync grower and packhouse master data
  4. Write quality assessment results back to FruitPak
  5. Poll for new batches on a schedule

Caches batch data locally for offline resilience.
Falls back to manual entry when FruitPak is unavailable.

Auth flow per FruitPak spec:
  POST /api/auth/login        → access_token (30 min) + refresh_token (7 days)
  POST /api/auth/refresh      → new token pair
  Bearer {access_token} on all subsequent requests

FruitPak API base URLs:
  Local dev:   http://localhost:3000
  Production:  https://api.fruitpak.com  (AWS-hosted)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta, date
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.qms_integrations import FruitPakGRNReference

logger = logging.getLogger("fruitpak")


class FruitPakError(Exception):
    """Base exception for FruitPak integration errors."""


class FruitPakConnectionError(FruitPakError):
    """Raised when FruitPak API is unreachable."""


class FruitPakAuthError(FruitPakError):
    """Raised when authentication with FruitPak fails."""


class FruitPakNotFoundError(FruitPakError):
    """Raised when the requested resource doesn't exist in FruitPak."""


class FruitPakRateLimitError(FruitPakError):
    """Raised when rate limit is exceeded (429)."""


class FruitPakClient:
    """
    Low-level HTTP client for FruitPak API with JWT token management.

    Handles login, automatic token refresh, and rate limit awareness.
    """

    def __init__(self):
        self.base_url = (settings.FRUITPAK_API_URL or "").rstrip("/")
        self.email = settings.FRUITPAK_EMAIL
        self.password = settings.FRUITPAK_PASSWORD
        self.timeout = settings.FRUITPAK_TIMEOUT_SECONDS

        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.email and self.password)

    async def _login(self) -> None:
        """Authenticate with FruitPak and store tokens."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/auth/login",
                json={"email": self.email, "password": self.password},
            )
            if resp.status_code == 401:
                raise FruitPakAuthError("Invalid FruitPak credentials")
            if resp.status_code == 429:
                raise FruitPakRateLimitError("Login rate limit exceeded")
            resp.raise_for_status()

            data = resp.json()
            self._access_token = data["access_token"]
            self._refresh_token = data["refresh_token"]
            # Access token expires in 30 min — refresh 2 min early
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=28)
            logger.info("Authenticated with FruitPak")

    async def _refresh(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            return await self._login()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/auth/refresh",
                    json={"refresh_token": self._refresh_token},
                )
                if resp.status_code in (401, 403):
                    # Refresh token expired — full re-login
                    return await self._login()
                resp.raise_for_status()

                data = resp.json()
                self._access_token = data["access_token"]
                self._refresh_token = data["refresh_token"]
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=28)
                logger.debug("Refreshed FruitPak access token")
        except (httpx.ConnectError, httpx.TimeoutException):
            raise FruitPakConnectionError("Cannot reach FruitPak for token refresh")

    async def _ensure_token(self) -> str:
        """Ensure we have a valid access token, refreshing if needed."""
        async with self._lock:
            if not self._access_token or (
                self._token_expires_at
                and datetime.now(timezone.utc) >= self._token_expires_at
            ):
                if self._refresh_token:
                    await self._refresh()
                else:
                    await self._login()
            return self._access_token

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        retry_auth: bool = True,
    ) -> httpx.Response:
        """
        Make an authenticated request to FruitPak API.

        Automatically handles token refresh on 401 responses.
        """
        if not self.is_configured:
            raise FruitPakConnectionError("FruitPak integration not configured")

        token = await self._ensure_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    headers=headers,
                    params=params,
                    json=json,
                )

                if resp.status_code == 401 and retry_auth:
                    # Token might have been revoked — refresh and retry once
                    async with self._lock:
                        await self._login()
                    return await self.request(
                        method, path, params=params, json=json, retry_auth=False
                    )

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After", "60")
                    raise FruitPakRateLimitError(
                        f"Rate limited. Retry after {retry_after}s"
                    )

                if resp.status_code == 404:
                    raise FruitPakNotFoundError(f"Not found: {path}")

                resp.raise_for_status()
                return resp

        except httpx.ConnectError:
            raise FruitPakConnectionError("Cannot connect to FruitPak")
        except httpx.TimeoutException:
            raise FruitPakConnectionError(
                f"FruitPak did not respond within {self.timeout}s"
            )
        except httpx.HTTPStatusError as e:
            raise FruitPakError(f"FruitPak error: {e.response.status_code}")

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PATCH", path, **kwargs)


# ---------------------------------------------------------------------------
# High-level integration service
# ---------------------------------------------------------------------------


class FruitPakIntegrationService:
    """
    High-level service for FruitPak integration.

    Provides business-logic methods for batch lookup, data sync,
    quality write-back, and health monitoring.
    """

    def __init__(self):
        self.client = FruitPakClient()

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured

    # ── Batch / GRN operations ────────────────────────────────────────────

    async def search_batches(
        self,
        *,
        search: str | None = None,
        grower_id: str | None = None,
        status: str | None = None,
        fruit_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict:
        """
        Search FruitPak batches.

        Maps to: GET /api/batches/?search=...&status=packing&...
        Returns: { items: [...], total, limit, next_cursor, has_more }
        """
        params = {}
        if search:
            params["search"] = search
        if grower_id:
            params["grower_id"] = grower_id
        if status:
            params["status"] = status
        if fruit_type:
            params["fruit_type"] = fruit_type
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if limit:
            params["limit"] = min(limit, 200)
        if cursor:
            params["cursor"] = cursor

        resp = await self.client.get("/api/batches/", params=params)
        return resp.json()

    async def get_batch(self, batch_id: str) -> dict:
        """
        Get full batch detail by FruitPak UUID.

        Maps to: GET /api/batches/{batch_id}
        Returns detail with quality_assessment, history, lots, etc.
        """
        resp = await self.client.get(f"/api/batches/{batch_id}")
        return resp.json()

    async def lookup_batch_by_code(self, batch_code: str) -> dict | None:
        """
        Look up a batch by its code (e.g. BATCH-2024-001).

        FruitPak has no direct lookup-by-code — uses search endpoint.
        Returns the first matching batch or None.
        """
        result = await self.search_batches(search=batch_code, limit=5)
        items = result.get("items", [])
        for item in items:
            if item.get("batch_code") == batch_code:
                return item
        return items[0] if items else None

    async def write_quality_result(
        self,
        batch_id: str,
        *,
        quality_grade: str | None = None,
        quality_assessment: dict | None = None,
        arrival_temp_c: float | None = None,
        brix_reading: float | None = None,
    ) -> dict:
        """
        Write QMS quality results back to FruitPak.

        Maps to: PATCH /api/batches/{batch_id}
        Only writes to quality fields — does NOT change batch status.
        """
        payload = {}
        if quality_grade is not None:
            payload["quality_grade"] = quality_grade
        if quality_assessment is not None:
            payload["quality_assessment"] = quality_assessment
        if arrival_temp_c is not None:
            payload["arrival_temp_c"] = arrival_temp_c
        if brix_reading is not None:
            payload["brix_reading"] = brix_reading

        resp = await self.client.patch(f"/api/batches/{batch_id}", json=payload)
        return resp.json()

    # ── Grower & Packhouse sync ───────────────────────────────────────────

    async def list_growers(self, limit: int = 500) -> list[dict]:
        """
        Fetch all growers from FruitPak (master data source).

        Maps to: GET /api/growers/?limit=500
        Returns list of grower dicts with id, name, grower_code,
        globalg_ap_number, region, total_hectares, etc.
        """
        resp = await self.client.get("/api/growers/", params={"limit": limit})
        data = resp.json()
        return data.get("items", data) if isinstance(data, dict) else data

    async def list_packhouses(self, limit: int = 100) -> list[dict]:
        """
        Fetch all packhouses from FruitPak (master data source).

        Maps to: GET /api/packhouses/?limit=100
        """
        resp = await self.client.get("/api/packhouses/", params={"limit": limit})
        data = resp.json()
        return data.get("items", data) if isinstance(data, dict) else data

    # ── GRN cache operations ──────────────────────────────────────────────

    async def validate_and_cache_grn(
        self,
        batch_code: str,
        packhouse_id: int,
        grower_id: int | None,
        db: AsyncSession,
    ) -> FruitPakGRNReference | None:
        """
        Look up a batch code in FruitPak and cache it locally.

        Returns the cached GRN reference, or None if not found.
        """
        batch = await self.lookup_batch_by_code(batch_code)
        if not batch:
            return None

        return await self._upsert_grn_cache(batch, packhouse_id, grower_id, db)

    async def sync_batches_to_cache(
        self,
        db: AsyncSession,
        packhouse_id: int,
        *,
        status: str = "packing",
        date_from: date | None = None,
    ) -> int:
        """
        Poll FruitPak for batches and cache them locally.

        Returns the number of batches synced.
        Uses cursor pagination to handle large result sets.
        """
        synced = 0
        cursor = None
        has_more = True

        while has_more:
            result = await self.search_batches(
                status=status,
                date_from=date_from,
                limit=200,
                cursor=cursor,
            )
            items = result.get("items", [])
            for batch in items:
                await self._upsert_grn_cache(batch, packhouse_id, None, db)
                synced += 1

            has_more = result.get("has_more", False)
            cursor = result.get("next_cursor")

        await db.commit()
        logger.info(f"Synced {synced} batches from FruitPak")
        return synced

    async def _upsert_grn_cache(
        self,
        batch: dict,
        packhouse_id: int,
        grower_id: int | None,
        db: AsyncSession,
    ) -> FruitPakGRNReference:
        """Insert or update a cached GRN reference from FruitPak batch data."""
        batch_code = batch.get("batch_code", "")
        fruitpak_id = batch.get("id", batch_code)

        result = await db.execute(
            select(FruitPakGRNReference).where(
                FruitPakGRNReference.fruitpak_grn_id == batch_code
            )
        )
        existing = result.scalar_one_or_none()

        harvest_date_raw = batch.get("harvest_date") or batch.get("intake_date")
        harvest_date = None
        if harvest_date_raw:
            try:
                harvest_date = datetime.fromisoformat(
                    harvest_date_raw.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                pass

        fields = dict(
            fruitpak_batch_id=str(fruitpak_id),
            grower_name=batch.get("grower_name"),
            grower_code=batch.get("grower_code"),
            crop_type=batch.get("fruit_type"),
            variety=batch.get("variety"),
            harvest_date=harvest_date,
            expected_quantity=batch.get("gross_weight_kg"),
            unit_of_measure="kg",
            batch_status=batch.get("status"),
            synced_at=datetime.now(timezone.utc),
        )

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            await db.flush()
            return existing

        ref = FruitPakGRNReference(
            packhouse_id=packhouse_id,
            grower_id=grower_id,
            fruitpak_grn_id=batch_code,
            **fields,
        )
        db.add(ref)
        await db.flush()
        return ref

    async def search_cached_grns(
        self,
        db: AsyncSession,
        packhouse_id: int | None = None,
        grower_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
    ) -> list:
        """Search locally cached GRN references."""
        query = select(FruitPakGRNReference)
        if packhouse_id:
            query = query.where(FruitPakGRNReference.packhouse_id == packhouse_id)
        if grower_id:
            query = query.where(FruitPakGRNReference.grower_id == grower_id)
        if search:
            query = query.where(
                FruitPakGRNReference.fruitpak_grn_id.ilike(f"%{search}%")
                | FruitPakGRNReference.grower_name.ilike(f"%{search}%")
                | FruitPakGRNReference.crop_type.ilike(f"%{search}%")
            )

        query = query.order_by(FruitPakGRNReference.synced_at.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    # ── Health check ──────────────────────────────────────────────────────

    async def health_check(self) -> dict:
        """
        Check FruitPak API health.

        Uses: GET /health/ready (checks DB + Redis on FruitPak side)
        """
        if not self.is_configured:
            return {"status": "not_configured", "message": "FruitPak credentials not set"}

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.client.base_url}/health/ready")
                return {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "http_status": resp.status_code,
                    "api_url": self.client.base_url,
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "api_url": self.client.base_url,
            }


# Singleton instance
fruitpak_service = FruitPakIntegrationService()
