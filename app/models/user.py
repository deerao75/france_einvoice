from flask_login import UserMixin
from app.extensions import db
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to intermediate table
    companies = db.relationship('UserCompany', back_populates='user')

class UserCompany(db.Model):
    __tablename__ = 'user_companies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    role = db.Column(db.String(20), default='admin')

    # Back_populates must match property names in User and Company
    user = db.relationship('User', back_populates='companies')
    company = db.relationship('Company', back_populates='users')
