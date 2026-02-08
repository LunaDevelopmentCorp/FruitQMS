from flask import Flask, session, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel, lazy_gettext as _l
from flask_wtf.csrf import CSRFProtect
import os
import json

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()
csrf = CSRFProtect()

LANGUAGES = {
    'en': 'English',
    'fr': 'Fran\u00e7ais',
    'es': 'Espa\u00f1ol',
    'pt': 'Portugu\u00eas',
    'de': 'Deutsch'
}

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qms_local.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(app.root_path, 'translations')
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # File uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    os.makedirs(os.path.join(app.instance_path, 'uploads', 'policies'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Initialize Babel
    babel.init_app(app)

    @babel.localeselector
    def get_locale():
        lang = session.get('lang')
        if lang and lang in LANGUAGES:
            return lang
        return request.accept_languages.best_match(LANGUAGES.keys())

    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = _l('Please log in to access this page.')
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Language switch route
    @app.route('/set-language/<lang>')
    def set_language(lang):
        if lang in LANGUAGES:
            session['lang'] = lang
        return redirect(request.referrer or url_for('main.index'))

    # Inject language data into all templates
    @app.context_processor
    def inject_locale():
        from flask_babel import get_locale as _get_locale
        return {
            'languages': LANGUAGES,
            'current_locale': _get_locale()
        }

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.setup import setup_bp
    from app.routes.wizard import wizard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(wizard_bp)

    # Custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return {}

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
