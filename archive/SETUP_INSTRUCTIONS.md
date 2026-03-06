# FruitQMS - Authentication & Setup Layer Installation

## Step-by-Step Instructions

### 1. Stop the running Flask app

Press `Ctrl+C` in your terminal to stop the current Flask server.

### 2. Apply database migrations

Run these commands to update your database with new models:

```bash
python3 -m flask db migrate -m "Add authentication and setup models"
python3 -m flask db upgrade
```

### 3. Seed the demo user

Run the seeding script to create a demo user account:

```bash
python3 seed_demo_user.py
```

You should see:
```
✓ Demo user created successfully!
Email: demo@qms.local
Password: demo123
Role: QA Manager
```

### 4. Restart the Flask app

```bash
python3 main.py
```

### 5. Test the application

Open your browser and go to: `http://127.0.0.1:5000`

#### Test Login
1. Click "Login to Get Started" or go to `http://127.0.0.1:5000/login`
2. Use these credentials:
   - **Email:** demo@qms.local
   - **Password:** demo123
3. You should be redirected to the Dashboard

#### Test Dashboard
- View the welcome page with role badge
- Click "Go to Settings" to access setup pages

#### Test Settings Page
Navigate to Settings and explore three tabs:

**Tab 1: Packhouse Setup**
- Fill in address (required) and country (required)
- Add operational details (water usage, staff count, etc.)
- Add protocols and file uploads
- Click "Save Packhouse Settings"

**Tab 2: Growers & Fields**
- Add a grower with:
  - Grower Code: GR001
  - Grower Name: Demo Grower
  - Field Name: Field A
  - Crop Type: Apples
- Click "Add Grower/Field"
- See the grower appear in the table below

**Tab 3: GLOBALG.A.P. IFA v6.0**
- Expand accordions to view control points
- See criticality badges:
  - Red = Major Must (suspension risk)
  - Orange = Minor Must
  - Green = Recommendation
- Notice "Overlap" badges with tooltips showing scheme connections
- Each control point has fields for:
  - Compliance status dropdown
  - Evidence file upload
  - Notes textarea

### 6. Test Logout

Click your name in the navbar → Logout

---

## What Was Added

### New Files Created:
- `app/forms.py` - FlaskForm classes for login, packhouse, and grower setup
- `app/routes/auth.py` - Login/logout routes
- `app/routes/dashboard.py` - Protected dashboard route
- `app/routes/setup.py` - Settings page with packhouse/grower/GLOBALG.A.P. sections
- `app/templates/auth/login.html` - Login form
- `app/templates/dashboard/index.html` - Dashboard with quick links
- `app/templates/setup/settings.html` - Tabbed settings interface with accordions
- `seed_demo_user.py` - Script to create demo user

### Files Updated:
- `app/__init__.py` - Added blueprint registration and CSRF protection
- `app/models.py` - Added User methods, Organization fields, Grower model, ControlPoint model
- `app/templates/base.html` - Added authentication-aware navbar, Bootstrap Icons, criticality badges
- `app/templates/index.html` - Added authentication-aware home page

### Database Models Added:
- **User:** name, role (qa_manager/auditor/viewer), password hashing
- **Organization:** Extended with packhouse fields (address, water usage, staff count, protocols, etc.)
- **Grower:** grower_code, grower_name, field details, crop info, conservation measures
- **ControlPoint:** GLOBALG.A.P. control points with compliance tracking

### Features Implemented:
✅ User authentication with Flask-Login
✅ Password hashing with werkzeug.security
✅ Role-based access control (QA Manager full access, others view-only)
✅ Packhouse setup form with all required fields
✅ Grower/field repeatable form
✅ GLOBALG.A.P. IFA v6.0 checklist with accordion structure
✅ Control point criticality badges (Major Must, Minor Must, Recommendation)
✅ Scheme overlap hints ("Overlaps with GRASP & SMETA")
✅ CSV upload buttons (placeholders for next phase)
✅ Paper-to-digital transition notes
✅ Bootstrap 5 responsive design
✅ Flash messages for user feedback
✅ Mobile-responsive layout

---

## Troubleshooting

### If you get "Table already exists" errors:
```bash
rm instance/qms_local.db
python3 -m flask db upgrade
python3 seed_demo_user.py
```

### If login doesn't work:
- Check that demo user was created: `python3 seed_demo_user.py`
- Check CSRF protection is enabled in `app/__init__.py`

### If you see template errors:
- Ensure `app/templates/auth/`, `app/templates/dashboard/`, and `app/templates/setup/` folders exist
- All template files should be inside `app/templates/`, not root `templates/`

---

## Next Steps (Reply when ready)

Once you confirm:
- ✅ Login works with demo@qms.local / demo123
- ✅ Dashboard displays with role badge
- ✅ Settings page shows all three tabs
- ✅ Packhouse form saves successfully
- ✅ Grower form adds entries to table
- ✅ GLOBALG.A.P. accordion shows control points with criticality badges

Reply with your confirmation, and we'll add:
1. CSV upload/download logic (pandas integration)
2. File upload handling for HACCP plans and evidence
3. Compliance status saving for control points
4. Scheme overlap dashboard
5. Audit trail logging
