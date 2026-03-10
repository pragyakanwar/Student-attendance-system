from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date
import cv2

app = Flask(__name__)

# -----------------------------
# Create Database
# -----------------------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
CREATE TABLE IF NOT EXISTS students(
id INTEGER PRIMARY KEY AUTOINCREMENT,
student_id TEXT UNIQUE,
name TEXT,
branch TEXT,
year TEXT,
password TEXT
)
""")
     
    cursor.execute("""
INSERT OR IGNORE INTO students(student_id,name,branch,year,password)
VALUES
('22AI001','Pragya','AI & DS','3rd','1234'),
('22AI002','Rahul','AI & DS','3rd','1234')
""")
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
student_id TEXT,
subject TEXT,
day TEXT,
status TEXT
)
""")
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT
)
""")

    cursor.execute("""
INSERT OR IGNORE INTO teachers(username,password)
VALUES ('teacher','1234')
""")
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Login Page
# -----------------------------

@app.route("/")
def login():
    return render_template("login.html")

# -----------------------------
# Teacher Login Page
# -----------------------------

@app.route("/teacher_login", methods=["POST"])
def teacher_login():

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM teachers WHERE username=? AND password=?",
        (username,password)
    )

    teacher = cursor.fetchone()

    conn.close()

    if teacher:
        return redirect("/teacher")
    else:
        return "Invalid Teacher Login"

# -----------------------------
# Student Dashboard
# -----------------------------


@app.route("/student_login", methods=["POST"])
def student():

    student_id = request.form["student_id"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name,branch,year FROM students WHERE student_id=?",
        (student_id,)
    )

    student = cursor.fetchone()

    if not student:
        return "Student not found"

    name, branch, year = student

    # total present
    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Present'",
        (student_id,)
    )
    present = cursor.fetchone()[0]

    # total classes
    cursor.execute(
        "SELECT COUNT(*) FROM attendance WHERE student_id=?",
        (student_id,)
    )
    total = cursor.fetchone()[0]

    percentage = 0

    if total > 0:
        percentage = round((present/total)*100,2)

    absent = 100 - percentage

    # SUBJECT-WISE ATTENDANCE
    cursor.execute("""
    SELECT subject,
    SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END),
    COUNT(*)
    FROM attendance
    WHERE student_id=?
    GROUP BY subject
    """, (student_id,))

    subject_data = cursor.fetchall()

    conn.close()

    return render_template(
        "student_dashboard.html",
        name=name,
        branch=branch,
        year=year,
        percentage=percentage,
        absent=absent,
        subject_data=subject_data
    )

@app.route("/student_profile")
def student_profile():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT student_id,name,branch,year FROM students LIMIT 1")

    student = cursor.fetchone()

    student_id,name,branch,year = student

    cursor.execute("""
    SELECT COUNT(*) FROM attendance
    WHERE student_id=? AND status='Present'
    """,(student_id,))

    present = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*) FROM attendance
    WHERE student_id=?
    """,(student_id,))

    total = cursor.fetchone()[0]

    percentage = 0

    if total > 0:
        percentage = round((present/total)*100,2)

    conn.close()

    return render_template(
        "student_profile.html",
        name=name,
        student_id=student_id,
        branch=branch,
        year=year,
        percentage=percentage
    )

# -----------------------------
# Teacher Dashboard
# -----------------------------

@app.route("/teacher")
def teacher():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # get attendance records
    cursor.execute("""
    SELECT attendance.id, students.name, attendance.subject, attendance.day, attendance.status
    FROM attendance
    JOIN students
    ON attendance.student_id = students.student_id
    """)

    data = cursor.fetchall()

    # get all students for dropdown
    cursor.execute("SELECT DISTINCT name FROM students")
    students = cursor.fetchall()

    conn.close()

    return render_template("teacher_dashboard.html", data=data, students=students)

# -----------------------------
# Teacher Marks Attendance
# -----------------------------

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():

    student_name = request.form["student_name"]
    subject = request.form["subject"]
    status = request.form["status"]
    day = request.form["day"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT student_id FROM students WHERE name=?",
        (student_name,)
    )

    result = cursor.fetchone()

    if result:

        student_id = result[0]

        # Check if attendance already exists
        cursor.execute(
            "SELECT * FROM attendance WHERE student_id=? AND subject=? AND day=?",
            (student_id, subject, day)
        )

        existing = cursor.fetchone()

        if not existing:

            cursor.execute(
                "INSERT INTO attendance(student_id,subject,day,status) VALUES (?,?,?,?)",
                (student_id, subject, day, status)
            )

            conn.commit()

    conn.close()

    return redirect("/teacher")

@app.route("/teacher_login_page")
def teacher_login_page():
    return render_template("teacher_login.html")

# -----------------------------
# Admin Dashboard
# -----------------------------

@app.route("/admin")
def admin():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Total teachers
    cursor.execute("SELECT COUNT(*) FROM teachers")
    total_teachers = cursor.fetchone()[0]

    # Total attendance records
    cursor.execute("SELECT COUNT(*) FROM attendance")
    total_attendance = cursor.fetchone()[0]

    # Student list
    cursor.execute("SELECT name, branch, year FROM students")
    students = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_teachers=total_teachers,
        total_attendance=total_attendance,
        students=students
    )

# -----------------------------
# FACE ATTENDENCE
# -----------------------------


@app.route("/face_attendance")
def face_attendance():
    return render_template("face_attendance.html")  


@app.route("/start_face_attendance")
def start_face_attendance():

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    video = cv2.VideoCapture(0)

    while True:

        ret, frame = video.read()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5
        )

        for (x, y, w, h) in faces:

            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

        cv2.imshow("Face Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

    return "Face detection finished"

app.run(debug=True)

