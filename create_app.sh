#!/bin/bash

# Script to create the Counselor RAG Mac App

APP_NAME="Counselor RAG"
APP_DIR="/Users/emiliosalas/Desktop/rag-system/counselor-rag/Counselor RAG.app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Creating $APP_NAME.app..."

# Create app bundle structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>CounselorRAG</string>
    <key>CFBundleGetInfoString</key>
    <string>Counselor RAG System</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.counselor.rag</string>
    <key>CFBundleName</key>
    <string>Counselor RAG</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create the main executable script
cat > "$APP_DIR/Contents/MacOS/CounselorRAG" << EOF
#!/bin/bash

# Get the app bundle directory
APP_BUNDLE="\$(dirname "\$(dirname "\$(dirname "\$(readlink -f "\$0" || echo "\$0")")")"
PROJECT_DIR="$SCRIPT_DIR"

# Change to project directory
cd "\$PROJECT_DIR"

# Check if Terminal is already running our script
if pgrep -f "start_app.sh" > /dev/null; then
    echo "Counselor RAG is already running!"
    open "http://localhost:5173"
    exit 0
fi

# Show a simple dialog
osascript -e 'display dialog "Starting Counselor RAG System..." with title "Counselor RAG" buttons {"OK"} default button 1 with icon note giving up after 3'

# Launch in Terminal
osascript -e "
tell application \"Terminal\"
    activate
    do script \"cd '\$PROJECT_DIR' && ./start_app.sh\"
end tell
"

# Wait a moment then try to open browser
sleep 3
open "http://localhost:5173" 2>/dev/null || true
EOF

# Make the executable script runnable
chmod +x "$APP_DIR/Contents/MacOS/CounselorRAG"

echo "✅ Created $APP_NAME.app successfully!"
echo "📍 Location: $APP_DIR"
echo ""
echo "🎯 Next steps:"
echo "1. You can now double-click the app to launch it"
echo "2. Add a custom icon if desired"
echo "3. Test the app functionality"