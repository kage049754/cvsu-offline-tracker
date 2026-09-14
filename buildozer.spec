[app]

title = CvSU Offline Attendance
package.name = cvsutracker
package.domain = org.cvsu

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

version = 3.0.0

# Keep dependencies limited to packages actually used by the phone app.
requirements = python3,kivy,qrcode,pillow,opencv,jnius

orientation = portrait
fullscreen = 0

# Android
android.api = 35
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

# Camera plus public Downloads access for the sideloaded school APK.
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.features = android.hardware.camera,android.hardware.camera.autofocus
android.request_legacy_external_storage = True

# Local FreeType recipe retained from the working build setup.
p4a.local_recipes = recipes

[buildozer]
log_level = 2
warn_on_root = 1
