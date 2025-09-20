import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed_password.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def create_user(self, username: str, email: str, password: str) -> str:
        """Create a new user and return user_id"""
        from database import DatabaseManager
        db_manager = DatabaseManager()
        
        # Check if user already exists
        if db_manager.user_exists(email):
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Create user
        user_id = db_manager.create_user(username, email, hashed_password)
        return user_id
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        from database import DatabaseManager
        db_manager = DatabaseManager()
        
        user = db_manager.get_user_by_email(email)
        if not user:
            return None
        
        if self.verify_password(password, user["password"]):
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"]
            }
        return None
    
    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

# Global auth manager instance
auth_manager = AuthManager()
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user data from database
    from database import DatabaseManager
    db_manager = DatabaseManager()
    user = db_manager.get_user_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"]
    }


