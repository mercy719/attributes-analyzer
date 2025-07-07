import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_for_session'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    RESULT_FOLDER = os.environ.get('RESULT_FOLDER', 'results')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # API配置
    DEFAULT_DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-0306bfe4b4974f8f93cc21cd18164167')
    
    # 生产环境配置
    DEBUG = os.environ.get('FLASK_ENV') != 'production'
    PORT = int(os.environ.get('PORT', 5001))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    # 任务配置
    TASKS_FILE = os.environ.get('TASKS_FILE', 'tasks.json')
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
    RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 2))
    
    # 线程池配置
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 5))
    TIMEOUT = int(os.environ.get('TIMEOUT', 300))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 