import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis for Background Jobs
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Uploads
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'storage')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
