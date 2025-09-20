#!/bin/bash

# Dynamic RAG Chatbot Setup Script
echo "🚀 Setting up Dynamic RAG Chatbot Application..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

# Check if MongoDB is running (optional)
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB doesn't seem to be running. Make sure MongoDB is installed and running."
    echo "   You can start it with: docker run -d -p 27017:27017 --name mongodb mongo:latest"
fi

echo "📦 Setting up backend dependencies..."
cd backend
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating backend .env file..."
    cp env.example .env
    echo "⚠️  Please edit backend/.env and add your GEMINI_API_KEY and other configuration."
fi

cd ..

echo "📦 Setting up frontend dependencies..."
cd frontend
npm install

# Create .env.local file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating frontend .env.local file..."
    cp env.local.example .env.local
    echo "✅ Frontend environment file created."
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env and add your GEMINI_API_KEY"
echo "2. Start MongoDB (if not already running)"
echo "3. Start the backend: cd backend && python main.py"
echo "4. Start the frontend: cd frontend && npm run dev"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📚 For more information, see README.md"


