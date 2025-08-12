#!/bin/bash

# Create a simple icon for the Counselor RAG app
# This script creates a basic icon using built-in macOS tools

APP_DIR="/Users/emiliosalas/Desktop/rag-system/counselor-rag/Counselor RAG.app"
ICON_DIR="$APP_DIR/Contents/Resources"

echo "Creating app icon..."

# Create a temporary icon using sf symbols (if available) or generic app icon
# Use the built-in generic application icon as base
TEMPLATE_ICON="/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns"

if [ -f "$TEMPLATE_ICON" ]; then
    cp "$TEMPLATE_ICON" "$ICON_DIR/icon.icns"
    echo "✅ Icon created using system template"
else
    echo "⚠️  Using default icon - you can replace $ICON_DIR/icon.icns with a custom one"
fi

echo "📁 Icon location: $ICON_DIR/icon.icns"