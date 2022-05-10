import json
import datetime
import os
from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# postgresql://username:password@host:port/database
DB_USER = os.environ["db_user"]
DB_PASSWORD = os.environ["db_p"]
DB_NAME = 'mtaa'
DB_PORT = '25060'
DB_HOST = 'app-d4835b9f-e235-4b21-bcc9-dfd9b2b8fb04-do-user-11023320-0.b.db.ondigitalocean.com'

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql://{}:{}@{}:{}/{}'.format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

db = SQLAlchemy(app)

from models import *


def isAuthorisated(request, id, doctor):
    try:
        auth = request.authorization
        username = auth.username
        password = auth.password
    except:
        return False
    if None in [username, password] or "" in [username, password]:
        return False

    if doctor == True:
        doctor = db.session.query(Doctor).filter(Doctor.id_number == username,
                                                 Doctor.password == password).first()
        if doctor is None:
            return False
        return True
    else:
        patient = db.session.query(Patient).filter(Patient.id == id, Patient.id_number == username,
                                                   Patient.password == password).first()
        if patient is None:
            return False
        return True

def isAuthorisatedWS(user, pwd, id, doctor):
    try:
        username = user
        password = pwd
    except:
        return False
    if None in [username, password] or "" in [username, password]:
        return False

    if doctor == True:
        doctor = db.session.query(Doctor).filter(Doctor.id_number == username,
                                                 Doctor.password == password).first()
        if doctor is None:
            return False
        return True
    else:
        patient = db.session.query(Patient).filter(Patient.id == id, Patient.id_number == username,
                                                   Patient.password == password).first()
        if patient is None:
            return False
        return True



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

    # zistenie ci sa rodne cislo uz nenachadza v databaze
    count = db.session.query(Patient).filter(Patient.id_number == id_num).count()
    count = count + db.session.query(Doctor).filter(Doctor.id_number == id_num).count()

    if count > 0:
        return Response(status=409, mimetype='application/json')
    else:
        patient = Patient(name=name, surname=surname,
                          id_number=id_num, email=email,
                          password=password)

        db.session.add(patient)
        db.session.commit()
        last_id = db.session.query(Patient).order_by(Patient.id.desc()).first().id
        response = {"response": {"id_patient": last_id}}
        return Response(json.dumps(response), status=201, mimetype='application/json')


@app.route('/login_patient', methods=['POST'])
def login_patient():
    try:
        patient_login_data = request.json['patient_login_data']
        id_number = patient_login_data['id_number']
        password = patient_login_data['password']
    except:
        return Response(status=400, mimetype='application/json')

    if None in [patient_login_data, id_number, password] \
            or "" in [patient_login_data, id_number, password]:
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
            response = {"response": {"id_patient": patient.id}}
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
            response = {"response": {"id_doctor": doctor.id}}
            return Response(json.dumps(response), status=202, mimetype='application/json')


@app.route('/check_status', methods=['GET'])
def check_status():
    try:
        args = request.args
        patient_id = int(args.get('patient_id'))
        date_string = args.get('date')
        datetime.datetime.fromisoformat(date_string)
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id, date_string] or "" in [patient_id, date_string]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, patient_id, False):
        return Response(status=401, mimetype='application/json')

    date_time_obj = datetime.datetime.fromisoformat(date_string)
    date_day = date_time_obj.date()
    date_hour = int(date_time_obj.hour)

    record = db.session.query(History).join(Patient_History).filter(Patient_History.patient_id == patient_id,
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
        patient_id = int(hist_request['patient_id'])
        date_full = hist_request['date']
        datetime.datetime.fromisoformat(date_full)
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id, date_full] or "" in [patient_id, date_full]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, patient_id, False):
        return Response(status=401, mimetype='application/json')

    date_day = datetime.datetime.fromisoformat(date_full).date()
    record = db.session.query(History).join(Patient_History).filter(Patient_History.patient_id == patient_id,
                                                                    History.date == date_day).first()
    if record is None:
        history = History(date=date_day)
        db.session.add(history)

        last_id_hist = db.session.query(History).order_by(History.id.desc()).first().id
        patient_history = Patient_History(patient_id=patient_id, history_id=last_id_hist)

        db.session.add(patient_history)
        db.session.commit()

    record = db.session.query(History).join(Patient_History).filter(Patient_History.patient_id == patient_id,
                                                                    History.date == date_day).first()

    json_response = {"response": {"id_hist_request": record.id, "morning": record.morning, "lunch": record.lunch,
                                  "evening": record.evening}}

    return Response(json.dumps(json_response), status=200, mimetype='application/json')


@app.route('/change_hist_rec', methods=['PUT'])
def change_hist_rec():
    try:
        hist_request = request.json['hist_record']
        patient_id = int(hist_request['patient_id'])
        id_hist_request = int(hist_request['id_hist_request'])
        if hist_request['morning'] != None:
            morning = float(hist_request['morning'])
        else:
            morning = None

        if hist_request['lunch'] != None:
            lunch = float(hist_request['lunch'])
        else:
            lunch = None

        if hist_request['evening'] != None:
            evening = float(hist_request['evening'])
        else:
            evening = None

    except:
        return Response(status=400, mimetype='application/json')
    if None in [hist_request, id_hist_request] or "" in [hist_request, id_hist_request]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, patient_id, False):
        return Response(status=401, mimetype='application/json')

    history = db.session.query(History).filter(History.id == id_hist_request).first()
    if history is None:
        return Response(status=400, mimetype='application/json')

    if (morning is None or 0 <= morning <= 30) and (lunch is None or 0 <= lunch <= 30) and (evening is None or 0 <= evening <= 30):
        history.morning = morning
        history.lunch = lunch
        history.evening = evening
        db.session.commit()
        return Response(status=200, mimetype='application/json')
    return Response(status=400, mimetype='application/json')


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

    sugar = sugar + carbohydrates / 5
    insulin_table = Insulin.query.all()

    for actual_rec in insulin_table:
        if actual_rec.sugar_from <= sugar <= actual_rec.sugar_to:
            json_resp = {"insulin_dose": actual_rec.recommended_insulin, "body": actual_rec.info}
            return Response(json.dumps(json_resp), status=200, mimetype='application/json')

    return Response(status=400, mimetype='application/json')


@app.route('/data_patient')
def data_patient():
    try:
        args = request.args
        patient_id = int(args.get('patient_id'))
        num_of_records = int(args.get('num_of_records'))
        date_full = args.get('date')
        datetime.datetime.fromisoformat(date_full)
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id, num_of_records, date_full]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, -1, True):
        return Response(status=401, mimetype='application/json')

    date_day = datetime.datetime.fromisoformat(date_full).date()

    records = db.session.query(History).join(Patient_History).filter(Patient_History.patient_id == patient_id,
                                                                     History.date <= date_day).order_by(
        History.id.desc()).limit(num_of_records)

    if records is None:
        json_response = {"response": []}
    else:
        response = []
        for history in records:
            response.append({"date": str(history.date.date()), "morning": history.morning, "lunch": history.lunch,
                             "evening": history.evening})
        json_response = {"response": response}

    return Response(json.dumps(json_response), status=200, mimetype='application/json')


@app.route('/photo_update', methods=['PUT'])
def update_photo():
    try:
        photo_update = request.form.to_dict(flat=False)
        id_patient_request = photo_update['patient_id'][0]
        file = request.files['image']
    except:
        return Response(status=400, mimetype='application/json')
    if None in [id_patient_request, file] or "" in [id_patient_request]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, id_patient_request, False):
        return Response(status=401, mimetype='application/json')

    type = file.mimetype
    patient = db.session.query(Patient).filter(Patient.id == id_patient_request).first()
    if patient is None:
        return Response(status=400, mimetype='application/json')
    else:
        patient.photo_file = file.read()
        patient.photo_type = type
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

    if not isAuthorisated(request, doctor_id, True):
        return Response(status=401, mimetype='application/json')

    p_d = db.session.query(Doctor_Patient).filter(Doctor_Patient.doctor_id == doctor_id).filter(
        Doctor_Patient.patient_id == patient_id).first()
    if p_d is None:
        return Response(status=400, mimetype='application/json')
    else:
        db.session.delete(p_d)
        db.session.commit()
        return Response(status=200, mimetype='application/json')


@app.route('/photo_patient/<id>', methods=['GET'])
def photo_get(id):
    if None in [id] or "" in [id]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, id, False):
        return Response(status=401, mimetype='application/json')

    patient = db.session.query(Patient).filter(Patient.id == id).first()
    if patient.photo_type == None:
        return Response(status=400, mimetype='application/json')
    else:
        return Response(patient.photo_file, mimetype=patient.photo_type, status=200)


@app.route('/detail_patient', methods=['GET'])
def patient_data_get():
    try:
        args = request.args
        patient_id = args.get('patient_id')
        doctor_id = args.get('doctor_id')
    except:
        return Response(status=400, mimetype='application/json')
    if None in [patient_id, doctor_id] or "" in [patient_id, doctor_id]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, doctor_id, True):
        return Response(status=401, mimetype='application/json')

    patient = db.session.query(Patient).filter(Patient.id == patient_id).first()
    response = {
        "response": {"patient_name": patient.name, "patient_surname": patient.surname, "patient_rc": patient.id_number,
                     "patient_mail": patient.email}}
    return Response(json.dumps(response), status=200, mimetype='application/json')


@sock.route('/assign_patient')
def assign_patient(ws):
    while True:
        try:
            data = ws.receive()
            assign_info = data.json['assign_info']
            id_doctor = assign_info['id_doctor']
            id_patient = assign_info['id_patient']
            u = assign_info['u']
            p = assign_info['p']

        except:
            ws.send("400")
            break
        if None in [id_doctor, id_patient] or "" in [id_patient, id_doctor]:
            ws.send("400")
            break

        if not isAuthorisatedWS(u, p, id_doctor, True):
            ws.send("401")
            break

        p_d = db.session.query(Doctor_Patient).filter(Doctor_Patient.patient_id == id_patient).first()
        if p_d is None:
            record = Doctor_Patient(patient_id=id_patient, doctor_id=id_doctor)
            db.session.add(record)
            db.session.commit()
            ws.send("200")
            break
        else:
            ws.send("409")
            break


@sock.route('/patient_exist')
def patient_rc(ws):
    print(f'User: {request.args.get("id_number_patient")}')
    while True:
        #data = ws.receive()
        #print(data)
        #ws.send(data)
        try:
            args = request.args
            patient_id = args.get('id_number_patient')
        except:
            ws.send("404")
            break
        if None in [patient_id] or "" in [patient_id]:
            ws.send("404")
            break

        patient = db.session.query(Patient).filter(Patient.id_number == patient_id).first()
        if patient is None:
            ws.send("204")
            break
        else:
            response = {"id_patient": patient.id}
            ws.send(json.dumps(response))
            break


@app.route('/get_patients/<id_doctor>', methods=['GET'])
def patient_get(id_doctor):
    if None in [id_doctor] or "" in [id_doctor]:
        return Response(status=400, mimetype='application/json')

    if not isAuthorisated(request, id_doctor, True):
        return Response(status=401, mimetype='application/json')

    patients = db.session.query(Patient).join(Doctor_Patient).filter(Doctor_Patient.doctor_id == id_doctor).all()
    if patients is None:  # doktor nema pacientov
        return Response(status=404, mimetype='application/json')
    data = []
    for patient in patients:
        data.append({"id_patient": patient.id, "id_number": patient.id_number})
    response = {"patients": data}
    return Response(json.dumps(response), status=200, mimetype='application/json')
