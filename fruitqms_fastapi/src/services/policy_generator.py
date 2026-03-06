"""
Policy document generator (Phase 2 — stubs only).

Ported from Flask: app/utils/policy_generator.py
Full implementation deferred; these stubs define the interface
so the setup wizard can reference them once routes are activated.
"""

from typing import Optional
from datetime import date


# ---------------------------------------------------------------------------
# Supported policy types (mirrors the original Flask generator)
# ---------------------------------------------------------------------------
POLICY_TYPES = [
    "haccp_plan",
    "spray_program",
    "environmental_policy",
    "waste_management",
    "training_log",
    "worker_welfare",
    "traceability_plan",
]


async def generate_policy(
    policy_type: str,
    organization_name: str,
    organization_id: int,
    *,
    packhouse_name: Optional[str] = None,
    audit_scope: Optional[str] = None,
    business_type: Optional[str] = None,
    crops: Optional[list[str]] = None,
    effective_date: Optional[date] = None,
) -> dict:
    """
    Generate a compliance policy document (PDF) for the given organization.

    Parameters
    ----------
    policy_type : str
        One of POLICY_TYPES.
    organization_name : str
        Company name for the document header.
    organization_id : int
        Used for file storage path.
    packhouse_name : str, optional
        Specific packhouse (if scoped).
    audit_scope : str, optional
        'GFS' or 'SMART'.
    business_type : str, optional
        e.g. 'grower', 'packhouse_only', 'packhouse_farms'.
    crops : list[str], optional
        Crops to reference in the policy.
    effective_date : date, optional
        Defaults to today.

    Returns
    -------
    dict
        {"policy_type": ..., "file_path": ..., "generated_at": ...}

    Raises
    ------
    NotImplementedError
        Phase 2 — generation logic not yet implemented.
    """
    raise NotImplementedError(
        f"Policy generation for '{policy_type}' is deferred to Phase 2. "
        "See Flask app/utils/policy_generator.py for reference implementation."
    )


async def generate_all_policies(
    organization_id: int,
    organization_name: str,
    applicable_policies: list[str],
    **kwargs,
) -> list[dict]:
    """
    Batch-generate all applicable policies for an organization.

    Called by the setup wizard after control-point analysis determines
    which policies are needed.

    Returns a list of generation result dicts (one per policy).
    """
    results = []
    for policy_type in applicable_policies:
        if policy_type in POLICY_TYPES:
            result = await generate_policy(
                policy_type=policy_type,
                organization_name=organization_name,
                organization_id=organization_id,
                **kwargs,
            )
            results.append(result)
    return results


def determine_policies_needed(
    business_type: str,
    has_haccp: bool = False,
    has_spray_program: bool = False,
    has_environmental_policy: bool = False,
    waste_management_plan: bool = False,
) -> list[str]:
    """
    Determine which policy documents an organization needs based on
    business type and existing compliance status.

    Ported from Flask: app/routes/wizard.py → determine_policies_needed()
    """
    needed = []

    # Everyone needs traceability
    needed.append("traceability_plan")

    # HACCP plan
    if not has_haccp:
        needed.append("haccp_plan")

    # Spray program — required for growers or mixed operations
    if not has_spray_program and business_type in (
        "grower", "packhouse_farms", "packhouse_contract", "packhouse_mixed"
    ):
        needed.append("spray_program")

    # Environmental policy — always required for GLOBALG.A.P.
    if not has_environmental_policy:
        needed.append("environmental_policy")

    # Waste management
    if not waste_management_plan:
        needed.append("waste_management")

    # Training and worker welfare — always required
    needed.append("training_log")
    needed.append("worker_welfare")

    return needed
