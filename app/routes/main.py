from flask import Blueprint, render_template, flash
from flask_babel import gettext as _

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    flash(_('FruitQMS is running locally'), 'success')
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('index.html')
