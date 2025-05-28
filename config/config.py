import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT"))
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    DEFAULT_EPOCH = int(os.getenv("DEFAULT_EPOCH", "100"))
    DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "16"))
    DEFAULT_LEARNING_RATE = float(os.getenv("DEFAULT_LEARNING_RATE", "0.001"))

    DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1', 't')
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Upload and storage configurations
    UPLOAD_FOLDER = 'uploads'
    MODEL_FOLDER = 'models'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    
    # Detection configurations
    DELETE_IMAGES_ON_DETECTION_DELETE = False
    DELETE_IMAGES_ON_RESULT_DELETE = False
    
    # External service configurations (optional)
    FRAUD_LABEL_SERVICE_URL = os.getenv("FRAUD_LABEL_SERVICE_URL", None)
    FRAUD_LABEL_API_KEY = os.getenv("FRAUD_LABEL_API_KEY", None)

    @staticmethod
    def init_app(app):
        upload_path = os.path.join(Config.BASE_DIR, Config.UPLOAD_FOLDER)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        model_path = os.path.join(Config.BASE_DIR, Config.MODEL_FOLDER)
        if not os.path.exists(model_path):
            os.makedirs(model_path)