from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, Response
from flask_login import login_required, current_user
from app import db
from app.models import Organization, Grower, ControlPoint, GrowerControlPoint
from app.forms import PackhouseSetupForm, GrowerSetupForm
import csv
import io
from datetime import datetime

setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

@setup_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.role not in ['qa_manager', 'auditor']:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Get or create organization
    organization = current_user.organization
    if not organization:
        organization = Organization(
            name='My Organization',
            org_type='packhouse'
        )
        db.session.add(organization)
        db.session.commit()
        current_user.organization_id = organization.id
        db.session.commit()

    packhouse_form = PackhouseSetupForm(obj=organization)
    grower_form = GrowerSetupForm()

    # Handle packhouse form submission
    if request.method == 'POST' and 'packhouse_submit' in request.form:
        if packhouse_form.validate():
            packhouse_form.populate_obj(organization)
            db.session.commit()
            flash('Packhouse settings updated successfully!', 'success')
            return redirect(url_for('setup.settings'))

    # Handle grower form submission
    if request.method == 'POST' and 'grower_submit' in request.form:
        if grower_form.validate():
            grower = Grower(organization_id=organization.id)
            grower_form.populate_obj(grower)
            db.session.add(grower)
            db.session.commit()
            flash('Grower/field added successfully!', 'success')
            return redirect(url_for('setup.settings'))

    # Get existing growers
    growers = Grower.query.filter_by(organization_id=organization.id).all()

    # Get REAL GLOBALG.A.P. control points from database
    control_points = get_globalgap_control_points_from_db(organization.id)

    return render_template('setup/settings.html',
                         packhouse_form=packhouse_form,
                         grower_form=grower_form,
                         growers=growers,
                         control_points=control_points)


def get_globalgap_control_points_from_db(organization_id):
    """Load all imported GLOBALG.A.P. control points from database"""

    # Get all control points for this organization
    all_control_points = ControlPoint.query.filter_by(
        organization_id=organization_id
    ).order_by(ControlPoint.code).all()

    if not all_control_points:
        # Return empty structure if no control points imported yet
        return {
            'No Control Points': {
                'Import Required': [
                    {
                        'code': 'N/A',
                        'description': 'No control points found. Run: python3 import_official_globalgap.py',
                        'criticality': 'N/A',
                        'overlap': None,
                        'compliance_criteria': 'Import the official GLOBALG.A.P. checklist first',
                        'notes': '',
                        'compliance_status': 'N/A'
                    }
                ]
            }
        }

    # Group by category (which contains the section information)
    grouped = {}
    for cp in all_control_points:
        # Extract section from description (format: "FV 01 SECTION_NAME - control point text")
        section = cp.category  # This is "Fruit & Vegetables"

        # Extract actual section from description
        desc_parts = cp.description.split(' - ')
        if len(desc_parts) >= 2:
            section_name = desc_parts[0].strip()  # e.g., "FV 01 INTERNAL DOCUMENTATION"
        else:
            section_name = "Other"

        if section_name not in grouped:
            grouped[section_name] = []

        # Extract compliance criteria from notes
        compliance_criteria = cp.notes.replace('Compliance Criteria: ', '') if cp.notes else ''

        # Extract just the control point text (after the section name)
        control_point_text = ' - '.join(desc_parts[1:]) if len(desc_parts) >= 2 else cp.description

        grouped[section_name].append({
            'id': cp.id,
            'code': cp.code,
            'description': control_point_text,
            'compliance_criteria': compliance_criteria,
            'criticality': cp.criticality,
            'overlap': cp.overlap_hint,
            'compliance_status': cp.compliance_status or 'N/A',
            'evidence_file': cp.evidence_file,
            'notes_field': cp.notes
        })

    # Convert to nested structure for template
    result = {}
    for section_name, points in sorted(grouped.items()):
        result[section_name] = {
            'Control Points': points
        }

    return result


@setup_bp.route('/download-grower-checklist-template', methods=['GET'])
@login_required
def download_grower_checklist_template():
    """Download CSV template for grower checklists"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash('No organization found.', 'danger')
        return redirect(url_for('setup.settings'))

    # Get all grower-applicable control points (sections FV 26, 28, 29, 30, 31, 32)
    grower_sections = ['FV 26', 'FV 28', 'FV 29', 'FV 30', 'FV 31', 'FV 32']

    control_points = ControlPoint.query.filter_by(
        organization_id=organization.id
    ).filter(
        db.or_(*[ControlPoint.description.like(f'{section}%') for section in grower_sections])
    ).order_by(ControlPoint.code).all()

    # Get all growers
    growers = Grower.query.filter_by(organization_id=organization.id).all()

    if not growers:
        flash('No growers found. Please add growers first.', 'warning')
        return redirect(url_for('setup.settings'))

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'Grower_Code',
        'Grower_Name',
        'Control_Point_Code',
        'Control_Point_Section',
        'Control_Point_Description',
        'Compliance_Criteria',
        'Criticality',
        'Compliance_Status',
        'Evidence_Filename',
        'Implementation_Notes',
        'Common_Response',
        'Last_Updated'
    ])

    # Write rows for each grower and control point combination
    for grower in growers:
        for cp in control_points:
            # Extract section name from description
            desc_parts = cp.description.split(' - ')
            section_name = desc_parts[0].strip() if desc_parts else ''
            control_point_text = ' - '.join(desc_parts[1:]) if len(desc_parts) > 1 else cp.description

            # Extract compliance criteria from notes
            compliance_criteria = cp.notes.replace('Compliance Criteria: ', '') if cp.notes else ''

            # Check if grower already has this control point filled in
            existing = GrowerControlPoint.query.filter_by(
                grower_id=grower.id,
                control_point_id=cp.id
            ).first()

            if existing:
                writer.writerow([
                    grower.grower_code,
                    grower.grower_name,
                    cp.code,
                    section_name,
                    control_point_text,
                    compliance_criteria,
                    cp.criticality,
                    existing.compliance_status or 'N/A',
                    existing.evidence_file or '',
                    existing.implementation_notes or '',
                    'YES' if existing.is_common_response else 'NO',
                    existing.updated_at.strftime('%Y-%m-%d') if existing.updated_at else ''
                ])
            else:
                # Empty row for new entry
                writer.writerow([
                    grower.grower_code,
                    grower.grower_name,
                    cp.code,
                    section_name,
                    control_point_text,
                    compliance_criteria,
                    cp.criticality,
                    'N/A',  # Default status
                    '',
                    '',
                    'NO',  # Default to not common
                    datetime.now().strftime('%Y-%m-%d')
                ])

    # Prepare response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=Grower_Checklist_Template_{organization.name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@setup_bp.route('/upload-grower-checklist', methods=['POST'])
@login_required
def upload_grower_checklist():
    """Upload and process CSV file with grower checklists"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash('No organization found.', 'danger')
        return redirect(url_for('setup.settings'))

    # Check if file was uploaded
    if 'csv_file' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('setup.settings'))

    file = request.files['csv_file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('setup.settings'))

    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file.', 'danger')
        return redirect(url_for('setup.settings'))

    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        csv_reader = csv.DictReader(stream)

        records_processed = 0
        records_created = 0
        records_updated = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            try:
                # Get grower by code
                grower = Grower.query.filter_by(
                    organization_id=organization.id,
                    grower_code=row['Grower_Code'].strip()
                ).first()

                if not grower:
                    errors.append(f"Row {row_num}: Grower '{row['Grower_Code']}' not found.")
                    continue

                # Get control point by code
                control_point = ControlPoint.query.filter_by(
                    organization_id=organization.id,
                    code=row['Control_Point_Code'].strip()
                ).first()

                if not control_point:
                    errors.append(f"Row {row_num}: Control point '{row['Control_Point_Code']}' not found.")
                    continue

                # Check if record exists
                grower_cp = GrowerControlPoint.query.filter_by(
                    grower_id=grower.id,
                    control_point_id=control_point.id
                ).first()

                # Parse common response
                is_common = row.get('Common_Response', 'NO').strip().upper() == 'YES'

                if grower_cp:
                    # Update existing record
                    grower_cp.compliance_status = row.get('Compliance_Status', 'N/A').strip()
                    grower_cp.evidence_file = row.get('Evidence_Filename', '').strip()
                    grower_cp.implementation_notes = row.get('Implementation_Notes', '').strip()
                    grower_cp.is_common_response = is_common
                    grower_cp.updated_at = datetime.now()
                    records_updated += 1
                else:
                    # Create new record
                    grower_cp = GrowerControlPoint(
                        grower_id=grower.id,
                        control_point_id=control_point.id,
                        compliance_status=row.get('Compliance_Status', 'N/A').strip(),
                        evidence_file=row.get('Evidence_Filename', '').strip(),
                        implementation_notes=row.get('Implementation_Notes', '').strip(),
                        is_common_response=is_common
                    )
                    db.session.add(grower_cp)
                    records_created += 1

                records_processed += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue

        # Commit all changes
        db.session.commit()

        # Provide feedback
        if errors:
            flash(f'Processed {records_processed} records ({records_created} created, {records_updated} updated). {len(errors)} errors occurred.', 'warning')
            for error in errors[:5]:  # Show first 5 errors
                flash(error, 'danger')
            if len(errors) > 5:
                flash(f'... and {len(errors) - 5} more errors.', 'danger')
        else:
            flash(f'Successfully processed {records_processed} records! ({records_created} created, {records_updated} updated)', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing CSV file: {str(e)}', 'danger')

    return redirect(url_for('setup.settings'))
