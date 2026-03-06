"""
Background poller for FruitPak batch data.

Runs as an asyncio task during the application lifespan.
Polls FruitPak every N minutes for new/updated batches in 'packing' status
and caches them locally for QMS intake inspections.

Polling is the recommended approach per FruitPak docs (webhooks planned
but not yet available). Uses cursor pagination for efficient incremental
fetching.
"""

import asyncio
import logging
from datetime import date, timedelta

from src.config import settings
from src.database.engine import async_session_factory
from src.services.fruitpak_integration_service import (
    fruitpak_service,
    FruitPakError,
)

logger = logging.getLogger("fruitpak.poller")


async def poll_fruitpak_batches() -> None:
    """
    Background task that polls FruitPak for new batches.

    Runs in a loop with configurable interval (FRUITPAK_POLL_INTERVAL_MINUTES).
    Only runs if FruitPak integration is configured.
    """
    if not fruitpak_service.is_configured:
        logger.info("FruitPak integration not configured — poller disabled")
        return

    interval = settings.FRUITPAK_POLL_INTERVAL_MINUTES * 60
    logger.info(
        f"FruitPak poller started (interval: {settings.FRUITPAK_POLL_INTERVAL_MINUTES} min)"
    )

    while True:
        try:
            # Look back 7 days to catch any missed updates
            date_from = date.today() - timedelta(days=7)

            async with async_session_factory() as db:
                # We need at least one packhouse to associate batches with.
                # Use packhouse_id=1 as default; in production this would be
                # resolved from the FruitPak packhouse sync.
                from sqlalchemy import select, func
                from src.models.organization import Packhouse

                result = await db.execute(
                    select(Packhouse.id).order_by(Packhouse.id).limit(1)
                )
                packhouse_id = result.scalar_one_or_none() or 1

                count = await fruitpak_service.sync_batches_to_cache(
                    db,
                    packhouse_id=packhouse_id,
                    status="packing",
                    date_from=date_from,
                )
                logger.info(f"Poll complete: synced {count} batches")

        except FruitPakError as e:
            logger.warning(f"FruitPak poll failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in FruitPak poller: {e}", exc_info=True)

        await asyncio.sleep(interval)
