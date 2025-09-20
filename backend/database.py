import pymongo
from pymongo import MongoClient
from datetime import datetime
import os
from typing import Dict, List, Optional
import uuid

class DatabaseManager:
    def __init__(self):
        # MongoDB connection
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = MongoClient(mongodb_url)
        self.db = self.client.rag_chatbot
        
        # Collections
        self.users = self.db.users
        self.content_metadata = self.db.content_metadata
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        self.users.create_index("email", unique=True)
        self.users.create_index("user_id", unique=True)
        self.content_metadata.create_index([("user_id", 1), ("content_id", 1)], unique=True)
        self.content_metadata.create_index("user_id")
    
    def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        return self.users.find_one({"email": email}) is not None
    
    def create_user(self, username: str, email: str, hashed_password: str) -> str:
        """Create a new user and return user_id"""
        user_id = str(uuid.uuid4())
        user_doc = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.users.insert_one(user_doc)
        return user_id
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        user = self.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id"""
        user = self.users.find_one({"user_id": user_id})
        if user:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string
        return user
    
    def save_content_metadata(self, user_id: str, content_id: str, metadata: Dict):
        """Save content metadata"""
        doc = {
            "user_id": user_id,
            "content_id": content_id,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }
        self.content_metadata.insert_one(doc)
    
    def get_user_content(self, user_id: str) -> List[Dict]:
        """Get all content for a user"""
        content_list = []
        cursor = self.content_metadata.find({"user_id": user_id})
        
        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            content_list.append({
                "content_id": doc["content_id"],
                "metadata": doc["metadata"],
                "created_at": doc["created_at"]
            })
        
        return content_list
    
    def delete_content_metadata(self, user_id: str, content_id: str):
        """Delete content metadata"""
        self.content_metadata.delete_one({
            "user_id": user_id,
            "content_id": content_id
        })
    
    def update_user(self, user_id: str, update_data: Dict):
        """Update user data"""
        update_data["updated_at"] = datetime.now().isoformat()
        self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    def delete_user(self, user_id: str):
        """Delete user and all associated data"""
        # Delete user
        self.users.delete_one({"user_id": user_id})
        
        # Delete user's content metadata
        self.content_metadata.delete_many({"user_id": user_id})
    
    def get_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        content_count = self.content_metadata.count_documents({"user_id": user_id})
        user = self.get_user_by_id(user_id)
        
        return {
            "content_count": content_count,
            "created_at": user["created_at"] if user else None
        }


