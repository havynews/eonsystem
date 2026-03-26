import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-change-me")
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///eonsystem.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # App settings
    APP_NAME = os.getenv("APP_NAME", "E.ON System")
    APP_URL = os.getenv("APP_URL", "http://localhost:5000")

    # Withdrawal
    MIN_WITHDRAWAL_AMOUNT = float(os.getenv("MIN_WITHDRAWAL_AMOUNT", "70"))

    # Upload settings
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))  # 16MB
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "app/static/uploads")

    # Mail (optional)
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DEV_DATABASE_URL", "sqlite:///eonsystem_dev.db")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


# Map string names to config classes
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Return the config class based on the FLASK_ENV environment variable."""
    env = os.getenv("FLASK_ENV", "default").lower()
    return config_map.get(env, DevelopmentConfig)