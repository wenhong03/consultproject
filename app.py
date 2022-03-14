from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

@app.route("/")
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
        query = """
        SELECT Students.StudentID, Students.Password
        FROM Students
        """
        cursor = db.execute(query)
        accounts = cursor.fetchall()
        print(accounts)

        valid = False
        for account in accounts:
            if account[0] == ID and account[1] == Password:
                valid = True
                break
        if valid:
            return render_template("student_homepage.html", ID=ID)
        else:
            return render_template("student_login.html")

@app.route("/booking/<ID>", methods=["GET", "POST"])
def booking(ID):
    if request.method == "GET":
        query = """
        SELECT Teachers.Name FROM Teachers, TeachingRecord, Students
        WHERE Teachers.TeacherID == TeachingRecord.TeacherID AND Students.StudentID == TeachingRecord.StudentID AND Students.StudentID == ?
        """
        db = sqlite3.connect("End of Year Project.db")
        # db.close()
        cursor = db.execute(query, (ID,))
        data = cursor.fetchall()
        # print(data)
        teachers = ()
        for teacher in data:
            teachers += (teacher[0],)
        # print(teachers)
        return render_template("display_teachers.html", teachers=teachers, ID=ID)
    
    else:
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
        # print(teacherID)
        # print(data)

        cursor = db.execute(read_all_consultations_query, (teacherID,))
        data = cursor.fetchall()

        return render_template("booking.html", data=data, ID=ID)

@app.route("/update_booking/<ID>", methods=["POST"])
def update_booking(ID):
    temp = request.form["slot"]
    slot = temp[1:-1]
    lst = slot.split(",")
    # date = lst[0][1:-1]
    # time = lst[1][2:-1]
    Current = lst[4][1:]
    ConsultationNo = lst[5][1:]

    print(lst)
    # print(slot)
    # print(temp)

    print(Current)
    print(ConsultationNo)

    db = sqlite3.connect("End of Year Project.db")

    checker_query = """
    SELECT ConsultationRecordNo FROM ConsultationRecord
    WHERE StudentID == ? AND ConsultationNo == ?
    """

    cursor = db.execute(checker_query, (ID, ConsultationNo))
    ConsultationRecordNo = cursor.fetchall()
    print(ConsultationRecordNo)

    # To prevent students from booking the same slots that they have previously booked.

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

        return "DONE"

    else:
        return render_template("rebook.html", ID=ID)

@app.route("/student_check_booking/<ID>", methods=["GET", "POST"])
def student_check_booking(ID):
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
    print(data)
    return render_template("student's display.html", data=data)

@app.route("/teacher/", methods=["GET", "POST"])
def teacher_login():
    if request.method == "GET":
        return render_template("teacher_login.html")
    else:
        ID = request.form["ID"]
        Password = request.form["Password"]
        db = sqlite3.connect("End of Year Project.db")
        query = """
        SELECT Teachers.TeacherID, Teachers.Password
        FROM Teachers
        """
        cursor = db.execute(query)
        accounts = cursor.fetchall()
        print(accounts)

        valid = False
        for account in accounts:
            if account[0] == ID and account[1] == Password:
                valid = True
                break
        if valid:
            return render_template("teacher_homepage.html", ID=ID)
        else:
            return render_template("teacher_login.html")

@app.route("/make_slots/<ID>", methods=["GET", "POST"])
def make_slots(ID):
    if request.method == "GET":
        return render_template("slot_making.html", ID=ID)
    else:
        date = request.form["date"]
        time = request.form["starthour"] + request.form["startmins"] + " - " + request.form["endhour"] + request.form["endmins"]
        # print(date)
        # print(time)
        minimum = request.form["min"]
        maximum = request.form["max"]

        db = sqlite3.connect("End of Year Project.db")
        query = """
        INSERT INTO Consultations(TeacherID, TimeSlot, Date, Max, Min) VALUES(?, ?, ?, ?, ?)
        """
        db.execute(query, (ID, time, date, maximum, minimum))
        db.commit()
        db.close()
        
        return "DONE"

@app.route("/teacher_check_slot/<ID>", methods=["GET", "POST"])
def teacher_check_slot(ID):
    db = sqlite3.connect("End of Year Project.db")

    # if want to check null must use "is"

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
    print(consultations)

    groups_of_names = []
    for consultation in consultations:
        cursor = db.execute(get_student_names_query, (ID, consultation[0], consultation[1], consultation[2], consultation[3], consultation[4]))
        student_names = cursor.fetchall()
        groups_of_names.append(student_names)
    print("groups_of_names", groups_of_names)

    return render_template("teacher_check_slot.html", consultations=consultations, groups_of_names=groups_of_names)

if __name__ == "__main__":
    app.run(debug=True, port=5050)