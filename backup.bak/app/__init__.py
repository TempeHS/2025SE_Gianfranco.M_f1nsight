from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)


    login_manager.login_view = 'auth.login'

    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app