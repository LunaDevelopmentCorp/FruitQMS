"""Audit logging helper — creates audit trail entries."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    organization_id: Optional[int] = None,
    field_changed: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """
    Create an audit log entry.

    Usage:
        await log_action(
            db, user.id, "create", "intake_inspection", inspection.id,
            organization_id=org.id,
            details={"grn": "GRN-001", "crop": "Mango"}
        )
    """
    entry = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        field_changed=field_changed,
        old_value=old_value,
        new_value=new_value,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    # Don't flush here — let the caller's transaction handle it
