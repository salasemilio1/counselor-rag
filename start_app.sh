#!/bin/bash

# Counselor RAG System Startup Script
# This script starts both the backend and frontend servers

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for a port to be available
wait_for_port() {
    local port=$1
    local timeout=30
    local count=0
    
    while ! nc -z localhost $port >/dev/null 2>&1; do
        if [ $count -eq $timeout ]; then
            return 1
        fi
        sleep 1
        count=$((count + 1))
    done
    return 0
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID >/dev/null 2>&1
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID >/dev/null 2>&1
    fi
    # Kill any remaining processes on our ports
    lsof -ti:8000 | xargs kill -9 >/dev/null 2>&1
    lsof -ti:5173 | xargs kill -9 >/dev/null 2>&1
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "Starting Counselor RAG System..."
print_status "Working directory: $SCRIPT_DIR"

# Check dependencies
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js and try again."
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed. Please install npm and try again."
    exit 1
fi

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv --upgrade-deps
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install Python dependencies"
    exit 1
fi

# Install Node.js dependencies for frontend
print_status "Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
    if [ $? -ne 0 ]; then
        print_error "Failed to install frontend dependencies"
        exit 1
    fi
fi
cd ..

# Kill any existing processes on our ports
print_status "Checking for existing processes..."
lsof -ti:8000 | xargs kill -9 >/dev/null 2>&1
lsof -ti:5173 | xargs kill -9 >/dev/null 2>&1

# Start ollama server
ollama serve

# Start backend server
print_status "Starting backend server on port 8000..."
cd backend
python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
print_status "Waiting for backend server to start..."
if wait_for_port 8000; then
    print_success "Backend server started successfully"
else
    print_error "Backend server failed to start"
    cleanup
    exit 1
fi

# Start frontend server
print_status "Starting frontend server on port 5173..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
print_status "Waiting for frontend server to start..."
if wait_for_port 5173; then
    print_success "Frontend server started successfully"
else
    print_error "Frontend server failed to start"
    cleanup
    exit 1
fi

# Open browser
print_success "All servers started successfully!"
print_status "Opening browser..."
sleep 2
open "http://localhost:5173"

print_success "Counselor RAG System is now running!"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo ""
print_status "Press Ctrl+C to stop the servers"

# Keep the script running
while true; do
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID >/dev/null 2>&1; then
        print_error "Backend server has stopped unexpectedly"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $FRONTEND_PID >/dev/null 2>&1; then
        print_error "Frontend server has stopped unexpectedly"
        cleanup
        exit 1
    fi
    
    sleep 5
done
