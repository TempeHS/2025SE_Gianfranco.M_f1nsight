# USER MODEL FOR F1NSIGHT
# HANDLES USER AUTHENTICATION AND DATABASE SCHEMA

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    # USER DATABASE MODEL
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        # HASH PASSWORD BEFORE STORING
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # VERIFY PASSWORD AGAINST HASH
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))