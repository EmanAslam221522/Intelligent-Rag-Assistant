# Multi-stage build for RAG Chatbot
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-build /app/frontend/out ./frontend/out

# Create directories for ChromaDB
RUN mkdir -p ./chroma_db

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Start the application
CMD ["python", "main.py"]

