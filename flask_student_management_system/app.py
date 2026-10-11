from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-before-deployment"
DB_PATH = Path(__file__).with_name("students.db")

def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                course TEXT NOT NULL
            )
        """)

@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    with get_db() as db:
        if query:
            students = db.execute(
                """SELECT * FROM students
                   WHERE name LIKE ? OR email LIKE ? OR course LIKE ?
                   ORDER BY name""",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            ).fetchall()
        else:
            students = db.execute("SELECT * FROM students ORDER BY name").fetchall()
    return render_template("index.html", students=students, query=query)

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        if not all([name, email, course]):
            flash("Please complete every field.", "error")
            return render_template("form.html", student=None, heading="Add student")
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO students (name, email, course) VALUES (?, ?, ?)",
                    (name, email, course)
                )
            flash("Student added successfully.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("That email address is already registered.", "error")
    return render_template("form.html", student=None, heading="Add student")

@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    with get_db() as db:
        student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if student is None:
        flash("Student not found.", "error")
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        if not all([name, email, course]):
            flash("Please complete every field.", "error")
            return render_template("form.html", student=student, heading="Edit student")
        try:
            with get_db() as db:
                db.execute(
                    "UPDATE students SET name = ?, email = ?, course = ? WHERE id = ?",
                    (name, email, course, student_id)
                )
            flash("Student updated successfully.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("That email address is already used by another student.", "error")
    return render_template("form.html", student=student, heading="Edit student")

@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    with get_db() as db:
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    flash("Student deleted.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
