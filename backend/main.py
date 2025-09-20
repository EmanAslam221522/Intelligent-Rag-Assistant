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
import PyPDF2
import docx
import csv
import io
import requests
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GEMINI_API_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
    print("✅ REAL Gemini API configured successfully")
else:
    print("❌ GEMINI_API_KEY not found")
    gemini_model = None
    llm = None
    embeddings = None

app = FastAPI(title="NexusAI Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple storage
users_db = {}
user_documents = {}  # Store user documents

# Auth functions
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
    print(f"✅ Token created for user: {user_id}")
    return token

def verify_token(token: str) -> Optional[dict]:
    try:
        secret_key = os.getenv("JWT_SECRET_KEY", "demo-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(f"✅ Token verified for user: {payload.get('user_id')}")
        return payload
    except Exception as e:
        print(f"❌ Token verification failed: {str(e)}")
        return None

class User:
    def __init__(self, username: str):
        self.username = username

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return User(username=payload.get("user_id"))

# Document processing functions
def extract_text_from_pdf(file: UploadFile):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def extract_text_from_docx(file: UploadFile):
    doc = docx.Document(io.BytesIO(file.file.read()))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text.strip()

def extract_text_from_csv(file: UploadFile):
    content = file.file.read().decode('utf-8')
    csv_reader = csv.reader(io.StringIO(content))
    text = ""
    for row in csv_reader:
        text += ", ".join(row) + "\n"
    return text.strip()

def extract_text_from_file(file: UploadFile):
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_extension == 'pdf':
        return extract_text_from_pdf(file)
    elif file_extension == 'docx':
        return extract_text_from_docx(file)
    elif file_extension == 'csv':
        return extract_text_from_csv(file)
    elif file_extension == 'txt':
        return file.file.read().decode('utf-8')
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "NexusAI Chatbot API is running"}

@app.post("/api/chat/general")
async def chat_general(message: str = Form(...)):
    try:
        if not gemini_model:
            raise HTTPException(status_code=500, detail="Gemini API not configured")
        
        # Call REAL Gemini API
        response = gemini_model.generate_content(message)
        return {"response": response.text, "source": "general"}
    except Exception as e:
        logging.error(f"Error in Gemini API call: {str(e)}")
        return {"response": f"I'm experiencing technical difficulties. Error: {str(e)}", "source": "error"}

# RAG chat endpoint for frontend
@app.post("/api/chat/rag")
async def chat_rag(message: str = Form(...), current_user: User = Depends(get_current_user)):
    try:
        if not gemini_model:
            raise HTTPException(status_code=500, detail="Gemini API not configured")

        # Check if user has documents stored
        if current_user.username not in user_documents or not user_documents[current_user.username]:
            # Fallback to general Gemini if no documents
            response = gemini_model.generate_content(message)
            return {"response": response.text, "source": "general"}
        
        # Try vector search first if available
        try:
            if embeddings:
                persist_directory = f"./chroma_db_{current_user.username}"
                if os.path.exists(persist_directory):
                    vector_store = Chroma(
                        collection_name=f"user_{current_user.username}",
                        embedding_function=embeddings,
                        persist_directory=persist_directory
                    )
                    
                    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
                    docs = retriever.get_relevant_documents(message)
                    
                    if docs:
                        context = "\n".join([doc.page_content for doc in docs])
                        prompt = f"Based on the following context from uploaded documents:\n\n{context}\n\nAnswer this question: {message}"
                        response = gemini_model.generate_content(prompt)
                        return {"response": response.text, "source": "documents", "sources": len(docs)}
        except Exception as vector_error:
            print(f"⚠️ Vector search failed, using simple text search: {str(vector_error)}")
        
        # Fallback to simple text search in stored documents
        user_docs = user_documents[current_user.username]
        relevant_content = []
        
        for doc in user_docs:
            if 'text_content' in doc:
                text_content = doc['text_content'].lower()
                message_lower = message.lower()
                
                # Simple keyword matching
                if any(word in text_content for word in message_lower.split()):
                    relevant_content.append(doc['text_content'])
        
        if relevant_content:
            context = "\n\n".join(relevant_content[:3])  # Limit to 3 most relevant
            prompt = f"Based on the following context from uploaded documents:\n\n{context}\n\nAnswer this question: {message}"
            response = gemini_model.generate_content(prompt)
            return {"response": response.text, "source": "documents", "sources": len(relevant_content)}
        else:
            # Fallback to general Gemini if no relevant content found
            response = gemini_model.generate_content(message)
            return {"response": response.text, "source": "general"}
            
    except Exception as e:
        logging.error(f"Error in RAG query: {str(e)}")
        # Fallback to general Gemini on RAG error
        if gemini_model:
            response = gemini_model.generate_content(message)
            return {"response": response.text, "source": "general"}
        else:
            return {"response": f"Could not query documents: {str(e)}", "source": "error"}

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        # Extract text from file
        text = extract_text_from_file(file)
        
        # Store document info and text content
        if current_user.username not in user_documents:
            user_documents[current_user.username] = []
        
        # Store document with full text content for simple RAG
        user_documents[current_user.username].append({
            "filename": file.filename,
            "text_content": text,  # Store full text for simple search
            "text_length": len(text),
            "upload_time": datetime.now().isoformat()
        })
        
        # Try vector storage if embeddings are available, but don't fail if quota exceeded
        try:
            if embeddings:
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = text_splitter.split_text(text)
                
                vector_store = Chroma.from_texts(
                    texts=chunks, 
                    embedding=embeddings,
                    collection_name=f"user_{current_user.username}",
                    persist_directory=f"./chroma_db_{current_user.username}"
                )
                vector_store.persist()
                print(f"✅ Vector storage successful for {file.filename}")
        except Exception as vector_error:
            print(f"⚠️ Vector storage failed (quota exceeded), using simple text storage: {str(vector_error)}")
        
        return {"status": "success", "message": "Document processed successfully", "filename": file.filename, "text_length": len(text)}
    except Exception as e:
        logging.error(f"Error uploading document: {str(e)}")
        return {"status": "error", "message": f"Upload failed: {str(e)}"}

@app.post("/api/query-documents")
async def query_documents(message: str = Form(...), current_user: User = Depends(get_current_user)):
    try:
        if not llm or not embeddings:
            raise HTTPException(status_code=500, detail="Gemini API or Embeddings not configured")

        # Check if user has documents
        persist_directory = f"./chroma_db_{current_user.username}"
        collection_name = f"user_{current_user.username}"

        if not os.path.exists(persist_directory):
            # Fallback to general Gemini if no documents
            response = gemini_model.generate_content(message)
            return {"response": response.text, "source": "general"}
        
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory
        )
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        docs = retriever.get_relevant_documents(message)
        
        if not docs:
            # Fallback to general Gemini if no relevant documents
            response = gemini_model.generate_content(message)
            return {"response": response.text, "source": "general"}
        
        context = "\n".join([doc.page_content for doc in docs])
        prompt = f"Based on the following context from uploaded documents:\n\n{context}\n\nAnswer this question: {message}"
        
        response = gemini_model.generate_content(prompt)
        
        return {"response": response.text, "source": "documents", "sources": len(docs)}
    except Exception as e:
        logging.error(f"Error in RAG query: {str(e)}")
        # Fallback to general Gemini on RAG error
        if gemini_model:
            response = gemini_model.generate_content(message)
            return {"response": response.text, "source": "general"}
        else:
            return {"response": f"Could not query documents: {str(e)}", "source": "error"}

# Content Management Endpoints
@app.get("/api/content/list")
async def list_content(current_user: User = Depends(get_current_user)):
    try:
        print(f"✅ Content list requested by user: {current_user.username}")
        if current_user.username not in user_documents:
            return {"content": []}
        
        documents = user_documents[current_user.username]
        # Remove text_content from response to reduce payload size
        response_docs = []
        for doc in documents:
            response_doc = {k: v for k, v in doc.items() if k != 'text_content'}
            response_docs.append(response_doc)
        
        print(f"✅ Returning {len(response_docs)} documents for user: {current_user.username}")
        return {"content": response_docs}
    except Exception as e:
        logging.error(f"Error listing content: {str(e)}")
        return {"content": []}

@app.delete("/api/content/{filename}")
async def delete_content(filename: str, current_user: User = Depends(get_current_user)):
    try:
        if current_user.username in user_documents:
            user_documents[current_user.username] = [
                doc for doc in user_documents[current_user.username] 
                if doc["filename"] != filename
            ]
        
        return {"status": "success", "message": f"Document {filename} deleted"}
    except Exception as e:
        logging.error(f"Error deleting content: {str(e)}")
        return {"status": "error", "message": f"Delete failed: {str(e)}"}

def extract_content_from_url(url: str):
    """Extract text content from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:10000]  # Limit to 10k characters
    except Exception as e:
        raise Exception(f"Failed to extract content from URL: {str(e)}")

@app.post("/api/content/url")
async def add_url_content(url: str = Form(...), current_user: User = Depends(get_current_user)):
    try:
        # Extract content from URL
        text_content = extract_content_from_url(url)
        
        # Store document info and text content
        if current_user.username not in user_documents:
            user_documents[current_user.username] = []
        
        # Store document with full text content for simple RAG
        user_documents[current_user.username].append({
            "filename": f"URL: {url}",
            "text_content": text_content,  # Store full text for simple search
            "text_length": len(text_content),
            "upload_time": datetime.now().isoformat(),
            "url": url
        })
        
        # Try vector storage if embeddings are available, but don't fail if quota exceeded
        try:
            if embeddings:
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                chunks = text_splitter.split_text(text_content)
                
                vector_store = Chroma.from_texts(
                    texts=chunks, 
                    embedding=embeddings,
                    collection_name=f"user_{current_user.username}",
                    persist_directory=f"./chroma_db_{current_user.username}"
                )
                vector_store.persist()
                print(f"✅ Vector storage successful for URL: {url}")
        except Exception as vector_error:
            print(f"⚠️ Vector storage failed (quota exceeded), using simple text storage: {str(vector_error)}")
        
        return {"status": "success", "message": f"URL content extracted and processed successfully", "text_length": len(text_content)}
    except Exception as e:
        logging.error(f"Error adding URL content: {str(e)}")
        return {"status": "error", "message": f"URL processing failed: {str(e)}"}

@app.post("/api/auth/register")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    print(f"🔐 Registration attempt for: {username} ({email})")
    
    if email in users_db:
        print(f"❌ User already exists: {email}")
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
    print(f"✅ User registered successfully: {username} with token: {token[:30]}...")
    
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
    print(f"🔐 Login attempt for: {email}")
    
    if email not in users_db:
        print(f"❌ User not found: {email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_data = users_db[email]
    if not verify_password(password, user_data["password"]):
        print(f"❌ Invalid password for: {email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user_data["user_id"])
    print(f"✅ User logged in successfully: {user_data['username']} with token: {token[:30]}...")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"]
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
