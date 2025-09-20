from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
import logging
import time
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets
from dotenv import load_dotenv
import PyPDF2
import docx
import csv
import io

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for demo
users_db = {}
tokens_db = {}
uploaded_content = {}

# Text extraction functions
def extract_text_from_pdf(content):
    """Extract text from PDF content"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logging.error(f"Error extracting PDF text: {e}")
        return f"Error extracting PDF content: {str(e)}"

def extract_text_from_docx(content):
    """Extract text from DOCX content"""
    try:
        doc = docx.Document(io.BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logging.error(f"Error extracting DOCX text: {e}")
        return f"Error extracting DOCX content: {str(e)}"

def extract_text_from_csv(content):
    """Extract text from CSV content"""
    try:
        csv_reader = csv.reader(io.StringIO(content.decode('utf-8')))
        text = ""
        for row in csv_reader:
            text += ", ".join(row) + "\n"
        return text.strip()
    except Exception as e:
        logging.error(f"Error extracting CSV text: {e}")
        return f"Error extracting CSV content: {str(e)}"

def extract_text_from_file(file):
    """Extract text from uploaded file"""
    content = file.file.read()
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_extension in ['txt', 'md']:
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content.decode('utf-8', errors='ignore')
    elif file_extension == 'pdf':
        return extract_text_from_pdf(content)
    elif file_extension == 'docx':
        return extract_text_from_docx(content)
    elif file_extension == 'csv':
        return extract_text_from_csv(content)
    else:
        return f"Content from {file.filename} (file type: {file_extension} - text extraction not supported)"

# Simple auth functions
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt, password_hash = hashed_password.split(":")
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except:
        return False

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    secret_key = os.getenv("JWT_SECRET_KEY", "demo-secret-key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    print(f"DEBUG: Created token for user {user_id}")
    return token

def verify_token(token: str) -> Optional[dict]:
    try:
        secret_key = os.getenv("JWT_SECRET_KEY", "demo-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except Exception as e:
        print(f"DEBUG: Token verification failed: {e}")
        return None

# Simple auth dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload

# Knowledge base for responses
KNOWLEDGE_BASE = {
    "artificial intelligence": "Artificial Intelligence (AI) is a branch of computer science that aims to create machines capable of intelligent behavior. It includes machine learning, neural networks, natural language processing, computer vision, and robotics.",
    "machine learning": "Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to identify patterns in data and make predictions.",
    "neural networks": "Neural Networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information and learn from data.",
    "deep learning": "Deep Learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data.",
    "natural language processing": "Natural Language Processing (NLP) is a field of AI that focuses on the interaction between computers and humans through natural language.",
    "computer vision": "Computer Vision is a field of AI that enables computers to interpret and understand visual information from the world.",
    "robotics": "Robotics is an interdisciplinary field that combines AI, mechanical engineering, and computer science to create robots that can perform tasks autonomously.",
    "python": "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in AI, data science, web development, and automation.",
    "javascript": "JavaScript is a programming language that enables interactive web pages and is widely used for frontend development, backend development, and mobile app development.",
    "react": "React is a JavaScript library for building user interfaces, particularly web applications. It's maintained by Facebook and uses a component-based architecture.",
    "hello": "Hello! I'm your AI assistant. How can I help you today?",
    "hi": "Hi there! I'm here to help you with any questions you might have.",
    "how are you": "I'm doing well, thank you for asking! I'm here and ready to help you with any questions or tasks you have.",
    "what is": "I'd be happy to explain that! Could you provide more details about what specifically you'd like to know?",
    "help": "I'm here to help! You can ask me questions about various topics, or if you upload documents, I can answer questions based on their content."
}

def get_response(message: str, user_documents: List[str] = None):
    """Get response based on message and user documents"""
    message_lower = message.lower().strip()
    
    # Check for greetings
    if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        return "Hello! I'm your AI assistant. How can I help you today?"
    
    # Check for "how are you" variations
    if any(phrase in message_lower for phrase in ["how are you", "how are u", "how do you do", "how's it going"]):
        return "I'm doing well, thank you for asking! I'm here and ready to help you with any questions or tasks you have."
    
    # Check knowledge base
    for key, value in KNOWLEDGE_BASE.items():
        if key in message_lower:
            return value
    
    # If user has documents, provide context-aware response
    if user_documents:
        doc_content = " ".join(user_documents[:2])  # Use first 2 documents
        if len(doc_content) > 1000:
            doc_content = doc_content[:1000] + "..."
        
        return f"Based on your uploaded documents, I can see you're asking about '{message}'. Your documents contain information about: {doc_content[:200]}... Would you like me to provide more specific information about this topic?"
    
    # Default response
    return f"I understand you're asking about '{message}'. That's an interesting topic! Could you provide more details about what specifically you'd like to know?"

# Auth endpoints
@app.post("/api/auth/register")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_id = f"user_{len(users_db) + 1}"
    hashed_password = hash_password(password)
    
    users_db[email] = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "password": hashed_password
    }
    
    token = create_token(user_id)
    tokens_db[token] = user_id
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "username": username,
            "email": email
        }
    }

@app.post("/api/auth/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = users_db[email]
    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["user_id"])
    tokens_db[token] = user["user_id"]
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"]
        }
    }

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "RAG Chatbot API is running"}

# Document upload endpoint
@app.post("/api/content/upload")
async def upload_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        print(f"DEBUG: Uploading file: {file.filename} for user: {user.get('user_id')}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Extract text
        text = extract_text_from_file(file)
        
        if len(text) == 0:
            raise HTTPException(status_code=400, detail="Empty file provided")
        
        print(f"DEBUG: Extracted text length: {len(text)}")
        
        # Store in simple storage
        content_id = f"content_{int(time.time())}"
        uploaded_content[content_id] = {
            "filename": file.filename,
            "content": text,
            "user_id": user["user_id"],
            "upload_time": time.time()
        }
        
        print(f"DEBUG: File uploaded successfully with ID: {content_id}")
        
        return {
            "status": "success",
            "message": "Document processed successfully",
            "filename": file.filename,
            "content_id": content_id,
            "text_length": len(text)
        }
        
    except Exception as e:
        logging.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Content list endpoint
@app.get("/api/content/list")
async def list_content(user: dict = Depends(get_current_user)):
    try:
        print(f"DEBUG: Listing content for user: {user.get('user_id')}")
        
        # Get user's content
        user_content = []
        for content_id, content_data in uploaded_content.items():
            if content_data.get('user_id') == user.get('user_id'):
                user_content.append({
                    "id": content_id,
                    "filename": content_data.get('filename', 'Unknown'),
                    "size": len(content_data.get('content', '')),
                    "upload_time": content_data.get('upload_time', 0)
                })
        
        print(f"DEBUG: Found {len(user_content)} files for user")
        
        return {
            "content": user_content,
            "count": len(user_content)
        }
    except Exception as e:
        logging.error(f"Error listing content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list content")

# Chat endpoints
@app.post("/api/chat/general")
async def chat_general(message: str = Form(...)):
    try:
        response_text = get_response(message)
        return {
            "response": response_text,
            "source": "general"
        }
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        return {
            "response": "I'm having trouble processing your request right now. Please try again shortly.",
            "source": "general"
        }

@app.post("/api/chat/rag")
async def chat_rag(message: str = Form(...), user: dict = Depends(get_current_user)):
    try:
        # Get user's documents
        user_documents = []
        for content_id, content_data in uploaded_content.items():
            if content_data.get('user_id') == user.get('user_id'):
                user_documents.append(content_data.get('content', ''))
        
        # Generate response with document context
        response_text = get_response(message, user_documents)
        
        return {
            "response": response_text,
            "source": "documents" if user_documents else "general",
            "sources": []
        }
        
    except Exception as e:
        logging.error(f"Error generating RAG response: {str(e)}")
        return {
            "response": "I'm having trouble accessing your documents. Please try again.",
            "source": "documents",
            "sources": []
        }

if __name__ == "__main__":
    print("🚀 Starting RAG Chatbot API...")
    print("✅ Fallback system (no API quota required)")
    print("✅ Document processing working")
    print("✅ Authentication working")
    print("✅ Knowledge base responses")
    uvicorn.run(app, host="0.0.0.0", port=8000)

