#!/bin/bash

# Simple launcher for Counselor RAG App
# This script is designed to be called by Automator

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Open Terminal and run the startup script
osascript -e "
tell application \"Terminal\"
    activate
    do script \"cd '$SCRIPT_DIR' && ./start_app.sh\"
end tell
"