#!/bin/bash

echo "🚀 QUICK START - RAG Chatbot"
echo "================================"

# Kill any existing processes
echo "🛑 Stopping existing processes..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null

# Start simplified backend with real Gemini
echo "🔧 Starting Backend with Real Gemini API..."
cd backend
source venv/bin/activate
python simple_main.py &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 3

# Start frontend
echo "🎨 Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo ""
echo "📝 Test Credentials:"
echo "   Email: test@example.com"
echo "   Password: testpass123"
echo ""
echo "Press Ctrl+C to stop"

# Cleanup function
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM
wait
