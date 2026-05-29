#!/bin/bash

set -e

echo "🏗️  Building Ereader Android App"
echo "================================"

cd app

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "✓ Dependencies already installed"
fi

# Create debug keystore if it doesn't exist
if [ ! -f "android/app/debug.keystore" ]; then
    echo "🔑 Creating debug keystore..."
    keytool -genkey -v -keystore android/app/debug.keystore \
        -storepass android -alias androiddebugkey -keypass android \
        -keyalg RSA -keysize 2048 -validity 10000 \
        -dname "CN=Android Debug,O=Android,C=US"
else
    echo "✓ Keystore already exists"
fi

# Setup Gradle wrapper if needed
if [ ! -f "android/gradle/wrapper/gradle-wrapper.jar" ]; then
    echo "🔧 Setting up Gradle wrapper..."
    cd ..
    ./setup-gradle.sh
    cd app
fi

echo "🔨 Building APK..."
cd android
./gradlew assembleRelease

echo ""
echo "✅ Build complete!"
echo ""
echo "APK location:"
echo "  $(pwd)/app/build/outputs/apk/release/app-release.apk"
echo ""
echo "To install on your phone:"
echo "  adb install app/build/outputs/apk/release/app-release.apk"
echo ""
echo "Or serve via HTTP (on same VPN):"
echo "  cd app/build/outputs/apk/release"
echo "  python3 -m http.server 8080"
echo "  # Visit http://YOUR_SERVER_IP:8080 on your phone"
