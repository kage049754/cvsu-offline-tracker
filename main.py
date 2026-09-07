import os
import sqlite3
import csv
from datetime import datetime

import qrcode

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.window import Window


# ============================================================
# APP STORAGE
# ============================================================

def get_app_folder():
    """
    Returns a writable folder for the application.
    Works on Windows and Android.
    """
    app = App.get_running_app()

    if app:
        folder = app.user_data_dir
    else:
        folder = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(folder, exist_ok=True)
    return folder


def get_database_path():
    return os.path.join(get_app_folder(), "cvsu_system.db")


def get_qr_folder():
    folder = os.path.join(get_app_folder(), "student_qrs")
    os.makedirs(folder, exist_ok=True)
    return folder


def get_reports_folder():
    folder = os.path.join(get_app_folder(), "reports")
    os.makedirs(folder, exist_ok=True)
    return folder


# ============================================================
# DATABASE
# ============================================================

def init_db():

    db_path = get_database_path()

    conn = sqlite3.connect(db_path)
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
            FOREIGN KEY(student_number)
            REFERENCES students(student_number)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# REGISTER STUDENT
# ============================================================

def register_student_db(student_number, full_name, course_year):

    student_number = student_number.strip()
    full_name = full_name.strip()
    course_year = course_year.strip()

    if not student_number or not full_name or not course_year:
        return "[ERROR] Please complete all fields."

    db_path = get_database_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO students
            (student_number, full_name, course_year)
            VALUES (?, ?, ?)
            """,
            (student_number, full_name, course_year)
        )

        conn.commit()

        message = f"[SUCCESS] Registered: {full_name}"

    except sqlite3.IntegrityError:

        message = "[INFO] Student ID already exists."

    finally:

        conn.close()

    # Generate QR code
    try:

        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5
        )

        qr.add_data(student_number)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        qr_folder = get_qr_folder()

        filename = os.path.join(
            qr_folder,
            f"{student_number}.png"
        )

        img.save(filename)

        message += f"\nQR saved successfully."

    except Exception as e:

        message += f"\n[WARNING] QR generation failed: {e}"

    return message


# ============================================================
# FIND STUDENT
# ============================================================

def get_student(student_number):

    student_number = student_number.strip()

    if not student_number:
        return None

    conn = sqlite3.connect(get_database_path())
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT student_number, full_name, course_year
        FROM students
        WHERE student_number = ?
        """,
        (student_number,)
    )

    row = cursor.fetchone()

    conn.close()

    return row


# ============================================================
# LOG STUDENT
# ============================================================

def log_student(student_number, mode_name, session_info):

    student_number = student_number.strip()

    if not student_number:
        return "[ERROR] Enter a student number."

    if not session_info.strip():
        session_info = f"General {mode_name} Session"

    student = get_student(student_number)

    if not student:
        return "[ERROR] Student ID not found."

    s_num, full_name, course_year = student

    conn = sqlite3.connect(get_database_path())
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO activity_logs
        (student_number, mode, session_info)
        VALUES (?, ?, ?)
        """,
        (s_num, mode_name, session_info)
    )

    conn.commit()
    conn.close()

    return (
        "[LOGGED]\n"
        f"Name: {full_name}\n"
        f"Course: {course_year}\n"
        f"ID: {s_num}\n"
        f"Mode: {mode_name}\n"
        f"Session: {session_info}"
    )


# ============================================================
# EXPORT REPORT
# ============================================================

def export_reports(mode_name, sort_by, export_type):

    conn = sqlite3.connect(get_database_path())
    cursor = conn.cursor()

    query = """
        SELECT
            l.timestamp,
            s.student_number,
            s.full_name,
            s.course_year,
            l.mode,
            l.session_info
        FROM activity_logs l
        JOIN students s
        ON l.student_number = s.student_number
        WHERE l.mode = ?
    """

    cursor.execute(query, (mode_name,))

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return f"[INFO] No records found for {mode_name}."

    # Sort
    if sort_by == "Alphabetical":

        rows = sorted(
            rows,
            key=lambda x: x[2].lower()
        )

    else:

        rows = sorted(
            rows,
            key=lambda x: x[0],
            reverse=True
        )

    reports_folder = get_reports_folder()

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    # CSV
    if export_type == "Spreadsheet (CSV)":

        filename = os.path.join(
            reports_folder,
            f"{mode_name}_Report_{timestamp}.csv"
        )

        with open(
            filename,
            mode="w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Timestamp",
                "Student Number",
                "Full Name",
                "Course & Year",
                "Facility Mode",
                "Session Title"
            ])

            writer.writerows(rows)

    # TXT
    else:

        filename = os.path.join(
            reports_folder,
            f"{mode_name}_Report_{timestamp}.txt"
        )

        with open(
            filename,
            mode="w",
            encoding="utf-8"
        ) as file:

            file.write(
                "==================================================\n"
            )

            file.write(
                f"CvSU SYSTEM FACILITY REPORT: "
                f"{mode_name.upper()}\n"
            )

            file.write(
                f"Generated On: "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            file.write(
                f"Sorting Rule: {sort_by}\n"
            )

            file.write(
                "==================================================\n\n"
            )

            for row in rows:

                file.write(
                    f"Time: {row[0]}\n"
                )

                file.write(
                    f"ID No: {row[1]}\n"
                )

                file.write(
                    f"Name: {row[2]}\n"
                )

                file.write(
                    f"Course: {row[3]}\n"
                )

                file.write(
                    f"Mode: {row[4]}\n"
                )

                file.write(
                    f"Session: {row[5]}\n"
                )

                file.write(
                    "-" * 40 + "\n"
                )

    return (
        "[SUCCESS] Report saved.\n"
        f"File: {filename}"
    )


# ============================================================
# MAIN USER INTERFACE
# ============================================================

class CvSUSystemUI(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"

        self.padding = dp(15)
        self.spacing = dp(8)

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = Label(
            text="CvSU Offline Student Tracker",
            font_size=dp(21),
            bold=True,
            size_hint_y=None,
            height=dp(45)
        )

        self.add_widget(title)

        # ----------------------------------------------------
        # SCROLL AREA
        # ----------------------------------------------------

        scroll = ScrollView()

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        content.bind(
            minimum_height=content.setter("height")
        )

        # ====================================================
        # REGISTRATION
        # ====================================================

        content.add_widget(
            Label(
                text="Student Registration",
                font_size=dp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30)
            )
        )

        self.txt_id = TextInput(
            hint_text="Student Number (e.g. 2023-12345)",
            multiline=False,
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.txt_id)

        self.txt_name = TextInput(
            hint_text="Full Name",
            multiline=False,
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.txt_name)

        self.txt_course = TextInput(
            hint_text="Course & Year (e.g. BSIT 3-1)",
            multiline=False,
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.txt_course)

        self.btn_register = Button(
            text="Register Student + Generate QR",
            size_hint_y=None,
            height=dp(48)
        )

        self.btn_register.bind(
            on_press=self.handle_registration
        )

        content.add_widget(self.btn_register)

        # ====================================================
        # FACILITY
        # ====================================================

        content.add_widget(
            Label(
                text="Facility & Session",
                font_size=dp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30)
            )
        )

        self.mode_spinner = Spinner(
            text="Attendance",
            values=(
                "Attendance",
                "Library",
                "Clinic",
                "Event Entry"
            ),
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.mode_spinner)

        self.txt_session = TextInput(
            hint_text="Session Title / Subject",
            multiline=False,
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.txt_session)

        # ====================================================
        # STUDENT LOGGING
        # ====================================================

        content.add_widget(
            Label(
                text="Student Check-In",
                font_size=dp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30)
            )
        )

        self.txt_scan_id = TextInput(
            hint_text="Enter Student Number",
            multiline=False,
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.txt_scan_id)

        self.btn_log = Button(
            text="Log Student",
            size_hint_y=None,
            height=dp(48)
        )

        self.btn_log.bind(
            on_press=self.handle_logging
        )

        content.add_widget(self.btn_log)

        # ====================================================
        # REPORT
        # ====================================================

        content.add_widget(
            Label(
                text="Reports & Export",
                font_size=dp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30)
            )
        )

        self.sort_spinner = Spinner(
            text="Recent",
            values=(
                "Recent",
                "Alphabetical"
            ),
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.sort_spinner)

        self.format_spinner = Spinner(
            text="Spreadsheet (CSV)",
            values=(
                "Spreadsheet (CSV)",
                "Text Document (.txt)"
            ),
            size_hint_y=None,
            height=dp(42)
        )

        content.add_widget(self.format_spinner)

        self.btn_export = Button(
            text="Export Report",
            size_hint_y=None,
            height=dp(48)
        )

        self.btn_export.bind(
            on_press=self.handle_export
        )

        content.add_widget(self.btn_export)

        # ====================================================
        # STATUS
        # ====================================================

        content.add_widget(
            Label(
                text="System ready.",
                size_hint_y=None,
                height=dp(100),
                halign="center",
                valign="middle"
            )
        )

        self.status_label = content.children[0]

        scroll.add_widget(content)

        self.add_widget(scroll)

    # ========================================================
    # BUTTON HANDLERS
    # ========================================================

    def handle_registration(self, instance):

        result = register_student_db(
            self.txt_id.text,
            self.txt_name.text,
            self.txt_course.text
        )

        self.status_label.text = result

    def handle_logging(self, instance):

        mode = self.mode_spinner.text

        session = self.txt_session.text.strip()

        student_id = self.txt_scan_id.text.strip()

        result = log_student(
            student_id,
            mode,
            session
        )

        self.status_label.text = result

    def handle_export(self, instance):

        mode = self.mode_spinner.text

        sorting = self.sort_spinner.text

        export_type = self.format_spinner.text

        result = export_reports(
            mode,
            sorting,
            export_type
        )

        self.status_label.text = result


# ============================================================
# APPLICATION
# ============================================================

class CvSUApp(App):

    def build(self):

        self.title = "CvSU Offline Student Tracker"

        init_db()

        # Create demo student for testing
        if not get_student("2023-12345"):

            register_student_db(
                "2023-12345",
                "Juan Dela Cruz",
                "BSIT 3-1"
            )

        return CvSUSystemUI()


# ============================================================
# START APP
# ============================================================

if __name__ == "__main__":

    CvSUApp().run()