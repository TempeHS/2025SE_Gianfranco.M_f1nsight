from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from f1nsight.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # endpoint name, not URL

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    from f1nsight.app.routes import auth, dashboard
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)

    return app
