[app]

title = CvSU Offline Student Tracker
package.name = cvsutracker
package.domain = org.cvsu

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

version = 1.0

requirements = python3,kivy,qrcode,pillow

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
