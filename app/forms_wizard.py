from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, SelectMultipleField, FileField
from wtforms.validators import DataRequired, Optional, Email
from wtforms.widgets import ListWidget, CheckboxInput
from flask_babel import lazy_gettext as _l
from app.utils.countries import get_country_choices

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class Step1BusinessTypeForm(FlaskForm):
    business_type = SelectField(_l('Business Type *'), choices=[
        ('', _l('Select Type')),
        ('grower', _l('Growers Only')),
        ('packhouse_only', _l('Packhouse Only')),
        ('packhouse_farms', _l('Packhouse and Farms')),
        ('packhouse_contract', _l('Packhouse + Contract Growers')),
        ('packhouse_mixed', _l('Packhouse + Own Farm + Contract Growers'))
    ], validators=[DataRequired()])

    audit_scope = SelectField(_l('GLOBALG.A.P. Audit Scope *'), choices=[
        ('', _l('Select Audit Scope')),
        ('GFS', _l('GFS (Individual Producer) - Single unified checklist')),
        ('SMART', _l('SMART (Multi-Site) - Central system + individual grower checklists'))
    ], validators=[DataRequired()])

    ggn_number = StringField(_l('GLOBALG.A.P. Number (GGN)'), validators=[Optional()])

    has_contract_growers = BooleanField(_l('Do you have contract growers?'))
    number_of_contract_growers = IntegerField(_l('How many contract growers?'), validators=[Optional()])


class Step2PackhouseForm(FlaskForm):
    number_of_packhouses = IntegerField(_l('How many packhouses do you operate?'), validators=[Optional()])
    packhouse_name = StringField(_l('Packhouse Name *'), validators=[DataRequired()])
    packhouse_address = TextAreaField(_l('Address *'), validators=[DataRequired()])
    packhouse_country = SelectField(_l('Country *'), choices=get_country_choices(), validators=[DataRequired()])

    packhouse_latitude = FloatField(_l('Latitude (GPS)'), validators=[Optional()])
    packhouse_longitude = FloatField(_l('Longitude (GPS)'), validators=[Optional()])

    packing_system_type = SelectField(_l('Packing System'), choices=[
        ('', _l('Select System')),
        ('manual', _l('Manual')),
        ('semi_automated', _l('Semi-Automated')),
        ('fully_automated', _l('Fully Automated'))
    ])

    crops_packed = MultiCheckboxField(_l('Crops Packed'), choices=[
        ('apples', 'Apples'),
        ('pears', 'Pears'),
        ('citrus', 'Citrus'),
        ('stone_fruit', 'Stone Fruit'),
        ('berries', 'Berries'),
        ('grapes', 'Grapes'),
        ('mangoes', 'Mangoes'),
        ('avocados', 'Avocados'),
        ('tropical', _l('Other Tropical Fruit')),
        ('melons', 'Melons'),
        ('other', _l('Other'))
    ])

    water_usage = FloatField(_l('Water Usage per packhouse (m\u00b3/day)'), validators=[Optional()])
    energy_usage = FloatField(_l('Energy Usage per packhouse (kWh/month)'), validators=[Optional()])


class Step3GrowerFieldForm(FlaskForm):
    has_own_fields = BooleanField(_l('Do you have your own fields/orchards?'))
    total_farm_size = FloatField(_l('Total Farm Size (hectares)'), validators=[Optional()])
    number_of_fields = IntegerField(_l('Number of Fields/Blocks'), validators=[Optional()])

    main_crops = MultiCheckboxField(_l('Main Crops Grown'), choices=[
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
        ('other', _l('Other'))
    ])

    irrigation_types = MultiCheckboxField(_l('Irrigation Types Used'), choices=[
        ('drip', _l('Drip Irrigation')),
        ('sprinkler', _l('Sprinkler')),
        ('flood', _l('Flood Irrigation')),
        ('micro_sprinkler', _l('Micro-Sprinkler')),
        ('none', _l('Rainfed Only'))
    ])


class Step4EnvironmentForm(FlaskForm):
    has_environmental_policy = BooleanField(_l('Do you have an environmental policy?'))
    has_haccp_plan = BooleanField(_l('Do you have a HACCP plan?'))
    has_spray_program = BooleanField(_l('Do you have a documented spray/IPM program?'))

    water_treatment_method = SelectField(_l('What is your water treatment method?'), choices=[
        ('', _l('Select Method')),
        ('chlorination', _l('Chlorination')),
        ('uv', _l('UV Treatment')),
        ('ozone', _l('Ozone')),
        ('filtration', _l('Filtration Only')),
        ('none', _l('No Treatment')),
        ('other', _l('Other'))
    ])

    waste_management_plan = BooleanField(_l('Do you have a waste management plan?'))
