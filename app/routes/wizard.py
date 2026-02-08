from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file
from flask_login import login_required, current_user
from app import db
from app.models import SetupWizard, Organization
from app.forms_wizard import (
    Step1BusinessTypeForm, Step2PackhouseForm,
    Step3GrowerFieldForm, Step4EnvironmentForm
)
import json
import os
from datetime import datetime

wizard_bp = Blueprint('wizard', __name__, url_prefix='/wizard')

def get_or_create_wizard():
    """Get existing wizard or create new one for current user"""
    wizard = SetupWizard.query.filter_by(user_id=current_user.id, completed=False).first()
    if not wizard:
        wizard = SetupWizard(user_id=current_user.id)
        db.session.add(wizard)
        db.session.commit()
    return wizard


@wizard_bp.route('/start')
@login_required
def start():
    """Start or resume wizard"""
    wizard = get_or_create_wizard()
    return redirect(url_for('wizard.step1'))


@wizard_bp.route('/step1', methods=['GET', 'POST'])
@login_required
def step1():
    """Step 1: Business Type"""
    wizard = get_or_create_wizard()
    form = Step1BusinessTypeForm()

    if form.validate_on_submit():
        wizard.business_type = form.business_type.data
        wizard.audit_scope = form.audit_scope.data
        wizard.ggn_number = form.ggn_number.data
        wizard.has_contract_growers = form.has_contract_growers.data
        wizard.number_of_contract_growers = form.number_of_contract_growers.data
        wizard.current_step = 2
        db.session.commit()
        flash('Business type and audit scope saved!', 'success')

        # Skip packhouse step if grower only
        if wizard.business_type == 'grower':
            return redirect(url_for('wizard.step3'))
        return redirect(url_for('wizard.step2'))

    # Pre-fill form
    if wizard.business_type:
        form.business_type.data = wizard.business_type
        form.audit_scope.data = wizard.audit_scope
        form.ggn_number.data = wizard.ggn_number
        form.has_contract_growers.data = wizard.has_contract_growers
        form.number_of_contract_growers.data = wizard.number_of_contract_growers

    return render_template('wizard/wizard.html',
                         form=form,
                         step=1,
                         total_steps=7,
                         wizard=wizard)


@wizard_bp.route('/step2', methods=['GET', 'POST'])
@login_required
def step2():
    """Step 2: Packhouse Details"""
    wizard = get_or_create_wizard()

    # Skip if grower only
    if wizard.business_type == 'grower':
        return redirect(url_for('wizard.step3'))

    form = Step2PackhouseForm()

    if form.validate_on_submit():
        wizard.number_of_packhouses = form.number_of_packhouses.data
        wizard.packhouse_name = form.packhouse_name.data
        wizard.packhouse_address = form.packhouse_address.data
        wizard.packhouse_country = form.packhouse_country.data
        wizard.packhouse_latitude = form.packhouse_latitude.data
        wizard.packhouse_longitude = form.packhouse_longitude.data
        wizard.packing_system_type = form.packing_system_type.data
        wizard.crops_packed = json.dumps(form.crops_packed.data) if form.crops_packed.data else None
        wizard.water_usage = form.water_usage.data
        wizard.energy_usage = form.energy_usage.data
        wizard.current_step = 3
        db.session.commit()
        flash('Packhouse details saved!', 'success')
        return redirect(url_for('wizard.step3'))

    # Pre-fill form
    if wizard.packhouse_name:
        form.number_of_packhouses.data = wizard.number_of_packhouses
        form.packhouse_name.data = wizard.packhouse_name
        form.packhouse_address.data = wizard.packhouse_address
        form.packhouse_country.data = wizard.packhouse_country
        form.packhouse_latitude.data = wizard.packhouse_latitude
        form.packhouse_longitude.data = wizard.packhouse_longitude
        form.packing_system_type.data = wizard.packing_system_type
        if wizard.crops_packed:
            try:
                form.crops_packed.data = json.loads(wizard.crops_packed)
            except:
                form.crops_packed.data = []
        form.water_usage.data = wizard.water_usage
        form.energy_usage.data = wizard.energy_usage

    return render_template('wizard/wizard.html',
                         form=form,
                         step=2,
                         total_steps=7,
                         wizard=wizard)


@wizard_bp.route('/step3', methods=['GET', 'POST'])
@login_required
def step3():
    """Step 3: Grower/Field Details"""
    wizard = get_or_create_wizard()
    form = Step3GrowerFieldForm()

    if form.validate_on_submit():
        wizard.has_own_fields = form.has_own_fields.data
        wizard.total_farm_size = form.total_farm_size.data
        wizard.number_of_fields = form.number_of_fields.data
        wizard.main_crops = json.dumps(form.main_crops.data) if form.main_crops.data else None
        wizard.irrigation_types = json.dumps(form.irrigation_types.data) if form.irrigation_types.data else None
        wizard.current_step = 4
        db.session.commit()
        flash('Farm details saved!', 'success')
        return redirect(url_for('wizard.step4'))

    # Pre-fill form
    form.has_own_fields.data = wizard.has_own_fields
    if wizard.total_farm_size:
        form.total_farm_size.data = wizard.total_farm_size
        form.number_of_fields.data = wizard.number_of_fields
    if wizard.main_crops:
        try:
            form.main_crops.data = json.loads(wizard.main_crops)
        except:
            form.main_crops.data = []
    if wizard.irrigation_types:
        try:
            form.irrigation_types.data = json.loads(wizard.irrigation_types)
        except:
            form.irrigation_types.data = []

    return render_template('wizard/wizard.html',
                         form=form,
                         step=3,
                         total_steps=7,
                         wizard=wizard)


@wizard_bp.route('/step4', methods=['GET', 'POST'])
@login_required
def step4():
    """Step 4: Environment & Compliance"""
    wizard = get_or_create_wizard()
    form = Step4EnvironmentForm()

    if form.validate_on_submit():
        wizard.has_environmental_policy = form.has_environmental_policy.data
        wizard.has_haccp_plan = form.has_haccp_plan.data
        wizard.has_spray_program = form.has_spray_program.data
        wizard.water_treatment_method = form.water_treatment_method.data
        wizard.waste_management_plan = form.waste_management_plan.data
        wizard.current_step = 5
        db.session.commit()
        flash('Environmental details saved!', 'success')
        return redirect(url_for('wizard.step5'))

    # Pre-fill form
    form.has_environmental_policy.data = wizard.has_environmental_policy
    form.has_haccp_plan.data = wizard.has_haccp_plan
    form.has_spray_program.data = wizard.has_spray_program
    if wizard.water_treatment_method:
        form.water_treatment_method.data = wizard.water_treatment_method
    form.waste_management_plan.data = wizard.waste_management_plan

    return render_template('wizard/wizard.html',
                         form=form,
                         step=4,
                         total_steps=7,
                         wizard=wizard)


@wizard_bp.route('/step5')
@login_required
def step5():
    """Step 5: GLOBALG.A.P. Analysis"""
    wizard = get_or_create_wizard()

    # Analyze applicable control points based on wizard data
    analysis = analyze_control_points(wizard)

    # Save analysis
    wizard.applicable_control_points = json.dumps(analysis)
    wizard.analysis_completed = True
    wizard.current_step = 6
    db.session.commit()

    return render_template('wizard/step5_analysis.html',
                         step=5,
                         total_steps=7,
                         wizard=wizard,
                         analysis=analysis)


@wizard_bp.route('/step6')
@login_required
def step6():
    """Step 6: Policy Generation"""
    wizard = get_or_create_wizard()

    # Determine which policies to generate
    policies_needed = determine_policies_needed(wizard)

    # Load any already-uploaded policies
    uploaded_policies = {}
    if wizard.policies_generated:
        try:
            uploaded_policies = json.loads(wizard.policies_generated)
        except:
            uploaded_policies = {}

    wizard.current_step = 7
    db.session.commit()

    return render_template('wizard/step6_policies.html',
                         step=6,
                         total_steps=7,
                         wizard=wizard,
                         policies=policies_needed,
                         uploaded_policies=uploaded_policies)


@wizard_bp.route('/upload-policy/<policy_type>', methods=['POST'])
@login_required
def upload_policy(policy_type):
    """Upload a policy document"""
    from flask import current_app
    from werkzeug.utils import secure_filename

    wizard = get_or_create_wizard()

    if 'policy_file' not in request.files:
        flash('No file selected.', 'warning')
        return redirect(url_for('wizard.step6'))

    file = request.files['policy_file']
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('wizard.step6'))

    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xlsx', 'xls'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        flash('File type not allowed. Please upload PDF, Word, or Excel files.', 'danger')
        return redirect(url_for('wizard.step6'))

    filename = secure_filename(file.filename)
    # Prefix with wizard id and policy type to avoid collisions
    stored_name = f"w{wizard.id}_{policy_type}_{filename}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'policies')
    file.save(os.path.join(upload_dir, stored_name))

    # Track in wizard
    uploaded = {}
    if wizard.policies_generated:
        try:
            uploaded = json.loads(wizard.policies_generated)
        except:
            uploaded = {}

    uploaded[policy_type] = {
        'filename': filename,
        'stored_name': stored_name,
        'uploaded_at': datetime.utcnow().isoformat()
    }
    wizard.policies_generated = json.dumps(uploaded)
    db.session.commit()

    flash(f'Policy "{filename}" uploaded successfully.', 'success')
    return redirect(url_for('wizard.step6'))


@wizard_bp.route('/remove-policy/<policy_type>', methods=['POST'])
@login_required
def remove_policy_upload(policy_type):
    """Remove an uploaded policy document"""
    from flask import current_app

    wizard = get_or_create_wizard()

    uploaded = {}
    if wizard.policies_generated:
        try:
            uploaded = json.loads(wizard.policies_generated)
        except:
            uploaded = {}

    if policy_type in uploaded:
        # Delete the file from disk
        stored_name = uploaded[policy_type].get('stored_name')
        if stored_name:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'policies', stored_name)
            if os.path.exists(file_path):
                os.remove(file_path)

        del uploaded[policy_type]
        wizard.policies_generated = json.dumps(uploaded)
        db.session.commit()
        flash('Policy removed.', 'info')

    return redirect(url_for('wizard.step6'))


@wizard_bp.route('/step7', methods=['GET', 'POST'])
@login_required
def step7():
    """Step 7: Review & Complete"""
    wizard = get_or_create_wizard()

    if request.method == 'POST':
        try:
            # Create organization from wizard data
            org = Organization(
                name=wizard.packhouse_name or f"{current_user.name}'s Farm",
                org_type=wizard.business_type,
                audit_scope=wizard.audit_scope,
                ggn_number=wizard.ggn_number,
                address=wizard.packhouse_address,
                country=wizard.packhouse_country,
                latitude=wizard.packhouse_latitude,
                longitude=wizard.packhouse_longitude,
                packing_system=wizard.packing_system_type,
                water_usage_m3_day=wizard.water_usage,
                energy_usage_kwh_month=wizard.energy_usage,
                water_treatment_method=wizard.water_treatment_method
            )
            db.session.add(org)
            db.session.commit()

            # Link organization to user and wizard
            current_user.organization_id = org.id
            wizard.organization_id = org.id
            wizard.completed = True
            wizard.completed_at = datetime.utcnow()
            db.session.commit()

            flash('Setup wizard completed successfully! Your organization has been created.', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error completing setup: {str(e)}', 'danger')
            return redirect(url_for('wizard.step7'))

    # Load analysis for review
    analysis = json.loads(wizard.applicable_control_points) if wizard.applicable_control_points else None

    return render_template('wizard/step7_review.html',
                         step=7,
                         total_steps=7,
                         wizard=wizard,
                         analysis=analysis)


@wizard_bp.route('/generate-policy/<policy_type>')
@login_required
def generate_policy(policy_type):
    """Generate and download policy document"""
    wizard = get_or_create_wizard()

    try:
        from app.utils.policy_generator import generate_policy_pdf

        pdf_path = generate_policy_pdf(wizard, policy_type)

        # Verify file exists
        if not os.path.exists(pdf_path):
            flash(f'Error: PDF file not created for {policy_type}', 'danger')
            return redirect(url_for('wizard.step6'))

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'{policy_type}_policy.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating policy PDF: {str(e)}', 'danger')
        return redirect(url_for('wizard.step6'))


def analyze_control_points(wizard):
    """Analyze which GLOBALG.A.P. control points apply"""
    from app.models import ControlPoint

    # Get control points from any existing org, or all if none yet
    all_cps = ControlPoint.query.order_by(ControlPoint.code).all()

    analysis = {
        'applicable': [],
        'not_applicable': [],
        'maybe_applicable': []
    }

    if not all_cps:
        return analysis

    for cp in all_cps:
        point = {
            'code': cp.code,
            'description': cp.description,
            'criticality': cp.criticality,
            'overlap': cp.overlap_hint
        }
        applicability = determine_applicability(wizard, point)

        point_data = {
            'section': cp.category,
            'category': cp.category,
            'code': cp.code,
            'description': cp.description,
            'criticality': cp.criticality,
            'overlap': cp.overlap_hint,
            'reason': applicability['reason']
        }

        if applicability['status'] == 'applicable':
            analysis['applicable'].append(point_data)
        elif applicability['status'] == 'not_applicable':
            analysis['not_applicable'].append(point_data)
        else:
            analysis['maybe_applicable'].append(point_data)

    return analysis


def determine_applicability(wizard, point):
    """Determine if a control point applies to this operation"""
    code = point['code']
    description = point.get('description', '').lower()

    # Packhouse-specific points (FV 2.x series)
    if 'FV 2' in code or 'produce handling' in description or 'packing' in description:
        # Applies to all packhouse types
        if wizard.business_type in ['packhouse_only', 'packhouse_farms', 'packhouse_contract', 'packhouse_mixed']:
            return {'status': 'applicable', 'reason': 'Packhouse operation'}
        else:
            return {'status': 'not_applicable', 'reason': 'No packhouse operations'}

    # Harvest/field points (FV 1.x series)
    if 'FV 1' in code or 'harvest' in description or 'field' in description:
        # Applies if they have own fields OR are grower-only
        if wizard.business_type == 'grower' or wizard.has_own_fields:
            return {'status': 'applicable', 'reason': 'Own farm/harvest operations'}
        elif wizard.business_type in ['packhouse_only', 'packhouse_contract'] and wizard.has_contract_growers:
            return {'status': 'maybe_applicable', 'reason': 'Contract grower oversight may require'}
        else:
            return {'status': 'not_applicable', 'reason': 'No own harvest operations'}

    # Contract grower management
    if 'contract' in description or 'outsourc' in description or 'supplier' in description:
        if wizard.has_contract_growers:
            return {'status': 'applicable', 'reason': f'Working with {wizard.number_of_contract_growers or "multiple"} contract growers'}
        else:
            return {'status': 'not_applicable', 'reason': 'No contract growers'}

    # Water treatment specific
    if 'water' in description and 'treatment' in description:
        if wizard.water_treatment_method and wizard.water_treatment_method != 'none':
            return {'status': 'applicable', 'reason': f'Uses {wizard.water_treatment_method}'}
        else:
            return {'status': 'maybe_applicable', 'reason': 'Water treatment recommended'}

    # Spray/IPM program points
    if 'spray' in description or 'pesticide' in description or 'ipm' in description or 'crop protection' in description:
        if wizard.business_type == 'grower' or wizard.has_own_fields:
            if wizard.has_spray_program:
                return {'status': 'applicable', 'reason': 'Spray program in place'}
            else:
                return {'status': 'applicable', 'reason': 'Spray program required'}
        else:
            return {'status': 'not_applicable', 'reason': 'No crop production'}

    # HACCP specific
    if 'haccp' in description or 'food safety' in description:
        if wizard.business_type in ['packhouse_only', 'packhouse_farms', 'packhouse_contract', 'packhouse_mixed']:
            if wizard.has_haccp_plan:
                return {'status': 'applicable', 'reason': 'HACCP plan in place'}
            else:
                return {'status': 'applicable', 'reason': 'HACCP plan required'}
        else:
            return {'status': 'maybe_applicable', 'reason': 'Food safety considerations'}

    # Environmental/conservation points
    if 'environment' in description or 'biodiversity' in description or 'conservation' in description:
        if wizard.has_environmental_policy:
            return {'status': 'applicable', 'reason': 'Environmental policy in place'}
        else:
            return {'status': 'applicable', 'reason': 'Environmental management required'}

    # Waste management
    if 'waste' in description:
        if wizard.waste_management_plan:
            return {'status': 'applicable', 'reason': 'Waste management plan in place'}
        else:
            return {'status': 'applicable', 'reason': 'Waste management required'}

    # Default: most points apply to all operations
    return {'status': 'applicable', 'reason': 'General GLOBALG.A.P. requirement'}


def determine_policies_needed(wizard):
    """Determine which policies need to be generated"""
    policies = []

    if not wizard.has_haccp_plan:
        policies.append({
            'name': 'HACCP Plan',
            'type': 'haccp',
            'description': 'Food safety management system required by GLOBALG.A.P.',
            'priority': 'High'
        })

    if not wizard.has_spray_program and (wizard.business_type in ['grower', 'packhouse_farms', 'packhouse_mixed'] or wizard.has_own_fields):
        policies.append({
            'name': 'Spray/IPM Program',
            'type': 'spray_program',
            'description': 'Integrated Pest Management and spray application records',
            'priority': 'High'
        })

    if not wizard.has_environmental_policy:
        policies.append({
            'name': 'Environmental Policy',
            'type': 'environmental',
            'description': 'Site management and conservation policy',
            'priority': 'Medium'
        })

    if not wizard.waste_management_plan:
        policies.append({
            'name': 'Waste Management Plan',
            'type': 'waste_management',
            'description': 'Waste handling and disposal procedures',
            'priority': 'Medium'
        })

    # Always offer these templates
    policies.append({
        'name': 'Worker Training Log',
        'type': 'training_log',
        'description': 'Template for documenting worker training',
        'priority': 'Low'
    })

    policies.append({
        'name': 'Traceability Template',
        'type': 'traceability',
        'description': 'Product traceability system template',
        'priority': 'Medium'
    })

    return policies
