from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    remaining_vacation_days = db.Column(db.Integer, default=30)
    remaining_sick_days = db.Column(db.Integer, default=0)
    last_updated_year = db.Column(db.Integer, nullable=True)
    days = db.relationship('UserDay', backref='user', lazy=True)

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class UserDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    day_type = db.Column(db.String(20), nullable=False)
    hours_worked = db.Column(db.Float, nullable=True)