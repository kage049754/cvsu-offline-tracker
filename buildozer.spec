[app]

title = CvSU Offline Attendance
package.name = cvsutracker
package.domain = org.cvsu

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

version = 3.0.1

# Keep the Android dependency set minimal and use python-for-android recipes.
requirements = python3,kivy,qrcode,pillow,opencv

orientation = portrait
fullscreen = 0

# Stable Android build target for Kivy/python-for-android.
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.features = android.hardware.camera,android.hardware.camera.autofocus
android.request_legacy_external_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
