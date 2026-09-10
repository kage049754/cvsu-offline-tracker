import os
import shutil
from kivy.logger import Logger
from kivy.app import App


class StorageManager:
    """
    Manages file storage for Android and desktop.
    Handles Downloads, Documents, and app-specific folders.
    """

    @staticmethod
    def get_app_folder():
        """
        Returns the app's private data directory.
        Works on both Android and desktop.
        """
        try:
            app = App.get_running_app()
            if app:
                folder = app.user_data_dir
            else:
                folder = os.path.dirname(os.path.abspath(__file__))
            os.makedirs(folder, exist_ok=True)
            Logger.info(f'StorageManager: App folder = {folder}')
            return folder
        except Exception as e:
            Logger.error(f'StorageManager: App folder error: {e}')
            return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def get_downloads_folder():
        """
        Returns the device's Downloads folder.
        On Android: /storage/emulated/0/Download
        On Desktop: ~/Downloads
        """
        try:
            # Try Android path first
            android_downloads = '/storage/emulated/0/Download'
            if os.path.exists(android_downloads):
                os.makedirs(android_downloads, exist_ok=True)
                Logger.info(f'StorageManager: Using Android Downloads: {android_downloads}')
                return android_downloads

            # Fallback to home directory
            home = os.path.expanduser('~')
            downloads = os.path.join(home, 'Downloads')
            os.makedirs(downloads, exist_ok=True)
            Logger.info(f'StorageManager: Using Desktop Downloads: {downloads}')
            return downloads
        except Exception as e:
            Logger.error(f'StorageManager: Downloads folder error: {e}')
            return StorageManager.get_app_folder()

    @staticmethod
    def get_documents_folder():
        """
        Returns the device's Documents folder.
        On Android: /storage/emulated/0/Documents
        On Desktop: ~/Documents
        """
        try:
            # Try Android path first
            android_docs = '/storage/emulated/0/Documents'
            if os.path.exists(android_docs):
                os.makedirs(android_docs, exist_ok=True)
                Logger.info(f'StorageManager: Using Android Documents: {android_docs}')
                return android_docs

            # Fallback to home directory
            home = os.path.expanduser('~')
            documents = os.path.join(home, 'Documents')
            os.makedirs(documents, exist_ok=True)
            Logger.info(f'StorageManager: Using Desktop Documents: {documents}')
            return documents
        except Exception as e:
            Logger.error(f'StorageManager: Documents folder error: {e}')
            return StorageManager.get_app_folder()

    @staticmethod
    def get_database_path():
        """
        Returns path to the SQLite database.
        """
        app_folder = StorageManager.get_app_folder()
        db_path = os.path.join(app_folder, 'cvsu_system.db')
        Logger.info(f'StorageManager: Database path = {db_path}')
        return db_path

    @staticmethod
    def get_qr_folder():
        """
        Returns path to QR codes folder (app-specific).
        """
        app_folder = StorageManager.get_app_folder()
        qr_folder = os.path.join(app_folder, 'student_qrs')
        os.makedirs(qr_folder, exist_ok=True)
        Logger.info(f'StorageManager: QR folder = {qr_folder}')
        return qr_folder

    @staticmethod
    def get_reports_folder():
        """
        Returns path to reports folder (in Downloads for user access).
        """
        downloads = StorageManager.get_downloads_folder()
        reports_folder = os.path.join(downloads, 'CvSU_Reports')
        os.makedirs(reports_folder, exist_ok=True)
        Logger.info(f'StorageManager: Reports folder = {reports_folder}')
        return reports_folder

    @staticmethod
    def copy_file_to_downloads(source_path, filename=None):
        """
        Copy a file to the Downloads folder for user access.
        
        Args:
            source_path (str): Source file path
            filename (str): Optional new filename
            
        Returns:
            str: Destination path if successful, None otherwise
        """
        try:
            if not os.path.exists(source_path):
                Logger.error(f'StorageManager: Source file not found: {source_path}')
                return None

            downloads = StorageManager.get_downloads_folder()
            if filename is None:
                filename = os.path.basename(source_path)
            
            dest_path = os.path.join(downloads, filename)
            shutil.copy2(source_path, dest_path)
            Logger.info(f'StorageManager: Copied {source_path} to {dest_path}')
            return dest_path
        except Exception as e:
            Logger.error(f'StorageManager: Copy file error: {e}')
            return None

    @staticmethod
    def list_files_in_folder(folder_path):
        """
        List all files in a folder.
        
        Args:
            folder_path (str): Path to folder
            
        Returns:
            list: List of filenames
        """
        try:
            if not os.path.exists(folder_path):
                Logger.warning(f'StorageManager: Folder not found: {folder_path}')
                return []
            
            files = [
                f for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]
            Logger.info(f'StorageManager: Found {len(files)} files in {folder_path}')
            return files
        except Exception as e:
            Logger.error(f'StorageManager: List files error: {e}')
            return []

    @staticmethod
    def get_file_size(file_path):
        """
        Get size of a file in bytes.
        
        Args:
            file_path (str): Path to file
            
        Returns:
            int: File size in bytes, or -1 if error
        """
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            Logger.warning(f'StorageManager: File not found: {file_path}')
            return -1
        except Exception as e:
            Logger.error(f'StorageManager: Get file size error: {e}')
            return -1
