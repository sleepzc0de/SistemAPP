import os
from datetime import timedelta

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    
    # Application settings
    APP_NAME = "Assets Planning Prediction (APP)"
    APP_VERSION = "1.0.0"
    ADMIN_EMAIL = "admin@admin.com"
    
    # External API settings
    SIMAN_API_URL = os.environ.get('SIMAN_API_URL', 'https://api.siman.kemenkeu.go.id')
    SIMAN_API_KEY = os.environ.get('SIMAN_API_KEY', 'dev_key')
    
    SAKTI_API_URL = os.environ.get('SAKTI_API_URL', 'https://api.sakti.kemenkeu.go.id')
    SAKTI_API_KEY = os.environ.get('SAKTI_API_KEY', 'dev_key')

class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    
class ProductionConfig(Config):
    """Production config."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # In production, always use HTTPS
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
class TestingConfig(Config):
    """Testing config."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Get current config
def get_config():
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config[config_name]