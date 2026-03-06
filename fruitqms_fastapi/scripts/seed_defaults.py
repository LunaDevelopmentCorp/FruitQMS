"""
Seed default form templates for a new organization.

Run: python -m scripts.seed_defaults

Creates standard packhouse form templates:
- INTAKE_CHECKLIST: Fruit quality on arrival
- DAILY_COLDCHAIN: Cold room temperature checks
- DAILY_HYGIENE: Sanitation and pest control
- PROCESS_CHECK: In-line quality during packing
- FINAL_INSPECTION: Pre-dispatch pallet check
"""

import asyncio
import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.engine import async_session_factory, engine
from src.models.base import Base
from src.models.qms_forms import FormTemplate
from src.models.auth import User
from src.models.organization import Organization, Packhouse, PackLine, Grower
from src.models.qms_operations import IntakeInspection, ProcessCheck, FinalInspection, DailyChecklist
from src.models.qms_integrations import FruitPakGRNReference
from src.models.audit import AuditLog
import src.models.standards  # noqa: F401 — register standards models for relationships
from src.middleware.auth import hash_password


DEFAULT_TEMPLATES = [
    {
        "name": "Intake Quality Checklist",
        "code": "INTAKE_CHECKLIST",
        "description": "Quality assessment of fruit on arrival at packhouse",
        "form_type": "intake",
        "schema": {
            "sections": [
                {
                    "id": "arrival",
                    "title": "Arrival Details",
                    "fields": [
                        {"id": "vehicle_clean", "label": "Transport vehicle clean and suitable?", "type": "boolean", "validation": {"required": True}},
                        {"id": "vehicle_temp", "label": "Vehicle temperature (°C)", "type": "number", "unit": "°C", "validation": {"required": True, "min": -5, "max": 40}},
                        {"id": "delivery_note_matches", "label": "Delivery note matches consignment?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "quality",
                    "title": "Fruit Quality Assessment",
                    "fields": [
                        {"id": "pulp_temp", "label": "Pulp temperature (°C)", "type": "number", "unit": "°C", "validation": {"required": True, "min": -5, "max": 40}},
                        {"id": "brix_level", "label": "Brix level (°Bx)", "type": "number", "unit": "°Bx", "validation": {"required": False, "min": 0, "max": 30}},
                        {"id": "firmness", "label": "Firmness (kg/cm²)", "type": "number", "unit": "kg/cm²", "validation": {"required": False, "min": 0, "max": 20}},
                        {"id": "colour_acceptable", "label": "Colour acceptable?", "type": "boolean", "validation": {"required": True}},
                        {"id": "size_within_spec", "label": "Size within specification?", "type": "boolean", "validation": {"required": True}},
                        {"id": "visual_defects", "label": "Visual defects found?", "type": "boolean", "validation": {"required": True},
                         "conditional": {"if_true": {"show_field": "defect_description", "require": True}}},
                        {"id": "defect_description", "label": "Describe defects found", "type": "text", "validation": {"max_length": 500}, "hidden": True},
                        {"id": "pest_damage", "label": "Any pest or disease damage?", "type": "boolean", "validation": {"required": True},
                         "conditional": {"if_true": {"show_field": "pest_description", "require": True}}},
                        {"id": "pest_description", "label": "Describe pest/disease damage", "type": "text", "validation": {"max_length": 500}, "hidden": True},
                    ]
                },
                {
                    "id": "decision",
                    "title": "Intake Decision",
                    "fields": [
                        {"id": "overall_quality", "label": "Overall quality rating", "type": "select",
                         "options": [{"value": "excellent", "label": "Excellent"}, {"value": "good", "label": "Good"}, {"value": "acceptable", "label": "Acceptable"}, {"value": "poor", "label": "Poor"}, {"value": "rejected", "label": "Rejected"}],
                         "validation": {"required": True}},
                        {"id": "intake_decision", "label": "Intake decision", "type": "select",
                         "options": [{"value": "accept", "label": "Accept"}, {"value": "conditional_accept", "label": "Conditional Accept"}, {"value": "quarantine", "label": "Quarantine"}, {"value": "reject", "label": "Reject"}],
                         "validation": {"required": True}},
                        {"id": "additional_notes", "label": "Additional notes", "type": "text", "validation": {"max_length": 1000}},
                    ]
                }
            ],
            "scoring": {"enabled": True, "threshold": 80, "calculation": "auto"}
        },
        "form_metadata": {"frequency": "per_batch", "applicability": "all_products"},
    },
    {
        "name": "Daily Cold Chain Checklist",
        "code": "DAILY_COLDCHAIN",
        "description": "Daily verification of cold storage temperatures and door integrity",
        "form_type": "daily_checklist",
        "schema": {
            "sections": [
                {
                    "id": "cold_room_1",
                    "title": "Cold Room 1",
                    "fields": [
                        {"id": "cr1_temp_morning", "label": "Temperature 06:00", "type": "number", "unit": "°C", "validation": {"required": True, "min": -30, "max": 15}},
                        {"id": "cr1_temp_midday", "label": "Temperature 12:00", "type": "number", "unit": "°C", "validation": {"required": True, "min": -30, "max": 15}},
                        {"id": "cr1_temp_evening", "label": "Temperature 18:00", "type": "number", "unit": "°C", "validation": {"required": True, "min": -30, "max": 15}},
                        {"id": "cr1_door_seals", "label": "Door seals intact?", "type": "boolean", "validation": {"required": True}},
                        {"id": "cr1_evaporator", "label": "Evaporator functioning correctly?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "cold_room_2",
                    "title": "Cold Room 2",
                    "fields": [
                        {"id": "cr2_temp_morning", "label": "Temperature 06:00", "type": "number", "unit": "°C", "validation": {"required": True, "min": -30, "max": 15}},
                        {"id": "cr2_temp_midday", "label": "Temperature 12:00", "type": "number", "unit": "°C", "validation": {"required": True, "min": -30, "max": 15}},
                        {"id": "cr2_temp_evening", "label": "Temperature 18:00", "type": "number", "unit": "°C", "validation": {"required": True, "min": -30, "max": 15}},
                        {"id": "cr2_door_seals", "label": "Door seals intact?", "type": "boolean", "validation": {"required": True}},
                        {"id": "cr2_evaporator", "label": "Evaporator functioning correctly?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "general",
                    "title": "General",
                    "fields": [
                        {"id": "all_alarms_functional", "label": "Temperature alarms functional?", "type": "boolean", "validation": {"required": True}},
                        {"id": "corrective_action", "label": "Corrective action taken (if any)", "type": "text", "validation": {"max_length": 500}},
                    ]
                }
            ],
            "scoring": {"enabled": True, "threshold": 100, "calculation": "auto"}
        },
        "form_metadata": {"frequency": "daily", "checklist_type": "cold_chain"},
    },
    {
        "name": "Daily Hygiene Checklist",
        "code": "DAILY_HYGIENE",
        "description": "Daily sanitation, hygiene, and pest control verification",
        "form_type": "daily_checklist",
        "schema": {
            "sections": [
                {
                    "id": "facility",
                    "title": "Facility Cleanliness",
                    "fields": [
                        {"id": "floors_clean", "label": "Floors clean and dry?", "type": "boolean", "validation": {"required": True}},
                        {"id": "walls_clean", "label": "Walls and ceilings clean?", "type": "boolean", "validation": {"required": True}},
                        {"id": "drains_clean", "label": "Drains clean and flowing?", "type": "boolean", "validation": {"required": True}},
                        {"id": "waste_bins_empty", "label": "Waste bins emptied?", "type": "boolean", "validation": {"required": True}},
                        {"id": "no_standing_water", "label": "No standing water?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "staff_hygiene",
                    "title": "Staff Hygiene",
                    "fields": [
                        {"id": "handwash_facilities", "label": "Hand wash facilities stocked?", "type": "boolean", "validation": {"required": True}},
                        {"id": "staff_wearing_ppe", "label": "Staff wearing correct PPE?", "type": "boolean", "validation": {"required": True}},
                        {"id": "no_jewellery", "label": "No jewellery or loose clothing?", "type": "boolean", "validation": {"required": True}},
                        {"id": "illness_check", "label": "Illness/injury declarations completed?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "pest_control",
                    "title": "Pest Control",
                    "fields": [
                        {"id": "bait_stations_intact", "label": "Bait stations intact and in place?", "type": "boolean", "validation": {"required": True}},
                        {"id": "fly_killers_working", "label": "Fly killers working?", "type": "boolean", "validation": {"required": True}},
                        {"id": "no_pest_evidence", "label": "No evidence of pest activity?", "type": "boolean", "validation": {"required": True}},
                        {"id": "doors_closed", "label": "External doors kept closed?", "type": "boolean", "validation": {"required": True}},
                    ]
                }
            ],
            "scoring": {"enabled": True, "threshold": 90, "calculation": "auto"}
        },
        "form_metadata": {"frequency": "daily", "checklist_type": "hygiene"},
    },
    {
        "name": "Process Line Quality Check",
        "code": "PROCESS_CHECK",
        "description": "In-line quality check during packing operations",
        "form_type": "process_check",
        "schema": {
            "sections": [
                {
                    "id": "line_setup",
                    "title": "Line Setup",
                    "fields": [
                        {"id": "line_clean_before_start", "label": "Line cleaned before start?", "type": "boolean", "validation": {"required": True}},
                        {"id": "correct_packaging", "label": "Correct packaging materials loaded?", "type": "boolean", "validation": {"required": True}},
                        {"id": "labels_correct", "label": "Labels correct for current batch?", "type": "boolean", "validation": {"required": True}},
                        {"id": "scale_calibrated", "label": "Scale calibrated?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "product_quality",
                    "title": "Product Quality",
                    "fields": [
                        {"id": "grade_correct", "label": "Grade/class sorting correct?", "type": "boolean", "validation": {"required": True}},
                        {"id": "size_correct", "label": "Size count correct?", "type": "boolean", "validation": {"required": True}},
                        {"id": "weight_in_spec", "label": "Box weight within spec?", "type": "boolean", "validation": {"required": True}},
                        {"id": "pack_presentation", "label": "Pack presentation acceptable?", "type": "boolean", "validation": {"required": True}},
                        {"id": "defects_within_tolerance", "label": "Defects within tolerance?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "traceability",
                    "title": "Traceability",
                    "fields": [
                        {"id": "batch_code_on_box", "label": "Batch code on every box?", "type": "boolean", "validation": {"required": True}},
                        {"id": "date_code_correct", "label": "Date code correct?", "type": "boolean", "validation": {"required": True}},
                    ]
                }
            ],
            "scoring": {"enabled": True, "threshold": 90, "calculation": "auto"}
        },
        "form_metadata": {"frequency": "per_batch", "applicability": "all_products"},
    },
    {
        "name": "Final Pack Inspection",
        "code": "FINAL_INSPECTION",
        "description": "Pre-dispatch quality verification on packed pallets",
        "form_type": "final_inspection",
        "schema": {
            "sections": [
                {
                    "id": "pallet_check",
                    "title": "Pallet Verification",
                    "fields": [
                        {"id": "pallet_stable", "label": "Pallet stable and correctly stacked?", "type": "boolean", "validation": {"required": True}},
                        {"id": "strapping_secure", "label": "Strapping/wrapping secure?", "type": "boolean", "validation": {"required": True}},
                        {"id": "pallet_label_correct", "label": "Pallet label matches contents?", "type": "boolean", "validation": {"required": True}},
                        {"id": "box_count_correct", "label": "Box count matches pallet label?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "product_check",
                    "title": "Product Spot Check",
                    "fields": [
                        {"id": "random_box_quality", "label": "Random box quality acceptable?", "type": "boolean", "validation": {"required": True}},
                        {"id": "pulp_temp_ok", "label": "Pulp temperature within spec?", "type": "boolean", "validation": {"required": True}},
                        {"id": "pulp_temp_reading", "label": "Pulp temperature (°C)", "type": "number", "unit": "°C", "validation": {"required": True, "min": -5, "max": 30}},
                        {"id": "no_foreign_objects", "label": "No foreign objects detected?", "type": "boolean", "validation": {"required": True}},
                    ]
                },
                {
                    "id": "documentation",
                    "title": "Documentation",
                    "fields": [
                        {"id": "phyto_cert_ready", "label": "Phytosanitary certificate ready?", "type": "boolean", "validation": {"required": False}},
                        {"id": "export_docs_complete", "label": "Export documents complete?", "type": "boolean", "validation": {"required": False}},
                        {"id": "release_notes", "label": "Release notes / comments", "type": "text", "validation": {"max_length": 500}},
                    ]
                }
            ],
            "scoring": {"enabled": True, "threshold": 100, "calculation": "auto"}
        },
        "form_metadata": {"frequency": "per_pallet", "applicability": "all_products"},
    },
]


async def seed_templates(org_id: int):
    """Seed default form templates for an organization."""
    async with async_session_factory() as db:
        for tmpl_data in DEFAULT_TEMPLATES:
            tmpl = FormTemplate(
                organization_id=org_id,
                **tmpl_data,
            )
            db.add(tmpl)
        await db.commit()
        print(f"Seeded {len(DEFAULT_TEMPLATES)} default templates for org {org_id}")


async def seed_demo_data():
    """Seed a complete demo environment: org, packhouse, user, and templates."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Create demo organization
        org = Organization(
            name="Demo Fruit Packers",
            org_type="packhouse",
            country="South Africa",
        )
        db.add(org)
        await db.flush()

        # Create packhouse
        packhouse = Packhouse(
            organization_id=org.id,
            code="PH-DEMO-01",
            name="Main Packhouse",
            country="South Africa",
            packing_system="Automated grading + manual packing",
            crops_packed=["Mango", "Avocado", "Citrus"],
            staff_count=45,
        )
        db.add(packhouse)
        await db.flush()

        # Create pack lines
        for i in range(1, 4):
            line = PackLine(
                packhouse_id=packhouse.id,
                code=f"LINE-{i:02d}",
                name=f"Pack Line {i}",
                line_number=i,
            )
            db.add(line)

        # Create demo growers
        growers_data = [
            ("GRW-001", "Botha Farms", "Block A - Mango", "Mango"),
            ("GRW-002", "Van der Merwe Estate", "Orchard 3", "Avocado"),
            ("GRW-003", "Patel Citrus", "Grove East", "Citrus"),
        ]
        for code, name, field, crop in growers_data:
            grower = Grower(
                organization_id=org.id,
                grower_code=code,
                grower_name=name,
                field_name=field,
                crop_type=crop,
            )
            db.add(grower)

        # Create demo user
        user = User(
            name="Demo QA Manager",
            username="demo_qa",
            email="demo@fruitqms.example.com",
            password_hash=hash_password("demo1234"),
            role="qa_manager",
            organization_id=org.id,
        )
        db.add(user)

        # Seed form templates
        for tmpl_data in DEFAULT_TEMPLATES:
            tmpl = FormTemplate(
                organization_id=org.id,
                **tmpl_data,
            )
            db.add(tmpl)

        await db.commit()
        print(f"Demo environment seeded successfully!")
        print(f"  Organization: {org.name} (ID: {org.id})")
        print(f"  Packhouse: {packhouse.name} (code: {packhouse.code})")
        print(f"  User: demo@fruitqms.example.com / demo1234")
        print(f"  Templates: {len(DEFAULT_TEMPLATES)} default forms")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
