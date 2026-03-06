# FruitQMS — Developer Handoff & Cleanup Instructions

**Project:** FruitQMS — Quality Management System for fruit industry certification & packhouse operations
**Owner:** David Rieger, Luna Development Corp
**Date:** 6 March 2026
**For:** Claude (VS Code developer)

---

## SITUATION

This project has TWO codebases in ONE repo that need to be cleaned up and unified:

1. **Original Flask app** (root of `/FruitQMS/`) — GLOBALG.A.P. certification tracker, setup wizard, policy generator. 4 git commits. This is the OLD code and should be treated as REFERENCE ONLY going forward.

2. **New FastAPI app** (`/FruitQMS/fruitqms_fastapi/`) — The replacement. Rebuilt from scratch in FastAPI to match FruitPak's stack. Contains both the operational QMS (active) and certification models (ported, routes deferred). Also has a React frontend. **This is NOT yet in git** — the entire `fruitqms_fastapi/` folder is untracked.

---

## CLEANUP TASKS (in order)

### Task 1: Purge stale bytecode caches

There are 218 `__pycache__` directories with 1,759 bytecode files compiled from mixed Python versions (3.10 and 3.12). Delete them all:

```bash
cd FruitQMS
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
```

### Task 2: Clean up root directory clutter

The root `/FruitQMS/` directory has leftover scripts and docs from the original build process that are no longer needed. These can be removed or moved to an `archive/` folder:

**Files to archive/remove:**
- `export_globalgap_summary.py` — one-off export script
- `import_globalgap.py` — one-off import script
- `import_official_globalgap.py` — one-off import script
- `inspect_checklist_sheets.py` — one-off inspection script
- `inspect_globalgap_file.py` — one-off inspection script
- `view_globalgap_complete.py` — one-off viewer script
- `migrate_add_applicability.py` — Flask migration script
- `seed_demo_user.py` — Flask seed script (replaced by `fruitqms_fastapi/scripts/seed_defaults.py`)
- `COMPLETE_GLOBALGAP_DISPLAY_FIXED.md` — build notes
- `GROWER_CHECKLIST_ANALYSIS.md` — build notes
- `GROWER_CHECKLIST_IMPLEMENTATION_COMPLETE.md` — build notes
- `IMPORT_GLOBALGAP_GUIDE.md` — build notes
- `SETUP_INSTRUCTIONS.md` — Flask setup (replaced by `fruitqms_fastapi/QUICKSTART.md`)
- `UPDATE_WIZARD_INSTRUCTIONS.md` — build notes
- `WIZARD_FIXES_COMPLETE.md` — build notes
- `WIZARD_SETUP_INSTRUCTIONS.md` — build notes

**Files to KEEP in root:**
- `app/` — Flask app (reference)
- `config.py` — Flask config (reference)
- `main.py` — Flask entry point (reference)
- `requirements.txt` — Flask deps (reference)
- `migrations/` — Flask DB migrations (reference)
- `babel.cfg` — Flask i18n config (reference)
- `instance/` — Flask SQLite DB
- `fruitqms_fastapi/` — **THE ACTIVE PROJECT**
- `.git/`, `.gitignore`
- GLOBALG.A.P. source data files (`.xlsx`, `.csv`)

### Task 3: Add a proper .gitignore

The current `.gitignore` likely doesn't cover the FastAPI project. Update it to include:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
venv/
.env

# Database
*.db
instance/

# IDE
.vscode/
.idea/
*.code-workspace

# Node
node_modules/
dist/

# OS
.DS_Store
Thumbs.db
```

### Task 4: Resolve Python version — use ONE version

The Flask venv uses Python 3.14, the FastAPI venv uses Python 3.12. Pick ONE and stick with it. Recommended: **Python 3.12** (stable, well-supported by all dependencies).

```bash
# Delete both old venvs
rm -rf FruitQMS/venv FruitQMS/fruitqms_fastapi/venv

# Create a fresh venv for FastAPI only
cd FruitQMS/fruitqms_fastapi
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Task 5: Test the FastAPI backend

```bash
cd FruitQMS/fruitqms_fastapi
source venv/bin/activate

# Seed demo data
python -m scripts.seed_defaults

# Start the server
uvicorn src.main:app --reload --port 8000
```

Verify at `http://localhost:8000/docs` — you should see all endpoints in Swagger UI.

Test login: `demo@fruitqms.local` / `demo1234`

### Task 6: Install and test the React frontend

```bash
cd FruitQMS/fruitqms_fastapi/frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. The Vite proxy forwards `/api` calls to port 8000.

### Task 7: Commit the FastAPI project to git

Once everything runs clean:

```bash
cd FruitQMS
git add fruitqms_fastapi/
git commit -m "Add FastAPI rebuild with React frontend

- FastAPI backend: 38 Python files covering auth, org management,
  QMS operations (intake/process/final/daily), dynamic form engine,
  FruitPak API integration, i18n (5 languages), audit logging,
  and GLOBALG.A.P. certification models (routes deferred to Phase 2)
- React frontend: Vite + Tailwind, 11 pages covering all endpoints
- Seed script with demo data and 5 default form templates"
```

---

## FASTAPI PROJECT STRUCTURE

```
fruitqms_fastapi/
├── src/
│   ├── main.py                          # App entry, router registration, table creation
│   ├── config.py                        # Pydantic Settings (DB, JWT, CORS, FruitPak)
│   ├── database/engine.py               # Async SQLAlchemy 2.0 engine + session
│   ├── models/
│   │   ├── base.py                      # DeclarativeBase + TimestampMixin
│   │   ├── auth.py                      # User (with language field)
│   │   ├── organization.py              # Organization, Packhouse, PackLine, Grower
│   │   ├── qms_forms.py                 # FormTemplate (JSON schema), FormSubmission (JSONB)
│   │   ├── qms_operations.py            # IntakeInspection, ProcessCheck, FinalInspection, DailyChecklist
│   │   ├── qms_integrations.py          # FruitPakGRNReference (cached GRN data)
│   │   ├── standards.py                 # ControlPoint, SetupWizard, GrowerControlPoint, Notification
│   │   └── audit.py                     # AuditLog with JSONB details
│   ├── schemas/
│   │   ├── auth.py                      # Login, Register, Token, UserOut
│   │   ├── organization.py              # Org, Packhouse, PackLine, Grower (Create/Update/Out)
│   │   ├── qms_forms.py                 # FormTemplate, FormSubmission, ValidationResult
│   │   └── qms_operations.py            # Intake, ProcessCheck, FinalInspection, DailyChecklist
│   ├── middleware/auth.py               # JWT create/validate, password hashing, role guards
│   ├── services/
│   │   ├── form_engine_service.py       # Schema validation, conditional logic, auto-scoring
│   │   ├── fruitpak_integration_service.py  # Async httpx client to FruitPak API
│   │   ├── i18n_service.py              # Language detection, translation store (5 languages)
│   │   ├── audit_service.py             # log_action() helper
│   │   ├── globalgap_master_data.py     # 82 GLOBALG.A.P. IFA v6.0 control points
│   │   └── policy_generator.py          # Stubs for 7 policy types (Phase 2)
│   └── api/v1/
│       ├── auth.py                      # POST login/register/refresh, GET me
│       ├── organization.py              # CRUD orgs, packhouses, pack lines, growers
│       ├── qms_forms.py                 # CRUD templates, submit/validate forms
│       ├── qms_operations.py            # CRUD intake, process, final, daily
│       ├── qms_reports.py               # GET dashboard, non-conformances
│       └── i18n.py                      # GET languages, GET/PATCH user language, GET translations
├── scripts/seed_defaults.py             # Demo org, packhouse, 3 growers, 5 form templates
├── frontend/                            # React SPA (Vite + Tailwind)
│   ├── src/
│   │   ├── api.js                       # Fetch wrapper with JWT interceptor
│   │   ├── AuthContext.jsx              # React context for auth state
│   │   ├── App.jsx                      # Router setup
│   │   ├── components/
│   │   │   ├── Layout.jsx               # Sidebar + main content
│   │   │   ├── Sidebar.jsx              # Navigation links
│   │   │   ├── ProtectedRoute.jsx       # Auth guard
│   │   │   └── DynamicForm.jsx          # Renders forms from JSON schema
│   │   └── pages/                       # 11 pages (login, register, dashboard, org,
│   │       └── ...                      #   intake, process, final, daily, forms, submit, settings)
│   ├── package.json
│   └── vite.config.js                   # Proxy /api → localhost:8000
├── requirements.txt
├── .env.example
└── QUICKSTART.md
```

---

## KNOWN ISSUES TO FIX

1. **Missing schemas for standards models** — `src/schemas/` has no Pydantic schemas for ControlPoint, SetupWizard, GrowerControlPoint, Notification. These are needed when Phase 2 routes are activated. Low priority for now.

2. **Circular import risk** — `qms_operations.py` and `qms_forms.py` reference each other via relationships. Currently handled with `TYPE_CHECKING` guards and string-based relationship references. If you see import errors, check these guards first.

3. **`fruitqms.db` may exist from a previous test run** — Delete it and re-run seed script for a clean start: `rm fruitqms.db && python -m scripts.seed_defaults`

4. **Frontend has no `node_modules/`** — Must run `npm install` before `npm run dev`.

---

## WHAT'S WORKING vs DEFERRED

**WORKING (Phase 1 — Operational QMS):**
- Full auth flow (JWT with refresh)
- Organization/Packhouse/PackLine/Grower CRUD
- All 4 QMS operation types with status workflows
- Dynamic form engine (JSON schema → rendered form with scoring)
- 5 seeded form templates (intake, cold chain, hygiene, process, final)
- FruitPak integration service (async, with offline fallback)
- Dashboard reporting (counts + pass rates)
- i18n (5 languages, user preference, org defaults)
- Audit logging
- React frontend covering all endpoints

**DEFERRED (Phase 2 — Certification & Standards):**
- ControlPoint / SetupWizard routes (models exist, no endpoints)
- GLOBALG.A.P. applicability analysis service
- Policy document PDF generation (stubs exist)
- Setup wizard frontend
- Multi-tenancy (schema-per-tenant like FruitPak)
- Alembic migrations (using create_all for now)
- Docker/deployment config
- Test suite

---

## FRUITPAK INTEGRATION

FruitQMS is designed to call FruitPak's API for GRN (Goods Received Note) data. The integration service is at `src/services/fruitpak_integration_service.py`.

To configure, set in `.env`:
```
FRUITPAK_API_URL=https://your-fruitpak-instance/api/v1
FRUITPAK_API_KEY=your-api-key
```

If FruitPak is unavailable, the system falls back to manual entry — the intake form accepts direct batch_code, grower, and crop input without requiring a FruitPak GRN reference.
