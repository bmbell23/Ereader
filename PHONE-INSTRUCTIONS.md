# Phone Setup Instructions

## ✅ Server is Ready!

Your backend server is running at:
- **Server URL**: `http://100.69.184.113:5000`
- **Status**: ✅ Connected to Calibre
- **Books Available**: 949 books

---

## Option 1: Direct APK Build (Recommended - Do This on Your Computer)

Since the server environment doesn't have all Android build tools, **build the APK on your computer** where you have Android Studio:

### On Your Computer (with Android Studio):

1. **Clone/Download the code**:
   ```bash
   scp -r brandon@100.69.184.113:/home/brandon/projects/Ereader ~/ereader-project
   cd ~/ereader-project/app
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Build with Android Studio**:
   - Open `~/ereader-project/app/android` in Android Studio
   - Let it sync and download dependencies
   - Build → Generate Signed Bundle / APK → APK → Release
   - Use the debug keystore at `app/android/app/debug.keystore` (password: `android`)

4. **Or build via command line** (if you have Android SDK):
   ```bash
   cd android
   ./gradlew assembleRelease
   ```

5. **Install on phone**:
   ```bash
   adb install app/build/outputs/apk/release/app-release.apk
   ```

---

## Option 2: Use Expo / React Native CLI (Easier)

If you have React Native CLI set up:

```bash
cd ~/ereader-project/app
npx react-native run-android --variant=release
```

This will build and install directly to your connected phone.

---

## Option 3: Download Pre-built APK (If Available)

I can create a simpler standalone APK. Would you like me to:
1. Create a web-only version you can access via browser?
2. Create a simpler native build?

---

## Once You Have the APK on Your Phone:

### 1. Install the APK
- Enable "Install from Unknown Sources" in Android settings
- Tap the APK file to install
- Grant any requested permissions

### 2. Configure the App
1. Open "My Ereader" app
2. Tap **"Settings"**
3. Enter Server URL: **`http://100.69.184.113:5000`**
4. Tap **"Save Settings"**
5. Tap **"Test Connection"** - should show "Successfully connected"

### 3. Start Reading!
1. Tap **"← Back"** to home screen
2. Tap **"Browse Server Library"**
3. You'll see all 949 books with covers!
4. Tap **⬇️** to download any book
5. Read from home screen

---

## Testing the Backend From Your Phone's Browser

You can test if the backend is accessible from your phone right now:

1. Open browser on your phone
2. Go to: `http://100.69.184.113:5000/api/health`
3. You should see:
   ```json
   {
     "status": "ok",
     "calibre_connected": true,
     "calibre_library": "library",
     "calibre_url": "http://localhost:8083"
   }
   ```

4. Try viewing books: `http://100.69.184.113:5000/api/books?limit=5`

If these work, your phone can reach the server!

---

## Temporary Web Interface Option

While you're building the APK, you can browse books via Calibre's built-in web interface:

**Direct Calibre Access**: `http://100.69.184.113:8083`

This is Calibre's own web reader - not as nice as the custom app, but works immediately!

---

## Need Help?

The backend is running and ready. The challenge is just building the Android APK.

**Easiest path**: Use a computer with Android Studio to build the APK, then install on phone.

Let me know which option works best for you!
