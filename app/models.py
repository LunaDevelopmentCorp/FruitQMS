from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='viewer')  # qa_manager, auditor, viewer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Foreign key to organization
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    org_type = db.Column(db.String(50), nullable=False)  # 'packhouse' or 'grower'
    ggn_number = db.Column(db.String(50), unique=True, nullable=True)
    audit_scope = db.Column(db.String(20), nullable=True)  # 'GFS' or 'SMART'

    # Address details
    address = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    local_laws_notes = db.Column(db.Text, nullable=True)

    # Packhouse-specific fields
    packing_system = db.Column(db.String(100), nullable=True)
    water_usage_m3_day = db.Column(db.Float, nullable=True)
    crops_packed = db.Column(db.Text, nullable=True)  # JSON stored as text
    water_treatment_method = db.Column(db.String(200), nullable=True)
    energy_usage_kwh_month = db.Column(db.Float, nullable=True)
    energy_systems = db.Column(db.Text, nullable=True)  # JSON stored as text
    staff_count = db.Column(db.Integer, nullable=True)
    supervisors_count = db.Column(db.Integer, nullable=True)
    avg_working_hours_per_week = db.Column(db.Float, nullable=True)
    shifts_per_day = db.Column(db.Integer, nullable=True)

    # File paths
    haccp_plan = db.Column(db.String(255), nullable=True)
    quality_control_checklist = db.Column(db.String(255), nullable=True)

    # Protocols
    intake_protocols = db.Column(db.Text, nullable=True)
    online_monitoring = db.Column(db.Text, nullable=True)
    final_packing_inspections = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    users = db.relationship('User', backref='organization', lazy=True)
    growers = db.relationship('Grower', backref='organization', lazy=True)

    def __repr__(self):
        return f'<Organization {self.name}>'


class Grower(db.Model):
    __tablename__ = 'growers'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    grower_code = db.Column(db.String(50), nullable=False)
    grower_name = db.Column(db.String(200), nullable=False)
    field_name = db.Column(db.String(200), nullable=False)
    size_hectares = db.Column(db.Float, nullable=True)
    gps_coordinates = db.Column(db.String(100), nullable=True)
    crop_type = db.Column(db.String(100), nullable=True)

    spray_program = db.Column(db.Text, nullable=True)
    harvest_schedule = db.Column(db.Text, nullable=True)
    fertilisation_plan = db.Column(db.Text, nullable=True)
    irrigation_type = db.Column(db.String(100), nullable=True)
    planting_date = db.Column(db.Date, nullable=True)
    pruning_method = db.Column(db.Text, nullable=True)

    conservation_points = db.Column(db.Text, nullable=True)
    biodiversity_measures = db.Column(db.Text, nullable=True)
    delicate_environments = db.Column(db.Boolean, default=False)
    delicate_environments_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Grower {self.grower_code} - {self.grower_name}>'


class ControlPoint(db.Model):
    __tablename__ = 'control_points'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    code = db.Column(db.String(20), nullable=False)  # e.g., AF 1.1.1
    category = db.Column(db.String(100), nullable=False)  # e.g., Site Management
    description = db.Column(db.Text, nullable=False)
    criticality = db.Column(db.String(50), nullable=False)  # Major Must, Minor Must, Recommendation

    compliance_status = db.Column(db.String(50), nullable=True)  # Compliant, Non-compliant, N/A
    evidence_file = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    overlap_hint = db.Column(db.Text, nullable=True)  # e.g., "Overlaps with GRASP & SMETA"

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ControlPoint {self.code}>'


class SetupWizard(db.Model):
    __tablename__ = 'setup_wizards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    # Step 1: Business Type
    business_type = db.Column(db.String(50), nullable=True)
    audit_scope = db.Column(db.String(20), nullable=True)  # 'GFS' or 'SMART'
    ggn_number = db.Column(db.String(50), nullable=True)
    has_contract_growers = db.Column(db.Boolean, default=False)
    number_of_contract_growers = db.Column(db.Integer, nullable=True)

    # Step 2: Packhouse Details
    packhouse_name = db.Column(db.String(200), nullable=True)
    packhouse_address = db.Column(db.Text, nullable=True)
    packhouse_country = db.Column(db.String(100), nullable=True)
    packhouse_latitude = db.Column(db.Float, nullable=True)
    packhouse_longitude = db.Column(db.Float, nullable=True)
    packing_system_type = db.Column(db.String(100), nullable=True)
    crops_packed = db.Column(db.Text, nullable=True)  # JSON array
    water_usage = db.Column(db.Float, nullable=True)
    energy_usage = db.Column(db.Float, nullable=True)
    staff_count = db.Column(db.Integer, nullable=True)

    # Step 3: Grower/Field Details
    has_own_fields = db.Column(db.Boolean, default=False)
    total_farm_size = db.Column(db.Float, nullable=True)
    number_of_fields = db.Column(db.Integer, nullable=True)
    main_crops = db.Column(db.Text, nullable=True)  # JSON array
    irrigation_types = db.Column(db.Text, nullable=True)

    # Step 4: Environment & Compliance
    has_environmental_policy = db.Column(db.Boolean, default=False)
    has_haccp_plan = db.Column(db.Boolean, default=False)
    has_spray_program = db.Column(db.Boolean, default=False)
    water_treatment_method = db.Column(db.String(200), nullable=True)
    waste_management_plan = db.Column(db.Boolean, default=False)
    local_regulations_notes = db.Column(db.Text, nullable=True)

    # Step 5: GLOBALG.A.P. Analysis Results (JSON)
    applicable_control_points = db.Column(db.Text, nullable=True)  # JSON
    analysis_completed = db.Column(db.Boolean, default=False)

    # Step 6: Policy Generation
    policies_generated = db.Column(db.Text, nullable=True)  # JSON list of generated policies

    # Wizard Progress
    current_step = db.Column(db.Integer, default=1)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='setup_wizards')

    def __repr__(self):
        return f'<SetupWizard {self.id} - Step {self.current_step}>'


class GrowerControlPoint(db.Model):
    """Individual control point compliance tracking for each grower (SMART multi-site)"""
    __tablename__ = 'grower_control_points'

    id = db.Column(db.Integer, primary_key=True)
    grower_id = db.Column(db.Integer, db.ForeignKey('growers.id'), nullable=False)
    control_point_id = db.Column(db.Integer, db.ForeignKey('control_points.id'), nullable=False)

    # Grower-specific compliance data
    compliance_status = db.Column(db.String(50), default='N/A')  # Compliant, Non-compliant, N/A
    evidence_file = db.Column(db.String(255), nullable=True)
    implementation_notes = db.Column(db.Text, nullable=True)

    # Common response flag - indicates if this response can be copied to other growers
    is_common_response = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    grower = db.relationship('Grower', backref='control_points', lazy=True)
    control_point = db.relationship('ControlPoint', backref='grower_records', lazy=True)

    # Unique constraint: one record per grower per control point
    __table_args__ = (
        db.UniqueConstraint('grower_id', 'control_point_id', name='unique_grower_control_point'),
    )

    def __repr__(self):
        return f'<GrowerControlPoint Grower:{self.grower_id} CP:{self.control_point_id}>'
