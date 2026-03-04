from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "left_hospital_secret_key"

DB_NAME = "appointments.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            severity_score INTEGER,
            risk_level TEXT,
            priority INTEGER,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return redirect(url_for("index"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/packages")
def packages():
    return render_template("packages.html")


@app.route("/specialities")
def specialities():
    return render_template("specialities.html")


@app.route("/patient")
def patient():
    return render_template("patient.html")


@app.route("/book-appointment", methods=["POST"])
def book_appointment():

    patient_name = request.form.get("patient_name")
    symptoms = request.form.getlist("symptoms")

    if not patient_name or not symptoms:
        return jsonify({"error": "Patient name and symptoms required"}), 400

    severity_score = len(symptoms) * 5

    if severity_score >= 15:
        risk_level = "High Risk"
        priority = 1
    elif severity_score >= 10:
        risk_level = "Medium Risk"
        priority = 2
    else:
        risk_level = "Low Risk"
        priority = 3

    conn = get_db()

    conn.execute(
        """
        INSERT INTO appointments
        (patient_name, symptoms, severity_score, risk_level, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            patient_name,
            ",".join(symptoms),
            severity_score,
            risk_level,
            priority,
            "Pending"
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Appointment booked successfully",
        "risk_level": risk_level
    })


@app.route("/doctor-login", methods=["GET", "POST"])
def doctor_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "doctor" and password == "doctor123":
            session["doctor_logged_in"] = True
            return redirect(url_for("doctor_dashboard"))

        return render_template("doctor_login.html", error="Invalid credentials")

    return render_template("doctor_login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/doctor")
def doctor_dashboard():

    if not session.get("doctor_logged_in"):
        return redirect(url_for("doctor_login"))

    return render_template("doctor.html")


@app.route("/appointments")
def get_appointments():

    if not session.get("doctor_logged_in"):
        return jsonify([])

    conn = get_db()

    rows = conn.execute("""
        SELECT id, patient_name, symptoms, severity_score, risk_level, priority, status
        FROM appointments
        ORDER BY priority ASC
    """).fetchall()

    conn.close()

    appointments = []

    for r in rows:
        appointments.append({
            "id": r["id"],
            "patient_name": r["patient_name"],
            "symptoms": r["symptoms"].split(","),
            "severity_score": r["severity_score"],
            "risk_level": r["risk_level"],
            "priority": r["priority"],
            "status": r["status"]
        })

    return jsonify(appointments)


@app.route("/complete-appointment/<int:id>", methods=["PUT"])
def complete_appointment(id):

    conn = get_db()

    conn.execute(
        "UPDATE appointments SET status='Completed' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Consultation completed"})


if __name__ == "__main__":
    app.run(debug=True)