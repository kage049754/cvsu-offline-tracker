[app]

title = CvSU Offline Student Tracker
package.name = cvsutracker
package.domain = org.cvsu

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

version = 2.0.0

# All required dependencies for production
requirements = python3,kivy,qrcode,pillow,opencv,pyzbar,jnius

orientation = portrait
fullscreen = 0

# Android Configuration
android.api = 35
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

# CRITICAL: All required Android permissions
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,INTERNET,ACCESS_FINE_LOCATION

# Hardware features required
android.features = android.hardware.camera,android.hardware.camera.autofocus

# Android metadata
android.meta_data = android.hardware.camera.autofocus

# Storage Configuration for Android 11+ (API 30+)
android.request_legacy_external_storage = True

# Use local FreeType recipe to avoid GitHub Actions failures
p4a.local_recipes = recipes

# Java classes for native access
android.java_classes = android.os.Environment,android.content.Intent

[buildozer]

log_level = 2
warn_on_root = 1
