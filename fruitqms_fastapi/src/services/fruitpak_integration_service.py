"""
FruitPak integration service.

Communicates with FruitPak's API to fetch GRN/Batch data for intake inspections.
Caches data locally for offline resilience.
Falls back to manual entry when FruitPak is unavailable.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.qms_integrations import FruitPakGRNReference


class FruitPakConnectionError(Exception):
    """Raised when FruitPak API is unreachable."""
    pass


class FruitPakNotFoundError(Exception):
    """Raised when the requested GRN/batch doesn't exist in FruitPak."""
    pass


class FruitPakIntegrationService:
    """
    Handles all communication with FruitPak API.

    Usage:
        service = FruitPakIntegrationService()
        grn_data = await service.validate_grn("GRN-2026-001", db)
    """

    def __init__(self):
        self.api_url = settings.FRUITPAK_API_URL
        self.api_key = settings.FRUITPAK_API_KEY
        self.timeout = settings.FRUITPAK_TIMEOUT_SECONDS

    @property
    def is_configured(self) -> bool:
        """Check if FruitPak integration is configured."""
        return bool(self.api_url)

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def validate_grn(self, grn_code: str) -> Dict[str, Any]:
        """
        Fetch GRN data from FruitPak's API.

        Returns dict with: grn_id, batch_id, grower_name, grower_code,
        crop_type, variety, harvest_date, expected_quantity, unit, status

        Raises:
            FruitPakConnectionError: if API is unreachable
            FruitPakNotFoundError: if GRN doesn't exist
        """
        if not self.is_configured:
            raise FruitPakConnectionError("FruitPak API URL not configured")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/api/v1/batches/grn/{grn_code}",
                    headers=self._get_headers(),
                )

                if response.status_code == 404:
                    raise FruitPakNotFoundError(
                        f"GRN '{grn_code}' not found in FruitPak"
                    )

                response.raise_for_status()
                return response.json()

        except httpx.ConnectError:
            raise FruitPakConnectionError(
                "Cannot connect to FruitPak. Service may be offline."
            )
        except httpx.TimeoutException:
            raise FruitPakConnectionError(
                f"FruitPak did not respond within {self.timeout}s"
            )
        except httpx.HTTPStatusError as e:
            raise FruitPakConnectionError(
                f"FruitPak returned error: {e.response.status_code}"
            )

    async def sync_grn_to_cache(
        self,
        grn_data: Dict[str, Any],
        packhouse_id: int,
        grower_id: Optional[int],
        db: AsyncSession,
    ) -> FruitPakGRNReference:
        """
        Cache GRN data locally after fetching from FruitPak API.

        If a cached reference already exists for this GRN, update it.
        """
        # Check if already cached
        result = await db.execute(
            select(FruitPakGRNReference).where(
                FruitPakGRNReference.fruitpak_grn_id == grn_data.get("grn_id", grn_data.get("grn_code"))
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update cached data
            existing.grower_name = grn_data.get("grower_name")
            existing.grower_code = grn_data.get("grower_code")
            existing.crop_type = grn_data.get("crop_type")
            existing.variety = grn_data.get("variety")
            existing.harvest_date = grn_data.get("harvest_date")
            existing.expected_quantity = grn_data.get("expected_quantity")
            existing.unit_of_measure = grn_data.get("unit_of_measure", grn_data.get("unit"))
            existing.batch_status = grn_data.get("status")
            existing.synced_at = datetime.now(timezone.utc)
            await db.flush()
            await db.refresh(existing)
            return existing

        # Create new cache entry
        ref = FruitPakGRNReference(
            packhouse_id=packhouse_id,
            grower_id=grower_id,
            fruitpak_grn_id=grn_data.get("grn_id", grn_data.get("grn_code")),
            fruitpak_batch_id=grn_data.get("batch_id"),
            grower_name=grn_data.get("grower_name"),
            grower_code=grn_data.get("grower_code"),
            crop_type=grn_data.get("crop_type"),
            variety=grn_data.get("variety"),
            harvest_date=grn_data.get("harvest_date"),
            expected_quantity=grn_data.get("expected_quantity"),
            unit_of_measure=grn_data.get("unit_of_measure", grn_data.get("unit")),
            batch_status=grn_data.get("status"),
        )
        db.add(ref)
        await db.flush()
        await db.refresh(ref)
        return ref

    async def search_cached_grns(
        self,
        db: AsyncSession,
        packhouse_id: Optional[int] = None,
        grower_id: Optional[int] = None,
        limit: int = 20,
    ) -> list:
        """Search locally cached GRN references."""
        query = select(FruitPakGRNReference)
        if packhouse_id:
            query = query.where(FruitPakGRNReference.packhouse_id == packhouse_id)
        if grower_id:
            query = query.where(FruitPakGRNReference.grower_id == grower_id)

        query = query.order_by(FruitPakGRNReference.synced_at.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def health_check(self) -> Dict[str, Any]:
        """Check if FruitPak API is reachable."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "FRUITPAK_API_URL not set",
            }

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.api_url}/health",
                    headers=self._get_headers(),
                )
                return {
                    "status": "connected" if response.status_code == 200 else "error",
                    "http_status": response.status_code,
                    "api_url": self.api_url,
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "message": str(e),
                "api_url": self.api_url,
            }


# Singleton instance
fruitpak_service = FruitPakIntegrationService()
