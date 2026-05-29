# Quick Start Guide

## Step 1: Your Calibre Server is Already Running! ✅

Good news! Your Calibre Content Server is already running at:
- **URL**: `http://localhost:8083`
- **Library**: `library`
- **Total Books**: 949

The backend is pre-configured to connect to it!

## Step 2: Start the Backend Server

```bash
# Navigate to the backend directory
cd backend

# Run the server (defaults already set for your Calibre)
./run.sh
```

The server will be accessible at `http://YOUR_SERVER_IP:5000`

To find your server's IP address:
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

## Step 3: Build the Android App

You have two options:

### Option A: Automated Build (Easy)
```bash
./build-app.sh
```

### Option B: Manual Build
```bash
cd app
npm install
cd android
./gradlew assembleRelease
```

The APK will be at: `app/android/app/build/outputs/apk/release/app-release.apk`

## Step 4: Install on Your Phone

### Method 1: Via ADB (Phone connected via USB)
```bash
adb install app/android/app/build/outputs/apk/release/app-release.apk
```

### Method 2: Via HTTP (Both on same VPN)
```bash
cd app/android/app/build/outputs/apk/release
python3 -m http.server 8080
```
Then open your phone's browser and navigate to:
`http://YOUR_SERVER_IP:8080`

Download and install the APK.

## Step 5: Configure and Use

1. **Open the app** on your phone
2. **Go to Settings** (tap the Settings button)
3. **Enter Server URL**: `http://YOUR_SERVER_IP:5000`
   - Replace `YOUR_SERVER_IP` with the actual IP address from Step 2
4. **Tap "Save Settings"**
5. **Tap "Test Connection"** - you should see "Successfully connected"
6. **Go back** to the home screen
7. **Tap "Browse Server Library"** to see your books
8. **Download books** by tapping the ⬇️ button
9. **Read books** from the home screen

## Current Features

✅ Browse books from your server
✅ Download books to your phone  
✅ Read PDF files
✅ Offline reading
✅ Simple, clean interface

## Coming Soon

🔜 EPUB support
🔜 Reading progress tracking
🔜 Bookmarks
🔜 Web interface for desktop reading

## Troubleshooting

**Can't connect to server?**
- Make sure both devices are on the same VPN
- Check that the backend server is running
- Verify your firewall isn't blocking port 5000

**Build fails?**
- Make sure you have JDK 17 installed
- Install Android SDK or Android Studio
- Try: `cd app/android && ./gradlew clean`

**No books showing up?**
- Verify your BOOKS_DIR path is correct
- Check that books are in supported formats (PDF, EPUB, MOBI)
- Look at server logs for errors

Need help? Check SETUP.md for detailed troubleshooting.
