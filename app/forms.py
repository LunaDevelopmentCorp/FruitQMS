from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, DateField, FileField
from wtforms.validators import DataRequired, Email, Length, Optional
from app.utils.countries import get_country_choices

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class PackhouseSetupForm(FlaskForm):
    address = TextAreaField('Address *', validators=[DataRequired()])
    country = SelectField('Country *', choices=get_country_choices(), validators=[DataRequired()])
    local_laws_notes = TextAreaField('Local Laws & Regulations Notes')

    packing_system = SelectField('Packing System', choices=[
        ('', 'Select System'),
        ('manual', 'Manual'),
        ('semi_automated', 'Semi-Automated'),
        ('fully_automated', 'Fully Automated')
    ])
    water_usage_m3_day = FloatField('Water Usage (m³/day)', validators=[Optional()])
    water_treatment_method = StringField('Water Treatment Method')
    energy_usage_kwh_month = FloatField('Energy Usage (kWh/month)', validators=[Optional()])
    staff_count = IntegerField('Staff Count', validators=[Optional()])
    supervisors_count = IntegerField('Supervisors Count', validators=[Optional()])
    avg_working_hours_per_week = FloatField('Avg Working Hours/Week', validators=[Optional()])
    shifts_per_day = IntegerField('Shifts per Day', validators=[Optional()])

    intake_protocols = TextAreaField('Intake Protocols')
    online_monitoring = TextAreaField('Online Monitoring')
    final_packing_inspections = TextAreaField('Final Packing Inspections')


class GrowerSetupForm(FlaskForm):
    grower_code = StringField('Grower Code *', validators=[DataRequired()])
    grower_name = StringField('Grower Name *', validators=[DataRequired()])
    field_name = StringField('Field Name *', validators=[DataRequired()])
    size_hectares = FloatField('Size (hectares)', validators=[Optional()])
    gps_coordinates = StringField('GPS Coordinates')
    crop_type = SelectField('Crop Type', choices=[
        ('', 'Select Crop'),
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
        ('other', 'Other')
    ])

    spray_program = TextAreaField('Spray Program')
    harvest_schedule = TextAreaField('Harvest Schedule')
    fertilisation_plan = TextAreaField('Fertilisation Plan')
    irrigation_type = StringField('Irrigation Type')
    planting_date = DateField('Planting Date', validators=[Optional()])
    pruning_method = TextAreaField('Pruning Method')

    conservation_points = TextAreaField('Conservation Points')
    biodiversity_measures = TextAreaField('Biodiversity Measures')
    delicate_environments = BooleanField('Delicate Environments Present')
    delicate_environments_notes = TextAreaField('Delicate Environments Notes')
