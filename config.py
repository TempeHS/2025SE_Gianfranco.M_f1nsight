import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///f1nsight.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache Configuration
    CACHE_TYPE = "SimpleCache"  # Flask-Caching configuration
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default cache timeout
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes session lifetime