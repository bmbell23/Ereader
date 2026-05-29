# Ereader App - Setup Instructions

This is a custom ereader app for Android that connects to your Linux server to browse and download books.

## Prerequisites

On your Linux server:
- Python 3.7+
- Node.js 18+
- npm or yarn

On your development machine or the server (for building):
- Android Studio or Android SDK
- Java Development Kit (JDK) 17

## Quick Start

### 1. Start the Backend Server

First, tell the backend where your books are stored:

```bash
cd backend

# Set your books directory
export BOOKS_DIR="/path/to/your/books"

# Run the server
./run.sh
```

The server will start on port 5000. Find your server's IP address with:
```bash
ip addr show | grep inet
```

### 2. Build the Android App

```bash
cd app

# Install dependencies
npm install

# For the first time, you may need to install the debug keystore
keytool -genkey -v -keystore android/app/debug.keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"

# Build the APK
cd android
./gradlew assembleRelease
```

The APK will be at: `app/android/app/build/outputs/apk/release/app-release.apk`

### 3. Install on Your Phone

Transfer the APK to your phone and install it. You can use:

```bash
# Via ADB (if phone is connected via USB):
adb install app/android/app/build/outputs/apk/release/app-release.apk

# Or via HTTP server (both on same VPN):
cd app/android/app/build/outputs/apk/release
python3 -m http.server 8080
# Then visit http://YOUR_SERVER_IP:8080 on your phone browser
```

### 4. Configure the App

1. Open the app on your phone
2. Go to Settings
3. Enter your server URL: `http://YOUR_SERVER_IP:5000`
4. Tap "Save Settings" and "Test Connection"
5. If connected successfully, go back to Home
6. Tap "Browse Server Library"
7. Download books by tapping the download button
8. Read books from the home screen

## Development Mode

For faster development, you can run in development mode:

```bash
cd app

# Start Metro bundler
npm start

# In another terminal, with phone connected via USB:
npm run android
```

This allows hot-reloading of changes without rebuilding the APK.

## Troubleshooting

### Server not connecting
- Make sure both devices are on the same VPN
- Check firewall settings on your server (port 5000 should be open)
- Verify the server is running with: `curl http://localhost:5000/api/health`

### Build errors
- Make sure you have JDK 17 installed
- Check that Android SDK is properly configured
- Try: `cd app/android && ./gradlew clean`

### App crashes on startup
- Check logcat: `adb logcat -s ReactNativeJS`
- Ensure all permissions are granted in Android settings

## Supported Formats

Currently supported:
- PDF ✅
- EPUB (coming soon)
- MOBI (coming soon)

## Future Enhancements

- Web interface for desktop reading
- EPUB support
- Reading progress sync
- Bookmarks and highlights
- Night mode / themes
- Font customization
