import os

class Config:
    def __init__(self):
        self.dev_config = DevelopmentConfig()
        self.prod_config = ProductionConfig()

class DevelopmentConfig():
    ENV = "development"
    HOST = "0.0.0.0"
    DEBUG = True
    PORT = 4000
    MONGODB_DATABASE_URI = 'mongodb://localhost:27017'
    REDIS_DATABASE_URI = 'redis://localhost'
    LLM_API_URI = 'http://localhost:8000'
    CELERY = dict(
        broker_url="redis://localhost",
        result_backend="redis://localhost",
    )

class ProductionConfig():
    ENV = "production"
    DEBUG = False
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = os.environ.get("PORT", '4000')
    MONGODB_DATABASE_URI = os.environ.get('MONGODB_DATABASE_URI', 'mongodb://localhost:27017')
    LLM_API_KEY = os.environ.get("LLM_API_KEY")
    LLM_API_URI = os.environ.get("LLM_API_URI", 'http://localhost:8000')
    REDIS_DATABASE_URI = os.environ.get('REDIS_DATABASE_URI', 'redis://localhost')
    CELERY = dict(
        broker_url=os.environ.get('CELERY_BROKER_URL', "redis://localhost"),
        result_backend=os.environ.get('CELERY_RESULT_BACKEND', "redis://localhost"),
    )