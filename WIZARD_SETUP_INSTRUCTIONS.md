# FruitQMS Setup Wizard - Installation Instructions

## Step-by-Step Setup

### 1. Stop Flask if running
Press `Ctrl+C` in your terminal.

### 2. Install new dependency (reportlab for PDF generation)
```bash
pip3 install reportlab==4.0.7
```

### 3. Run database migrations
```bash
python3 -m flask db migrate -m "Add SetupWizard model"
python3 -m flask db upgrade
```

### 4. Restart Flask
```bash
python3 main.py
```

### 5. Access the Setup Wizard
Go to: `http://127.0.0.1:5000/wizard/start`

Or from the Dashboard, add a link to start the wizard.

---

## Wizard Flow (7 Steps)

### Step 1: Business Type
- Select: Packhouse Only, Grower/Farm Only, or Both
- Enter GGN Number (optional)

### Step 2: Packhouse Details (skipped if Grower Only)
- Packhouse name, address, country
- Packing system type
- Crops packed (multi-select checkboxes)
- Water/energy usage, staff count

### Step 3: Grower/Field Details
- Own fields checkbox
- Total farm size (hectares)
- Number of fields
- Main crops grown (multi-select)
- Irrigation types (multi-select)

### Step 4: Environment & Compliance
- Existing policies checkboxes:
  - Environmental policy
  - HACCP plan
  - Spray/IPM program
  - Waste management plan
- Water treatment method
- Local regulations notes

### Step 5: GLOBALG.A.P. Analysis
- Automatic analysis of applicable control points
- Shows:
  - Applicable control points (green)
  - Review required (orange)
  - Not applicable (gray)
- Each point shows code, criticality, description, reason for applicability

### Step 6: Policy Generation
- Lists policies you need based on Step 4 answers
- Click to download PDF templates:
  - HACCP Plan (if missing)
  - Spray/IPM Program (if missing)
  - Environmental Policy (if missing)
  - Waste Management Plan (if missing)
  - Worker Training Log
  - Traceability Template
- Each PDF is pre-filled with relevant data from wizard

### Step 7: Review & Complete
- Shows summary of all entered data
- Displays compliance status
- Click "Complete Setup" to:
  - Create Organization in database
  - Link organization to current user
  - Mark wizard as completed
  - Redirect to dashboard

---

## Files Created

**Models:**
- `app/models.py` - Added `SetupWizard` model

**Forms:**
- `app/forms_wizard.py` - Step 1-4 forms with multi-select checkboxes

**Routes:**
- `app/routes/wizard.py` - All 7 wizard steps + policy generation

**Utilities:**
- `app/utils/__init__.py`
- `app/utils/policy_generator.py` - PDF generation using reportlab

**Templates:**
- `app/templates/wizard/wizard.html` - Main wizard template with progress bar
- `app/templates/wizard/step5_analysis.html` - GLOBALG.A.P. analysis display
- `app/templates/wizard/step6_policies.html` - Policy download cards
- `app/templates/wizard/step7_review.html` - Final review page

**Updated Files:**
- `app/__init__.py` - Registered wizard blueprint
- `requirements.txt` - Added reportlab==4.0.7

---

## Testing the Wizard

1. **Login:** `demo@fruitqms.com` / `demo123`

2. **Start wizard:** Go to `/wizard/start`

3. **Test Step 1:** Select "Packhouse + Own Farms", enter GGN

4. **Test Step 2:** Fill packhouse details, select multiple crops

5. **Test Step 3:** Check "own fields", enter farm details

6. **Test Step 4:** Leave some policies unchecked to see policy generation

7. **Test Step 5:** View analysis - see which control points apply

8. **Test Step 6:** Download a PDF policy template (e.g., HACCP)

9. **Test Step 7:** Review summary and click "Complete Setup"

10. **Verify:** Check that Organization was created and linked to user

---

## Key Features

✅ **Multi-step wizard** with Bootstrap 5 progress bar
✅ **Conditional logic** - Skip packhouse step if grower only
✅ **Multi-select checkboxes** for crops and irrigation types
✅ **GLOBALG.A.P. analysis** - Determines applicable control points based on business type
✅ **Smart policy detection** - Only suggests missing policies
✅ **PDF generation** - ReportLab creates formatted policy templates
✅ **Pre-filled templates** - Uses wizard data in generated PDFs
✅ **Complete tables** - HACCP CCPs, spray records, training logs
✅ **Organization creation** - Automatically creates and links org on completion
✅ **Data persistence** - Wizard saves progress, can be resumed

---

## Customization

**Add more control points to analysis:**
- Edit `determine_applicability()` in `wizard.py`
- Add logic for specific control point codes

**Add new policy templates:**
- Add policy type to `determine_policies_needed()`
- Add generation function in `policy_generator.py`

**Modify PDF styling:**
- Edit ReportLab styles in `policy_generator.py`
- Change colors, fonts, table layouts

---

## Troubleshooting

**ImportError: No module named 'reportlab'**
```bash
pip3 install reportlab==4.0.7
```

**Table 'setup_wizards' doesn't exist**
```bash
python3 -m flask db upgrade
```

**PDF not downloading**
- Check `instance/uploads/policies/` folder exists
- Ensure write permissions

**Wizard shows old data**
- Wizard loads incomplete wizard for current user
- To start fresh: Delete wizard record or complete existing one

---

## Next Steps

Once wizard is working:
1. Add "Start Setup Wizard" button to dashboard
2. Link from login page for first-time users
3. Add ability to edit wizard data after completion
4. Create report showing wizard completion stats
5. Add email notification when wizard completed
6. Generate certificate of completion

---

**Test and confirm wizard works end-to-end, then reply ready for next phase!**
