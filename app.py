
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "healthcare_demo_key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "healthcare.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            contact TEXT NOT NULL,
            blood_pressure INTEGER NOT NULL,
            glucose REAL NOT NULL,
            risk_level TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def calculate_risk(blood_pressure, glucose):
    # Simplified educational rules, not a medical diagnosis.
    if blood_pressure >= 140 or glucose >= 180:
        return "High"

    elif blood_pressure >= 130 or glucose >= 140:
        return "Medium"

    return "Low"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        patient_id = request.form.get("patient_id", "").strip()
        name = request.form.get("name", "").strip()
        age_text = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        contact = request.form.get("contact", "").strip()
        bp_text = request.form.get("blood_pressure", "").strip()
        glucose_text = request.form.get("glucose", "").strip()

        if not all([
            patient_id, name, age_text, gender,
            contact, bp_text, glucose_text
        ]):
            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        try:
            age = int(age_text)
            blood_pressure = int(bp_text)
            glucose = float(glucose_text)

            if not 1 <= age <= 120:
                raise ValueError

            if blood_pressure <= 0 or glucose <= 0:
                raise ValueError

        except ValueError:
            flash("Please enter valid positive numeric values.")
            return redirect(url_for("register"))

        risk_level = calculate_risk(blood_pressure, glucose)

        connection = get_db_connection()

        try:
            connection.execute("""
                INSERT INTO patients (
                    patient_id, name, age, gender, contact,
                    blood_pressure, glucose, risk_level
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id, name, age, gender, contact,
                blood_pressure, glucose, risk_level
            ))

            connection.commit()

            flash("Patient registered and saved successfully!")

        except sqlite3.IntegrityError:
            flash("This Patient ID already exists. Please use another ID.")

        finally:
            connection.close()

        return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/patients")
def patients():

    connection = get_db_connection()

    records = connection.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template("patients.html", patients=records)


@app.route("/dashboard")
def dashboard():

    connection = get_db_connection()

    stats = {
        "total": connection.execute(
            "SELECT COUNT(*) FROM patients"
        ).fetchone()[0],

        "low": connection.execute(
            "SELECT COUNT(*) FROM patients WHERE risk_level = 'Low'"
        ).fetchone()[0],

        "medium": connection.execute(
            "SELECT COUNT(*) FROM patients WHERE risk_level = 'Medium'"
        ).fetchone()[0],

        "high": connection.execute(
            "SELECT COUNT(*) FROM patients WHERE risk_level = 'High'"
        ).fetchone()[0]
    }

    connection.close()

    return render_template("dashboard.html", stats=stats)


# Create the database table when the application starts.
create_database()


if __name__ == "__main__":
    app.run(debug=True)
