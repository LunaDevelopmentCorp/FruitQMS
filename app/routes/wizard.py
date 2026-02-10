from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.models import SetupWizard, Organization, ControlPoint
from app.forms_wizard import (
    Step1BusinessTypeForm, Step2PackhouseForm,
    Step3GrowerFieldForm, Step4EnvironmentForm
)
import json
import os
from datetime import datetime

wizard_bp = Blueprint('wizard', __name__, url_prefix='/wizard')


# ============================================================
# GLOBALG.A.P. IFA v6.0 MASTER CONTROL POINTS
# Seeded into the org's database on wizard completion
# ============================================================

GLOBALGAP_MASTER_POINTS = [
    # ── AF: All Farm Base ──
    {'code': 'AF 1.1.1', 'section': 'AF 01 Site History & Management', 'category': 'Site Management', 'description': 'Is there a reference system for each site/field?', 'compliance_criteria': 'A reference system exists to identify each site/plot.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'LEAF, Rainforest Alliance'},
    {'code': 'AF 1.2.1', 'section': 'AF 01 Site History & Management', 'category': 'Site Management', 'description': 'Is a risk assessment available for new sites?', 'compliance_criteria': 'Risk assessment for new agricultural sites documented.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'LEAF, Rainforest Alliance'},
    {'code': 'AF 2.1', 'section': 'AF 02 Record Keeping & Self-Assessment', 'category': 'Record Keeping', 'description': 'Are all records kept for a minimum of 2 years?', 'compliance_criteria': 'Records accessible for at least 2 years.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'BRC, IFS, SMETA'},
    {'code': 'AF 2.2', 'section': 'AF 02 Record Keeping & Self-Assessment', 'category': 'Record Keeping', 'description': 'Does the producer carry out at least one self-assessment per year?', 'compliance_criteria': 'Annual internal self-assessment completed and documented.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'BRC, IFS'},
    {'code': 'AF 3.1', 'section': 'AF 03 Hygiene', 'category': 'Hygiene', 'description': 'Is there a hygiene risk assessment?', 'compliance_criteria': 'Written hygiene risk assessment available.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'BRC, IFS, SMETA'},
    {'code': 'AF 3.2', 'section': 'AF 03 Hygiene', 'category': 'Hygiene', 'description': 'Do workers have access to clean toilet and handwashing facilities?', 'compliance_criteria': 'Toilet and handwashing facilities near the work area.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'GRASP, SMETA, Tesco Nurture'},
    {'code': 'AF 3.3', 'section': 'AF 03 Hygiene', 'category': 'Hygiene', 'description': 'Are hygiene instructions communicated to workers?', 'compliance_criteria': 'Visible hygiene signage; workers briefed.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'BRC, SMETA'},
    {'code': 'AF 4.1', 'section': 'AF 04 Workers Health, Safety & Welfare', 'category': 'Worker Welfare', 'description': 'Is there a health, safety and welfare risk assessment?', 'compliance_criteria': 'Documented risk assessment for worker H&S.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'GRASP, SMETA, SPRING'},
    {'code': 'AF 4.2', 'section': 'AF 04 Workers Health, Safety & Welfare', 'category': 'Worker Welfare', 'description': 'Do workers receive health and safety training?', 'compliance_criteria': 'Training records for all workers.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'GRASP, SMETA, SPRING'},
    {'code': 'AF 4.3', 'section': 'AF 04 Workers Health, Safety & Welfare', 'category': 'Worker Welfare', 'description': 'Are accident/emergency procedures in place?', 'compliance_criteria': 'Written emergency procedures visible at workplace.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'SMETA, SPRING'},
    {'code': 'AF 4.4', 'section': 'AF 04 Workers Health, Safety & Welfare', 'category': 'Worker Welfare', 'description': 'Is personal protective equipment (PPE) available?', 'compliance_criteria': 'PPE provided and maintained for all tasks.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'SMETA'},
    {'code': 'AF 4.5', 'section': 'AF 04 Workers Health, Safety & Welfare', 'category': 'Worker Welfare', 'description': 'Is first-aid equipment available and accessible?', 'compliance_criteria': 'First-aid kits at all work sites; trained first-aiders.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'SMETA'},
    {'code': 'AF 5.1', 'section': 'AF 05 Subcontractors', 'category': 'Subcontractors', 'description': 'Is there an assessment of subcontractors for compliance?', 'compliance_criteria': 'Subcontractors assessed for GLOBALG.A.P. compliance.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'SMETA, SPRING'},
    {'code': 'AF 6.1', 'section': 'AF 06 Waste & Pollution Management', 'category': 'Waste Management', 'description': 'Is a waste management plan in place?', 'compliance_criteria': 'Written waste and pollution management plan.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'LEAF, Rainforest Alliance'},
    {'code': 'AF 6.2', 'section': 'AF 06 Waste & Pollution Management', 'category': 'Waste Management', 'description': 'Is waste minimized and recycled where possible?', 'compliance_criteria': 'Evidence of waste reduction and recycling efforts.', 'criticality': 'Recommendation', 'applies_to': 'all', 'overlap': 'LEAF, Rainforest Alliance'},
    {'code': 'AF 7.1', 'section': 'AF 07 Conservation & Environment', 'category': 'Environment', 'description': 'Is an environmental management plan in place?', 'compliance_criteria': 'Documented plan addressing biodiversity and conservation.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'LEAF, Rainforest Alliance, Tesco Nurture'},
    {'code': 'AF 7.2', 'section': 'AF 07 Conservation & Environment', 'category': 'Environment', 'description': 'Has a wildlife and biodiversity action plan been established?', 'compliance_criteria': 'Baseline audit of biodiversity on farm.', 'criticality': 'Recommendation', 'applies_to': 'grower', 'overlap': 'LEAF, Rainforest Alliance, Tesco Nurture'},
    {'code': 'AF 8.1', 'section': 'AF 08 Complaints', 'category': 'Complaints', 'description': 'Is there a procedure for handling complaints?', 'compliance_criteria': 'Documented complaint procedure accessible to workers.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'GRASP, SMETA'},
    {'code': 'AF 9.1', 'section': 'AF 09 Recall/Withdrawal Procedure', 'category': 'Traceability', 'description': 'Is a documented recall procedure in place?', 'compliance_criteria': 'Written recall procedure tested at least once per year.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'BRC, IFS'},

    # ── FV 01: Site Management & Planning ──
    {'code': 'FV 01.01', 'section': 'FV 01 Site Management', 'category': 'Site Management', 'description': 'Have rotations and cropping plans been documented?', 'compliance_criteria': 'Rotation plans available for all sites.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': 'LEAF'},
    {'code': 'FV 01.02', 'section': 'FV 01 Site Management', 'category': 'Site Management', 'description': 'Have all production sites been identified on a map?', 'compliance_criteria': 'Farm map showing all production sites.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': 'LEAF, Rainforest Alliance'},

    # ── FV 02: Soil & Substrate Management ──
    {'code': 'FV 02.01', 'section': 'FV 02 Soil Management', 'category': 'Soil Management', 'description': 'Has a soil management plan been developed?', 'compliance_criteria': 'Soil maps and/or analysis records available.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': 'LEAF'},
    {'code': 'FV 02.02', 'section': 'FV 02 Soil Management', 'category': 'Soil Management', 'description': 'Are techniques used to improve/maintain soil structure?', 'compliance_criteria': 'Evidence of soil management techniques.', 'criticality': 'Recommendation', 'applies_to': 'grower', 'overlap': 'LEAF, Rainforest Alliance'},
    {'code': 'FV 02.03', 'section': 'FV 02 Soil Management', 'category': 'Soil Management', 'description': 'Is soil erosion minimized?', 'compliance_criteria': 'Anti-erosion measures documented.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': 'LEAF, Rainforest Alliance'},

    # ── FV 03: Fertilizer Use ──
    {'code': 'FV 03.01', 'section': 'FV 03 Fertilizer Use', 'category': 'Fertilizers', 'description': 'Are fertilizer recommendations based on soil/leaf analysis?', 'compliance_criteria': 'Competent adviser records or soil analysis.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'LEAF, Tesco Nurture'},
    {'code': 'FV 03.02', 'section': 'FV 03 Fertilizer Use', 'category': 'Fertilizers', 'description': 'Are records of all fertilizer applications maintained?', 'compliance_criteria': 'Application records: date, product, rate, operator, field.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'LEAF'},
    {'code': 'FV 03.03', 'section': 'FV 03 Fertilizer Use', 'category': 'Fertilizers', 'description': 'Are fertilizers stored properly?', 'compliance_criteria': 'Covered, clean, dry area away from product.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': None},
    {'code': 'FV 03.04', 'section': 'FV 03 Fertilizer Use', 'category': 'Fertilizers', 'description': 'Are organic fertilizers assessed for risks?', 'compliance_criteria': 'Risk assessment for organic fertilizer use documented.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': None},

    # ── FV 04: Water Management ──
    {'code': 'FV 04.01', 'section': 'FV 04 Water Management', 'category': 'Water Management', 'description': 'Has a water management plan been developed?', 'compliance_criteria': 'Written water management plan.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'LEAF, Rainforest Alliance, SPRING'},
    {'code': 'FV 04.02', 'section': 'FV 04 Water Management', 'category': 'Water Management', 'description': 'Is irrigation water quality tested at least annually?', 'compliance_criteria': 'Annual water analysis report.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'LEAF'},
    {'code': 'FV 04.03', 'section': 'FV 04 Water Management', 'category': 'Water Management', 'description': 'Is pre-harvest water quality tested?', 'compliance_criteria': 'Water risk assessment and test results.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': None},
    {'code': 'FV 04.04', 'section': 'FV 04 Water Management', 'category': 'Water Management', 'description': 'Is post-harvest wash water quality tested?', 'compliance_criteria': 'Wash water quality monitoring records.', 'criticality': 'Major Must', 'applies_to': 'packhouse', 'overlap': 'BRC, IFS'},

    # ── FV 05: Integrated Pest Management (IPM) ──
    {'code': 'FV 05.01', 'section': 'FV 05 IPM', 'category': 'IPM', 'description': 'Is there an IPM system in place?', 'compliance_criteria': 'Documented IPM plan or equivalent.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'LEAF, Tesco Nurture, Rainforest Alliance'},
    {'code': 'FV 05.02', 'section': 'FV 05 IPM', 'category': 'IPM', 'description': 'Are pest monitoring records maintained?', 'compliance_criteria': 'Scouting records with pest ID and threshold data.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': 'LEAF, Tesco Nurture'},
    {'code': 'FV 05.03', 'section': 'FV 05 IPM', 'category': 'IPM', 'description': 'Are non-chemical pest control measures used?', 'compliance_criteria': 'Evidence of biological/cultural controls.', 'criticality': 'Recommendation', 'applies_to': 'grower', 'overlap': 'LEAF, Tesco Nurture, Rainforest Alliance'},

    # ── FV 06: Plant Protection Products (PPP) ──
    {'code': 'FV 06.01', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Are only registered PPPs used?', 'compliance_criteria': 'PPPs registered for target crop and pest in country.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'Tesco Nurture, Rainforest Alliance'},
    {'code': 'FV 06.02', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Are all PPP applications recorded?', 'compliance_criteria': 'Records: date, product, target, dose, PHI, operator.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'Tesco Nurture'},
    {'code': 'FV 06.03', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Are pre-harvest intervals (PHIs) respected?', 'compliance_criteria': 'PHI recorded and verified before harvest.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'BRC, IFS'},
    {'code': 'FV 06.04', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Is PPP application equipment calibrated?', 'compliance_criteria': 'Annual calibration records for spraying equipment.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': None},
    {'code': 'FV 06.05', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Are PPPs stored safely?', 'compliance_criteria': 'Locked, ventilated store with spill containment.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': None},
    {'code': 'FV 06.06', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Are empty PPP containers disposed of properly?', 'compliance_criteria': 'Triple-rinsed and disposed via approved scheme.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': 'Rainforest Alliance'},
    {'code': 'FV 06.07', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Are MRL (Maximum Residue Limit) requirements known?', 'compliance_criteria': 'Awareness of destination-country MRLs.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'BRC, IFS, Tesco Nurture'},
    {'code': 'FV 06.08', 'section': 'FV 06 Plant Protection Products', 'category': 'Plant Protection', 'description': 'Are PPP residue analyses conducted?', 'compliance_criteria': 'Annual residue testing results available.', 'criticality': 'Recommendation', 'applies_to': 'all', 'overlap': 'BRC, IFS, Tesco Nurture'},

    # ── FV 07: Harvesting ──
    {'code': 'FV 07.01', 'section': 'FV 07 Harvesting', 'category': 'Harvesting', 'description': 'Is there a harvest hygiene risk assessment?', 'compliance_criteria': 'Risk assessment for hygiene during harvest.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'BRC'},
    {'code': 'FV 07.02', 'section': 'FV 07 Harvesting', 'category': 'Harvesting', 'description': 'Are harvest containers clean and fit for purpose?', 'compliance_criteria': 'Containers cleaned, maintained, food-grade only.', 'criticality': 'Major Must', 'applies_to': 'grower', 'overlap': 'BRC'},
    {'code': 'FV 07.03', 'section': 'FV 07 Harvesting', 'category': 'Harvesting', 'description': 'Is produce transported hygienically from field?', 'compliance_criteria': 'Transport vehicles clean; produce protected.', 'criticality': 'Minor Must', 'applies_to': 'grower', 'overlap': 'BRC'},

    # ── FV 08: Produce Handling (Packhouse) ──
    {'code': 'FV 08.01', 'section': 'FV 08 Produce Handling', 'category': 'Produce Handling', 'description': 'Is there a HACCP plan or food safety plan?', 'compliance_criteria': 'Documented HACCP/food safety plan for packhouse.', 'criticality': 'Major Must', 'applies_to': 'packhouse', 'overlap': 'BRC, IFS, SMETA'},
    {'code': 'FV 08.02', 'section': 'FV 08 Produce Handling', 'category': 'Produce Handling', 'description': 'Is the packhouse hygienic and well-maintained?', 'compliance_criteria': 'Cleaning schedules, pest control, maintenance logs.', 'criticality': 'Major Must', 'applies_to': 'packhouse', 'overlap': 'BRC, IFS'},
    {'code': 'FV 08.03', 'section': 'FV 08 Produce Handling', 'category': 'Produce Handling', 'description': 'Is cold chain management documented?', 'compliance_criteria': 'Temperature monitoring records for cold storage.', 'criticality': 'Major Must', 'applies_to': 'packhouse', 'overlap': 'BRC, IFS'},
    {'code': 'FV 08.04', 'section': 'FV 08 Produce Handling', 'category': 'Produce Handling', 'description': 'Are quality control checks performed during packing?', 'compliance_criteria': 'QC records for grading, sizing, defects.', 'criticality': 'Minor Must', 'applies_to': 'packhouse', 'overlap': 'BRC'},
    {'code': 'FV 08.05', 'section': 'FV 08 Produce Handling', 'category': 'Produce Handling', 'description': 'Are packaging materials food-safe and stored properly?', 'compliance_criteria': 'Certificates of conformity for packaging; clean storage.', 'criticality': 'Major Must', 'applies_to': 'packhouse', 'overlap': 'BRC, IFS'},
    {'code': 'FV 08.06', 'section': 'FV 08 Produce Handling', 'category': 'Produce Handling', 'description': 'Is post-harvest water treatment monitored?', 'compliance_criteria': 'Water treatment records (chlorine, pH).', 'criticality': 'Major Must', 'applies_to': 'packhouse', 'overlap': 'BRC'},

    # ── FV 09: Traceability ──
    {'code': 'FV 09.01', 'section': 'FV 09 Traceability', 'category': 'Traceability', 'description': 'Can produce be traced back to the registered farm?', 'compliance_criteria': 'Lot coding system linking packed product to field/grower.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'BRC, IFS'},
    {'code': 'FV 09.02', 'section': 'FV 09 Traceability', 'category': 'Traceability', 'description': 'Are traceability records maintained for all inputs?', 'compliance_criteria': 'Input supplier records (seeds, chemicals, packaging).', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'BRC, IFS'},

    # ── GRASP Add-On: Social Practice ──
    {'code': 'GRASP 1', 'section': 'GRASP Social Practice', 'category': 'Social Practice', 'description': 'Is there a documented workers\' representative system?', 'compliance_criteria': 'Elected workers\' representative with documented role.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'SMETA, SPRING'},
    {'code': 'GRASP 2', 'section': 'GRASP Social Practice', 'category': 'Social Practice', 'description': 'Is there a grievance procedure for workers?', 'compliance_criteria': 'Documented, accessible grievance procedure.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'SMETA, SPRING'},
    {'code': 'GRASP 3', 'section': 'GRASP Social Practice', 'category': 'Social Practice', 'description': 'Do employment contracts exist for all workers?', 'compliance_criteria': 'Written contracts; compliance with local labour law.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'SMETA, SPRING'},
    {'code': 'GRASP 4', 'section': 'GRASP Social Practice', 'category': 'Social Practice', 'description': 'Are payslips provided with transparent deductions?', 'compliance_criteria': 'Regular payslips showing gross, deductions, net.', 'criticality': 'Minor Must', 'applies_to': 'all', 'overlap': 'SMETA'},
    {'code': 'GRASP 5', 'section': 'GRASP Social Practice', 'category': 'Social Practice', 'description': 'Are working hours documented and within legal limits?', 'compliance_criteria': 'Time records; compliance with labour law max hours.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'SMETA, SPRING'},
    {'code': 'GRASP 6', 'section': 'GRASP Social Practice', 'category': 'Social Practice', 'description': 'Is there a policy against child labour and forced labour?', 'compliance_criteria': 'Written policy; age verification system.', 'criticality': 'Major Must', 'applies_to': 'all', 'overlap': 'SMETA, SPRING, Rainforest Alliance'},
]


def get_or_create_wizard():
    wizard = SetupWizard.query.filter_by(user_id=current_user.id, completed=False).first()
    if not wizard:
        wizard = SetupWizard(user_id=current_user.id)
        db.session.add(wizard)
        db.session.commit()
    return wizard


@wizard_bp.route('/start')
@login_required
def start():
    wizard = get_or_create_wizard()
    return redirect(url_for('wizard.step1'))


@wizard_bp.route('/step1', methods=['GET', 'POST'])
@login_required
def step1():
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
        flash(_('Business type and audit scope saved!'), 'success')
        if wizard.business_type == 'grower':
            return redirect(url_for('wizard.step3'))
        return redirect(url_for('wizard.step2'))

    if wizard.business_type:
        form.business_type.data = wizard.business_type
        form.audit_scope.data = wizard.audit_scope
        form.ggn_number.data = wizard.ggn_number
        form.has_contract_growers.data = wizard.has_contract_growers
        form.number_of_contract_growers.data = wizard.number_of_contract_growers

    return render_template('wizard/wizard.html', form=form, step=1, total_steps=7, wizard=wizard)


@wizard_bp.route('/step2', methods=['GET', 'POST'])
@login_required
def step2():
    wizard = get_or_create_wizard()
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
        wizard.staff_count = form.staff_count.data
        wizard.current_step = 3
        db.session.commit()
        flash(_('Packhouse details saved!'), 'success')
        return redirect(url_for('wizard.step3'))

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
            except (ValueError, TypeError):
                form.crops_packed.data = []
        form.water_usage.data = wizard.water_usage
        form.energy_usage.data = wizard.energy_usage

    return render_template('wizard/wizard.html', form=form, step=2, total_steps=7, wizard=wizard)


@wizard_bp.route('/step3', methods=['GET', 'POST'])
@login_required
def step3():
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
        flash(_('Farm details saved!'), 'success')
        return redirect(url_for('wizard.step4'))

    form.has_own_fields.data = wizard.has_own_fields
    if wizard.total_farm_size:
        form.total_farm_size.data = wizard.total_farm_size
        form.number_of_fields.data = wizard.number_of_fields
    if wizard.main_crops:
        try:
            form.main_crops.data = json.loads(wizard.main_crops)
        except (ValueError, TypeError):
            form.main_crops.data = []
    if wizard.irrigation_types:
        try:
            form.irrigation_types.data = json.loads(wizard.irrigation_types)
        except (ValueError, TypeError):
            form.irrigation_types.data = []

    return render_template('wizard/wizard.html', form=form, step=3, total_steps=7, wizard=wizard)


@wizard_bp.route('/step4', methods=['GET', 'POST'])
@login_required
def step4():
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
        flash(_('Environmental details saved!'), 'success')
        return redirect(url_for('wizard.step5'))

    form.has_environmental_policy.data = wizard.has_environmental_policy
    form.has_haccp_plan.data = wizard.has_haccp_plan
    form.has_spray_program.data = wizard.has_spray_program
    if wizard.water_treatment_method:
        form.water_treatment_method.data = wizard.water_treatment_method
    form.waste_management_plan.data = wizard.waste_management_plan

    return render_template('wizard/wizard.html', form=form, step=4, total_steps=7, wizard=wizard)


@wizard_bp.route('/step5')
@login_required
def step5():
    wizard = get_or_create_wizard()
    analysis = analyze_control_points(wizard)
    wizard.applicable_control_points = json.dumps(analysis)
    wizard.analysis_completed = True
    wizard.current_step = 6
    db.session.commit()

    return render_template('wizard/step5_analysis.html',
                         step=5, total_steps=7, wizard=wizard, analysis=analysis)


@wizard_bp.route('/step6')
@login_required
def step6():
    wizard = get_or_create_wizard()
    policies_needed = determine_policies_needed(wizard)

    uploaded_policies = {}
    if wizard.policies_generated:
        try:
            uploaded_policies = json.loads(wizard.policies_generated)
        except (ValueError, TypeError):
            uploaded_policies = {}

    wizard.current_step = 7
    db.session.commit()

    return render_template('wizard/step6_policies.html',
                         step=6, total_steps=7, wizard=wizard,
                         policies=policies_needed, uploaded_policies=uploaded_policies)


@wizard_bp.route('/upload-policy/<policy_type>', methods=['POST'])
@login_required
def upload_policy(policy_type):
    from flask import current_app
    from werkzeug.utils import secure_filename

    wizard = get_or_create_wizard()

    if 'policy_file' not in request.files:
        flash(_('No file selected.'), 'warning')
        return redirect(url_for('wizard.step6'))

    file = request.files['policy_file']
    if file.filename == '':
        flash(_('No file selected.'), 'warning')
        return redirect(url_for('wizard.step6'))

    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xlsx', 'xls'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        flash(_('File type not allowed. Please upload PDF, Word, or Excel files.'), 'danger')
        return redirect(url_for('wizard.step6'))

    filename = secure_filename(file.filename)
    stored_name = f"w{wizard.id}_{policy_type}_{filename}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'policies')
    file.save(os.path.join(upload_dir, stored_name))

    uploaded = {}
    if wizard.policies_generated:
        try:
            uploaded = json.loads(wizard.policies_generated)
        except (ValueError, TypeError):
            uploaded = {}

    uploaded[policy_type] = {
        'filename': filename,
        'stored_name': stored_name,
        'uploaded_at': datetime.utcnow().isoformat()
    }
    wizard.policies_generated = json.dumps(uploaded)
    db.session.commit()

    flash(_('Policy "%(filename)s" uploaded successfully.', filename=filename), 'success')
    return redirect(url_for('wizard.step6'))


@wizard_bp.route('/remove-policy/<policy_type>', methods=['POST'])
@login_required
def remove_policy_upload(policy_type):
    from flask import current_app

    wizard = get_or_create_wizard()
    uploaded = {}
    if wizard.policies_generated:
        try:
            uploaded = json.loads(wizard.policies_generated)
        except (ValueError, TypeError):
            uploaded = {}

    if policy_type in uploaded:
        stored_name = uploaded[policy_type].get('stored_name')
        if stored_name:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'policies', stored_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        del uploaded[policy_type]
        wizard.policies_generated = json.dumps(uploaded)
        db.session.commit()
        flash(_('Policy removed.'), 'info')

    return redirect(url_for('wizard.step6'))


@wizard_bp.route('/step7', methods=['GET', 'POST'])
@login_required
def step7():
    wizard = get_or_create_wizard()

    if request.method == 'POST':
        try:
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
                water_treatment_method=wizard.water_treatment_method,
                staff_count=wizard.staff_count,
            )
            db.session.add(org)
            db.session.commit()

            current_user.organization_id = org.id
            wizard.organization_id = org.id
            wizard.completed = True
            wizard.completed_at = datetime.utcnow()
            db.session.commit()

            # Seed GLOBALG.A.P. control points with applicability flags
            seed_control_points_for_org(org, wizard)

            flash(_('Setup complete! %(count)d GLOBALG.A.P. control points loaded for your operation.',
                     count=len(GLOBALGAP_MASTER_POINTS)), 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash(_('Error completing setup: %(error)s', error=str(e)), 'danger')
            return redirect(url_for('wizard.step7'))

    analysis = json.loads(wizard.applicable_control_points) if wizard.applicable_control_points else None

    return render_template('wizard/step7_review.html',
                         step=7, total_steps=7, wizard=wizard, analysis=analysis)


@wizard_bp.route('/generate-policy/<policy_type>')
@login_required
def generate_policy(policy_type):
    wizard = get_or_create_wizard()
    try:
        from app.utils.policy_generator import generate_policy_pdf
        pdf_path = generate_policy_pdf(wizard, policy_type)
        if not os.path.exists(pdf_path):
            flash(_('Error: PDF file not created for %(type)s', type=policy_type), 'danger')
            return redirect(url_for('wizard.step6'))
        return send_file(pdf_path, as_attachment=True,
                         download_name=f'{policy_type}_policy.pdf', mimetype='application/pdf')
    except Exception as e:
        flash(_('Error generating policy PDF: %(error)s', error=str(e)), 'danger')
        return redirect(url_for('wizard.step6'))


# ============================================================
# SEED CONTROL POINTS FOR NEW ORGANIZATION
# ============================================================

def seed_control_points_for_org(org, wizard):
    """Create GLOBALG.A.P. control points for an organization with applicability pre-set."""

    # Build lookup from wizard analysis
    analysis_lookup = {}
    if wizard.applicable_control_points:
        try:
            analysis = json.loads(wizard.applicable_control_points)
            for pt in analysis.get('applicable', []):
                analysis_lookup[pt['code']] = ('applicable', pt.get('reason', 'Applicable'))
            for pt in analysis.get('not_applicable', []):
                analysis_lookup[pt['code']] = ('not_applicable', pt.get('reason', 'Not applicable'))
            for pt in analysis.get('maybe_applicable', []):
                analysis_lookup[pt['code']] = ('maybe', pt.get('reason', 'Review recommended'))
        except (ValueError, TypeError):
            pass

    for mp in GLOBALGAP_MASTER_POINTS:
        code = mp['code']

        if code in analysis_lookup:
            status, reason = analysis_lookup[code]
            is_applicable = status != 'not_applicable'
        else:
            is_applicable = determine_applicability_simple(wizard, mp)
            reason = 'Based on operation type'

        cp = ControlPoint(
            organization_id=org.id,
            code=code,
            section=mp['section'],
            category=mp['category'],
            description=mp['section'] + ' - ' + mp['description'],
            compliance_criteria=mp.get('compliance_criteria', ''),
            criticality=mp['criticality'],
            applies_to=mp.get('applies_to', 'all'),
            is_applicable=is_applicable,
            applicability_reason=reason,
            overlap_hint=mp.get('overlap'),
        )
        db.session.add(cp)

    db.session.commit()


def determine_applicability_simple(wizard, point):
    applies_to = point.get('applies_to', 'all')
    btype = wizard.business_type or ''
    if applies_to == 'all':
        return True
    elif applies_to == 'grower':
        return btype in ('grower', 'packhouse_farms', 'packhouse_mixed') or wizard.has_own_fields
    elif applies_to == 'packhouse':
        return btype in ('packhouse_only', 'packhouse_farms', 'packhouse_contract', 'packhouse_mixed')
    return True


# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

def analyze_control_points(wizard):
    analysis = {'applicable': [], 'not_applicable': [], 'maybe_applicable': []}

    for mp in GLOBALGAP_MASTER_POINTS:
        point_data = {
            'code': mp['code'],
            'section': mp.get('section', ''),
            'category': mp.get('category', ''),
            'description': mp['description'],
            'criticality': mp['criticality'],
            'overlap': mp.get('overlap'),
        }
        result = determine_applicability(wizard, mp)
        point_data['reason'] = result['reason']

        if result['status'] == 'applicable':
            analysis['applicable'].append(point_data)
        elif result['status'] == 'not_applicable':
            analysis['not_applicable'].append(point_data)
        else:
            analysis['maybe_applicable'].append(point_data)

    return analysis


def determine_applicability(wizard, point):
    applies_to = point.get('applies_to', 'all')
    desc = point.get('description', '').lower()
    btype = wizard.business_type or ''
    is_grower = btype in ('grower', 'packhouse_farms', 'packhouse_mixed') or wizard.has_own_fields
    is_packhouse = btype in ('packhouse_only', 'packhouse_farms', 'packhouse_contract', 'packhouse_mixed')

    if applies_to == 'packhouse':
        if is_packhouse:
            return {'status': 'applicable', 'reason': 'Packhouse operation'}
        return {'status': 'not_applicable', 'reason': 'No packhouse operations'}

    if applies_to == 'grower':
        if is_grower:
            return {'status': 'applicable', 'reason': 'Farm/field operations'}
        elif wizard.has_contract_growers:
            return {'status': 'maybe_applicable', 'reason': 'Contract grower oversight may require'}
        return {'status': 'not_applicable', 'reason': 'No farm/field operations'}

    if 'haccp' in desc or 'food safety plan' in desc:
        if is_packhouse:
            return {'status': 'applicable', 'reason': 'HACCP plan ' + ('in place' if wizard.has_haccp_plan else 'required')}
        return {'status': 'maybe_applicable', 'reason': 'Food safety recommended'}

    if 'subcontract' in desc or 'contract' in desc:
        if wizard.has_contract_growers:
            return {'status': 'applicable', 'reason': f'{wizard.number_of_contract_growers or "Multiple"} contract growers'}
        return {'status': 'not_applicable', 'reason': 'No subcontractors/contract growers'}

    return {'status': 'applicable', 'reason': 'General GLOBALG.A.P. requirement'}


def determine_policies_needed(wizard):
    policies = []

    if not wizard.has_haccp_plan:
        policies.append({'name': _('HACCP Plan'), 'type': 'haccp',
                         'description': _('Food safety management system required by GLOBALG.A.P.'), 'priority': 'High'})

    if not wizard.has_spray_program and (wizard.business_type in ['grower', 'packhouse_farms', 'packhouse_mixed'] or wizard.has_own_fields):
        policies.append({'name': _('Spray/IPM Program'), 'type': 'spray_program',
                         'description': _('Integrated Pest Management and spray application records'), 'priority': 'High'})

    if not wizard.has_environmental_policy:
        policies.append({'name': _('Environmental Policy'), 'type': 'environmental',
                         'description': _('Site management and conservation policy'), 'priority': 'Medium'})

    if not wizard.waste_management_plan:
        policies.append({'name': _('Waste Management Plan'), 'type': 'waste_management',
                         'description': _('Waste handling and disposal procedures'), 'priority': 'Medium'})

    # Always offer these
    policies.append({'name': _('Worker Welfare Policy'), 'type': 'worker_welfare',
                     'description': _('Health, safety & welfare policy covering GRASP requirements'), 'priority': 'High'})
    policies.append({'name': _('Worker Training Log'), 'type': 'training_log',
                     'description': _('Template for documenting worker training'), 'priority': 'Low'})
    policies.append({'name': _('Traceability Template'), 'type': 'traceability',
                     'description': _('Product traceability system template'), 'priority': 'Medium'})

    return policies
