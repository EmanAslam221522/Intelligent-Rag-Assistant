#!/bin/bash

echo "🚀 Starting RAG Chatbot Deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start MongoDB
echo "📦 Starting MongoDB..."
docker start mongodb > /dev/null 2>&1 || docker run -d --name mongodb -p 27017:27017 mongo:latest

# Wait for MongoDB to be ready
echo "⏳ Waiting for MongoDB to be ready..."
sleep 5

# Start Backend
echo "🔧 Starting Backend..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start Frontend
echo "🎨 Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Deployment complete!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "📊 MongoDB: localhost:27017"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait


