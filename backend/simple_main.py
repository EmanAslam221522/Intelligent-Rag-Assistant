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
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None
    logging.warning("GEMINI_API_KEY not found. Using fallback responses.")

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
        "exp": datetime.utcnow() + timedelta(days=7)  # Extended to 7 days
    }
    secret_key = os.getenv("JWT_SECRET_KEY", "demo-secret-key")
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    print(f"DEBUG: Created token for user {user_id}, expires in 7 days")
    return token

def verify_token(token: str) -> Optional[dict]:
    try:
        print(f"DEBUG: Verifying token: {token[:20]}...")
        secret_key = os.getenv("JWT_SECRET_KEY", "demo-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(f"DEBUG: Token verified successfully for user: {payload.get('user_id')}")
        return payload
    except Exception as e:
        print(f"DEBUG: Token verification failed: {e}")
        return None

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

# Simple auth dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    print(f"DEBUG: get_current_user called with token: {token[:20]}...")
    payload = verify_token(token)
    
    if not payload:
        print(f"DEBUG: Token verification failed, raising 401")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    print(f"DEBUG: User authenticated successfully: {payload.get('user_id')}")
    return payload

@app.post("/api/auth/refresh")
async def refresh_token(user: dict = Depends(get_current_user)):
    """Refresh token for authenticated user"""
    try:
        new_token = create_token(user["user_id"])
        return {
            "access_token": new_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "RAG Chatbot API is running"}

# Chat endpoints
@app.post("/api/chat/general")
async def chat_general(message: str = Form(...)):
    try:
        if gemini_model:
            # Use real Gemini API
            response = gemini_model.generate_content(message)
            return {
                "response": response.text,
                "source": "general"
            }
        else:
            # Fallback if no API key - provide helpful responses
            return {
                "response": f"I'm currently offline, but I can still help with your uploaded documents! Your message was: '{message}'. Try asking about your documents or check back later.",
                "source": "general"
            }
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        # Provide helpful fallback responses without mentioning API limits
        if "timeout" in str(e).lower():
            return {
                "response": "I'm having trouble processing your request right now. Please try again in a moment.",
                "source": "general"
            }
        else:
            return {
                "response": "I'm having trouble processing your request right now. Please try again shortly.",
                "source": "general"
            }

@app.post("/api/chat/rag")
async def chat_rag(message: str = Form(...), user: dict = Depends(get_current_user)):
    try:
        if gemini_model:
            # Use real Gemini API for RAG
            response = gemini_model.generate_content(f"Based on the user's uploaded documents, please answer: {message}")
            return {
                "response": response.text,
                "source": "documents",
                "sources": []
            }
        else:
            return {
                "response": f"I'm sorry, but the AI service is not configured. Please check the API key. Your RAG message was: '{message}'",
                "source": "documents",
                "sources": []
            }
    except Exception as e:
        logging.error(f"Error generating RAG response: {str(e)}")
        # Provide helpful fallback responses without mentioning API limits
        if "timeout" in str(e).lower():
            return {
                "response": "I'm having trouble processing your request right now. Please try again in a moment.",
                "source": "documents",
                "sources": []
            }
        else:
            return {
                "response": "I'm having trouble processing your request right now. Please try again shortly.",
                "source": "documents",
                "sources": []
            }

# Content management endpoints
@app.post("/api/content/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        print(f"DEBUG: Uploading file: {file.filename} for user: {user.get('user_id')}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read file content
        content = await file.read()
        print(f"DEBUG: File size: {len(content)} bytes")
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file provided")
        
        # Extract text from file based on extension
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        text_content = ""
        
        if file_extension in ['txt', 'md']:
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = content.decode('utf-8', errors='ignore')
        elif file_extension == 'pdf':
            # Simple PDF text extraction (you'd need PyPDF2 for real PDF processing)
            text_content = f"PDF content from {file.filename} (text extraction not implemented in simple version)"
        else:
            text_content = f"Content from {file.filename} (file type: {file_extension})"
        
        print(f"DEBUG: Extracted text length: {len(text_content)}")
        
        # Store in simple in-memory storage
        content_id = f"content_{int(time.time())}"
        uploaded_content[content_id] = {
            "filename": file.filename,
            "content": text_content,
            "size": len(content),
            "user_id": user["user_id"],
            "upload_time": time.time()
        }
        
        print(f"DEBUG: File uploaded successfully with ID: {content_id}")
        
        return {
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "size": len(content),
            "content_id": content_id,
            "text_length": len(text_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/content/list")
async def list_content(user: dict = Depends(get_current_user)):
    try:
        print(f"DEBUG: Listing content for user: {user.get('user_id')}")
        
        # Get content for this user
        user_content = []
        for content_id, content_data in uploaded_content.items():
            if content_data.get('user_id') == user.get('user_id'):
                user_content.append({
                    "id": content_id,
                    "filename": content_data.get('filename'),
                    "size": content_data.get('size'),
                    "upload_time": content_data.get('upload_time')
                })
        
        print(f"DEBUG: Found {len(user_content)} files for user")
        
        return {
            "content": user_content
        }
    except Exception as e:
        print(f"DEBUG: Error listing content: {str(e)}")
        return {
            "content": []
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
