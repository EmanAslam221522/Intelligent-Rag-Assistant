#!/bin/bash

# Start Dynamic RAG Chatbot Application

echo "🚀 Starting Dynamic RAG Chatbot Application..."

# Check if backend .env exists
if [ ! -f backend/.env ]; then
    echo "❌ Backend .env file not found. Please run ./setup.sh first."
    exit 1
fi

# Check if frontend .env.local exists
if [ ! -f frontend/.env.local ]; then
    echo "❌ Frontend .env.local file not found. Please run ./setup.sh first."
    exit 1
fi

echo "🔧 Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!

echo "⏳ Waiting for backend to start..."
sleep 5

echo "🎨 Starting frontend development server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Application started successfully!"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Process IDs:"
echo "   Backend: $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "🛑 To stop the application, press Ctrl+C or run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"

# Wait for user interrupt
trap "echo ''; echo '🛑 Stopping application...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT

# Keep script running
wait


