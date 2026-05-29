#!/bin/bash

# Generate placeholder app icons
# For production, replace with proper icons using Android Asset Studio

echo "📱 Generating placeholder app icons..."

# We'll use ImageMagick if available, otherwise just create XML drawables
if command -v convert &> /dev/null; then
    echo "Using ImageMagick to generate icons..."
    
    # Generate different sizes
    convert -size 192x192 xc:#2196F3 \
        -gravity center -pointsize 100 -fill white -annotate +0+0 "📚" \
        app/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
    
    convert -size 144x144 xc:#2196F3 \
        -gravity center -pointsize 80 -fill white -annotate +0+0 "📚" \
        app/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png
    
    convert -size 96x96 xc:#2196F3 \
        -gravity center -pointsize 60 -fill white -annotate +0+0 "📚" \
        app/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png
    
    convert -size 72x72 xc:#2196F3 \
        -gravity center -pointsize 40 -fill white -annotate +0+0 "📚" \
        app/android/app/src/main/res/mipmap-hdpi/ic_launcher.png
    
    convert -size 48x48 xc:#2196F3 \
        -gravity center -pointsize 30 -fill white -annotate +0+0 "📚" \
        app/android/app/src/main/res/mipmap-mdpi/ic_launcher.png
    
    echo "✅ Icons generated!"
else
    echo "⚠️  ImageMagick not found. Skipping icon generation."
    echo "The app will use default icons."
    echo ""
    echo "To generate custom icons later:"
    echo "1. Install ImageMagick: apt-get install imagemagick"
    echo "2. Run: ./generate-icons.sh"
    echo "Or use Android Asset Studio: https://romannurik.github.io/AndroidAssetStudio/"
fi
