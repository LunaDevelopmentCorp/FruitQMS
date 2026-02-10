from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, jsonify, current_app, send_file
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.models import Organization, Grower, ControlPoint, GrowerControlPoint, AuditLog, SetupWizard
from app.forms import PackhouseSetupForm, GrowerSetupForm
import csv
import io
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

ALLOWED_EVIDENCE_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'xls', 'xlsx'}


def allowed_evidence_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EVIDENCE_EXTENSIONS


def log_audit(action, entity_type, entity_id, field_changed=None, old_value=None, new_value=None, details=None):
    """Helper to create audit log entries"""
    entry = AuditLog(
        user_id=current_user.id,
        organization_id=current_user.organization_id or 0,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        field_changed=field_changed,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        details=details
    )
    db.session.add(entry)


@setup_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('You do not have permission to access this page.'), 'danger')
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
            log_audit('update_settings', 'organization', organization.id, details='Packhouse settings updated')
            db.session.commit()
            flash(_('Packhouse settings updated successfully!'), 'success')
            return redirect(url_for('setup.settings'))

    # Handle grower form submission
    if request.method == 'POST' and 'grower_submit' in request.form:
        if grower_form.validate():
            grower = Grower(organization_id=organization.id)
            grower_form.populate_obj(grower)
            db.session.add(grower)
            db.session.commit()
            log_audit('create', 'grower', grower.id, details=f'Added grower {grower.grower_code}')
            db.session.commit()
            flash(_('Grower/field added successfully!'), 'success')
            return redirect(url_for('setup.settings'))

    # Get existing growers
    growers = Grower.query.filter_by(organization_id=organization.id).all()

    # Get GLOBALG.A.P. control points grouped by section
    control_points = get_globalgap_control_points_from_db(organization.id)

    # Get uploaded/generated policies for the Policies tab
    policies_info = get_organization_policies(organization.id)

    # Compliance summary stats
    stats = get_compliance_stats(organization.id)

    return render_template('setup/settings.html',
                         packhouse_form=packhouse_form,
                         grower_form=grower_form,
                         growers=growers,
                         control_points=control_points,
                         policies_info=policies_info,
                         stats=stats,
                         organization=organization)


# ============================================================
# COMPLIANCE WORKFLOW: Save control point status/notes via AJAX
# ============================================================

@setup_bp.route('/save-control-point', methods=['POST'])
@login_required
def save_control_point():
    """Save compliance status and notes for a control point (AJAX)"""
    if current_user.role not in ['qa_manager', 'auditor']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    if not data or 'cp_id' not in data:
        return jsonify({'error': 'Missing control point ID'}), 400

    cp = ControlPoint.query.get(data['cp_id'])
    if not cp or cp.organization_id != current_user.organization_id:
        return jsonify({'error': 'Control point not found'}), 404

    old_status = cp.compliance_status
    old_notes = cp.notes

    if 'compliance_status' in data:
        cp.compliance_status = data['compliance_status']
    if 'notes' in data:
        cp.notes = data['notes']

    cp.updated_at = datetime.utcnow()
    db.session.commit()

    # Audit log
    if old_status != cp.compliance_status:
        log_audit('update_compliance', 'control_point', cp.id,
                  field_changed='compliance_status',
                  old_value=old_status, new_value=cp.compliance_status)
    if old_notes != cp.notes:
        log_audit('update_notes', 'control_point', cp.id,
                  field_changed='notes',
                  old_value=old_notes[:100] if old_notes else None,
                  new_value=cp.notes[:100] if cp.notes else None)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Control point updated'})


# ============================================================
# TOGGLE APPLICABILITY (AJAX)
# ============================================================

@setup_bp.route('/toggle-applicability/<int:cp_id>', methods=['POST'])
@login_required
def toggle_applicability(cp_id):
    """Toggle is_applicable flag on a control point"""
    if current_user.role not in ['qa_manager', 'auditor']:
        return jsonify({'error': 'Permission denied'}), 403

    cp = ControlPoint.query.get(cp_id)
    if not cp or cp.organization_id != current_user.organization_id:
        return jsonify({'error': 'Control point not found'}), 404

    old_val = cp.is_applicable
    cp.is_applicable = not cp.is_applicable
    cp.applicability_reason = 'Manually toggled by user'
    cp.updated_at = datetime.utcnow()
    db.session.commit()

    log_audit('toggle_applicability', 'control_point', cp.id,
              field_changed='is_applicable',
              old_value=str(old_val), new_value=str(cp.is_applicable))
    db.session.commit()

    return jsonify({
        'success': True,
        'is_applicable': cp.is_applicable,
        'message': f'Control point {cp.code} {"enabled" if cp.is_applicable else "disabled"}'
    })


# ============================================================
# REFRESH APPLICABILITY (re-run wizard analysis on existing CPs)
# ============================================================

@setup_bp.route('/refresh-applicability', methods=['POST'])
@login_required
def refresh_applicability():
    """Re-run applicability analysis based on the latest wizard data."""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('setup.settings'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    # Find the most recent completed wizard for this user
    wizard = SetupWizard.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).order_by(SetupWizard.completed_at.desc()).first()

    if not wizard:
        flash(_('No completed setup wizard found. Please complete the setup wizard first.'), 'warning')
        return redirect(url_for('setup.settings'))

    from app.routes.wizard import determine_applicability_simple, GLOBALGAP_MASTER_POINTS

    # Build a lookup from master points
    master_lookup = {mp['code']: mp for mp in GLOBALGAP_MASTER_POINTS}

    control_points = ControlPoint.query.filter_by(organization_id=organization.id).all()
    updated = 0
    for cp in control_points:
        mp = master_lookup.get(cp.code)
        if mp:
            new_applicable = determine_applicability_simple(wizard, mp)
            if cp.is_applicable != new_applicable:
                cp.is_applicable = new_applicable
                cp.applicability_reason = 'Refreshed from wizard data'
                cp.updated_at = datetime.utcnow()
                updated += 1

    db.session.commit()
    log_audit('refresh_applicability', 'organization', organization.id,
              details=f'Applicability refreshed: {updated} control points updated')
    db.session.commit()

    flash(_('Applicability refreshed! %(count)d control points updated.', count=updated), 'success')
    return redirect(url_for('setup.settings') + '#globalgap')


# ============================================================
# EVIDENCE FILE UPLOADS
# ============================================================

@setup_bp.route('/upload-evidence/<int:cp_id>', methods=['POST'])
@login_required
def upload_evidence(cp_id):
    """Upload evidence file for a control point"""
    if current_user.role not in ['qa_manager', 'auditor']:
        return jsonify({'error': 'Permission denied'}), 403

    cp = ControlPoint.query.get(cp_id)
    if not cp or cp.organization_id != current_user.organization_id:
        return jsonify({'error': 'Control point not found'}), 404

    if 'evidence_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['evidence_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_evidence_file(file.filename):
        return jsonify({'error': 'File type not allowed. Use PDF, DOC, DOCX, JPG, PNG, XLS, XLSX'}), 400

    # Save file
    evidence_dir = os.path.join(current_app.instance_path, 'uploads', 'evidence')
    os.makedirs(evidence_dir, exist_ok=True)

    filename = secure_filename(f"cp_{cp.code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
    filepath = os.path.join(evidence_dir, filename)
    file.save(filepath)

    old_file = cp.evidence_file
    cp.evidence_file = filename
    cp.updated_at = datetime.utcnow()
    db.session.commit()

    log_audit('upload_evidence', 'control_point', cp.id,
              field_changed='evidence_file',
              old_value=old_file, new_value=filename)
    db.session.commit()

    return jsonify({'success': True, 'filename': filename})


@setup_bp.route('/download-evidence/<int:cp_id>')
@login_required
def download_evidence(cp_id):
    """Download evidence file for a control point"""
    cp = ControlPoint.query.get(cp_id)
    if not cp or cp.organization_id != current_user.organization_id:
        flash(_('Control point not found.'), 'danger')
        return redirect(url_for('setup.settings'))

    if not cp.evidence_file:
        flash(_('No evidence file available.'), 'warning')
        return redirect(url_for('setup.settings'))

    filepath = os.path.join(current_app.instance_path, 'uploads', 'evidence', cp.evidence_file)
    if not os.path.exists(filepath):
        flash(_('Evidence file not found on server.'), 'danger')
        return redirect(url_for('setup.settings'))

    return send_file(filepath, as_attachment=True, download_name=cp.evidence_file)


# ============================================================
# POLICY GENERATION & DOWNLOAD FROM SETTINGS
# ============================================================

@setup_bp.route('/generate-policy/<policy_type>')
@login_required
def generate_policy(policy_type):
    """Generate & download a policy PDF from the Settings page"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('setup.settings'))

    # Find the wizard (completed) to use for content generation
    wizard = SetupWizard.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).order_by(SetupWizard.completed_at.desc()).first()

    if not wizard:
        flash(_('No completed setup wizard found. Please complete the setup wizard first.'), 'warning')
        return redirect(url_for('setup.settings'))

    try:
        from app.utils.policy_generator import generate_policy_pdf
        pdf_path = generate_policy_pdf(wizard, policy_type)
        if not os.path.exists(pdf_path):
            flash(_('Error: PDF not created for %(type)s', type=policy_type), 'danger')
            return redirect(url_for('setup.settings') + '#policies')
        return send_file(pdf_path, as_attachment=True,
                         download_name=f'{policy_type}_policy.pdf', mimetype='application/pdf')
    except Exception as e:
        flash(_('Error generating policy PDF: %(error)s', error=str(e)), 'danger')
        return redirect(url_for('setup.settings') + '#policies')


# ============================================================
# GROWER MANAGEMENT
# ============================================================

@setup_bp.route('/delete-grower/<int:grower_id>', methods=['POST'])
@login_required
def delete_grower(grower_id):
    """Delete a grower"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('You do not have permission.'), 'danger')
        return redirect(url_for('setup.settings'))

    grower = Grower.query.get(grower_id)
    if not grower or grower.organization_id != current_user.organization_id:
        flash(_('Grower not found.'), 'danger')
        return redirect(url_for('setup.settings'))

    grower_name = grower.grower_name
    grower_code = grower.grower_code

    # Delete associated grower control points first
    GrowerControlPoint.query.filter_by(grower_id=grower.id).delete()
    db.session.delete(grower)
    db.session.commit()

    log_audit('delete', 'grower', grower_id, details=f'Deleted grower {grower_code} ({grower_name})')
    db.session.commit()

    flash(_('Grower "%(name)s" deleted successfully.', name=grower_name), 'success')
    return redirect(url_for('setup.settings'))


# ============================================================
# CSV: GROWER/FIELD TEMPLATE DOWNLOAD & UPLOAD
# ============================================================

@setup_bp.route('/download-grower-csv', methods=['GET'])
@login_required
def download_grower_csv():
    """Download CSV template for grower/field data"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    growers = Grower.query.filter_by(organization_id=organization.id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Grower_Code', 'Grower_Name', 'Field_Name', 'Size_Hectares',
        'GPS_Coordinates', 'Crop_Type', 'Spray_Program', 'Harvest_Schedule',
        'Fertilisation_Plan', 'Irrigation_Type', 'Planting_Date', 'Pruning_Method',
        'Conservation_Points', 'Biodiversity_Measures'
    ])

    if growers:
        for g in growers:
            writer.writerow([
                g.grower_code, g.grower_name, g.field_name, g.size_hectares or '',
                g.gps_coordinates or '', g.crop_type or '', g.spray_program or '',
                g.harvest_schedule or '', g.fertilisation_plan or '', g.irrigation_type or '',
                g.planting_date.strftime('%Y-%m-%d') if g.planting_date else '',
                g.pruning_method or '', g.conservation_points or '', g.biodiversity_measures or ''
            ])
    else:
        # Write example row
        writer.writerow([
            'GRW-001', 'Example Farm', 'Field A', '12.5',
            '-33.9249, 18.4241', 'apples', '', '',
            '', 'drip', '', '',
            '', ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=Grower_Template_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@setup_bp.route('/upload-grower-csv', methods=['POST'])
@login_required
def upload_grower_csv():
    """Upload CSV to create/update growers"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    if 'csv_file' not in request.files:
        flash(_('No file uploaded.'), 'danger')
        return redirect(url_for('setup.settings'))

    file = request.files['csv_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        flash(_('Please upload a CSV file.'), 'danger')
        return redirect(url_for('setup.settings'))

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        csv_reader = csv.DictReader(stream)

        created = 0
        updated = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                code = row.get('Grower_Code', '').strip()
                name = row.get('Grower_Name', '').strip()
                field = row.get('Field_Name', '').strip()

                if not code or not name or not field:
                    errors.append(f"Row {row_num}: Grower_Code, Grower_Name, and Field_Name are required.")
                    continue

                existing = Grower.query.filter_by(
                    organization_id=organization.id,
                    grower_code=code
                ).first()

                if existing:
                    existing.grower_name = name
                    existing.field_name = field
                    existing.size_hectares = float(row['Size_Hectares']) if row.get('Size_Hectares', '').strip() else None
                    existing.gps_coordinates = row.get('GPS_Coordinates', '').strip() or None
                    existing.crop_type = row.get('Crop_Type', '').strip() or None
                    existing.spray_program = row.get('Spray_Program', '').strip() or None
                    existing.harvest_schedule = row.get('Harvest_Schedule', '').strip() or None
                    existing.fertilisation_plan = row.get('Fertilisation_Plan', '').strip() or None
                    existing.irrigation_type = row.get('Irrigation_Type', '').strip() or None
                    if row.get('Planting_Date', '').strip():
                        try:
                            existing.planting_date = datetime.strptime(row['Planting_Date'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    existing.pruning_method = row.get('Pruning_Method', '').strip() or None
                    existing.conservation_points = row.get('Conservation_Points', '').strip() or None
                    existing.biodiversity_measures = row.get('Biodiversity_Measures', '').strip() or None
                    updated += 1
                else:
                    grower = Grower(
                        organization_id=organization.id,
                        grower_code=code,
                        grower_name=name,
                        field_name=field,
                        size_hectares=float(row['Size_Hectares']) if row.get('Size_Hectares', '').strip() else None,
                        gps_coordinates=row.get('GPS_Coordinates', '').strip() or None,
                        crop_type=row.get('Crop_Type', '').strip() or None,
                        spray_program=row.get('Spray_Program', '').strip() or None,
                        harvest_schedule=row.get('Harvest_Schedule', '').strip() or None,
                        fertilisation_plan=row.get('Fertilisation_Plan', '').strip() or None,
                        irrigation_type=row.get('Irrigation_Type', '').strip() or None,
                        pruning_method=row.get('Pruning_Method', '').strip() or None,
                        conservation_points=row.get('Conservation_Points', '').strip() or None,
                        biodiversity_measures=row.get('Biodiversity_Measures', '').strip() or None,
                    )
                    if row.get('Planting_Date', '').strip():
                        try:
                            grower.planting_date = datetime.strptime(row['Planting_Date'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    db.session.add(grower)
                    created += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        db.session.commit()
        log_audit('csv_upload', 'grower', 0, details=f'Grower CSV: {created} created, {updated} updated')
        db.session.commit()

        if errors:
            flash(_('Processed: %(created)d created, %(updated)d updated. %(errors)d errors.',
                     created=created, updated=updated, errors=len(errors)), 'warning')
            for e in errors[:5]:
                flash(e, 'danger')
        else:
            flash(_('Successfully imported growers! %(created)d created, %(updated)d updated.',
                     created=created, updated=updated), 'success')

    except Exception as e:
        db.session.rollback()
        flash(_('Error processing CSV: %(error)s', error=str(e)), 'danger')

    return redirect(url_for('setup.settings'))


# ============================================================
# CSV: COMPLIANCE TEMPLATE DOWNLOAD & UPLOAD
# ============================================================

@setup_bp.route('/download-compliance-csv', methods=['GET'])
@login_required
def download_compliance_csv():
    """Download CSV template for GLOBALG.A.P. compliance"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    control_points = ControlPoint.query.filter_by(
        organization_id=organization.id
    ).order_by(ControlPoint.code).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Control_Point_Code', 'Section', 'Description',
        'Compliance_Criteria', 'Criticality', 'Applicable',
        'Overlap', 'Compliance_Status', 'Evidence_Filename', 'Implementation_Notes'
    ])

    for cp in control_points:
        # Use the new section field if available, else parse from description
        section_name = cp.section or ''
        if not section_name and ' - ' in cp.description:
            section_name = cp.description.split(' - ')[0].strip()

        control_text = cp.description
        if section_name and cp.description.startswith(section_name + ' - '):
            control_text = cp.description[len(section_name) + 3:]

        writer.writerow([
            cp.code, section_name, control_text,
            cp.compliance_criteria or '', cp.criticality,
            'Yes' if cp.is_applicable else 'No',
            cp.overlap_hint or '',
            cp.compliance_status or 'N/A', cp.evidence_file or '', cp.notes or ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=GLOBALGAP_Compliance_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@setup_bp.route('/upload-compliance-csv', methods=['POST'])
@login_required
def upload_compliance_csv():
    """Upload CSV to update GLOBALG.A.P. compliance status"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    if 'csv_file' not in request.files:
        flash(_('No file uploaded.'), 'danger')
        return redirect(url_for('setup.settings'))

    file = request.files['csv_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        flash(_('Please upload a CSV file.'), 'danger')
        return redirect(url_for('setup.settings'))

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        csv_reader = csv.DictReader(stream)

        updated = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                code = row.get('Control_Point_Code', '').strip()
                if not code:
                    errors.append(f"Row {row_num}: Missing Control_Point_Code.")
                    continue

                cp = ControlPoint.query.filter_by(
                    organization_id=organization.id,
                    code=code
                ).first()

                if not cp:
                    errors.append(f"Row {row_num}: Control point '{code}' not found.")
                    continue

                status = row.get('Compliance_Status', '').strip()
                if status and status in ('Compliant', 'Non-compliant', 'N/A'):
                    old_status = cp.compliance_status
                    cp.compliance_status = status
                    if old_status != status:
                        log_audit('csv_update_compliance', 'control_point', cp.id,
                                  field_changed='compliance_status',
                                  old_value=old_status, new_value=status)

                notes = row.get('Implementation_Notes', '').strip()
                if notes:
                    cp.notes = notes

                cp.updated_at = datetime.utcnow()
                updated += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        db.session.commit()

        if errors:
            flash(_('Updated %(count)d control points. %(errors)d errors.',
                     count=updated, errors=len(errors)), 'warning')
            for e in errors[:5]:
                flash(e, 'danger')
        else:
            flash(_('Successfully updated %(count)d control points!', count=updated), 'success')

    except Exception as e:
        db.session.rollback()
        flash(_('Error processing CSV: %(error)s', error=str(e)), 'danger')

    return redirect(url_for('setup.settings'))


# ============================================================
# CSV: GROWER CHECKLIST TEMPLATE DOWNLOAD & UPLOAD
# ============================================================

@setup_bp.route('/download-grower-checklist-template', methods=['GET'])
@login_required
def download_grower_checklist_template():
    """Download CSV template for grower checklists"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('You do not have permission to access this page.'), 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    grower_sections = ['FV 26', 'FV 28', 'FV 29', 'FV 30', 'FV 31', 'FV 32']

    control_points = ControlPoint.query.filter_by(
        organization_id=organization.id
    ).filter(
        db.or_(*[ControlPoint.description.like(f'{section}%') for section in grower_sections])
    ).order_by(ControlPoint.code).all()

    growers = Grower.query.filter_by(organization_id=organization.id).all()

    if not growers:
        flash(_('No growers found. Please add growers first.'), 'warning')
        return redirect(url_for('setup.settings'))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Grower_Code', 'Grower_Name', 'Control_Point_Code',
        'Control_Point_Section', 'Control_Point_Description',
        'Compliance_Criteria', 'Criticality',
        'Compliance_Status', 'Evidence_Filename',
        'Implementation_Notes', 'Common_Response', 'Last_Updated'
    ])

    for grower in growers:
        for cp in control_points:
            section_name = cp.section or ''
            if not section_name and ' - ' in cp.description:
                section_name = cp.description.split(' - ')[0].strip()

            control_point_text = cp.description
            if section_name and cp.description.startswith(section_name + ' - '):
                control_point_text = cp.description[len(section_name) + 3:]

            existing = GrowerControlPoint.query.filter_by(
                grower_id=grower.id,
                control_point_id=cp.id
            ).first()

            if existing:
                writer.writerow([
                    grower.grower_code, grower.grower_name, cp.code,
                    section_name, control_point_text, cp.compliance_criteria or '',
                    cp.criticality, existing.compliance_status or 'N/A',
                    existing.evidence_file or '', existing.implementation_notes or '',
                    'YES' if existing.is_common_response else 'NO',
                    existing.updated_at.strftime('%Y-%m-%d') if existing.updated_at else ''
                ])
            else:
                writer.writerow([
                    grower.grower_code, grower.grower_name, cp.code,
                    section_name, control_point_text, cp.compliance_criteria or '',
                    cp.criticality, 'N/A', '', '', 'NO',
                    datetime.now().strftime('%Y-%m-%d')
                ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=Grower_Checklist_{organization.name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


@setup_bp.route('/upload-grower-checklist', methods=['POST'])
@login_required
def upload_grower_checklist():
    """Upload and process CSV file with grower checklists"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('You do not have permission to access this page.'), 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    if 'csv_file' not in request.files:
        flash(_('No file uploaded.'), 'danger')
        return redirect(url_for('setup.settings'))

    file = request.files['csv_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        flash(_('Please upload a CSV file.'), 'danger')
        return redirect(url_for('setup.settings'))

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        csv_reader = csv.DictReader(stream)

        records_processed = 0
        records_created = 0
        records_updated = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                grower = Grower.query.filter_by(
                    organization_id=organization.id,
                    grower_code=row['Grower_Code'].strip()
                ).first()

                if not grower:
                    errors.append(f"Row {row_num}: Grower '{row['Grower_Code']}' not found.")
                    continue

                control_point = ControlPoint.query.filter_by(
                    organization_id=organization.id,
                    code=row['Control_Point_Code'].strip()
                ).first()

                if not control_point:
                    errors.append(f"Row {row_num}: Control point '{row['Control_Point_Code']}' not found.")
                    continue

                grower_cp = GrowerControlPoint.query.filter_by(
                    grower_id=grower.id,
                    control_point_id=control_point.id
                ).first()

                is_common = row.get('Common_Response', 'NO').strip().upper() == 'YES'

                if grower_cp:
                    grower_cp.compliance_status = row.get('Compliance_Status', 'N/A').strip()
                    grower_cp.evidence_file = row.get('Evidence_Filename', '').strip()
                    grower_cp.implementation_notes = row.get('Implementation_Notes', '').strip()
                    grower_cp.is_common_response = is_common
                    grower_cp.updated_at = datetime.now()
                    records_updated += 1
                else:
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

        db.session.commit()
        log_audit('csv_upload', 'grower_checklist', 0,
                  details=f'Grower checklist CSV: {records_created} created, {records_updated} updated')
        db.session.commit()

        if errors:
            flash(_('Processed %(processed)d records (%(created)d created, %(updated)d updated). %(errors)d errors occurred.',
                     processed=records_processed, created=records_created, updated=records_updated, errors=len(errors)), 'warning')
            for error in errors[:5]:
                flash(error, 'danger')
            if len(errors) > 5:
                flash(_('... and %(count)d more errors.', count=len(errors) - 5), 'danger')
        else:
            flash(_('Successfully processed %(processed)d records! (%(created)d created, %(updated)d updated)',
                     processed=records_processed, created=records_created, updated=records_updated), 'success')

    except Exception as e:
        db.session.rollback()
        flash(_('Error processing CSV file: %(error)s', error=str(e)), 'danger')

    return redirect(url_for('setup.settings'))


# ============================================================
# REPORTING: Export compliance report as CSV
# ============================================================

@setup_bp.route('/export-compliance-report', methods=['GET'])
@login_required
def export_compliance_report():
    """Export full compliance report as CSV"""
    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    control_points = ControlPoint.query.filter_by(
        organization_id=organization.id
    ).order_by(ControlPoint.code).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Organization', 'Report_Date', 'Control_Point_Code',
        'Section', 'Description', 'Criticality', 'Applicable',
        'Overlap', 'Compliance_Status', 'Evidence_File', 'Last_Updated'
    ])

    for cp in control_points:
        section_name = cp.section or ''
        if not section_name and ' - ' in cp.description:
            section_name = cp.description.split(' - ')[0].strip()

        desc = cp.description
        if section_name and cp.description.startswith(section_name + ' - '):
            desc = cp.description[len(section_name) + 3:]

        writer.writerow([
            organization.name, datetime.now().strftime('%Y-%m-%d'),
            cp.code, section_name, desc, cp.criticality,
            'Yes' if cp.is_applicable else 'No',
            cp.overlap_hint or '',
            cp.compliance_status or 'N/A', cp.evidence_file or '',
            cp.updated_at.strftime('%Y-%m-%d') if cp.updated_at else ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=Compliance_Report_{organization.name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv'
        }
    )


# ============================================================
# AUDIT TRAIL VIEW
# ============================================================

@setup_bp.route('/audit-log')
@login_required
def audit_log():
    """View audit trail"""
    if current_user.role not in ['qa_manager', 'auditor']:
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('dashboard.index'))

    organization = current_user.organization
    if not organization:
        flash(_('No organization found.'), 'danger')
        return redirect(url_for('setup.settings'))

    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.filter_by(
        organization_id=organization.id
    ).order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)

    return render_template('setup/audit_log.html', logs=logs)


# ============================================================
# HELPER: Load control points for template
# ============================================================

def get_globalgap_control_points_from_db(organization_id):
    """Load all GLOBALG.A.P. control points grouped by section."""

    all_control_points = ControlPoint.query.filter_by(
        organization_id=organization_id
    ).order_by(ControlPoint.code).all()

    if not all_control_points:
        return {
            'No Control Points': {
                'Control Points': [
                    {
                        'id': 0,
                        'code': 'N/A',
                        'description': 'No control points found. Complete the Setup Wizard to load GLOBALG.A.P. control points.',
                        'compliance_criteria': '',
                        'criticality': 'N/A',
                        'overlap': None,
                        'compliance_status': 'N/A',
                        'evidence_file': None,
                        'notes_field': '',
                        'is_applicable': True,
                        'applicability_reason': '',
                        'section': '',
                    }
                ]
            }
        }

    grouped = {}
    for cp in all_control_points:
        # Use the section field directly if available
        section_name = cp.section or ''
        if not section_name:
            # Legacy fallback: parse from description
            desc_parts = cp.description.split(' - ')
            section_name = desc_parts[0].strip() if len(desc_parts) >= 2 else 'Other'

        if section_name not in grouped:
            grouped[section_name] = []

        # Extract control text (remove section prefix from description)
        control_text = cp.description
        if section_name and cp.description.startswith(section_name + ' - '):
            control_text = cp.description[len(section_name) + 3:]

        grouped[section_name].append({
            'id': cp.id,
            'code': cp.code,
            'description': control_text,
            'compliance_criteria': cp.compliance_criteria or '',
            'criticality': cp.criticality,
            'overlap': cp.overlap_hint,
            'compliance_status': cp.compliance_status or 'N/A',
            'evidence_file': cp.evidence_file,
            'notes_field': cp.notes,
            'is_applicable': cp.is_applicable,
            'applicability_reason': cp.applicability_reason or '',
            'section': section_name,
        })

    result = {}
    for section_name, points in sorted(grouped.items()):
        result[section_name] = {
            'Control Points': points
        }

    return result


def get_organization_policies(organization_id):
    """Get list of available policies for the Policies tab."""
    # Find the completed wizard for this organization
    wizard = SetupWizard.query.filter_by(
        organization_id=organization_id,
        completed=True
    ).order_by(SetupWizard.completed_at.desc()).first()

    policy_types = [
        {'type': 'haccp', 'name': 'HACCP Plan', 'icon': 'bi-shield-check', 'priority': 'High',
         'description': 'Hazard Analysis & Critical Control Points — food safety management'},
        {'type': 'spray_program', 'name': 'Spray/IPM Program', 'icon': 'bi-bug', 'priority': 'High',
         'description': 'Integrated Pest Management and spray application records'},
        {'type': 'environmental', 'name': 'Environmental Policy', 'icon': 'bi-tree', 'priority': 'Medium',
         'description': 'Biodiversity conservation, water, soil, and energy management'},
        {'type': 'waste_management', 'name': 'Waste Management Plan', 'icon': 'bi-recycle', 'priority': 'Medium',
         'description': 'Waste segregation, recycling, and disposal procedures'},
        {'type': 'worker_welfare', 'name': 'Worker Welfare Policy', 'icon': 'bi-people', 'priority': 'High',
         'description': 'Health, safety & welfare policy covering GRASP requirements'},
        {'type': 'training_log', 'name': 'Worker Training Log', 'icon': 'bi-journal-text', 'priority': 'Low',
         'description': 'Template for documenting worker training sessions'},
        {'type': 'traceability', 'name': 'Traceability Template', 'icon': 'bi-diagram-3', 'priority': 'Medium',
         'description': 'Product traceability and lot tracking system template'},
    ]

    uploaded_policies = {}
    if wizard and wizard.policies_generated:
        try:
            uploaded_policies = json.loads(wizard.policies_generated)
        except (ValueError, TypeError):
            uploaded_policies = {}

    for p in policy_types:
        p['uploaded'] = p['type'] in uploaded_policies
        if p['uploaded']:
            p['upload_info'] = uploaded_policies[p['type']]

    return {
        'policies': policy_types,
        'has_wizard': wizard is not None,
    }


def get_compliance_stats(organization_id):
    """Compute summary stats for the compliance dashboard."""
    all_cps = ControlPoint.query.filter_by(organization_id=organization_id).all()
    if not all_cps:
        return {'total': 0, 'applicable': 0, 'compliant': 0, 'non_compliant': 0, 'not_assessed': 0,
                'major_must_total': 0, 'major_must_compliant': 0, 'minor_must_total': 0, 'minor_must_compliant': 0,
                'recom_total': 0, 'recom_compliant': 0, 'pct': 0}

    applicable = [cp for cp in all_cps if cp.is_applicable]
    compliant = [cp for cp in applicable if cp.compliance_status == 'Compliant']
    non_compliant = [cp for cp in applicable if cp.compliance_status == 'Non-compliant']
    not_assessed = [cp for cp in applicable if cp.compliance_status not in ('Compliant', 'Non-compliant')]

    major = [cp for cp in applicable if 'Major' in (cp.criticality or '')]
    minor = [cp for cp in applicable if 'Minor' in (cp.criticality or '')]
    recom = [cp for cp in applicable if 'Recommendation' in (cp.criticality or '')]

    pct = round(len(compliant) / len(applicable) * 100) if applicable else 0

    return {
        'total': len(all_cps),
        'applicable': len(applicable),
        'compliant': len(compliant),
        'non_compliant': len(non_compliant),
        'not_assessed': len(not_assessed),
        'major_must_total': len(major),
        'major_must_compliant': len([cp for cp in major if cp.compliance_status == 'Compliant']),
        'minor_must_total': len(minor),
        'minor_must_compliant': len([cp for cp in minor if cp.compliance_status == 'Compliant']),
        'recom_total': len(recom),
        'recom_compliant': len([cp for cp in recom if cp.compliance_status == 'Compliant']),
        'pct': pct,
    }
