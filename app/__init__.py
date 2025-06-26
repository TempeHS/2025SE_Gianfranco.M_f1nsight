from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_caching import Cache
from config import Config
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_message = ''
migrate = Migrate()
cache = Cache()

def format_datetime(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value.strftime('%B %d, %Y')

def country_flag_emoji(country_code):
    """Convert a country code to a flag emoji"""
    if not country_code or len(country_code) != 2:
        return ''
    
    # REGIONAL INDICATOR SYMBOLS OFFSET
    country_code = country_code.upper()
    return chr(ord(country_code[0]) + 127397) + chr(ord(country_code[1]) + 127397)

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # DISABLE CACHING
    app.config['MIME_TYPES'] = {'css': 'text/css'}  # ENSURE CORRECT MIME TYPES

    # INITIALIZE EXTENSIONS
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Initialize caching
    cache.init_app(app)

    # REGISTER FILTERS
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['country_flag_emoji'] = country_flag_emoji
    
    # REGISTER TEMPLATE GLOBALS
    from app.services.jolpica import get_country_code
    app.jinja_env.globals['get_country_code'] = get_country_code

    # REGISTER BLUEPRINTS WITH PROPER URL PREFIXES
    from app.routes import auth, dashboard, home, standings, drivers, errors
    app.register_blueprint(home.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth') 
    app.register_blueprint(dashboard.bp, url_prefix='/dashboard')
    app.register_blueprint(standings.bp, url_prefix='/standings')
    app.register_blueprint(drivers.bp, url_prefix='/drivers')
    app.register_blueprint(errors.bp)  # ERROR HANDLERS - NO PREFIX

    return app