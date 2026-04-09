import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = False
    TESTING = False
    
class DevConfig(Config):
    DEBUG = True
    
class ProdConfig(Config):
    DEBUG = False

class TestConfig(Config):
    TESTING = True


    