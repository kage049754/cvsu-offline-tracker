[app]

title = CvSU Offline Student Tracker
package.name = cvsutracker
package.domain = org.cvsu

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

version = 2.0.0

requirements = python3,kivy,qrcode,pillow,opencv,pyzbar,jnius

orientation = portrait
fullscreen = 0

# Android Configuration
android.api = 35
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1

# Permissions Required
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,INTERNET

# Features Required
android.features = android.hardware.camera

# App Permissions
android.meta_data = android.hardware.camera.autofocus

# Storage Configuration for Android 11+
android.request_legacy_external_storage = True

# Use local FreeType recipe
p4a.local_recipes = recipes

# Java classes to use
android.java_classes = android.os.Environment,android.content.Intent

[buildozer]

log_level = 2
warn_on_root = 1
