#!/bin/bash

echo "🚀 STARTING RAG CHATBOT AUTOMATICALLY..."
echo "========================================"
echo ""

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use"
        return 0
    else
        echo "Port $1 is available"
        return 1
    fi
}

# Function to kill processes on specific ports
kill_port() {
    echo "Stopping processes on port $1..."
    lsof -ti:$1 | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Kill existing processes
echo "🔄 Stopping existing processes..."
kill_port 8000
kill_port 3000
sleep 3

# Start backend
echo "🚀 Starting Backend..."
cd /home/eman-aslam/Documents/Bot/backend
source venv/bin/activate
python3 fallback_main.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if check_port 8000; then
    echo "✅ Backend is running on port 8000"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend
echo "🚀 Starting Frontend..."
cd /home/eman-aslam/Documents/Bot/frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 10

# Check if frontend is running
if check_port 3000; then
    echo "✅ Frontend is running on port 3000"
else
    echo "❌ Frontend failed to start"
    exit 1
fi

# Test the system
echo "🧪 Testing the system..."
sleep 3

# Test backend
echo "Testing backend health..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
fi

# Test frontend
echo "Testing frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
fi

echo ""
echo "🎉 RAG CHATBOT IS READY!"
echo "========================"
echo ""
echo "✅ Backend: http://localhost:8000"
echo "✅ Frontend: http://localhost:3000"
echo ""
echo "📝 What you can do:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Try general chat (no login required)"
echo "   3. Click 'Login / Register' to create account"
echo "   4. Upload documents (PDF, DOCX, CSV, TXT)"
echo "   5. Ask questions about your documents"
echo ""
echo "🌐 Opening browser..."
xdg-open http://localhost:3000 2>/dev/null || echo "Please manually open http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"

# Keep the script running and handle Ctrl+C
trap 'echo ""; echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ Services stopped"; exit 0' INT

# Wait for user to stop
wait

