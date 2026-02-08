from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Optional, Email
from wtforms.widgets import ListWidget, CheckboxInput
from app.utils.countries import get_country_choices

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class Step1BusinessTypeForm(FlaskForm):
    business_type = SelectField('Business Type *', choices=[
        ('', 'Select Type'),
        ('grower', 'Growers Only'),
        ('packhouse_only', 'Packhouse Only'),
        ('packhouse_farms', 'Packhouse and Farms'),
        ('packhouse_contract', 'Packhouse + Contract Growers'),
        ('packhouse_mixed', 'Packhouse + Own Farm + Contract Growers')
    ], validators=[DataRequired()])

    audit_scope = SelectField('GLOBALG.A.P. Audit Scope *', choices=[
        ('', 'Select Audit Scope'),
        ('GFS', 'GFS (Individual Producer) - Single unified checklist'),
        ('SMART', 'SMART (Multi-Site) - Central system + individual grower checklists')
    ], validators=[DataRequired()])

    ggn_number = StringField('GLOBALG.A.P. Number (GGN)', validators=[Optional()])

    has_contract_growers = BooleanField('Do you have contract growers?')
    number_of_contract_growers = IntegerField('How many contract growers?', validators=[Optional()])


class Step2PackhouseForm(FlaskForm):
    number_of_packhouses = IntegerField('How many packhouses do you operate?', validators=[Optional()])
    packhouse_name = StringField('Packhouse Name *', validators=[DataRequired()])
    packhouse_address = TextAreaField('Address *', validators=[DataRequired()])
    packhouse_country = SelectField('Country *', choices=get_country_choices(), validators=[DataRequired()])

    packhouse_latitude = FloatField('Latitude (GPS)', validators=[Optional()])
    packhouse_longitude = FloatField('Longitude (GPS)', validators=[Optional()])

    packing_system_type = SelectField('Packing System', choices=[
        ('', 'Select System'),
        ('manual', 'Manual'),
        ('semi_automated', 'Semi-Automated'),
        ('fully_automated', 'Fully Automated')
    ])

    crops_packed = MultiCheckboxField('Crops Packed', choices=[
        ('apples', 'Apples'),
        ('pears', 'Pears'),
        ('citrus', 'Citrus'),
        ('stone_fruit', 'Stone Fruit'),
        ('berries', 'Berries'),
        ('grapes', 'Grapes'),
        ('mangoes', 'Mangoes'),
        ('avocados', 'Avocados'),
        ('tropical', 'Other Tropical Fruit'),
        ('melons', 'Melons'),
        ('other', 'Other')
    ])

    water_usage = FloatField('Water Usage per packhouse (m³/day)', validators=[Optional()])
    energy_usage = FloatField('Energy Usage per packhouse (kWh/month)', validators=[Optional()])


class Step3GrowerFieldForm(FlaskForm):
    has_own_fields = BooleanField('Do you have your own fields/orchards?')
    total_farm_size = FloatField('Total Farm Size (hectares)', validators=[Optional()])
    number_of_fields = IntegerField('Number of Fields/Blocks', validators=[Optional()])

    main_crops = MultiCheckboxField('Main Crops Grown', choices=[
        ('apples', 'Apples'),
        ('pears', 'Pears'),
        ('citrus', 'Citrus'),
        ('peaches', 'Peaches'),
        ('nectarines', 'Nectarines'),
        ('plums', 'Plums'),
        ('cherries', 'Cherries'),
        ('berries', 'Berries'),
        ('grapes', 'Table Grapes'),
        ('mangoes', 'Mangoes'),
        ('avocados', 'Avocados'),
        ('bananas', 'Bananas'),
        ('other', 'Other')
    ])

    irrigation_types = MultiCheckboxField('Irrigation Types Used', choices=[
        ('drip', 'Drip Irrigation'),
        ('sprinkler', 'Sprinkler'),
        ('flood', 'Flood Irrigation'),
        ('micro_sprinkler', 'Micro-Sprinkler'),
        ('none', 'Rainfed Only')
    ])


class Step4EnvironmentForm(FlaskForm):
    has_environmental_policy = BooleanField('Do you have an environmental policy?')
    has_haccp_plan = BooleanField('Do you have a HACCP plan?')
    has_spray_program = BooleanField('Do you have a documented spray/IPM program?')

    water_treatment_method = SelectField('What is your water treatment method?', choices=[
        ('', 'Select Method'),
        ('chlorination', 'Chlorination'),
        ('uv', 'UV Treatment'),
        ('ozone', 'Ozone'),
        ('filtration', 'Filtration Only'),
        ('none', 'No Treatment'),
        ('other', 'Other')
    ])

    waste_management_plan = BooleanField('Do you have a waste management plan?')
