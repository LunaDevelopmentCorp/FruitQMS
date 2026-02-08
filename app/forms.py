from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, DateField, FileField
from wtforms.validators import DataRequired, Email, Length, Optional
from flask_babel import lazy_gettext as _l
from app.utils.countries import get_country_choices

class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])


class PackhouseSetupForm(FlaskForm):
    address = TextAreaField(_l('Address *'), validators=[DataRequired()])
    country = SelectField(_l('Country *'), choices=get_country_choices(), validators=[DataRequired()])
    local_laws_notes = TextAreaField(_l('Local Laws & Regulations Notes'))

    packing_system = SelectField(_l('Packing System'), choices=[
        ('', _l('Select System')),
        ('manual', _l('Manual')),
        ('semi_automated', _l('Semi-Automated')),
        ('fully_automated', _l('Fully Automated'))
    ])
    water_usage_m3_day = FloatField(_l('Water Usage (m\u00b3/day)'), validators=[Optional()])
    water_treatment_method = StringField(_l('Water Treatment Method'))
    energy_usage_kwh_month = FloatField(_l('Energy Usage (kWh/month)'), validators=[Optional()])
    staff_count = IntegerField(_l('Staff Count'), validators=[Optional()])
    supervisors_count = IntegerField(_l('Supervisors Count'), validators=[Optional()])
    avg_working_hours_per_week = FloatField(_l('Avg Working Hours/Week'), validators=[Optional()])
    shifts_per_day = IntegerField(_l('Shifts per Day'), validators=[Optional()])

    intake_protocols = TextAreaField(_l('Intake Protocols'))
    online_monitoring = TextAreaField(_l('Online Monitoring'))
    final_packing_inspections = TextAreaField(_l('Final Packing Inspections'))


class GrowerSetupForm(FlaskForm):
    grower_code = StringField(_l('Grower Code *'), validators=[DataRequired()])
    grower_name = StringField(_l('Grower Name *'), validators=[DataRequired()])
    field_name = StringField(_l('Field Name *'), validators=[DataRequired()])
    size_hectares = FloatField(_l('Size (hectares)'), validators=[Optional()])
    gps_coordinates = StringField(_l('GPS Coordinates'))
    crop_type = SelectField(_l('Crop Type'), choices=[
        ('', _l('Select Crop')),
        # Pome Fruit
        ('apples', 'Apples'),
        ('pears', 'Pears'),
        ('quince', 'Quince'),
        # Stone Fruit
        ('peaches', 'Peaches'),
        ('nectarines', 'Nectarines'),
        ('plums', 'Plums'),
        ('apricots', 'Apricots'),
        ('cherries', 'Cherries'),
        # Citrus
        ('oranges', 'Oranges'),
        ('lemons', 'Lemons'),
        ('limes', 'Limes'),
        ('grapefruit', 'Grapefruit'),
        ('mandarins', 'Mandarins/Clementines'),
        ('pomelo', 'Pomelo'),
        # Berries
        ('strawberries', 'Strawberries'),
        ('blueberries', 'Blueberries'),
        ('raspberries', 'Raspberries'),
        ('blackberries', 'Blackberries'),
        ('cranberries', 'Cranberries'),
        # Grapes
        ('table_grapes', 'Table Grapes'),
        ('wine_grapes', 'Wine Grapes'),
        # Tropical Fruit
        ('mangoes', 'Mangoes'),
        ('avocados', 'Avocados'),
        ('bananas', 'Bananas'),
        ('pineapples', 'Pineapples'),
        ('papayas', 'Papayas'),
        ('passion_fruit', 'Passion Fruit'),
        ('litchis', 'Litchis'),
        ('guavas', 'Guavas'),
        ('dragon_fruit', 'Dragon Fruit'),
        ('kiwi', 'Kiwifruit'),
        ('pomegranates', 'Pomegranates'),
        ('figs', 'Figs'),
        ('dates', 'Dates'),
        # Melons
        ('watermelon', 'Watermelon'),
        ('cantaloupe', 'Cantaloupe/Rockmelon'),
        ('honeydew', 'Honeydew Melon'),
        # Other
        ('persimmons', 'Persimmons'),
        ('rhubarb', 'Rhubarb'),
        ('other', _l('Other'))
    ])

    spray_program = TextAreaField(_l('Spray Program'))
    harvest_schedule = TextAreaField(_l('Harvest Schedule'))
    fertilisation_plan = TextAreaField(_l('Fertilisation Plan'))
    irrigation_type = StringField(_l('Irrigation Type'))
    planting_date = DateField(_l('Planting Date'), validators=[Optional()])
    pruning_method = TextAreaField(_l('Pruning Method'))

    conservation_points = TextAreaField(_l('Conservation Points'))
    biodiversity_measures = TextAreaField(_l('Biodiversity Measures'))
    delicate_environments = BooleanField(_l('Delicate Environments Present'))
    delicate_environments_notes = TextAreaField(_l('Delicate Environments Notes'))
