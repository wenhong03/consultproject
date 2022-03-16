from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")

@app.route("/role/", methods=["GET", "POST"])
def role():
    if request.method == "GET":
        return render_template("role.html")
    else:        
        if request.form["role"] == "teacher":
            return redirect(url_for("teacher_login"))
        else:
            return redirect(url_for("student_login"))

@app.route("/student/", methods=["GET", "POST"])
def student_login():
    if request.method == "GET":
        return render_template("student_login.html")
    else:
        ID = request.form["ID"]
        Password = request.form["Password"]
        db = sqlite3.connect("End of Year Project.db")

        valid = False

        search_query = """
        SELECT * FROM Students
        WHERE StudentID = ? AND Password = ?
        """

        cursor = db.execute(search_query, (ID, Password))
        data = cursor.fetchall()
        if len(data) != 0:
            valid = True

        if valid:
            return render_template("student_homepage.html", ID=ID)
        else:
            error_message = "Incorrect Username or Password"
            return render_template("student_login.html", error_message=error_message)


@app.route("/student_homepage/", methods=["GET", "POST"])
def student_homepage():
    ID = request.form["ID"]
    return render_template("student_homepage.html", ID=ID)

@app.route("/display_teachers/", methods=["GET", "POST"])
def display_teachers():
    ID = request.form["ID"]

    query = """
    SELECT Teachers.Name FROM Teachers, TeachingRecord, Students
    WHERE Teachers.TeacherID == TeachingRecord.TeacherID AND Students.StudentID == TeachingRecord.StudentID AND Students.StudentID == ?
    """
    db = sqlite3.connect("End of Year Project.db")
    cursor = db.execute(query, (ID,))
    data = cursor.fetchall()
    teachers = ()
    for teacher in data:
        teachers += (teacher[0],)
    return render_template("display_teachers.html", teachers=teachers, ID=ID)
    
@app.route("/booking/", methods=["GET", "POST"])
def booking():
    ID = request.form["ID"]
    teacher = request.form["teacher"]
    db = sqlite3.connect("End of Year Project.db")

    teacherID_query = """
    SELECT Teachers.TeacherID FROM Teachers
    WHERE Teachers.Name == ?
    """

    read_all_consultations_query = """
    SELECT Date, TimeSlot, Min, Max, Current, ConsultationNo FROM Consultations
    WHERE TeacherID == ? AND Current < Max
    """

    cursor = db.execute(teacherID_query, (teacher,))
    data = cursor.fetchall()
    teacherID = data[0][0]

    cursor = db.execute(read_all_consultations_query, (teacherID,))
    data = cursor.fetchall()

    return render_template("booking.html", data=data, ID=ID)

@app.route("/update_booking/", methods=["POST"])
def update_booking():
    ID = request.form["ID"]
    temp = request.form["slot"]
    slot = temp[1:-1]
    lst = slot.split(",")
    date = lst[0][1:-1]
    time = lst[1][2:-1]
    Current = lst[4][1:]
    ConsultationNo = lst[5][1:]

    db = sqlite3.connect("End of Year Project.db")

    # To prevent students from booking the same slots that they have previously booked.
    checker_query = """
    SELECT ConsultationRecordNo FROM ConsultationRecord
    WHERE StudentID == ? AND ConsultationNo == ?
    """

    cursor = db.execute(checker_query, (ID, ConsultationNo))
    ConsultationRecordNo = cursor.fetchall()

    if not ConsultationRecordNo: 
        add_ConsultationRecord = """
        INSERT INTO ConsultationRecord(ConsultationNo, StudentID) VALUES(?, ?)
        """

        db.execute(add_ConsultationRecord, (ConsultationNo, ID))

        set_Current_query = """
        UPDATE Consultations SET Current = ?
        WHERE ConsultationNo == ?
        """

        db.execute(set_Current_query, (int(Current)+1, ConsultationNo))
        db.commit()
        db.close()

        return render_template("successful_booking.html", ID=ID)

    else:
        return render_template("rebook.html", ID=ID)

@app.route("/student_check_booking/", methods=["GET", "POST"])
def student_check_booking():
    ID = request.form["ID"]
    db = sqlite3.connect("End of Year Project.db")
    query = """
    SELECT Consultations.Date, Consultations.TimeSlot, Consultations.Current, Teachers.Name, Consultations.Max, Consultations.Min
    FROM Consultations, Teachers, ConsultationRecord, Students
    WHERE ConsultationRecord.StudentID == Students.StudentID AND 
    ConsultationRecord.ConsultationNo == Consultations.ConsultationNo AND 
    Teachers.TeacherID == Consultations.TeacherID AND
    Students.StudentID == ?
    """
    cursor = db.execute(query, (ID,))
    data = cursor.fetchall()
    return render_template("student's display.html", data=data, ID=ID)

@app.route("/cancel_booking_a/", methods=["GET", "POST"])
def cancel_booking_a():
    ID = request.form["ID"]
    db = sqlite3.connect("End of Year Project.db")
    query = """
    SELECT Consultations.Date, Consultations.TimeSlot, Teachers.Name, Consultations.ConsultationNo, ConsultationRecord.ConsultationRecordNo
    FROM Teachers, Consultations, ConsultationRecord, Students
    WHERE Students.StudentID = ? AND ConsultationRecord.StudentID = Students.StudentID
    AND ConsultationRecord.ConsultationNo == Consultations.ConsultationNo
    AND Consultations.TeacherID = Teachers.TeacherID
    """
    cursor = db.execute(query, (ID,))
    data = cursor.fetchall()

    return render_template("cancel_booking.html", ID=ID, data=data)

@app.route("/cancel_booking_b/", methods=["GET", "POST"])
def cancel_booking_b():
    ID = request.form["ID"]
    slot = request.form["slot"]

    slot = slot[1:-1]
    lst = slot.split(", ")
    
    consultationNo, consultationRecordNo = lst[3], lst[4]

    db = sqlite3.connect("End of Year Project.db")

    delete_consultationRecord_query = """
    DELETE FROM ConsultationRecord WHERE ConsultationRecordNo = ?
    """

    db.execute(delete_consultationRecord_query, (consultationRecordNo,))

    get_current_query = """
    SELECT Current FROM Consultations
    WHERE ConsultationNo = ?
    """

    cursor = db.execute(get_current_query, (consultationNo,))
    current = int(cursor.fetchone()[0])

    update_current_query = """
    UPDATE Consultations SET Current = ?
    WHERE ConsultationNo = ?
    """

    db.execute(update_current_query, (current-1, consultationNo))
    db.commit()
    db.close()

    return render_template("successful_cancel_booking.html", ID=ID)

@app.route("/teacher/", methods=["GET", "POST"])
def teacher_login():
    if request.method == "GET":
        return render_template("teacher_login.html")
    else:
        ID = request.form["ID"]
        Password = request.form["Password"]
        db = sqlite3.connect("End of Year Project.db")

        valid = False

        search_query = """
        SELECT * FROM Teachers
        WHERE TeacherID = ? AND Password = ?
        """

        cursor = db.execute(search_query, (ID, Password))
        data = cursor.fetchall()
        if len(data) != 0:
            valid = True
        if valid:
            return render_template("teacher_homepage.html", ID=ID)
        else:
            return render_template("teacher_login.html", error_message="Incorrect Username or Password")

@app.route("/teacher_homepage/", methods=["GET", "POST"])
def teacher_homepage():
    ID = request.form["ID"]
    return render_template("teacher_homepage.html", ID=ID)

@app.route("/make_slots_a/", methods=["GET", "POST"])
def make_slots_a():
    ID = request.form["ID"]
    return render_template("slot_making.html", ID=ID)

@app.route("/make_slots_b/", methods=["GET", "POST"])
def make_slots_b():
    ID = request.form["ID"]
    date = request.form["date"]
    time = request.form["starthour"] + request.form["startmins"] + " - " + request.form["endhour"] + request.form["endmins"]
    minimum = request.form["min"]
    maximum = request.form["max"]

    db = sqlite3.connect("End of Year Project.db")

    # to prevent teachers from making the same slot again
    check_query = """
    SELECT * FROM Consultations
    WHERE TeacherID = ? AND TimeSlot = ? AND Date = ?
    """

    cursor = db.execute(check_query, (ID, time, date))
    consultation = cursor.fetchall()

    if not consultation:
        query = """
        INSERT INTO Consultations(TeacherID, TimeSlot, Date, Max, Min) VALUES(?, ?, ?, ?, ?)
        """
        db.execute(query, (ID, time, date, maximum, minimum))
        db.commit()
        db.close()
        
        return render_template("successful_making.html", ID=ID)

    else:
        return render_template("remake.html", ID=ID)


@app.route("/teacher_check_slot/", methods=["GET", "POST"])
def teacher_check_slot():
    ID = request.form["ID"]
    db = sqlite3.connect("End of Year Project.db")

    get_consultations_query = """
    SELECT Consultations.Date, Consultations.TimeSlot, Consultations.Max, Consultations.Min, Consultations.Current
    FROM Consultations
    WHERE Consultations.TeacherID == ?
    """

    get_student_names_query = """
    SELECT Students.Name
    FROM Students, Consultations, ConsultationRecord, Teachers
    WHERE Students.StudentID == ConsultationRecord.StudentID AND
    ConsultationRecord.ConsultationNo == Consultations.ConsultationNo AND
    Consultations.TeacherID == Teachers.TeacherID AND 
    Teachers.TeacherID == ? AND 
    Consultations.Date == ? AND Consultations.TimeSlot == ? AND 
    Consultations.Max == ? AND Consultations.Min == ? AND Consultations.Current == ?
    """

    cursor = db.execute(get_consultations_query, (ID, ))
    consultations = cursor.fetchall()

    groups_of_names = []
    for consultation in consultations:
        cursor = db.execute(get_student_names_query, (ID, consultation[0], consultation[1], consultation[2], consultation[3], consultation[4]))
        student_names = cursor.fetchall()
        groups_of_names.append(student_names)

    return render_template("teacher_check_slot.html", consultations=consultations, groups_of_names=groups_of_names, ID=ID)

@app.route("/cancel_slot_a/", methods=["GET", "POST"])
def cancel_slot_a():
    ID = request.form["ID"]
    db = sqlite3.connect("End of Year Project.db")
    query = """
    SELECT Date, TimeSlot, ConsultationNo FROM Consultations
    WHERE TeacherID = ?
    """
    cursor = db.execute(query, (ID,))
    data = cursor.fetchall()

    return render_template("cancel_slot.html", ID=ID, data=data)

@app.route("/cancel_slot_b/", methods=["GET", "POST"])
def cancel_slot_b():
    ID = request.form["ID"]
    slot = request.form["slot"]

    slot = slot[1:-1]
    lst = slot.split(", ")
    
    consultationNo = lst[2]

    db = sqlite3.connect("End of Year Project.db")

    delete_consultationRecord_query = """
    DELETE FROM ConsultationRecord WHERE ConsultationNo = ?
    """

    delete_consultations_query = """
    DELETE FROM Consultations WHERE ConsultationNo = ?
    """

    db.execute(delete_consultationRecord_query, (consultationNo,))
    db.execute(delete_consultations_query, (consultationNo,))

    db.commit()
    db.close()

    return render_template("successful_cancel_slot.html", ID=ID)

if __name__ == "__main__":
    app.run(debug=False, port=5002)
