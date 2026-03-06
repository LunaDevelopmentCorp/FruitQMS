# FruitQMS FastAPI — Quick Start

## Setup

```bash
cd fruitqms_fastapi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

## Run

```bash
# Start the server
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# Seed demo data (optional — creates demo org, packhouse, user, and form templates)
python -m scripts.seed_defaults
```

## Access

- **API Docs (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Demo login:** demo@fruitqms.example.com / demo1234

## Project Structure

```
src/
├── main.py                     # FastAPI app entry point
├── config.py                   # Environment-based configuration
├── database/engine.py          # Async SQLAlchemy engine + session
├── middleware/auth.py           # JWT auth + role-based access
├── models/
│   ├── auth.py                 # User
│   ├── organization.py         # Organization, Packhouse, PackLine, Grower
│   ├── qms_forms.py            # FormTemplate, FormSubmission (dynamic form engine)
│   ├── qms_operations.py       # IntakeInspection, ProcessCheck, FinalInspection, DailyChecklist
│   ├── qms_integrations.py     # FruitPakGRNReference (cached GRN data)
│   └── audit.py                # AuditLog
├── schemas/                    # Pydantic validation models
├── services/
│   ├── form_engine_service.py  # Form validation, scoring, conditional logic
│   ├── fruitpak_integration_service.py  # FruitPak API client + offline fallback
│   └── audit_service.py        # Audit trail helper
└── api/v1/
    ├── auth.py                 # POST /login, /register, /refresh, GET /me
    ├── organization.py         # CRUD: organizations, packhouses, pack lines, growers
    ├── qms_forms.py            # CRUD: form templates + submissions (with validation)
    ├── qms_operations.py       # CRUD: intake, process checks, final inspections, daily checklists
    └── qms_reports.py          # Dashboard stats + non-conformance reports
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/login | Login → JWT tokens |
| POST | /api/v1/auth/register | Register new user |
| GET | /api/v1/auth/me | Current user profile |
| GET/POST | /api/v1/organizations | List/create organizations |
| GET/POST | /api/v1/packhouses | List/create packhouses |
| GET/POST | /api/v1/growers | List/create growers |
| GET/POST | /api/v1/forms/templates | List/create form templates |
| POST | /api/v1/forms/submissions | Submit a completed form |
| POST | /api/v1/forms/validate | Validate form without saving |
| POST | /api/v1/qms/intake | Create intake inspection |
| POST | /api/v1/qms/process-checks | Create process check |
| POST | /api/v1/qms/final-inspections | Create final inspection |
| POST | /api/v1/qms/daily-checklists | Create daily checklist |
| GET | /api/v1/qms/reports/dashboard | Dashboard summary stats |
| GET | /api/v1/qms/reports/non-conformances | Non-conformance list |

## FruitPak Integration

Set `FRUITPAK_API_URL` in `.env` to enable. When enabled:
- Intake inspections can reference a FruitPak GRN code
- QMS validates the GRN against FruitPak's API
- GRN data is cached locally for offline resilience
- If FruitPak is unavailable, manual entry fallback is used
