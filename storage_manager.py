import os
import shutil
from kivy.app import App
from kivy.logger import Logger


class StorageManager:
    """Cross-platform persistent storage for the offline app."""

    @staticmethod
    def get_app_folder():
        try:
            app = App.get_running_app()
            folder = app.user_data_dir if app else os.path.join(os.path.expanduser("~"), ".cvsutracker")
            os.makedirs(folder, exist_ok=True)
            return folder
        except Exception as exc:
            Logger.warning(f"Storage: app folder fallback: {exc}")
            folder = os.path.join(os.path.expanduser("~"), ".cvsutracker")
            os.makedirs(folder, exist_ok=True)
            return folder

    @staticmethod
    def get_downloads_folder():
        """Return a user-visible Downloads folder when available."""
        candidates = []
        if os.name == "nt":
            candidates.append(os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Downloads"))
        candidates.extend([
            "/storage/emulated/0/Download",
            "/sdcard/Download",
            os.path.join(os.path.expanduser("~"), "Downloads"),
        ])
        for folder in candidates:
            try:
                os.makedirs(folder, exist_ok=True)
                if os.path.isdir(folder) and os.access(folder, os.W_OK):
                    return folder
            except Exception:
                continue
        return StorageManager.get_app_folder()

    @staticmethod
    def get_documents_folder():
        folder = "/storage/emulated/0/Documents" if os.name != "nt" else os.path.join(os.path.expanduser("~"), "Documents")
        try:
            os.makedirs(folder, exist_ok=True)
            return folder
        except Exception:
            folder = os.path.join(os.path.expanduser("~"), "Documents")
            os.makedirs(folder, exist_ok=True)
            return folder

    @staticmethod
    def get_database_path():
        return os.path.join(StorageManager.get_app_folder(), "cvsu_system.db")

    @staticmethod
    def get_qr_folder():
        folder = os.path.join(StorageManager.get_app_folder(), "student_qrs")
        os.makedirs(folder, exist_ok=True)
        return folder

    @staticmethod
    def get_reports_folder():
        folder = os.path.join(StorageManager.get_downloads_folder(), "CvSU_Reports")
        try:
            os.makedirs(folder, exist_ok=True)
            return folder
        except Exception:
            folder = os.path.join(StorageManager.get_app_folder(), "reports")
            os.makedirs(folder, exist_ok=True)
            return folder

    @staticmethod
    def copy_file_to_downloads(source_path, filename=None):
        try:
            if not os.path.isfile(source_path):
                return None
            filename = filename or os.path.basename(source_path)
            destination = os.path.join(StorageManager.get_downloads_folder(), filename)
            shutil.copy2(source_path, destination)
            return destination
        except Exception as exc:
            Logger.error(f"Storage: copy failed: {exc}")
            # Always keep a persistent local copy even when public storage is unavailable.
            fallback = os.path.join(StorageManager.get_app_folder(), filename or os.path.basename(source_path))
            try:
                shutil.copy2(source_path, fallback)
                return fallback
            except Exception:
                return None

    @staticmethod
    def list_files_in_folder(folder_path):
        try:
            return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        except Exception:
            return []

    @staticmethod
    def get_file_size(file_path):
        try:
            return os.path.getsize(file_path) if os.path.isfile(file_path) else -1
        except Exception:
            return -1
