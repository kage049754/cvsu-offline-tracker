import os
import sqlite3
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.garden.xcamera import XCamera
from kivy.core.window import Window
from kivy.logger import Logger

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    Logger.warning('QRScanner: pyzbar not available')

import cv2
import numpy as np


class QRScannerModule:
    """
    Separate QR Scanner module for camera-based scanning.
    Works on both desktop and Android.
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.camera_available = self._check_camera_availability()

    def _check_camera_availability(self):
        """Check if camera is available on this device."""
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.release()
                return True
        except Exception as e:
            Logger.warning(f'QRScanner: Camera check failed: {e}')
        return False

    def scan_qr_code(self, timeout=30):
        """
        Scan QR code from camera.
        
        Args:
            timeout (int): Timeout in seconds
            
        Returns:
            str: Decoded student number or None if timeout/no code found
        """
        if not self.camera_available:
            Logger.error('QRScanner: Camera not available')
            return None

        if not PYZBAR_AVAILABLE:
            Logger.error('QRScanner: pyzbar library not available')
            return None

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            Logger.error('QRScanner: Failed to open camera')
            return None

        try:
            start_time = datetime.now()
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Timeout check
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    Logger.info('QRScanner: Timeout reached')
                    break

                # Decode QR codes
                decoded_objects = pyzbar.decode(frame)
                for obj in decoded_objects:
                    student_number = obj.data.decode('utf-8')
                    Logger.info(f'QRScanner: Successfully scanned: {student_number}')
                    return student_number

                # Display frame with countdown (for desktop testing)
                cv2.putText(frame, f"Scanning... {int(timeout - elapsed)}s", (50, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow('QR Scanner - Press Q to quit', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            Logger.error(f'QRScanner: Scanning error: {e}')
        finally:
            cap.release()
            cv2.destroyAllWindows()

        return None

    def log_scanned_student(self, student_number, mode_name, session_info):
        """
        Log a scanned student to the database.
        
        Args:
            student_number (str): Student ID from QR code
            mode_name (str): Facility mode
            session_info (str): Session details
            
        Returns:
            dict: Success status and message
        """
        student_number = student_number.strip()

        if not student_number:
            return {
                'success': False,
                'message': '[ERROR] No student number scanned.'
            }

        if not session_info.strip():
            session_info = f"General {mode_name} Session"

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if student exists
            cursor.execute(
                "SELECT student_number, full_name, course_year FROM students WHERE student_number = ?",
                (student_number,)
            )
            row = cursor.fetchone()

            if not row:
                conn.close()
                return {
                    'success': False,
                    'message': f'[ERROR] Student {student_number} not found in database.'
                }

            s_num, full_name, course_year = row

            # Check for duplicate entry (same student, same mode, same session within 5 seconds)
            cursor.execute(
                """
                SELECT COUNT(*) FROM activity_logs 
                WHERE student_number = ? AND mode = ? AND session_info = ?
                AND datetime(timestamp) > datetime('now', '-5 seconds')
                """,
                (s_num, mode_name, session_info)
            )
            if cursor.fetchone()[0] > 0:
                conn.close()
                return {
                    'success': False,
                    'message': f'[WARNING] {full_name} already logged in last 5 seconds!'
                }

            # Insert log entry
            cursor.execute(
                """
                INSERT INTO activity_logs (student_number, mode, session_info)
                VALUES (?, ?, ?)
                """,
                (s_num, mode_name, session_info)
            )
            conn.commit()
            conn.close()

            Logger.info(f'QRScanner: Logged {full_name} ({s_num})')
            return {
                'success': True,
                'message': (
                    f'[LOGGED]\n'
                    f'Name: {full_name}\n'
                    f'Course: {course_year}\n'
                    f'ID: {s_num}\n'
                    f'Mode: {mode_name}\n'
                    f'Session: {session_info}'
                )
            }
        except Exception as e:
            Logger.error(f'QRScanner: Database error: {e}')
            return {
                'success': False,
                'message': f'[ERROR] Database error: {str(e)}'
            }
