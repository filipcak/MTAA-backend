import json
import datetime
import os
from flask import Flask, request, jsonify, make_response, Response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# postgresql://username:password@host:port/database
DB_HOST = 'ec2-34-247-151-118.eu-west-1.compute.amazonaws.com'
DB_USER = os.environ["db_user"]
DB_PASSWORD = os.environ["db_p"]
DB_NAME = 'd1vm4vs3lu9a5u'
DB_PORT = '5432'

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

db = SQLAlchemy(app)

from models import *


@app.route('/test/<meno>/<priezvisko>/<id_num>')
def v1_health(meno, priezvisko, id_num):
    doctor = Doctor(name=meno, surname=priezvisko, id_number=id_num, password="1234")
    db.session.add(doctor)
    db.session.commit()

    return "<p>Zapisany pouzivatel</p>"


@app.route('/reg_patient', methods=['POST'])
def registrate_patient():
    try:
        patient_data = request.json['patient_data']
        id_num = patient_data['id_number']
        name = patient_data['name']
        surname = patient_data['surname']
        email = patient_data['email']
        password = patient_data['password']
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_data, id_num, password] or "" in [patient_data, id_num, password]:
        return Response(status=400, mimetype='application/json')


    count = db.session.query(Patient).filter(Patient.id_number == id_num).count()

    if count > 0:
        return Response(status=409, mimetype='application/json')
    else:
        patient = Patient(name=name, surname=surname,
                          id_number=id_num, email=email,
                          password=password)

        db.session.add(patient)
        db.session.commit()
        last_id = db.session.query(Patient).order_by(Patient.id.desc()).first().id
        response = {"result": {"id_patient": last_id}}
        return Response(json.dumps(response), status=201, mimetype='application/json')


@app.route('/login_patient', methods=['POST'])
def login_patient():
    try:
        patient_login_data = request.json['patient_login_data']
        id_number = patient_login_data['id_number']
        password = patient_login_data['password']
    except:
        return Response(status=400, mimetype='application/json')

    if None in [patient_login_data,  id_number, password] \
            or "" in [patient_login_data,  id_number, password]:
        return Response(status=400, mimetype='application/json')


    patient = db.session.query(Patient).filter(Patient.id_number == id_number).first()

    # Zistenie ci existuje dany pouzivatel
    if patient is None:
        return Response(status=401, mimetype='application/json')
    else:
        # Zistenie, ci ma opravnenie vstupit
        if patient.password != password:
            return Response(status=401, mimetype='application/json')
        else:
            response = {"result": {"id_patient": patient.id}}
            return Response(json.dumps(response), status=202, mimetype='application/json')


@app.route('/login_doctor', methods=['POST'])
def login_doctor():
    try:
        doctor_login_data = request.json['doctor_login_data']
        id_number = doctor_login_data['id_number']
        password = doctor_login_data['password']
    except:
        return Response(status=400, mimetype='application/json')

    if None in [doctor_login_data, id_number, password] or "" in [doctor_login_data, id_number, password]:
        return Response(status=400, mimetype='application/json')

    doctor = db.session.query(Doctor).filter(Doctor.id_number == id_number).first()

    # Zistenie ci existuje dany pouzivatel
    if doctor is None:
        return Response(status=401, mimetype='application/json')
    else:
        # Zistenie, ci ma opravnenie vstupit
        if doctor.password != password:
            return Response(status=401, mimetype='application/json')
        else:
            response = {"result": {"id_doctor": doctor.id}}
            return Response(json.dumps(response), status=202, mimetype='application/json')


@app.route('/check_status', methods=['GET'])
def check_status():
    try:
        args = request.args
        patient_id = args.get('patient_id')
        date_string = args.get('date')
        datetime.datetime.fromisoformat(date_string)
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id, date_string] or "" in [patient_id, date_string]:
        return Response(status=400, mimetype='application/json')


    date_time_obj = datetime.datetime.fromisoformat(date_string)
    date_day = date_time_obj.date()
    date_hour = int(date_time_obj.hour)

    record = db.session.query(History).join(Patient_History).filter(Patient.id == patient_id,
                                                                    History.date == date_day).first()
    found = 0
    if record is not None:
        if date_hour < 10:
            if record.morning is not None:
                found = 1
        elif 10 <= date_hour <= 16:
            if record.lunch is not None:
                found = 1
        else:
            if record.evening is not None:
                found = 1
    if found == 1:
        return Response(status=200, mimetype='application/json')
    else:
        return Response(status=204, mimetype='application/json')

@app.route('/get_hist_item', methods=['PUT'])
def get_hist_item():
    try:
        hist_request = request.json['hist_request']
        patient_id = hist_request['patient_id']
        date_full = hist_request['date']
        datetime.datetime.fromisoformat(date_full)
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id, date_full] or "" in [patient_id, date_full]:
        return Response(status=400, mimetype='application/json')

    date_day = datetime.datetime.fromisoformat(date_full).date()
    record = db.session.query(History).join(Patient_History).filter(Patient.id == patient_id,
                                                                    History.date == date_day).first()
    if record is None:
        last_id_hist = db.session.query(History).order_by(History.id.desc()).first().id
        patient_history = Patient_History(patient_id=patient_id, history_id=last_id_hist+1)
        history = History(id=last_id_hist+1, date=date_day)
        db.session.add(history)
        db.session.add(patient_history)
        db.session.commit()

    record = db.session.query(History).join(Patient_History).filter(Patient.id == patient_id,
                                                                    History.date == date_day).first()

    json_response = {"response": {"id_hist_request": record.id, "morning": record.morning, "lunch": record.lunch,
                                  "evening": record.evening}}

    return Response(json.dumps(json_response), status=200, mimetype='application/json')

@app.route('/change_hist_rec', methods=['PUT'])
def change_hist_rec():
    try:
        hist_request = request.json['hist_record']
        id_hist_request = hist_request['id_hist_request']
        morning = hist_request['morning']
        lunch = hist_request['lunch']
        evening = hist_request['evening']
    except:
        return Response(status=400, mimetype='application/json')
    if None in [hist_request, id_hist_request] or "" in [hist_request, id_hist_request]:
        return Response(status=400, mimetype='application/json')

    history = db.session.query(History).filter(History.id == id_hist_request).first()
    if history is None:
        return Response(status=400, mimetype='application/json')

    history.morning = morning
    history.lunch = lunch
    history.evening = evening
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/calculate_sugar')
def calculate_sugar():
    try:
        args = request.args
        sugar = float(args.get('sugar'))
        carbohydrates = float(args.get('carbohydrates'))
    except:
        return Response(status=400, mimetype='application/json')
    if None in [sugar, carbohydrates]:
        return Response(status=400, mimetype='application/json')

    sugar = sugar + carbohydrates/5
    insulin_table = Insulin.query.all()

    for actual_rec in insulin_table:
        if actual_rec.sugar_from <= sugar <= actual_rec.sugar_to:
            json_resp = {"insulin_dose": actual_rec.recommended_insulin, "body": actual_rec.info}
            return Response(json.dumps(json_resp), status=200, mimetype='application/json')

    return Response(status=400, mimetype='application/json')

@app.route('/photo_update', methods=['PUT'])
def update_photo():
    try:
        photo_update = request.json['photo_update']
        id_patient_request = photo_update['patient_id']
        photo_bytes = photo_update['photo']
        photo_type = photo_update['photo_types']
    except:
        return Response(status=400, mimetype='application/json')
    if None in [id_patient_request, photo_update] or "" in [photo_update, id_patient_request]:
        return Response(status=400, mimetype='application/json')

    patient = db.session.query(Patient).filter(Patient.id == id_patient_request).first()
    if patient is None:
        return Response(status=400, mimetype='application/json')
    patient.photo_file = photo_bytes
    patient.photo_type = photo_type
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/remove', methods=['DELETE'])
def delete_patient_doctor():
    try:
        args = request.args
        patient_id = args.get('patient_id')
        doctor_id = args.get('doctor_id')
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id] or "" in [patient_id]:
        return Response(status=400, mimetype='application/json')

    p_d = db.session.query(Doctor_Patient).filter(Doctor_Patient.doctor_id==doctor_id and Doctor_Patient.patient_id==patient_id)
    if p_d is None:
        return Response(status=424, mimetype='application/json')
    db.session.delete(p_d)
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/photo_patient/{id}', methods=['GET'])
def photo_get(id):
    if None in [id] or "" in [id]:
        return Response(status=400, mimetype='application/json')

    patient = db.session.query.with_entities(Patient.photo_file, Patient.photo_file).filter(Patient.id == id)
    if patient.photo_type == None:
        return Response(status=424, mimetype='application/json')
    else:
        response = {"response": {"photo": patient.photo_file, "photo_type": patient.photo_type}}
        return Response(json.dumps(response), status=200, mimetype='application/json')

@app.route('/detail_patient/{id}', methods=['GET'])
def patient_data_get(id):
    if None in [id] or "" in [id]:
        return Response(status=424, mimetype='application/json')

    patient = db.session.query.with_entities(Patient.name, Patient.surname, Patient.id_number, Patient.email).filter(Patient.id == id)
    response = {"response": {"patient_name": patient.name, "patient_surname": patient.surname, "patient_rc": patient.id_number, "patient_mail": patient.email}}
    return Response(json.dumps(response), status=200, mimetype='application/json')

@app.route('/assign_patient', methods=['PUT'])
def assign_patient():
    try:
        assign_info = request.json['assign_info']
        id_doctor = assign_info['id_doctor']
        id_patient = assign_info['id_patient']
    except:
        return Response(status=400, mimetype='application/json')
    if None in [id_doctor, id_patient] or "" in [id_patient, id_doctor]:
        return Response(status=400, mimetype='application/json')

    p_d = db.session.query(Doctor_Patient).filter(Doctor_Patient.doctor_id==id_doctor and Doctor_Patient.patient_id==id_patient)
    if p_d is not None:
        return Response(status=409, mimetype='application/json')
    p_d.doctor_id = id_doctor
    p_d.patient_id = id_patient
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/patient_exist', methods=['GET'])
def patient_rc():
    try:
        args = request.args
        patient_id = args.get('id_number_patient')
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id] or "" in [patient_id]:
        return Response(status=400, mimetype='application/json')

    patient = db.session.query.with_entities(Patient.id_number).filter(Patient.id == patient_id)
    if patient.id_number is not None:
        return Response(status=204, mimetype='application/json')
    else:
        return Response(status=200, mimetype='application/json')

@app.route('/get_patients/{id_doctor}', methods=['GET'])
def patient_data_get(id_doctor):
    if None in [id_doctor] or "" in [id_doctor]:
        return Response(status=404, mimetype='application/json')

    patients = db.session.query(Doctor_Patient).join(Patient).filter(Doctor_Patient.doctor_id == id_doctor)
    if patients is None:    # doktor nema pacientov
        return Response(status=404, mimetype='application/json')
    data = []
    for patient in patients:
        data.append({"id_patient": patient.id, "id_number": patient.id_number})
    response = {"patients": data}
    return Response(json.dumps(response), status=200, mimetype='application/json')


@app.route('/napln_insulin')
def napln_insulin():
    insulin1 = Insulin(sugar_from=0, sugar_to=3, recommended_insulin=0, info="Ihneď si dajte rýchle pôsobiace sa charidy v množstve od 20-40g")
    insulin2 = Insulin(sugar_from=3, sugar_to=4, recommended_insulin=0, info="Dajte si sacharidy v množstve 10-20g")
    insulin3 = Insulin(sugar_from=4, sugar_to=7, recommended_insulin=0, info="Hladina je v poriadku")
    insulin4 = Insulin(sugar_from=7, sugar_to=11, recommended_insulin=2, info="Zvýšte si dávku inzulínu")
    insulin5 = Insulin(sugar_from=11, sugar_to=15, recommended_insulin=3, info="Zvýšte si dávku inzulínu")
    insulin6 = Insulin(sugar_from=15, sugar_to=22, recommended_insulin=4, info="Zvýšte si dávku inzulínu")
    insulin7 = Insulin(sugar_from=22, sugar_to=30, recommended_insulin=5, info="Zvýšte si dávku inzulínu, ihneď vykonajte skúšku moči na acetón")

    db.session.add(insulin1)
    db.session.add(insulin2)
    db.session.add(insulin3)
    db.session.add(insulin4)
    db.session.add(insulin5)
    db.session.add(insulin6)
    db.session.add(insulin7)

    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/napln_doktor')
def napln_doktor():
    doctor1 = Doctor(name="Matej", surname="Hornozemský", id_number="123456/0000", password="1234")
    doctor2 = Doctor(name="Juraj", surname="Veľký", id_number="135789/1578", password="0000")
    doctor3 = Doctor(name="Franta", surname="Dolnozemský", id_number="123458/0000", password="1234")

    db.session.add(doctor1)
    db.session.add(doctor2)
    db.session.add(doctor3)
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/napln_pacient')
def napln_pacient():
    patient1 = Patient(name="Daniel", surname="Petrov", id_number="123457/0123", password="1234", email="dan.pet@gmail.com")
    patient2 = Patient(name="Peter", surname="Malý", id_number="122789/1578", password="0kom", email="peter.maly@szm.sk")
    patient3 = Patient(name="Božena", surname="Svetlá", id_number="003456/0000", password="1589")

    db.session.add(patient1)
    db.session.add(patient2)
    db.session.add(patient3)
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/napln_doktor_pacient')
def napln_doktor_pacient():
    doctor_patient1 = Doctor_Patient(doctor_id=1, patient_id=1)
    doctor_patient2 = Doctor_Patient(doctor_id=3, patient_id=2)

    db.session.add(doctor_patient1)
    db.session.add(doctor_patient2)
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/napln_historia')
def napln_historia():
    history1 = History(date=datetime.datetime.strptime("2022-03-20", '%Y-%m-%d').date(), morning=4.7, lunch=4, evening=3.8)
    history2 = History(date=datetime.datetime.strptime("2022-03-21", '%Y-%m-%d').date(), morning=5, lunch=8.4, evening=7.6)
    history3 = History(date=datetime.datetime.strptime("2022-03-22", '%Y-%m-%d').date(), morning=2.8, lunch=4, evening=5.2)

    db.session.add(history1)
    db.session.add(history2)
    db.session.add(history3)
    db.session.commit()
    return Response(status=200, mimetype='application/json')

@app.route('/napln_pacient_historia')
def napln_pacient_historia():
    patient_history1 = Patient_History(patient_id=1, history_id=1)
    patient_history2 = Patient_History(patient_id=1, history_id=2)
    patient_history3 = Patient_History(patient_id=1, history_id=3)

    db.session.add(patient_history1)
    db.session.add(patient_history2)
    db.session.add(patient_history3)
    db.session.commit()
    return Response(status=200, mimetype='application/json')
