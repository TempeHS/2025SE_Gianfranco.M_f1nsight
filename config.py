import os

class config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///f1nsight.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
