import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY                     = os.environ.get("SECRET_KEY", "dev-secret")
    DEBUG                          = False
    POSTGRESQL_CONNEXION = {
        'host': 'localhost',
        'user': 'postgres',
        'password': '12Monkeys#',
        'database': 'nammglobalBD',
        'port': '5432'
    }
    
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRESQL_CONNEXION['user']}:{POSTGRESQL_CONNEXION['password']}"
        f"@{POSTGRESQL_CONNEXION['host']}:{POSTGRESQL_CONNEXION['port']}"
        f"/{POSTGRESQL_CONNEXION['database']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY                 = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES       = timedelta(hours=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS","24")))
    JWT_REFRESH_TOKEN_EXPIRES      = timedelta(days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS","30")))
    JWT_TOKEN_LOCATION             = ["headers"]
    JWT_HEADER_NAME                = "Authorization"
    JWT_HEADER_TYPE                = "Bearer"
    JWT_BLACKLIST_ENABLED          = True
    JWT_BLACKLIST_TOKEN_CHECKS     = ["access","refresh"]
    FRONTEND_URL                   = os.environ.get("FRONTEND_URL","http://localhost:5500")
    FLUTTERWAVE_SECRET_KEY         = os.environ.get("FLUTTERWAVE_SECRET_KEY","")
    CLOUDINARY_CLOUD_NAME          = os.environ.get("CLOUDINARY_CLOUD_NAME","")
    CLOUDINARY_API_KEY             = os.environ.get("CLOUDINARY_API_KEY","")
    CLOUDINARY_API_SECRET          = os.environ.get("CLOUDINARY_API_SECRET","")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING                 = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

config_map = {"development":DevelopmentConfig,"production":ProductionConfig,"testing":TestingConfig}

def get_config():
    return config_map.get(os.environ.get("FLASK_ENV","development"), DevelopmentConfig)
