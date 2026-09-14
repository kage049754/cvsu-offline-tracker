#!/usr/bin/env python3
"""CvSU Offline Student Tracker - phone-ready offline attendance app."""

import csv
import os
import shutil
import sqlite3
from datetime import datetime

import cv2
import numpy as np
import qrcode
from PIL import Image as PILImage, ImageDraw, ImageFont

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from storage_manager import StorageManager

try:
    from permissions_handler import PermissionsHandler
except Exception:
    PermissionsHandler = None

DB_PATH = StorageManager.get_database_path()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        student_number TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        course_year TEXT NOT NULL,
        section_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(section_id) REFERENCES sections(id) ON DELETE SET NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_number TEXT NOT NULL,
        mode TEXT NOT NULL,
        session_info TEXT NOT NULL,
        section_name TEXT,
        timestamp TEXT NOT NULL,
        attendance_date TEXT NOT NULL,
        FOREIGN KEY(student_number) REFERENCES students(student_number)
    )""")

    # Upgrade databases created by the older app without deleting existing data.
    cols = {r[1] for r in cur.execute("PRAGMA table_info(students)").fetchall()}
    if "section_id" not in cols:
        cur.execute("ALTER TABLE students ADD COLUMN section_id INTEGER")
    log_cols = {r[1] for r in cur.execute("PRAGMA table_info(activity_logs)").fetchall()}
    if "section_name" not in log_cols:
        cur.execute("ALTER TABLE activity_logs ADD COLUMN section_name TEXT")
    if "attendance_date" not in log_cols:
        cur.execute("ALTER TABLE activity_logs ADD COLUMN attendance_date TEXT")
        cur.execute("UPDATE activity_logs SET attendance_date = substr(timestamp,1,10) WHERE attendance_date IS NULL")
    if "timestamp" not in log_cols:
        cur.execute("ALTER TABLE activity_logs ADD COLUMN timestamp TEXT")
        cur.execute("UPDATE activity_logs SET timestamp = datetime('now') WHERE timestamp IS NULL")
    conn.commit()
    conn.close()


def ensure_section(name):
    name = name.strip()
    if not name:
        return None
    conn = db()
    conn.execute("INSERT OR IGNORE INTO sections(name) VALUES (?)", (name,))
    row = conn.execute("SELECT id FROM sections WHERE name=?", (name,)).fetchone()
    conn.commit()
    conn.close()
    return row[0] if row else None


def section_names():
    conn = db()
    rows = conn.execute("SELECT name FROM sections ORDER BY name COLLATE NOCASE").fetchall()
    conn.close()
    return [r[0] for r in rows]


def create_qr_card(student_number, full_name, course_year, section_name):
    """Create a printable/student-shareable QR card with the student's name."""
    qr = qrcode.QRCode(version=None, box_size=10, border=4)
    qr.add_data(student_number)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    width = qr_img.width
    card = PILImage.new("RGB", (width, width + 190), "white")
    card.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(card)
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 20)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
    y = width + 15
    draw.text((width // 2, y), full_name, fill="black", font=font_big, anchor="ma")
    draw.text((width // 2, y + 45), f"ID: {student_number}", fill="black", font=font_small, anchor="ma")
    draw.text((width // 2, y + 75), f"{course_year}  •  {section_name}", fill="black", font=font_small, anchor="ma")
    draw.text((width // 2, y + 110), "CvSU Offline Student Tracker", fill="black", font=font_small, anchor="ma")
    folder = StorageManager.get_qr_folder()
    path = os.path.join(folder, f"{student_number}.png")
    card.save(path, "PNG")
    return path


def register_student(student_number, full_name, course_year, section_name):
    student_number = student_number.strip()
    full_name = full_name.strip()
    course_year = course_year.strip()
    section_name = section_name.strip()
    if not all((student_number, full_name, course_year, section_name)):
        return False, "Please complete Student ID, Name, Course & Year, and Section."
    section_id = ensure_section(section_name)
    conn = db()
    try:
        conn.execute("INSERT INTO students(student_number,full_name,course_year,section_id) VALUES(?,?,?,?)",
                     (student_number, full_name, course_year, section_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False, "That Student ID is already registered."
    conn.close()
    try:
        qr_path = create_qr_card(student_number, full_name, course_year, section_name)
    except Exception as exc:
        return True, f"Student saved, but QR creation failed: {exc}"
    return True, qr_path


def find_student(student_number):
    conn = db()
    row = conn.execute("""SELECT s.student_number,s.full_name,s.course_year,COALESCE(sec.name,'')
                          FROM students s LEFT JOIN sections sec ON sec.id=s.section_id
                          WHERE s.student_number=?""", (student_number.strip(),)).fetchone()
    conn.close()
    return row


def record_attendance(student_number, mode, session, selected_section):
    student = find_student(student_number)
    if not student:
        return False, "Student ID is not registered."
    sid, name, course, student_section = student
    if selected_section and student_section != selected_section:
        return False, f"REJECTED: {name} belongs to {student_section or 'another section'}, not {selected_section}."
    now = datetime.now()
    session = session.strip() or f"General {mode} Session"
    conn = db()
    duplicate = conn.execute("""SELECT id FROM activity_logs
        WHERE student_number=? AND mode=? AND session_info=? AND attendance_date=?""",
        (sid, mode, session, now.strftime("%Y-%m-%d"))).fetchone()
    if duplicate:
        conn.close()
        return False, f"Already marked present today: {name}."
    conn.execute("""INSERT INTO activity_logs
        (student_number,mode,session_info,section_name,timestamp,attendance_date)
        VALUES(?,?,?,?,?,?)""", (sid, mode, session, student_section, now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return True, f"PRESENT\n{name}\n{sid}\nArrival: {now.strftime('%Y-%m-%d %I:%M:%S %p')}"


def export_report(mode, section):
    conn = db()
    query = """SELECT l.timestamp,s.student_number,s.full_name,s.course_year,COALESCE(l.section_name,''),l.mode,l.session_info
               FROM activity_logs l JOIN students s ON s.student_number=l.student_number WHERE l.mode=?"""
    args = [mode]
    if section:
        query += " AND l.section_name=?"
        args.append(section)
    query += " ORDER BY l.timestamp DESC"
    rows = conn.execute(query, args).fetchall()
    conn.close()
    if not rows:
        return None
    folder = StorageManager.get_reports_folder()
    path = os.path.join(folder, f"{mode}_{section or 'All'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Arrival Date/Time","Student ID","Name","Course & Year","Section","Mode","Session"])
        w.writerows(rows)
    return path


def android_share(path):
    """Open the Android share sheet for an image/file. No internet is used."""
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        StrictMode = autoclass("android.os.StrictMode")
        StrictMode.setVmPolicy(StrictMode.VmPolicy.Builder().build())
        intent = Intent(Intent.ACTION_SEND)
        intent.setType("image/png" if path.lower().endswith(".png") else "text/csv")
        intent.putExtra(Intent.EXTRA_STREAM, Uri.fromFile(java.io.File(path)) if False else Uri.parse("file://" + path))
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        chooser = Intent.createChooser(intent, "Share CvSU file")
        PythonActivity.mActivity.startActivity(chooser)
        return True
    except Exception:
        return False


class ScannerPopup(Popup):
    def __init__(self, on_result, **kwargs):
        super().__init__(title="Scan Student QR", size_hint=(0.96, 0.86), **kwargs)
        self.on_result = on_result
        self.camera = Camera(play=True, resolution=(640, 480), index=0)
        self.last_value = None
        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        root.add_widget(self.camera)
        root.add_widget(Label(text="Point the camera at the student's QR code", size_hint_y=None, height=dp(45)))
        close = Button(text="Cancel", size_hint_y=None, height=dp(48))
        close.bind(on_release=self.dismiss)
        root.add_widget(close)
        self.content = root
        Clock.schedule_interval(self.scan_frame, 0.35)

    def scan_frame(self, _dt):
        if not self.camera.texture:
            return
        try:
            tex = self.camera.texture
            pixels = np.frombuffer(tex.pixels, dtype=np.uint8)
            frame = pixels.reshape(tex.height, tex.width, 4)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            value, points, _ = cv2.QRCodeDetector().detectAndDecode(frame)
            if value and value != self.last_value:
                self.last_value = value.strip()
                Clock.unschedule(self.scan_frame)
                self.dismiss()
                self.on_result(self.last_value)
        except Exception:
            pass

    def dismiss(self, *args, **kwargs):
        Clock.unschedule(self.scan_frame)
        try:
            self.camera.play = False
        except Exception:
            pass
        return super().dismiss(*args, **kwargs)


class AppUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(8), **kwargs)
        self.qr_path = None
        self.build_ui()
        self.refresh_sections()

    def label(self, text, size=30):
        return Label(text=text, bold=True, font_size=dp(size), size_hint_y=None, height=dp(36))

    def build_ui(self):
        self.add_widget(self.label("CvSU Offline Attendance", 20))
        scroll = ScrollView()
        body = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        body.add_widget(self.label("1. Section", 16))
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.section_spinner = Spinner(text="Select Section", values=(), size_hint_x=0.65)
        row.add_widget(self.section_spinner)
        self.new_section = TextInput(hint_text="New section (BSIT 2-6)", multiline=False, size_hint_x=0.35)
        row.add_widget(self.new_section)
        body.add_widget(row)
        add_section = Button(text="Add / Select Section", size_hint_y=None, height=dp(44))
        add_section.bind(on_release=self.add_section)
        body.add_widget(add_section)

        body.add_widget(self.label("2. Register Student + QR", 16))
        self.student_id = TextInput(hint_text="Student ID", multiline=False, size_hint_y=None, height=dp(44))
        self.student_name = TextInput(hint_text="Full Name", multiline=False, size_hint_y=None, height=dp(44))
        self.student_course = TextInput(hint_text="Course & Year", multiline=False, size_hint_y=None, height=dp(44))
        for w in (self.student_id, self.student_name, self.student_course): body.add_widget(w)
        reg = Button(text="Create Student QR", size_hint_y=None, height=dp(48))
        reg.bind(on_release=self.register)
        body.add_widget(reg)

        body.add_widget(self.label("3. Attendance", 16))
        self.session = TextInput(hint_text="Subject / Session", multiline=False, size_hint_y=None, height=dp(44))
        body.add_widget(self.session)
        scan_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        scan = Button(text="SCAN QR")
        scan.bind(on_release=self.scan)
        manual = Button(text="Mark by ID")
        manual.bind(on_release=self.manual_attendance)
        scan_row.add_widget(scan); scan_row.add_widget(manual)
        body.add_widget(scan_row)
        self.manual_id = TextInput(hint_text="Student ID for manual check-in", multiline=False, size_hint_y=None, height=dp(44))
        body.add_widget(self.manual_id)

        body.add_widget(self.label("4. Reports", 16))
        export = Button(text="Export Section Attendance CSV", size_hint_y=None, height=dp(48))
        export.bind(on_release=self.export)
        body.add_widget(export)

        self.status = Label(text="Offline database ready. Data is saved on this phone.", halign="center", valign="middle", size_hint_y=None, height=dp(110))
        self.status.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        body.add_widget(self.status)
        scroll.add_widget(body)
        self.add_widget(scroll)

    def refresh_sections(self):
        names = section_names()
        self.section_spinner.values = names
        if names and self.section_spinner.text == "Select Section":
            self.section_spinner.text = names[0]

    def selected_section(self):
        return "" if self.section_spinner.text == "Select Section" else self.section_spinner.text.strip()

    def add_section(self, *_):
        name = self.new_section.text.strip()
        if not name:
            self.status.text = "Enter a section name first."
            return
        ensure_section(name)
        self.new_section.text = ""
        self.refresh_sections()
        self.section_spinner.text = name
        self.status.text = f"Section ready: {name}"

    def register(self, *_):
        section = self.selected_section()
        ok, result = register_student(self.student_id.text, self.student_name.text, self.student_course.text, section)
        if not ok:
            self.status.text = result
            return
        self.student_id.text = self.student_name.text = self.student_course.text = ""
        self.qr_path = result
        student = find_student(os.path.basename(result).rsplit(".",1)[0]) if result.endswith(".png") else None
        if student:
            self.show_qr(student, result)
        else:
            self.status.text = "Student saved and QR generated."

    def show_qr(self, student, path):
        sid, name, course, section = student
        box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        box.add_widget(Label(text=f"{name}\n{sid}\n{course} • {section}", size_hint_y=None, height=dp(70), halign="center"))
        box.add_widget(Image(source=path, allow_stretch=True, keep_ratio=True))
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        download = Button(text="Download")
        share = Button(text="Share")
        close = Button(text="Close")
        buttons.add_widget(download); buttons.add_widget(share); buttons.add_widget(close)
        box.add_widget(buttons)
        popup = Popup(title="Student QR Code", content=box, size_hint=(0.94, 0.90))
        download.bind(on_release=lambda *_: self.download_qr(path, popup))
        share.bind(on_release=lambda *_: self.share_qr(path))
        close.bind(on_release=popup.dismiss)
        popup.open()

    def download_qr(self, path, popup=None):
        dest = StorageManager.copy_file_to_downloads(path, os.path.basename(path))
        self.status.text = f"QR downloaded: {os.path.basename(dest or path)}"
        if popup: popup.dismiss()

    def share_qr(self, path):
        if not android_share(path):
            self.status.text = "Share sheet could not open. Use Download instead."

    def scan(self, *_):
        if PermissionsHandler:
            try: PermissionsHandler.request_camera_permission()
            except Exception: pass
        ScannerPopup(self.process_scan).open()

    def process_scan(self, value):
        self.manual_id.text = value
        self.manual_attendance()

    def manual_attendance(self, *_):
        ok, msg = record_attendance(self.manual_id.text, "Attendance", self.session.text, self.selected_section())
        self.status.text = msg
        if ok: self.manual_id.text = ""

    def export(self, *_):
        path = export_report("Attendance", self.selected_section())
        self.status.text = f"Report saved: {os.path.basename(path)}" if path else "No attendance records for this section."


class CvSUApp(App):
    def build(self):
        self.title = "CvSU Offline Attendance"
        Window.softinput_mode = "below_target"
        init_db()
        if PermissionsHandler:
            try: PermissionsHandler.request_all_permissions()
            except Exception: pass
        return AppUI()


if __name__ == "__main__":
    CvSUApp().run()
