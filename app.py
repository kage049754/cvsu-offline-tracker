import os
import sqlite3
import csv
import qrcode
import cv2
from datetime import datetime
from pyzbar import pyzbar
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.core.window import Window

Window.size = (400, 750)

# 1. Initialize Local SQLite Database
def init_db():
    conn = sqlite3.connect("cvsu_system.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_number TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            course_year TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_number TEXT,
            mode TEXT,
            session_info TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_number) REFERENCES students(student_number)
        )
    """)
    conn.commit()
    conn.close()

# 2. Register Student & Generate QR
def register_student_db(student_number, full_name, course_year):
    if not student_number or not full_name or not course_year:
        return "[ERROR] All fields are required."
    
    conn = sqlite3.connect("cvsu_system.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (student_number, full_name, course_year) VALUES (?, ?, ?)", 
                       (student_number, full_name, course_year))
        conn.commit()
        msg = f"[SUCCESS] Registered: {full_name}"
    except sqlite3.IntegrityError:
        msg = "[INFO] Student ID already exists."
    finally:
        conn.close()
        
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(student_number)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    os.makedirs("student_qrs", exist_ok=True)
    img.save(f"student_qrs/{student_number}.png")
    
    return msg

# 3. Scanner Handler showing Full Student Profile on Scan
def run_scanner_backend(mode_name, session_info):
    if not session_info.strip():
        session_info = f"General {mode_name} Session"
        
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Fallback test image scan if no webcam is available
        test_img_path = "student_qrs/2023-12345.png"
        if os.path.exists(test_img_path):
            image = cv2.imread(test_img_path)
            decoded_objects = pyzbar.decode(image)
            for obj in decoded_objects:
                s_num = obj.data.decode('utf-8')
                conn = sqlite3.connect("cvsu_system.db")
                cursor = conn.cursor()
                cursor.execute("SELECT full_name, course_year FROM students WHERE student_number = ?", (s_num,))
                row = cursor.fetchone()
                if row:
                    full_name, course_year = row
                    cursor.execute("INSERT INTO activity_logs (student_number, mode, session_info) VALUES (?, ?, ?)", 
                                   (s_num, mode_name, session_info))
                    conn.commit()
                    conn.close()
                    return f"LOGGED: {full_name} ({s_num}) - {course_year} | [{session_info}]"
                conn.close()
        return "[ERROR] No webcam found & no fallback QR image."

    logged_msg = f"[INFO] Active Session: {session_info}"
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        decoded_objects = pyzbar.decode(frame)
        for obj in decoded_objects:
            s_num = obj.data.decode('utf-8')
            conn = sqlite3.connect("cvsu_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, course_year FROM students WHERE student_number = ?", (s_num,))
            row = cursor.fetchone()
            if row:
                full_name, course_year = row
                cursor.execute("INSERT INTO activity_logs (student_number, mode, session_info) VALUES (?, ?, ?)", 
                               (s_num, mode_name, session_info))
                conn.commit()
                # Display full details in feed
                logged_msg = f"LOGGED: {full_name} | {course_year} | ID: {s_num}"
                cv2.putText(frame, f"{full_name} ({course_year})", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            conn.close()
            break
        
        cv2.imshow(f"CvSU Scanner - {session_info} (Press 'q' to stop)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return logged_msg

# 4. Document & Spreadsheet Export Module
def export_reports(mode_name, sort_by, export_type):
    conn = sqlite3.connect("cvsu_system.db")
    cursor = conn.cursor()
    
    query = """
        SELECT l.timestamp, s.student_number, s.full_name, s.course_year, l.mode, l.session_info 
        FROM activity_logs l
        JOIN students s ON l.student_number = s.student_number
        WHERE l.mode = ?
    """
    cursor.execute(query, (mode_name,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"[INFO] No records found for {mode_name}."

    # Sorting
    if sort_by == "Alphabetical":
        rows = sorted(rows, key=lambda x: x[2])
    else:
        rows = sorted(rows, key=lambda x: x[0], reverse=True)

    os.makedirs("reports", exist_ok=True)
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    if export_type == "Spreadsheet (CSV)":
        filename = f"reports/{mode_name}_Report_{timestamp_str}.csv"
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Student Number", "Full Name", "Course & Year", "Facility Mode", "Session Title"])
            writer.writerows(rows)
    else:
        # Export as a formatted Text Document (.txt)
        filename = f"reports/{mode_name}_Report_{timestamp_str}.txt"
        with open(filename, mode='w', encoding='utf-8') as f:
            f.write(f"==================================================\n")
            f.write(f"CvSU SYSTEM FACILITY REPORT: {mode_name.upper()}\n")
            f.write(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Sorting Rule: {sort_by}\n")
            f.write(f"==================================================\n\n")
            for row in rows:
                f.write(f"Time: {row[0]}\n")
                f.write(f"ID No: {row[1]}\n")
                f.write(f"Name: {row[2]}\n")
                f.write(f"Course: {row[3]}\n")
                f.write(f"Session: {row[5]}\n")
                f.write("-" * 40 + "\n")
                
    return f"[SUCCESS] Report saved: {filename}"

# 5. Kivy Graphical User Interface
class CvSUSystemUI(BoxLayout):
    def __init__(self, **kwargs):
        super(CvSUSystemUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        self.add_widget(Label(text="CvSU Offline System", font_size=20, size_hint_y=None, height=35, bold=True))

        # Registration Section
        self.add_widget(Label(text="Student Registration", font_size=14, size_hint_y=None, height=25, color=(0.2, 0.6, 1, 1)))
        self.txt_id = TextInput(hint_text="Student Number (e.g. 2023-12345)", multiline=False, size_hint_y=None, height=38)
        self.add_widget(self.txt_id)
        self.txt_name = TextInput(hint_text="Full Name", multiline=False, size_hint_y=None, height=38)
        self.add_widget(self.txt_name)
        self.txt_course = TextInput(hint_text="Course & Year (e.g. BSIT 3-1)", multiline=False, size_hint_y=None, height=38)
        self.add_widget(self.txt_course)

        self.btn_register = Button(text="Register Student & QR", size_hint_y=None, height=42, background_color=(0.1, 0.6, 0.3, 1))
        self.btn_register.bind(on_press=self.handle_registration)
        self.add_widget(self.btn_register)

        # Operational Mode & Session
        self.add_widget(Label(text="Facility & Session Setup", font_size=14, size_hint_y=None, height=25, color=(0.2, 0.6, 1, 1)))
        self.mode_spinner = Spinner(text='Attendance', values=('Attendance', 'Library', 'Clinic', 'Event Entry'), size_hint_y=None, height=38)
        self.add_widget(self.mode_spinner)

        self.txt_session = TextInput(hint_text="Session Title / Subject (e.g. IT 311 - Midterms)", multiline=False, size_hint_y=None, height=38)
        self.add_widget(self.txt_session)

        self.btn_scan = Button(text="Launch Scanner (Shows Full Profile)", size_hint_y=None, height=42, background_color=(0.2, 0.4, 0.8, 1))
        self.btn_scan.bind(on_press=self.handle_scanning)
        self.add_widget(self.btn_scan)

        # Report & Export Configuration
        self.add_widget(Label(text="Document Export & Sorting", font_size=14, size_hint_y=None, height=25, color=(0.2, 0.6, 1, 1)))
        
        # Row layout for sorting and format spinners
        options_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=38, spacing=5)
        self.sort_spinner = Spinner(text='Recent', values=('Recent', 'Alphabetical'))
        self.format_spinner = Spinner(text='Spreadsheet (CSV)', values=('Spreadsheet (CSV)', 'Text Document (.txt)'))
        options_layout.add_widget(self.sort_spinner)
        options_layout.add_widget(self.format_spinner)
        self.add_widget(options_layout)

        self.btn_export = Button(text="Export Report Document", size_hint_y=None, height=42, background_color=(0.8, 0.4, 0.1, 1))
        self.btn_export.bind(on_press=self.handle_export)
        self.add_widget(self.btn_export)

        # Status Display Box
        self.status_label = Label(text="System ready. Offline DB active.", font_size=13, halign='center', valign='middle')
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.add_widget(self.status_label)

    def handle_registration(self, instance):
        self.status_label.text = register_student_db(self.txt_id.text.strip(), self.txt_name.text.strip(), self.txt_course.text.strip())

    def handle_scanning(self, instance):
        mode = self.mode_spinner.text
        session = self.txt_session.text.strip()
        self.status_label.text = f"Running scanner for [{session}]..."
        self.status_label.text = run_scanner_backend(mode, session)

    def handle_export(self, instance):
        mode = self.mode_spinner.text
        sorting = self.sort_spinner.text
        doc_format = self.format_spinner.text
        self.status_label.text = export_reports(mode, sorting, doc_format)

class CvSUApp(App):
    def build(self):
        init_db()
        register_student_db("2023-12345", "Juan Dela Cruz", "BSIT 3-1")
        self.title = "CvSU Offline Student Tracker"
        return CvSUSystemUI()

if __name__ == '__main__':
    CvSUApp().run()