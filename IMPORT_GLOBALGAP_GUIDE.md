# Import GLOBALG.A.P. Control Points from Excel

## You Have Two Options:

### Option 1: Import Your Existing GLOBALG.A.P. Excel Document (Recommended)

If you already have a GLOBALG.A.P. Excel file with all control points:

1. **Copy your Excel file** to the FruitQMS folder:
   ```bash
   cp /path/to/your/GLOBALG.A.P.xlsx /Users/davidrieger/Desktop/FruitQMS/
   ```

2. **Run the import script**:
   ```bash
   cd /Users/davidrieger/Desktop/FruitQMS
   python3 import_globalgap.py --import your-file.xlsx
   ```

3. The script will:
   - Read all control points from your Excel file
   - Let you select which organization to import for
   - Store the complete GLOBALG.A.P. scope in the database
   - Show you a summary of what was imported

### Option 2: Generate a Template and Fill It In

If you need to create a new Excel file:

1. **Generate template with sample data**:
   ```bash
   python3 import_globalgap.py --sample
   ```

2. **Open the generated file**: `GLOBALG.A.P._Sample.xlsx`

3. **Fill in your control points** following the format

4. **Import when ready**:
   ```bash
   python3 import_globalgap.py --import GLOBALG.A.P._Sample.xlsx
   ```

---

## Expected Excel Format

Your Excel file should have these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Code** | Control point code | `AF 1.1.1` or `FV 2.3.1` |
| **Section** | Main section | `All Farm Base`, `Fruit & Vegetables` |
| **Category** | Category name | `Site Management`, `Crop Protection` |
| **Sub-Category** | Sub-category (optional) | `Site History`, `Hygiene` |
| **Control Point** | The requirement/question | `Is there a documented hygiene policy?` |
| **Compliance Criteria** | Evidence needed | `Written policy covering cleaning, personnel hygiene, pest control` |
| **Criticality** | Importance level | `Major Must`, `Minor Must`, `Recommendation` |
| **Level** | Audit level | `L1`, `L2`, `L1+L2` |
| **Applies To** | Who it applies to | `All`, `Grower`, `Packhouse`, `Mixed` |
| **Overlap Schemes** | Other standards | `GRASP, SMETA, BRC` |
| **Notes** | Additional guidance | Any notes or reminders |

---

## What Happens After Import?

Once imported, the control points will be:

1. **Stored in your organization's database**
2. **Available in Settings > GLOBALG.A.P. Checklist**
3. **Used for compliance tracking**
4. **Referenced in audit preparation**
5. **Filtered dynamically** based on your business type (from wizard)

---

## Filtering in the Wizard

When you complete the Setup Wizard (Step 5), FruitQMS will automatically filter control points based on:

- **Business Type**: Grower only, Packhouse only, or Mixed
- **Contract Growers**: Whether you work with contract growers
- **Existing Policies**: HACCP, Spray Program, Environmental, etc.
- **Operations**: Own fields, water treatment, etc.

This ensures you only see relevant control points for YOUR operation!

---

## Next Steps After Import

1. **View Control Points**: Go to Settings > GLOBALG.A.P. Checklist
2. **Mark Compliance Status**: For each control point, mark as:
   - ✅ Compliant
   - ❌ Non-compliant
   - ⚠️ N/A (not applicable)
3. **Upload Evidence**: Attach documents, photos, or records
4. **Track Progress**: See overall compliance % on dashboard map
5. **Generate Reports**: Export compliance reports for audits

---

## Tips for Your Existing GLOBALG.A.P. Document

If your Excel file has different column names, you can either:

1. **Rename columns** to match the template format
2. **Or modify the import script** (lines 150-165 in `import_globalgap.py`)

The script is flexible and can handle variations in formatting.

---

## Example Import Session

```bash
$ python3 import_globalgap.py --import MyGlobalGAP.xlsx

Using organization: Western Cape Packers

✓ Found 387 control points in Excel file
✓ Imported successfully into organization: Western Cape Packers

Summary:
  - Total control points: 387
  - Major Must: 156
  - Minor Must: 189
  - Recommendations: 42

  By Section:
    • All Farm Base: 198 points
    • Fruit & Vegetables: 189 points

✓ Import complete! Control points are now available in FruitQMS.
  Go to Settings > GLOBALG.A.P. Checklist to view and track compliance.
```

---

## Troubleshooting

**"Error: No organizations found"**
- Complete the Setup Wizard first to create an organization

**"Column not found"**
- Check that your Excel has the expected column headers in row 1

**"Invalid criticality level"**
- Ensure criticality is one of: `Major Must`, `Minor Must`, `Recommendation`

**"File not found"**
- Make sure you're in the FruitQMS directory
- Use the full path to your Excel file

---

## Ready to Import?

Just copy your GLOBALG.A.P. Excel file to the FruitQMS folder and run:

```bash
python3 import_globalgap.py --import your-file.xlsx
```

The script will guide you through the rest!
