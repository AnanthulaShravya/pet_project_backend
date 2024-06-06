
from flask import Flask, jsonify,request
from flask_cors import CORS
from flask_mysqldb import MySQL
import json
import datetime


app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'qazplm123'
app.config['MYSQL_DB'] = 'project'

mysql = MySQL(app)


@app.route("/patient", methods=['GET'])
def patients():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM patient")
    patients = []
    for row in cursor.fetchall():
        patient = {}
        for i, column in enumerate(cursor.description):
            patient[column[0]] = row[i]
        patients.append(patient)
    cursor.close()

    return json.dumps(patients)

@app.route("/patient/<string:patient_id>/reports",methods=['GET'])
def patient_reports(patient_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM patient_reports where patient_id='{}'".format(patient_id))
    columns = [col[0] for col in cursor.description]

    results = cursor.fetchall()

    patient_reports = []

    for row in results:
        patient_report = {}
        for i, column in enumerate(columns):
           
            if isinstance(row[i], datetime.date):
                patient_report[column] = row[i].strftime('%Y-%m-%d')
            else:
                patient_report[column] = row[i]

        
        patient_reports.append(patient_report)
    cursor.close()
    print(patient_reports)
    return json.dumps(patient_reports)

@app.route("/doctor", methods=['GET'])
def doctors():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM doctor")
    columns = [col[0] for col in cursor.description]  
    doctors = []
    for row in cursor.fetchall():
        doctor = {}
        for i, column in enumerate(columns):
            doctor[column] = row[i]
        doctors.append(doctor)
    cursor.close()

    return json.dumps(doctors)

@app.route("/doctor/<string:doctor_id>/attendance", methods=['GET', 'PUT'])
def doctor_attendance(doctor_id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM doctor_attendance WHERE doctor_id = %s", (doctor_id,))
        attendance = []
        for row in cursor.fetchall():
            attendance_entry = {}
            for i, column in enumerate(cursor.description):
                attendance_entry[column[0]] = row[i]
            attendance.append(attendance_entry)
        cursor.close()
        return jsonify(attendance)
    elif request.method == 'PUT':
        data = request.get_json()
        attendance = data['attendance']
        cursor = mysql.connection.cursor()

        for entry in attendance:
            date = entry['attendance_date']
            status = entry['status']
            cursor.execute(
                "SELECT * FROM doctor_attendance WHERE doctor_id = %s AND attendance_date = %s",
                (doctor_id, date)
            )
            existing_entry = cursor.fetchone()

            if existing_entry:
                cursor.execute(
                    "UPDATE doctor_attendance SET status = %s WHERE doctor_id = %s AND attendance_date = %s",
                    (status, doctor_id, date)
                )
            else:
                cursor.execute(
                    "INSERT INTO doctor_attendance (doctor_id, attendance_date, status) VALUES (%s, %s, %s)",
                    (doctor_id, date, status)
                )
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message": "Attendance updated successfully"})


@app.route("/doctor/<string:doctor_id>/patients", methods=['GET'])
def doctor_patients(doctor_id):
    cursor = mysql.connection.cursor()
    query = """
        SELECT p.id, p.name, p.age, p.gender, p.email
        FROM doctor_patients dp
        JOIN patient p ON dp.patient_id = p.id
        WHERE dp.doctor_id = %s
    """
    cursor.execute(query, (doctor_id,))
    patient_details = []
    for row in cursor.fetchall():
        patient = {}
        for i, column in enumerate(cursor.description):
            patient[column[0]] = row[i]
        patient_details.append(patient)
    cursor.close()

    return jsonify(patient_details)

@app.route("/appointments/<string:user_id>", methods=['GET'])
def appointments(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT 
            a.id,
            a.appointment_date,
            a.appointment_time,
            a.status,
            p.name AS patient_name,
            d.name AS doctor_name
          
        FROM appointments a
        JOIN patient p ON a.patient_id = p.id
        JOIN doctor d ON a.doctor_id = d.id
        WHERE a.patient_id = %s OR a.doctor_id = %s
        """,
        (user_id, user_id)
    )
    columns = [col[0] for col in cursor.description]
    appointments = []
    for row in cursor.fetchall():
        appointment = {}
        for i, column in enumerate(columns):
            if isinstance(row[i], datetime.date):
                appointment[column] = row[i].strftime('%Y-%m-%d')
            elif isinstance(row[i], datetime.time):
                appointment[column] = row[i].strftime('%H:%M:%S')
            elif isinstance(row[i], datetime.timedelta):
                appointment[column] = str(row[i])
            else:
                appointment[column] = row[i]
        appointments.append(appointment)
    cursor.close()
    return json.dumps(appointments)

@app.route("/appointments", methods=['PUT'])
def update_appointments():
    data = request.get_json()
    appointments = data['appointmentData'] 
    cursor = mysql.connection.cursor()

    for entry in appointments:
        appointment_date = entry['date']  
        appointment_time = entry['time'] 
        patient_id = entry['patientId']  
        doctor_id = entry['doctorId']
        status = entry['status']
        
        cursor.execute(
            "INSERT INTO appointments (appointment_date, appointment_time, patient_id, doctor_id, status) VALUES (%s, %s, %s, %s, %s)",
            (appointment_date, appointment_time, patient_id, doctor_id, status)
        )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Appointments updated successfully"})

@app.route("/appointments/<int:id>", methods=['PATCH'])
def update_status(id):
    data = request.get_json()
    status = data.get('status')
    
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE appointments SET status = %s WHERE id = %s",
        (status, id)
    )

    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Status updated successfully"})

if __name__ == "__main__":
    app.run(debug=True)