# Update Setup Wizard - Contract Growers Option

## Changes Made

Added more business type options to Step 1 of the setup wizard:

**New Options:**
1. **Grower/Farm Only** (no packhouse)
2. **Packhouse Only** (contract growers only) ← NEW
3. **Packhouse + Own Farms**
4. **Packhouse + Own Farms + Contract Growers** ← NEW

**New Fields:**
- "Do you work with contract growers?" checkbox
- "Number of Contract Growers" field

---

## Installation Commands

**1. Stop Flask (Ctrl+C if running)**

**2. Run database migration:**
```bash
python3 -m flask db migrate -m "Add contract grower fields to wizard"
python3 -m flask db upgrade
```

**3. Restart Flask:**
```bash
python3 main.py
```

**4. Test:**
- Go to: `http://127.0.0.1:5000/wizard/start`
- See new business type options in Step 1
- Check the "contract growers" checkbox
- Enter number of contract growers
- Complete wizard and see info in Step 7 review

---

## What Was Updated

**Files Modified:**
- `app/forms_wizard.py` - Updated Step1 form with new business types and contract grower fields
- `app/models.py` - Added `has_contract_growers` and `number_of_contract_growers` columns
- `app/routes/wizard.py` - Updated step1 to save contract grower data
- `app/templates/wizard/step7_review.html` - Shows contract grower info in review

**New Business Types:**
- `grower` - Grower/Farm Only (no packhouse)
- `packhouse_only` - Packhouse with contract growers only
- `packhouse_own_farms` - Packhouse with own farms
- `packhouse_mixed` - Packhouse with both own farms and contract growers

---

## Usage

**Example 1: Packhouse with contract growers only**
- Select "Packhouse Only (contract growers only)"
- Check "Do you work with contract growers?"
- Enter number: 25
- Continue through wizard

**Example 2: Mixed operation**
- Select "Packhouse + Own Farms + Contract Growers"
- Check "contract growers" checkbox
- Enter number: 15
- Fill in own farm details in Step 3
- Continue through wizard

---

**Run the migration command and test the wizard!**
