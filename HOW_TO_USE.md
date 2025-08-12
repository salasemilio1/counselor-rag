# Counselor RAG System - User Guide

## Quick Start

1. **Double-click** the `Counselor RAG.app` to start the system
2. **Wait** for the terminal window to show "All servers started successfully!"
3. **Use** the system in your web browser (should open automatically)

## What Happens When You Start the App

1. A terminal window will open showing startup progress
2. The system will install any needed dependencies
3. Both backend and frontend servers will start
4. Your web browser will automatically open to the application
5. You can now use the Counselor RAG system normally

## System Requirements

- **macOS** 10.12 or later
- **Python 3** (will be installed if not present)
- **Node.js** and **npm** (will need to be installed separately if not present)
- **Internet connection** (for initial setup and AI queries)

## Troubleshooting

### If the app won't start:
1. Make sure you have **Python 3** installed
2. Make sure you have **Node.js** and **npm** installed
3. Try running the terminal command directly: `./start_app.sh`

### If you see "Permission denied":
1. Right-click the app and select "Open"
2. Click "Open" when macOS asks for confirmation
3. This only needs to be done once

### If servers won't start:
1. Check that ports 8000 and 5173 aren't being used by other applications
2. Try restarting your computer
3. Check the `backend.log` and `frontend.log` files for error details

### If the browser doesn't open automatically:
- Manually navigate to: `http://localhost:5173`

## Stopping the System

- **Click the red X** on the terminal window, or
- **Press Ctrl+C** in the terminal window
- This will properly shut down both servers

## Files and Folders

- `Counselor RAG.app` - The main application (double-click this!)
- `start_app.sh` - The startup script (can be run directly in terminal)
- `backend/` - Server code and data
- `frontend/` - Web interface code
- `data/` - Your client data and chat history
- `venv/` - Python virtual environment (created automatically)

## Need Help?

If you encounter any issues:

1. Check the log files: `backend.log` and `frontend.log`
2. Make sure all system requirements are met
3. Try restarting the application
4. Contact support with any error messages you see

---

**Note**: The first time you run the app, it may take a few minutes to install dependencies. Subsequent launches will be much faster.