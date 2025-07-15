from extensions import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    enrolled_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False, cascade='all, delete'))