import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
import threading
import serial

# Initialize Firebase Admin SDK
cred = credentials.Certificate(r'C:\Users\Hp\Desktop\Testcode\env\serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://testdatabase-2cbe4-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "testdatabase-2cbe4.appspot.com"
})

bucket = storage.bucket()

def get_latitude_longitude_utc(port, baudrate):
    latitude, longitude, utc = None, None, None
    
    def parse_gpgga(sentence):
        nonlocal latitude, longitude, utc
        fields = sentence.split(",")
        if fields[0] == "$GPGGA":
            utc = fields[1]
            latitude = fields[2]
            if fields[3] == "S":
                latitude = -float(latitude)
            else:
                latitude = float(latitude)
            longitude = fields[4]
            if fields[5] == "W":
                longitude = -float(longitude)
            else:
                longitude = float(longitude)

    def read_gps_data():
        try:
            with serial.Serial(port, baudrate, timeout=1) as ser:
                while True:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('ascii', errors='replace').strip()
                        if line.startswith("$GPGGA"):
                            parse_gpgga(line)
                            break
        except Exception as e:
            print(f"Error: {e}")
    
    read_gps_data()
    return latitude, longitude, utc

def register_student():
    def submit_data():
        student_id = entry_id.get()
        
        # Retrieve GPS data
        gps_port = "/dev/ttyS0"
        baud_rate = 9600
        latitude, longitude, utc = get_latitude_longitude_utc(gps_port, baud_rate)

        student_data = {
            "ID": entry_id.get(),
            "name": entry_name.get(),
            "major": entry_major.get(),
            "starting_year": int(entry_starting_year.get()),
            "total_attendance": 0,
            "standing": entry_standing.get(),
            "year": int(entry_year.get()),
            "last_attendance_time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": latitude,
            "longitude": longitude,
            "utc": utc
        }
        
        ref = db.reference('Students')
        ref.child(student_id).set(student_data)
        messagebox.showinfo("Success", "Data submitted successfully!")
        register_window.destroy()

    register_window = tk.Toplevel(root)
    register_window.title("Register Information")

    tk.Label(register_window, text="Student ID").grid(row=0, column=0)
    entry_id = tk.Entry(register_window)
    entry_id.grid(row=0, column=1)

    tk.Label(register_window, text="Name").grid(row=1, column=0)
    entry_name = tk.Entry(register_window)
    entry_name.grid(row=1, column=1)

    tk.Label(register_window, text="Major").grid(row=2, column=0)
    entry_major = tk.Entry(register_window)
    entry_major.grid(row=2, column=1)

    tk.Label(register_window, text="Starting Year").grid(row=3, column=0)
    entry_starting_year = tk.Entry(register_window)
    entry_starting_year.grid(row=3, column=1)

    tk.Label(register_window, text="Standing").grid(row=4, column=0)
    entry_standing = tk.Entry(register_window)
    entry_standing.grid(row=4, column=1)

    tk.Label(register_window, text="Year").grid(row=5, column=0)
    entry_year = tk.Entry(register_window)
    entry_year.grid(row=5, column=1)

    submit_button = tk.Button(register_window, text="Submit", command=submit_data)
    submit_button.grid(row=6, column=1)

def login():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    imgBackground = cv2.imread('Resources/background.png')

    # Importing the mode images into a list
    folderModePath = 'Resources/Modes'
    modePathList = os.listdir(folderModePath)
    imgModeList = []
    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

    # Load the encoding file
    print("Loading Encode File ...")
    file = open('EncodeFile.p', 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    print("Encode File Loaded")

    modeType = 0
    counter = 0
    id = -1
    imgStudent = []

    while True:
        success, img = cap.read()

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if faceCurFrame:
            recognized = False
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    recognized = True
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                    id = studentIds[matchIndex]
                    if counter == 0:
                        cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                        cv2.imshow("Face Attendance", imgBackground)
                        cv2.waitKey(1)
                        counter = 1
                        modeType = 1

            if not recognized:
                cv2.putText(imgBackground, "Not Recognized", (250, 300), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 3)
                cv2.imshow("Face Attendance", imgBackground)
                cv2.waitKey(3000)  # Display for 3 seconds
                counter = 0
                modeType = 0
                continue

            if counter != 0:
                if counter == 1:
                    # Get the Data
                    studentInfo = db.reference(f'Students/{id}').get()
                    if studentInfo is None:
                        modeType = 0
                        counter = 0
                        continue

                    # Get the Image from the storage
                    blob = bucket.get_blob(f'Images/{id}.png')
                    if blob is None:
                        cv2.putText(imgBackground, "No Image Found", (250, 300), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 3)
                        cv2.imshow("Face Attendance", imgBackground)
                        cv2.waitKey(3000)  # Display for 3 seconds
                        counter = 0
                        modeType = 0
                        continue

                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                    
                    # Retrieve GPS data
                    gps_port = "/dev/ttyS0"
                    baud_rate = 9600
                    latitude, longitude, utc = get_latitude_longitude_utc(gps_port, baud_rate)
                    studentInfo['latitude'] = latitude
                    studentInfo['longitude'] = longitude
                    studentInfo['utc'] = utc

                    # Update data of attendance
                    last_attendance_time = studentInfo.get('last_attendance_time', "")
                    if last_attendance_time:
                        datetimeObject = datetime.strptime(last_attendance_time, "%Y-%m-%d %H:%M:%S")
                        secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    else:
                        secondsElapsed = 86401  # Set to more than 24 hours to allow attendance update
                    
                    if secondsElapsed > 86400:  # 24 hours = 86400 seconds
                        ref = db.reference(f'Students/{id}')
                        studentInfo['total_attendance'] += 1
                        ref.child('total_attendance').set(studentInfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        ref.child('latitude').set(latitude)
                        ref.child('longitude').set(longitude)
                        ref.child('utc').set(utc)
                        modeType = 4  # Set to scan successful mode
                    else:
                        modeType = 3
                        counter = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if modeType != 3:
                    if modeType == 4:
                        cv2.putText(imgBackground, "Scan Successful", (250, 300),
                                    cv2.FONT_HERSHEY_COMPLEX, 2, (0, 255, 0), 3)
                        cv2.imshow("Face Attendance", imgBackground)
                        cv2.waitKey(3000)  # Display for 3 seconds
                        counter = 0
                        modeType = 0
                    else:
                        if 10 < counter < 20:
                            modeType = 2

                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                        if counter <= 10:
                            cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                            cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                            cv2.putText(imgBackground, str(id), (1006, 493),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                            cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                            cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                            cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                            (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                            offset = (414 - w) // 2
                            cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                                        cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                            imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

                        counter += 1

                        if counter >= 20:
                            counter = 0
                            modeType = 0
                            studentInfo = []
                            imgStudent = []
                            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        else:
            modeType = 0
            counter = 0

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        cv2.imshow("Face Attendance", imgBackground)

    cap.release()
    cv2.destroyAllWindows()

def register_face():
    def run_script():
        os.system(r'python C:\Users\Hp\Desktop\Testcode\env\encodetest.py')
    
    thread = threading.Thread(target=run_script)
    thread.start()

# Initial GUI Window
root = tk.Tk()
root.title("Student Management System")

tk.Button(root, text="Register", command=register_student, width=20, height=2).pack(pady=10)
tk.Button(root, text="Register Face", command=register_face, width=20, height=2).pack(pady=10)
tk.Button(root, text="Login", command=login, width=20, height=2).pack(pady=10)

root.mainloop()