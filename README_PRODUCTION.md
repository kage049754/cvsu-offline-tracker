# CvSU Offline Student Tracker - Production Version

## 🚀 Production-Ready Features

This is the enhanced Android production version with:

### ✅ Core Features
- **QR Code Scanning** - Separate `qr_scanner.py` module
- **QR Code Generation** - Automatic QR creation for each student
- **Manual Entry** - Fallback text input for check-in
- **Offline Database** - SQLite with no internet required
- **Attendance Reports** - CSV and TXT export formats
- **Multi-facility Support** - Attendance, Library, Clinic, Event Entry

### ✅ Android-Specific
- **Runtime Permissions** - Camera, storage access with `permissions_handler.py`
- **Proper Storage Access** - Downloads folder for user-accessible reports
- **Smart File Management** - `storage_manager.py` for cross-platform compatibility
- **Enhanced UI** - Responsive layout with dp() scaling
- **Background Threading** - QR scanning in separate thread
- **Error Handling** - Graceful fallbacks and user-friendly messages

### ✅ Security & Reliability
- **Duplicate Prevention** - Prevents duplicate logins within 5 seconds
- **Database Validation** - Student verification before logging
- **Permission Checks** - Runtime permission verification
- **Logging** - Full Kivy logger integration for debugging

---

## 📋 File Structure

```
cvsu-offline-tracker/
├── main_production.py          ← PRODUCTION ENTRY POINT (replaces main.py)
├── qr_scanner.py              ← QR code scanning module
├── permissions_handler.py      ← Android permission management
├── storage_manager.py         ← File storage for all platforms
├── buildozer_production.spec  ← Android build config (PRODUCTION)
├── requirements.txt           ← Python dependencies
├── README_PRODUCTION.md       ← This file
├── buildozer.spec            ← Original (keep for reference)
├── main.py                   ← Original (keep for reference)
├── app.py                    ← Original (keep for reference)
└── recipes/
    └── freetype/__init__.py   ← Custom FreeType build recipe
```

---

## 🔧 Setup & Build

### Desktop Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
python main_production.py
```

### Android Build

```bash
# Install Buildozer and dependencies
pip install buildozer cython

# Navigate to project directory
cd cvsu-offline-tracker

# Build APK (uses buildozer_production.spec)
buildozer -v android debug -s buildozer_production.spec

# Output: bin/cvsutracker-2.0.0-debug.apk
```

### Deploy to Device

```bash
# Connect Android device via USB (developer mode enabled)
adb install -r bin/cvsutracker-2.0.0-debug.apk

# Or use Buildozer directly
buildozer android debug deploy run
```

---

## 📱 Android Permissions

The app requires these permissions (automatically requested):

| Permission | Purpose |
|-----------|----------|
| **CAMERA** | QR code scanning |
| **READ_EXTERNAL_STORAGE** | File access |
| **WRITE_EXTERNAL_STORAGE** | Report export to Downloads |
| **MANAGE_EXTERNAL_STORAGE** | Android 11+ full file access |

---

## 💾 Storage Locations

### Android
- **Database**: `/data/data/org.cvsu.cvsutracker/files/cvsu_system.db`
- **QR Codes**: `/data/data/org.cvsu.cvsutracker/files/student_qrs/`
- **Reports**: `/storage/emulated/0/Download/CvSU_Reports/` (user-accessible)

### Desktop
- **Database**: `~/.cvsutracker/cvsu_system.db`
- **QR Codes**: `~/.cvsutracker/student_qrs/`
- **Reports**: `~/Downloads/CvSU_Reports/`

---

## 🎯 Key Improvements Over Original

| Feature | Original | Production |
|---------|----------|------------|
| **QR Scanning** | Manual entry only | Full camera scanning |
| **Android Perms** | None defined | All required perms |
| **Storage Access** | App folder only | Downloads (user-visible) |
| **Error Handling** | Basic | Comprehensive with fallbacks |
| **File Management** | Hardcoded paths | Platform-aware |
| **Threading** | Blocking | Background threads |
| **UI Feedback** | Status text | Enhanced indicators |
| **Duplicate Prevention** | None | 5-second window |
| **Logging** | Limited | Full Kivy logger |

---

## 🔍 Usage Guide

### 1. Register Students
- Enter: Student Number, Full Name, Course & Year
- Click: "Register Student + Generate QR"
- Result: Student added to database, QR code generated

### 2. Log Attendance (Manual)
- Select: Facility mode (Attendance/Library/Clinic/Event Entry)
- Enter: Session title (optional)
- Enter/Scan: Student number
- Click: "Log Student" or "Scan QR"

### 3. Export Reports
- Select: Facility mode
- Select: Sort order (Recent/Alphabetical)
- Select: Format (CSV/TXT)
- Click: "Export Report to Downloads"
- Files saved to: `/storage/emulated/0/Download/CvSU_Reports/`

---

## 🐛 Troubleshooting

### Camera Not Working
- Check: App has CAMERA permission (Settings > App Permissions)
- Try: Manual entry as fallback
- Check: Device has working front/back camera

### Files Not Saving
- Check: WRITE_EXTERNAL_STORAGE permission granted
- Check: Download folder exists
- Try: Manual folder creation in Files app

### Build Fails
- Run: `buildozer android clean`
- Update: `pip install --upgrade buildozer cython`
- Check: Java 17+ installed (`java -version`)

### App Crashes on Startup
- Check: Logcat output: `adb logcat | grep cvsutracker`
- Verify: Database file not corrupted
- Try: Delete app data: `adb shell pm clear org.cvsu.cvsutracker`

---

## 📊 Dependencies

- **kivy** (2.2.1) - UI framework
- **qrcode** (7.4.2) - QR generation
- **pillow** (10.0.0) - Image processing
- **opencv-python** (4.8.0.76) - Camera/image processing
- **pyzbar** (0.1.9) - QR decoding
- **cython** (0.29.33) - Performance optimization

---

## 📝 License

Cavite State University - Student Tracker System

---

## 🤝 Support

For issues, check:
1. Logcat: `adb logcat | grep cvsutracker`
2. File permissions in Android Settings
3. Database integrity: Check if `.db` file exists
4. Buildozer cache: Run `buildozer android clean`

---

**Version**: 2.0.0  
**Last Updated**: 2026-09-10  
**Status**: ✅ Production Ready
