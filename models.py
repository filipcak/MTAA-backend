from flask_sqlalchemy import SQLAlchemy
from typing import Callable
from app import db


# error fix cause python :)
class OwnSQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Integer: Callable
    Float: Callable
    Text: Callable
    DateTime: Callable
    ForeignKey: Callable
    relationship: Callable
    backref: Callable

# models
class Doctor(db.Model):
    __table_args__ = {'schema': 'dbs_mtaa'}
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    id_number = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Patient(db.Model):
    __table_args__ = {'schema': 'dbs_mtaa'}
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    id_number = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50))
    photo_file = db.Column(db.String(50))
    photo_type = db.Column(db.String(50))

    children = db.relationship("Patient_History", back_populates="patient")

class Insulin(db.Model):
    __table_args__ = {'schema': 'dbs_mtaa'}
    __tablename__ = 'insulin'
    id = db.Column(db.Integer, primary_key=True)
    sugar_from = db.Column(db.Float)
    sugar_to = db.Column(db.Float)
    recommended_insulin = db.Column(db.Float)
    info = db.Column(db.Text)

class History(db.Model):
    __table_args__ = {'schema': 'dbs_mtaa'}
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, unique=True, nullable=False)
    morning = db.Column(db.Float)
    lunch = db.Column(db.Float)
    evening = db.Column(db.Float)

    #children = db.relationship("Patient_History", back_populates="patient")

class Doctor_Patient(db.Model):
    __table_args__ = (db.PrimaryKeyConstraint('doctor_id', 'patient_id'), {'schema': 'dbs_mtaa'})
    __tablename__ = 'doctor_patient'

    doctor_id = db.Column(db.Integer, db.ForeignKey('dbs_mtaa.doctor.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('dbs_mtaa.patient.id'), nullable=False)

class Patient_History(db.Model):
    __table_args__ = (db.PrimaryKeyConstraint('patient_id', 'history_id'), {'schema': 'dbs_mtaa'})
    __tablename__ = 'patient_history'
    patient_id = db.Column(db.Integer, db.ForeignKey('dbs_mtaa.patient.id'), nullable=False)
    history_id = db.Column(db.Integer, db.ForeignKey('dbs_mtaa.history.id'), nullable=False)

    patient = db.relationship("Patient", back_populates="children")






