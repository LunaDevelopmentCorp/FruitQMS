"""FruitPak integration models: cached GRN references for offline resilience."""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, Float, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class FruitPakGRNReference(Base, TimestampMixin):
    """
    Lightweight cache of GRN/Batch data pulled from FruitPak's API.

    Purpose: QMS stores a local copy so it can work even when FruitPak
    is temporarily unavailable. This is NOT a full sync — just the
    minimum data needed to link intake inspections to FruitPak batches.
    """

    __tablename__ = "fruitpak_grn_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    packhouse_id: Mapped[int] = mapped_column(ForeignKey("packhouses.id"), index=True)
    grower_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("growers.id"), nullable=True
    )

    # FruitPak identifiers
    fruitpak_grn_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    fruitpak_batch_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Cached data (minimal set needed for QMS intake)
    grower_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    grower_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    crop_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    variety: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    batch_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Last synced from FruitPak
    synced_at: Mapped[datetime] = mapped_column(default=func.now())

    # Link back to QMS intake inspection (set after inspection is created)
    intake_inspection_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("intake_inspections.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<FruitPakGRNReference {self.fruitpak_grn_id}>"
