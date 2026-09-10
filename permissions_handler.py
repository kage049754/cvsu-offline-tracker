import os
from kivy.logger import Logger
from jnius import autoclass, cast
from android.permissions import request_permissions, Permission, check_permission


class PermissionsHandler:
    """
    Handles Android runtime permissions.
    Supports camera, storage, and file access.
    """

    # Android permission constants
    CAMERA = 'android.permission.CAMERA'
    READ_EXTERNAL_STORAGE = 'android.permission.READ_EXTERNAL_STORAGE'
    WRITE_EXTERNAL_STORAGE = 'android.permission.WRITE_EXTERNAL_STORAGE'
    MANAGE_EXTERNAL_STORAGE = 'android.permission.MANAGE_EXTERNAL_STORAGE'

    # Maps for modern Android versions (API 30+)
    PERMISSIONS_MAP = {
        'camera': Permission.CAMERA,
        'storage_read': Permission.READ_EXTERNAL_STORAGE,
        'storage_write': Permission.WRITE_EXTERNAL_STORAGE,
    }

    @staticmethod
    def request_camera_permission():
        """
        Request camera permission from user.
        Returns True if granted or already available.
        """
        try:
            if check_permission(Permission.CAMERA):
                Logger.info('PermissionsHandler: Camera permission already granted')
                return True

            Logger.info('PermissionsHandler: Requesting camera permission...')
            request_permissions([Permission.CAMERA])
            return True
        except Exception as e:
            Logger.error(f'PermissionsHandler: Camera permission error: {e}')
            return False

    @staticmethod
    def request_storage_permissions():
        """
        Request storage permissions for file read/write.
        Returns True if granted or already available.
        """
        try:
            permissions = [
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]

            all_granted = all(
                check_permission(perm) for perm in permissions
            )

            if all_granted:
                Logger.info('PermissionsHandler: Storage permissions already granted')
                return True

            Logger.info('PermissionsHandler: Requesting storage permissions...')
            request_permissions(permissions)
            return True
        except Exception as e:
            Logger.error(f'PermissionsHandler: Storage permission error: {e}')
            return False

    @staticmethod
    def request_all_permissions():
        """
        Request all required permissions at once.
        """
        try:
            Logger.info('PermissionsHandler: Requesting all permissions...')
            permissions = [
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]
            request_permissions(permissions)
            return True
        except Exception as e:
            Logger.error(f'PermissionsHandler: All permissions request error: {e}')
            return False

    @staticmethod
    def check_permission_status(permission_name):
        """
        Check if specific permission is granted.
        
        Args:
            permission_name (str): 'camera', 'storage_read', or 'storage_write'
            
        Returns:
            bool: True if granted, False otherwise
        """
        try:
            perm_map = {
                'camera': Permission.CAMERA,
                'storage_read': Permission.READ_EXTERNAL_STORAGE,
                'storage_write': Permission.WRITE_EXTERNAL_STORAGE,
            }
            perm = perm_map.get(permission_name)
            if perm:
                status = check_permission(perm)
                Logger.info(f'PermissionsHandler: {permission_name} = {status}')
                return status
            return False
        except Exception as e:
            Logger.error(f'PermissionsHandler: Check permission error: {e}')
            return False
