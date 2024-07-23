import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk

# Initialize Firebase
cred = credentials.Certificate(r'C:\Users\Hp\Desktop\Testcode\env\serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://testdatabase-2cbe4-default-rtdb.asia-southeast1.firebasedatabase.app/",
    'storageBucket': "testdatabase-2cbe4.appspot.com"
})

bucket = storage.bucket()
folderPath = 'Images'

# Camera port (0 for laptop camera, 1 for external webcam, etc.)
camera_port = 0

# Predefined admin credentials
ADMIN_ID = "admin"
ADMIN_PASSWORD = "1234"

def upload_image():
    file_path = filedialog.askopenfilename()
    if file_path:
        img = cv2.imread(file_path)
        face_locations = face_recognition.face_locations(img)
        if face_locations:
            cv2.imshow("Selected Image", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            def submit_id():
                student_id = entry_id.get()
                if student_id:
                    file_name = f'{folderPath}/{student_id}.png'
                    img_resized = cv2.resize(img, (216, 216))
                    cv2.imwrite(file_name, img_resized)
                    process_and_upload_image(file_name, img_resized)
                    upload_window.destroy()
                else:
                    messagebox.showerror("Error", "Please enter a valid student ID.")

            upload_window = tk.Toplevel(root)
            upload_window.title("Upload Image")

            tk.Label(upload_window, text="Enter Student ID:").pack()
            entry_id = tk.Entry(upload_window)
            entry_id.pack()

            submit_button = tk.Button(upload_window, text="Submit", command=submit_id)
            submit_button.pack()
        else:
            messagebox.showerror("Error", "No face detected in the image. Please try again.")

def capture_image():
    def show_frame():
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(frame_rgb)
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # Correct color display
            imgtk = ImageTk.PhotoImage(image=img)
            label.imgtk = imgtk
            label.configure(image=imgtk)
        label.after(10, show_frame)
    
    def snap():
        nonlocal snap_image
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(frame_rgb)
            if face_locations:
                frame = cv2.resize(frame, (216, 216))
                snap_image = frame
                capture_window.destroy()
                cap.release()
                show_captured_image(snap_image)
            else:
                messagebox.showerror("Error", "No face detected in the frame. Please try again.")

    capture_window = tk.Toplevel(root)
    capture_window.title("Capture Image")

    cap = cv2.VideoCapture(camera_port)
    snap_image = None

    label = tk.Label(capture_window)
    label.pack()

    capture_button = tk.Button(capture_window, text="Snap", command=snap)
    capture_button.pack()

    show_frame()

def show_captured_image(image):
    def save_image():
        student_id = entry_id.get()
        if student_id:
            file_name = f'{folderPath}/{student_id}.png'
            cv2.imwrite(file_name, image)
            process_and_upload_image(file_name, image)
            snap_window.destroy()
        else:
            messagebox.showerror("Error", "Please enter a valid student ID.")

    def resnap_image():
        snap_window.destroy()
        capture_image()

    snap_window = tk.Toplevel(root)
    snap_window.title("Captured Image")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image_rgb)
    image_tk = ImageTk.PhotoImage(image_pil)

    label = tk.Label(snap_window, image=image_tk)
    label.image = image_tk
    label.pack()

    tk.Label(snap_window, text="Enter Student ID:").pack()
    entry_id = tk.Entry(snap_window)
    entry_id.pack()

    save_button = tk.Button(snap_window, text="Save", command=save_image)
    save_button.pack()

    resnap_button = tk.Button(snap_window, text="Resnap", command=resnap_image)
    resnap_button.pack()

def process_and_upload_image(file_path, image):
    student_id = os.path.splitext(os.path.basename(file_path))[0]
    blob = bucket.blob(f'Images/{student_id}.png')
    blob.upload_from_filename(file_path)

    encode_image(image, student_id)

def encode_image(image, student_id):
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(img_rgb)
    if encodings:
        encode = encodings[0]
        encode_list = [encode]
        student_ids = [student_id]

        encodeListKnownWithIds = [encode_list, student_ids]
        
        with open("EncodeFile.p", 'wb') as file:
            pickle.dump(encodeListKnownWithIds, file)

        messagebox.showinfo("Success", f"Image and encodings for {student_id} have been uploaded and saved.")
    else:
        messagebox.showerror("Error", "No face detected in the image. Please try again.")

def show_login_window():
    login_window = tk.Toplevel(root)
    login_window.title("Admin Login")

    tk.Label(login_window, text="Admin ID:").pack()
    entry_id = tk.Entry(login_window)
    entry_id.pack()

    tk.Label(login_window, text="Password:").pack()
    entry_password = tk.Entry(login_window, show='*')
    entry_password.pack()

    def login():
        admin_id = entry_id.get()
        admin_password = entry_password.get()
        if admin_id == ADMIN_ID and admin_password == ADMIN_PASSWORD:
            login_window.destroy()
            show_main_window()
        else:
            messagebox.showerror("Error", "Admin unidentified")
            entry_id.delete(0, tk.END)
            entry_password.delete(0, tk.END)
            try_again_button.pack()

    login_button = tk.Button(login_window, text="Login", command=login)
    login_button.pack()

    try_again_button = tk.Button(login_window, text="Try Again", command=lambda: [entry_id.delete(0, tk.END), entry_password.delete(0, tk.END)])
    try_again_button.pack_forget()  # Initially hide the try again button

def show_main_window():
    main_window = tk.Toplevel(root)
    main_window.title("Upload or Capture Image")

    def return_to_login():
        main_window.destroy()
        show_login_window()

    upload_button = tk.Button(main_window, text="Upload", command=upload_image, width=20, height=2)
    upload_button.pack(pady=10)

    capture_button = tk.Button(main_window, text="Capture", command=capture_image, width=20, height=2)
    capture_button.pack(pady=10)

    return_button = tk.Button(main_window, text="Return to Login", command=return_to_login, width=20, height=2)
    return_button.pack(pady=10)

    # Dropdown menu to select camera port
    def set_camera_port(selected_port):
        global camera_port
        camera_port = int(selected_port)

    camera_port_label = tk.Label(main_window, text="Select Camera Port:")
    camera_port_label.pack(pady=5)

    camera_port_var = tk.StringVar(value="0")
    camera_port_menu = tk.OptionMenu(main_window, camera_port_var, "0", "1", "2", command=set_camera_port)
    camera_port_menu.pack(pady=5)

# Initial root window
root = tk.Tk()
root.withdraw()  # Hide the root window

show_login_window()  # Show the login window first

root.mainloop()
