# CvSU Offline Student Tracker - Complete Setup & Troubleshooting Guide

## 🚀 Quick Start

### Desktop (Windows/Mac/Linux)

```bash
# 1. Clone repository
git clone https://github.com/kage049754/cvsu-offline-tracker.git
cd cvsu-offline-tracker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run app
python main.py
```

### Android APK Build

```bash
# 1. Install buildozer and dependencies
pip install buildozer cython

# 2. Build APK (uses buildozer.spec)
cd cvsu-offline-tracker
buildozer -v android debug

# 3. Deploy to device
adb install -r bin/cvsutracker-2.0.0-debug.apk
```

---

## 📋 What's Fixed in This Version

### ✅ Android Permissions (CRITICAL FIX)
**Problem**: App had no Android permissions defined, so camera and storage access were blocked.

**Solution**: Updated `buildozer.spec` with:
```ini
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,INTERNET
android.features = android.hardware.camera,android.hardware.camera.autofocus
android.request_legacy_external_storage = True
```

### ✅ Dependencies (CRITICAL FIX)
**Problem**: Original spec was missing critical packages for QR scanning and camera access.

**Solution**: Added to requirements:
- `opencv-python==4.8.0.76` - Camera access
- `pyzbar==0.1.9` - QR code decoding
- `jnius` - Java interop for Android

### ✅ Main Entry Point
**Problem**: Two separate versions (main.py and main_production.py) caused confusion.

**Solution**: Merged into single `main.py` that works on both desktop and Android.

### ✅ Storage Management
**Problem**: Reports and files weren't being saved to accessible locations on Android.

**Solution**: `storage_manager.py` now:
- Saves database in app-private folder
- Saves reports to Downloads folder (user-visible)
- Works on both Android and desktop

### ✅ QR Scanner Module
**Problem**: QR scanning wasn't fully integrated with proper error handling.

**Solution**: `qr_scanner.py` now:
- Uses OpenCV for camera access
- Uses pyzbar for QR decoding
- Runs in background thread
- Has 30-second timeout
- Falls back to manual entry

### ✅ Permission Handler
**Problem**: No runtime permission requests on Android.

**Solution**: `permissions_handler.py` now:
- Requests CAMERA permission
- Requests READ/WRITE storage permissions
- Checks permission status
- Gracefully handles permission denial

---

## 🔧 Common Issues & Solutions

### Issue 1: "Permission Denied" on Android

**Cause**: App permissions not granted by user.

**Solution**:
1. Open Android Settings
2. Go to Apps > CvSU Tracker
3. Tap Permissions
4. Enable:
   - Camera
   - Files and Media
   - Location (optional)
5. Restart app

**Code Level**:
- Permissions are auto-requested in `main.py` lines 518-524
- Checked in `permissions_handler.py`
- Graceful fallback to manual entry if camera unavailable

---

### Issue 2: "Camera Not Working / QR Scan Fails"

**Cause**: Camera permission denied OR device doesn't have working camera.

**Solution**:
1. Check camera permission (see Issue 1)
2. Test camera with another app
3. Use manual entry as fallback

**Code Level**:
- Camera check: `qr_scanner.py` lines 35-44
- Fallback UI: `main.py` has both "Log Student" and "Scan QR" buttons
- Manual entry textbox: `main.py` line 350-354

---

### Issue 3: "Reports Not Saving / Files Not Visible"

**Cause**: Storage permission denied OR incorrect storage path.

**Solution**:
1. Check storage permission (see Issue 1)
2. Check Downloads folder:
   - Android: Settings > Apps > File Manager > go to Downloads
   - Desktop: ~/Downloads
3. Look for "CvSU_Reports" folder

**Code Level**:
- Storage path: `storage_manager.py` lines 33-55
- Reports folder: `storage_manager.py` lines 104-112
- Export logic: `main.py` lines 180-238

---

### Issue 4: "Database Corrupted / App Crashes on Startup"

**Cause**: Database file is corrupted OR outdated schema.

**Solution**:
```bash
# Option 1: Android device
adb shell pm clear org.cvsu.cvsutracker
# This clears all app data including corrupted database

# Option 2: Desktop
rm ~/.cvsutracker/cvsu_system.db
# Delete database file, app will recreate on startup
```

**Code Level**:
- Database init: `main.py` lines 40-68
- Schema creation: Tables are created with IF NOT EXISTS, safe for reinstalls
- Try-except error handling throughout

---

### Issue 5: "OpenCV or pyzbar Import Error"

**Cause**: Dependencies not installed properly.

**Solution**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# For OpenCV, may need system libraries on Linux:
sudo apt-get install python3-opencv  # Ubuntu/Debian

# For Android, buildozer handles this automatically
# But if build fails, clean and retry:
buildozer android clean
buildozer -v android debug
```

**Code Level**:
- Try-except for missing libraries: `qr_scanner.py` lines 14-19
- Graceful degradation if pyzbar unavailable
- Logs all dependency issues

---

### Issue 6: "Build Fails on GitHub Actions / Slow Build"

**Cause**: FreeType recipe download fails OR missing Java/Android SDK.

**Solution**:
```bash
# Ensure you have:
# - Java 17+ installed
java -version

# - Android SDK (buildozer installs automatically)
# - NDK 25b (specified in buildozer.spec)

# Clean build directory
buildozer android clean

# Use local recipes (already configured in buildozer.spec)
# These are in the recipes/ folder and don't need downloading
```

**Code Level**:
- Local recipes: `buildozer.spec` line 36: `p4a.local_recipes = recipes`
- NDK version: `buildozer.spec` line 18: `android.ndk = 25b`
- Java detection: Built into buildozer

---

## 🎯 File Structure Explained

```
cvsu-offline-tracker/
├── main.py                    ← MAIN ENTRY POINT (use this!)
├── storage_manager.py         ← Handles file storage (Android + Desktop)
├── qr_scanner.py             ← QR scanning module with OpenCV
├── permissions_handler.py     ← Android runtime permissions
├── buildozer.spec            ← BUILD CONFIG (updated with all fixes)
├── requirements.txt          ← Python dependencies (updated)
├── recipes/                  ← Local build recipes (avoids download issues)
│   └── freetype/
├── student_qrs/              ← Generated QR codes stored here
├── cvsu_system.db           ← SQLite database (created at runtime)
├── SETUP_GUIDE.md           ← This file
└── README.md                ← Project overview
```

---

## 📊 Dependency Versions & Why They Matter

| Package | Version | Purpose | Critical? |
|---------|---------|---------|----------|
| kivy | 2.2.1 | UI Framework | ✅ Yes |
| qrcode | 7.4.2 | Generate QR codes | ✅ Yes |
| pillow | 10.0.0 | Image processing for QR | ✅ Yes |
| opencv-python | 4.8.0.76 | Camera access & frame processing | ✅ Yes (for QR scan) |
| pyzbar | 0.1.9 | QR code decoding | ✅ Yes (for QR scan) |
| cython | 0.29.33 | Performance optimization | ✅ Yes (for Android) |
| python-for-android | >=2023.12.0 | Android build framework | ✅ Yes (Android only) |
| jnius | Latest | Java interop (Android) | ✅ Yes (Android only) |

**Why pinned versions?**
- Ensures consistent behavior across all devices
- Avoids breaking API changes in newer versions
- Tested combinations that work together

---

## 🔍 Testing Checklist

### Desktop Testing
- [ ] Run `python main.py` - App launches
- [ ] Register student - Student added to database
- [ ] Generate QR - QR code appears in `student_qrs/` folder
- [ ] Log student (manual) - Entry appears in database
- [ ] Scan QR (with webcam) - QR scanning works
- [ ] Export report (CSV) - File appears in `~/Downloads/CvSU_Reports/`
- [ ] Export report (TXT) - File appears in `~/Downloads/CvSU_Reports/`

### Android Testing (On Device)
- [ ] APK installs without errors
- [ ] App launches
- [ ] Permission dialog appears (first time)
- [ ] Register student works
- [ ] Camera permission works (if granted)
- [ ] QR scanning works (if camera available)
- [ ] Reports save to Downloads (if storage permission granted)
- [ ] Database persists after app restart

---

## 📱 Android Specific Notes

### Storage Paths on Android
```
Database: /data/data/org.cvsu.cvsutracker/files/cvsu_system.db
QR Codes: /data/data/org.cvsu.cvsutracker/files/student_qrs/
Reports:  /storage/emulated/0/Download/CvSU_Reports/  (User-visible!)
```

### Required Permissions Explanation

| Permission | Why Needed | When |
|-----------|-----------|------|
| CAMERA | QR scanning | When user clicks "Scan QR" |
| READ_EXTERNAL_STORAGE | Access files | Report viewing |
| WRITE_EXTERNAL_STORAGE | Save reports | Export functionality |
| MANAGE_EXTERNAL_STORAGE | Android 11+ full access | All file operations |
| INTERNET | Future cloud features | Not used yet, but included |

### Android 11+ (API 30+) Changes
```ini
# This allows app to work with Android 11+ scoped storage
android.request_legacy_external_storage = True
```

Without this, Downloads folder access fails on Android 11+.

---

## 🐛 Debug Tips

### View Android Logs
```bash
adb logcat | grep cvsutracker
# Shows all app logs in real-time
```

### View App Data on Device
```bash
# List app files
adb shell ls /data/data/org.cvsu.cvsutracker/files/

# Pull database for inspection
adb pull /data/data/org.cvsu.cvsutracker/files/cvsu_system.db .

# Then inspect with sqlite3
sqlite3 cvsu_system.db
```

### Desktop Debug Mode
```python
# Add to main.py after line 5
from kivy.logger import Logger
Logger.setLevel(logging.DEBUG)

# Shows detailed Kivy logs
```

---

## 📝 Version History

**v2.0.0** (Current - Fixed Production Version)
- ✅ Added all Android permissions
- ✅ Fixed QR scanning module
- ✅ Fixed storage management
- ✅ Unified main.py entry point
- ✅ Added comprehensive error handling
- ✅ Complete documentation

**v1.0** (Original - Issues)
- ❌ No Android permissions
- ❌ No QR scanning
- ❌ Inconsistent storage paths
- ❌ No error handling

---

## 📞 Support & Next Steps

### If App Still Doesn't Work:
1. Check logcat: `adb logcat | grep cvsutracker`
2. Verify permissions in Settings app
3. Try clearing app data: `adb shell pm clear org.cvsu.cvsutracker`
4. Rebuild from scratch: `buildozer android clean && buildozer android debug`

### For Production Deployment:
1. Use `buildozer android release` (requires keystore)
2. Test on multiple Android versions (API 21+)
3. Test on multiple devices (phones, tablets)
4. Monitor logcat for crash reports
5. Consider adding automatic crash reporting

### Future Enhancements:
- [ ] Cloud sync capability
- [ ] Biometric authentication
- [ ] Barcode scanning (in addition to QR)
- [ ] Dark mode UI
- [ ] Attendance analytics dashboard
- [ ] Push notifications

---

**Last Updated**: 2026-09-10
**Status**: ✅ Production Ready
