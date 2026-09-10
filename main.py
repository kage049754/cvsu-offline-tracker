#!/usr/bin/env python3
"""
CvSU Offline Student Tracker - Main Production Entry Point

This is the unified main entry point that works on both desktop and Android.
Use this file instead of main_production.py.

Features:
- QR Code scanning and manual entry
- Offline SQLite database
- Report export to CSV/TXT
- Multi-facility support
- Full Android permission handling
- Cross-platform storage management
"""

import os
import sqlite3
import csv
from datetime import datetime
from threading import Thread

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
from kivy.logger import Logger
from kivy.clock import Clock

from storage_manager import StorageManager
from qr_scanner import QRScannerModule

try:
    from permissions_handler import PermissionsHandler
    PERMISSIONS_AVAILABLE = True
    Logger.info('Main: Android permissions handler loaded')
except ImportError:
    PERMISSIONS_AVAILABLE = False
    Logger.warning('Main: Android permissions not available (normal on desktop)')


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """Initialize SQLite database with required tables."""
    try:
        db_path = StorageManager.get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_number TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                course_year TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create activity logs table
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
        Logger.info('Database: Initialized successfully')
    except Exception as e:
        Logger.error(f'Database: Initialization error: {e}')
        raise


def register_student_db(student_number, full_name, course_year):
    """Register a new student and generate QR code."""
    student_number = student_number.strip()
    full_name = full_name.strip()
    course_year = course_year.strip()

    if not student_number or not full_name or not course_year:
        return {'success': False, 'message': '[ERROR] Please complete all fields.'}

    db_path = StorageManager.get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO students (student_number, full_name, course_year) VALUES (?, ?, ?)",
            (student_number, full_name, course_year)
        )
        conn.commit()
        message = f"[SUCCESS] Registered: {full_name}"
    except sqlite3.IntegrityError:
        conn.close()
        return {'success': False, 'message': '[INFO] Student ID already exists.'}
    finally:
        conn.close()

    # Generate QR code
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(student_number)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        qr_folder = StorageManager.get_qr_folder()
        filename = os.path.join(qr_folder, f"{student_number}.png")
        img.save(filename)
        message += f"\nQR saved: {student_number}.png"
        Logger.info(f'Database: Generated QR for {student_number}')
    except Exception as e:
        message += f"\n[WARNING] QR generation failed: {e}"
        Logger.error(f'Database: QR generation error: {e}')

    return {'success': True, 'message': message}


def get_student(student_number):
    """Retrieve student information from database."""
    student_number = student_number.strip()
    if not student_number:
        return None

    db_path = StorageManager.get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT student_number, full_name, course_year FROM students WHERE student_number = ?",
        (student_number,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def log_student(student_number, mode_name, session_info):
    """Log a student's attendance manually."""
    student_number = student_number.strip()

    if not student_number:
        return {'success': False, 'message': '[ERROR] Enter a student number.'}

    if not session_info.strip():
        session_info = f"General {mode_name} Session"

    student = get_student(student_number)
    if not student:
        return {'success': False, 'message': '[ERROR] Student ID not found.'}

    s_num, full_name, course_year = student

    db_path = StorageManager.get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO activity_logs (student_number, mode, session_info) VALUES (?, ?, ?)",
            (s_num, mode_name, session_info)
        )
        conn.commit()
        Logger.info(f'Database: Logged {full_name}')
        return {
            'success': True,
            'message': (
                f"[LOGGED]\n"
                f"Name: {full_name}\n"
                f"Course: {course_year}\n"
                f"ID: {s_num}\n"
                f"Mode: {mode_name}\n"
                f"Session: {session_info}"
            )
        }
    except Exception as e:
        Logger.error(f'Database: Log student error: {e}')
        return {'success': False, 'message': f'[ERROR] Database error: {str(e)}'}
    finally:
        conn.close()


def export_reports(mode_name, sort_by, export_type):
    """Export attendance reports to CSV or TXT format."""
    db_path = StorageManager.get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT l.timestamp, s.student_number, s.full_name, s.course_year, l.mode, l.session_info
        FROM activity_logs l
        JOIN students s ON l.student_number = s.student_number
        WHERE l.mode = ?
        """,
        (mode_name,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {'success': False, 'message': f'[INFO] No records found for {mode_name}.'}

    # Sort records
    if sort_by == "Alphabetical":
        rows = sorted(rows, key=lambda x: x[2].lower())
    else:
        rows = sorted(rows, key=lambda x: x[0], reverse=True)

    reports_folder = StorageManager.get_reports_folder()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    try:
        if export_type == "Spreadsheet (CSV)":
            filename = os.path.join(reports_folder, f"{mode_name}_Report_{timestamp}.csv")
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Student Number", "Full Name", "Course & Year", "Facility Mode", "Session Title"])
                writer.writerows(rows)
        else:
            filename = os.path.join(reports_folder, f"{mode_name}_Report_{timestamp}.txt")
            with open(filename, mode='w', encoding='utf-8') as file:
                file.write("==================================================\n")
                file.write(f"CvSU SYSTEM FACILITY REPORT: {mode_name.upper()}\n")
                file.write(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write(f"Sorting Rule: {sort_by}\n")
                file.write(f"==================================================\n\n")
                for row in rows:
                    file.write(f"Time: {row[0]}\n")
                    file.write(f"ID No: {row[1]}\n")
                    file.write(f"Name: {row[2]}\n")
                    file.write(f"Course: {row[3]}\n")
                    file.write(f"Mode: {row[4]}\n")
                    file.write(f"Session: {row[5]}\n")
                    file.write("-" * 40 + "\n")

        Logger.info(f'Database: Report exported to {filename}')
        return {'success': True, 'message': f'[SUCCESS] Report saved to Downloads folder.\nFile: {os.path.basename(filename)}'}
    except Exception as e:
        Logger.error(f'Database: Export error: {e}')
        return {'success': False, 'message': f'[ERROR] Export failed: {str(e)}'}


# ============================================================
# MAIN USER INTERFACE
# ============================================================

class CvSUSystemUI(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(15)
        self.spacing = dp(8)

        self.qr_scanner = QRScannerModule(StorageManager.get_database_path())
        self.scanning = False

        # Title bar
        title_box = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        title = Label(
            text="CvSU Offline Student Tracker",
            font_size=dp(18),
            bold=True
        )
        title_box.add_widget(title)
        self.add_widget(title_box)

        # Scroll area
        scroll = ScrollView()
        content = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # Registration section
        content.add_widget(
            Label(text="Student Registration", font_size=dp(16), bold=True,
                  size_hint_y=None, height=dp(30))
        )

        self.txt_id = TextInput(
            hint_text="Student Number (e.g. 2023-12345)",
            multiline=False, size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.txt_id)

        self.txt_name = TextInput(
            hint_text="Full Name", multiline=False,
            size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.txt_name)

        self.txt_course = TextInput(
            hint_text="Course & Year (e.g. BSIT 3-1)",
            multiline=False, size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.txt_course)

        self.btn_register = Button(
            text="Register Student + Generate QR",
            size_hint_y=None, height=dp(48),
            background_color=(0.1, 0.6, 0.3, 1)
        )
        self.btn_register.bind(on_press=self.handle_registration)
        content.add_widget(self.btn_register)

        # Facility & Session
        content.add_widget(
            Label(text="Facility & Session", font_size=dp(16), bold=True,
                  size_hint_y=None, height=dp(30))
        )

        self.mode_spinner = Spinner(
            text="Attendance",
            values=("Attendance", "Library", "Clinic", "Event Entry"),
            size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.mode_spinner)

        self.txt_session = TextInput(
            hint_text="Session Title / Subject",
            multiline=False, size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.txt_session)

        # Student Check-in
        content.add_widget(
            Label(text="Student Check-In", font_size=dp(16), bold=True,
                  size_hint_y=None, height=dp(30))
        )

        self.txt_scan_id = TextInput(
            hint_text="Enter Student Number or scan QR",
            multiline=False, size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.txt_scan_id)

        btn_layout = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))

        self.btn_log = Button(
            text="Log Student",
            size_hint_x=0.6,
            background_color=(0.2, 0.4, 0.8, 1)
        )
        self.btn_log.bind(on_press=self.handle_logging)
        btn_layout.add_widget(self.btn_log)

        self.btn_scan_qr = Button(
            text="Scan QR",
            size_hint_x=0.4,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        self.btn_scan_qr.bind(on_press=self.handle_qr_scan)
        btn_layout.add_widget(self.btn_scan_qr)
        content.add_widget(btn_layout)

        # Reports & Export
        content.add_widget(
            Label(text="Reports & Export", font_size=dp(16), bold=True,
                  size_hint_y=None, height=dp(30))
        )

        self.sort_spinner = Spinner(
            text="Recent",
            values=("Recent", "Alphabetical"),
            size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.sort_spinner)

        self.format_spinner = Spinner(
            text="Spreadsheet (CSV)",
            values=("Spreadsheet (CSV)", "Text Document (.txt)"),
            size_hint_y=None, height=dp(42)
        )
        content.add_widget(self.format_spinner)

        self.btn_export = Button(
            text="Export Report to Downloads",
            size_hint_y=None, height=dp(48),
            background_color=(0.8, 0.4, 0.1, 1)
        )
        self.btn_export.bind(on_press=self.handle_export)
        content.add_widget(self.btn_export)

        # Status display
        self.status_label = Label(
            text="System ready. Waiting for input...",
            size_hint_y=None, height=dp(120),
            halign="center", valign="middle"
        )
        self.status_label.bind(texture_size=self.status_label.setter('size'))
        content.add_widget(self.status_label)

        scroll.add_widget(content)
        self.add_widget(scroll)

    def handle_registration(self, instance):
        """Handle student registration."""
        result = register_student_db(
            self.txt_id.text, self.txt_name.text, self.txt_course.text
        )
        self.status_label.text = result['message']
        if result['success']:
            self.txt_id.text = ""
            self.txt_name.text = ""
            self.txt_course.text = ""

    def handle_logging(self, instance):
        """Handle manual student logging."""
        mode = self.mode_spinner.text
        session = self.txt_session.text.strip()
        student_id = self.txt_scan_id.text.strip()

        result = log_student(student_id, mode, session)
        self.status_label.text = result['message']
        if result['success']:
            self.txt_scan_id.text = ""

    def handle_qr_scan(self, instance):
        """Handle QR code scanning in background thread."""
        if self.scanning:
            self.status_label.text = "[INFO] Scan already in progress..."
            return

        if not self.qr_scanner.camera_available:
            self.status_label.text = "[ERROR] Camera not available. Use manual entry."
            return

        self.scanning = True
        self.btn_scan_qr.disabled = True
        self.status_label.text = "[INFO] Starting QR scan... Please point camera at QR code."

        thread = Thread(target=self._scan_qr_thread, daemon=True)
        thread.start()

    def _scan_qr_thread(self):
        """Background thread for QR scanning."""
        try:
            student_number = self.qr_scanner.scan_qr_code(timeout=30)
            if student_number:
                Clock.schedule_once(lambda dt: self._handle_scanned_student(student_number), 0)
            else:
                Clock.schedule_once(lambda dt: self._scan_timeout(), 0)
        except Exception as e:
            Logger.error(f'Scan error: {e}')
            Clock.schedule_once(lambda dt: self._scan_error(str(e)), 0)

    def _handle_scanned_student(self, student_number):
        """Process scanned student."""
        self.txt_scan_id.text = student_number
        mode = self.mode_spinner.text
        session = self.txt_session.text.strip()
        result = self.qr_scanner.log_scanned_student(student_number, mode, session)
        self.status_label.text = result['message']
        self.scanning = False
        self.btn_scan_qr.disabled = False

    def _scan_timeout(self):
        """Handle scan timeout."""
        self.status_label.text = "[INFO] QR scan timeout. No code detected."
        self.scanning = False
        self.btn_scan_qr.disabled = False

    def _scan_error(self, error):
        """Handle scan error."""
        self.status_label.text = f"[ERROR] Scan error: {error}"
        self.scanning = False
        self.btn_scan_qr.disabled = False

    def handle_export(self, instance):
        """Handle report export."""
        mode = self.mode_spinner.text
        sorting = self.sort_spinner.text
        export_type = self.format_spinner.text

        self.status_label.text = "[INFO] Exporting report..."
        result = export_reports(mode, sorting, export_type)
        self.status_label.text = result['message']


# ============================================================
# APPLICATION
# ============================================================

class CvSUApp(App):

    def build(self):
        self.title = "CvSU Offline Student Tracker"

        # Request permissions on Android
        if PERMISSIONS_AVAILABLE:
            try:
                PermissionsHandler.request_all_permissions()
                Logger.info('App: Permissions requested')
            except Exception as e:
                Logger.warning(f'App: Permission request failed: {e}')

        # Initialize database
        init_db()

        # Create demo student if needed
        if not get_student("2023-12345"):
            register_student_db("2023-12345", "Juan Dela Cruz", "BSIT 3-1")

        return CvSUSystemUI()


if __name__ == "__main__":
    CvSUApp().run()
