from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_message = ''
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'

    # REGISTER BLUEPRINTS WITH PROPER URL PREFIXES
    from app.routes import auth, dashboard, home
    app.register_blueprint(home.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth') 
    app.register_blueprint(dashboard.bp, url_prefix='/dashboard')

    return app