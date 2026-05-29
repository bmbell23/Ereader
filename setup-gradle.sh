#!/bin/bash

set -e

echo "🔧 Setting up Gradle wrapper..."

cd app/android

# Create gradle wrapper directory if it doesn't exist
mkdir -p gradle/wrapper

# Download gradle wrapper jar if not present
if [ ! -f "gradle/wrapper/gradle-wrapper.jar" ]; then
    echo "📥 Downloading Gradle wrapper..."
    curl -L https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradle-wrapper.jar \
        -o gradle/wrapper/gradle-wrapper.jar
    echo "✅ Gradle wrapper downloaded"
else
    echo "✅ Gradle wrapper already exists"
fi

# Make gradlew executable
chmod +x gradlew

echo "✅ Gradle setup complete!"
