from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_message = ''
migrate = Migrate()

def format_datetime(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value.strftime('%B %d, %Y')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    
    # REGISTER DATETIME FILTER
    app.jinja_env.filters['datetime'] = format_datetime

    # REGISTER BLUEPRINTS WITH PROPER URL PREFIXES
    from app.routes import auth, dashboard, home, standings, drivers, errors
    app.register_blueprint(home.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth') 
    app.register_blueprint(dashboard.bp, url_prefix='/dashboard')
    app.register_blueprint(standings.bp, url_prefix='/standings')
    app.register_blueprint(drivers.bp, url_prefix='/drivers')
    app.register_blueprint(errors.bp)  # Error handlers don't need a URL prefix

    return app