from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
session_manager = Session()
scheduler = BackgroundScheduler()