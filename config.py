import os
from datetime import timedelta
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env إذا كان موجوداً
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///library.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Application settings
    DEFAULT_LANGUAGE = 'ar'
    CURRENCY_SYMBOL = 'ج.م'
    DATE_FORMAT = '%d/%m/%Y'
    
    # Alert settings
    DEFAULT_MIN_STOCK_THRESHOLD = 10

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///library.db'

class ProductionConfig(Config):
    DEBUG = False
    # Production-specific settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///library.db'
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS attacks
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)  # Shorter session for production

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 