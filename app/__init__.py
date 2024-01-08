from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from app.config.config import Config
from pymongo import MongoClient
from .utils import celery_init_app
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
CORS(app)

config = Config().dev_config
app.env = config.ENV

db = MongoClient(config.MONGODB_DATABASE_URI).automated_summaries
socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    message_queue=config.REDIS_DATABASE_URI)

app.config["CELERY"] = config.CELERY
celery = celery_init_app(app)
celery.set_default()

from app.controllers.socket_controller import *

from app.controllers.book_controller import books
from app.controllers.summary_controller import summary
app.register_blueprint(books, url_prefix="/books")
app.register_blueprint(summary, url_prefix="/summary")

