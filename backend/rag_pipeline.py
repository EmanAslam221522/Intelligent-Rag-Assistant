import os
import google.generativeai as genai
from chromadb import Client, Settings
from chromadb.config import Settings as ChromaSettings
import uuid
from typing import List, Dict, Tuple, Optional
import logging
import numpy as np

# Try to import sentence-transformers, but don't fail if it's not available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

class RAGPipeline:
    def __init__(self):
        # Initialize Gemini API
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize ChromaDB
        self.chroma_client = Client(Settings(
            persist_directory="./chroma_db",
            anonymized_telemetry=False
        ))
        
        # Initialize embedding model (fallback to sentence-transformers if needed)
        try:
            self.embedding_model = genai.embed_content
            self.use_fallback_embeddings = False
        except:
            # Fallback to sentence-transformers
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.use_fallback_embeddings = True
                except:
                    # If sentence-transformers fails, use a simple fallback
                    self.embedding_model = None
                    self.use_fallback_embeddings = False
                    print("Warning: No embedding model available. RAG functionality will be limited.")
            else:
                # If sentence-transformers is not available, use a simple fallback
                self.embedding_model = None
                self.use_fallback_embeddings = False
                print("Warning: No embedding model available. RAG functionality will be limited.")
        
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
    def create_user_collection(self, user_id: str) -> str:
        """Create a new collection for a user"""
        try:
            collection_name = f"user_{user_id}"
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"user_id": user_id}
            )
            return collection_name
        except Exception as e:
            logging.error(f"Error creating collection for user {user_id}: {str(e)}")
            raise
    
    def get_user_collection(self, user_id: str):
        """Get user's collection"""
        try:
            collection_name = f"user_{user_id}"
            return self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logging.error(f"Error getting collection for user {user_id}: {str(e)}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + self.chunk_size // 2:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts with quota handling"""
        try:
            if self.embedding_model is None:
                # Simple fallback: return hash-based embeddings
                return self._generate_hash_embeddings(texts)
            elif hasattr(self, 'use_fallback_embeddings') and self.use_fallback_embeddings:
                # Use sentence-transformers
                embeddings = self.embedding_model.encode(texts)
                return embeddings.tolist()
            else:
                # Use Gemini embeddings with quota handling
                embeddings = []
                for text in texts:
                    try:
                        result = genai.embed_content(
                            model="models/embedding-001",
                            content=text,
                            task_type="retrieval_document"
                        )
                        embeddings.append(result['embedding'])
                    except Exception as e:
                        if "quota" in str(e).lower() or "429" in str(e):
                            logging.warning(f"Gemini quota exceeded, using fallback embeddings: {str(e)}")
                            # Use hash-based embeddings as fallback
                            embeddings.append(self._generate_hash_embeddings([text])[0])
                        else:
                            raise e
                return embeddings
        except Exception as e:
            logging.error(f"Error generating embeddings: {str(e)}")
            # Fallback to hash-based embeddings
            return self._generate_hash_embeddings(texts)
    
    def _generate_hash_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic hash-based embeddings as fallback"""
        import hashlib
        embeddings = []
        for text in texts:
            # Create deterministic hash-based embedding
            text_hash = hashlib.md5(text.encode()).hexdigest()
            embedding = []
            for i in range(0, min(len(text_hash), 384), 2):
                embedding.append(float(int(text_hash[i:i+2], 16)) / 255.0)
            # Pad to 384 dimensions
            while len(embedding) < 384:
                embedding.append(0.0)
            embeddings.append(embedding[:384])
        return embeddings
    
    def add_document(self, user_id: str, content: str, source: str, content_type: str) -> str:
        """Add a document to user's collection with comprehensive error handling"""
        try:
            logging.info(f"Starting document addition for user {user_id}, source: {source}")
            
            # Validate inputs
            if not content or len(content.strip()) < 10:
                raise ValueError("Content is too short or empty")
            
            if not user_id:
                raise ValueError("User ID is required")
            
            # Get or create user collection
            try:
                collection = self.get_user_collection(user_id)
                logging.info(f"Retrieved existing collection for user {user_id}")
            except Exception as e:
                logging.info(f"Collection not found for user {user_id}, creating new one: {str(e)}")
                collection_name = self.create_user_collection(user_id)
                collection = self.get_user_collection(user_id)
                logging.info(f"Created new collection: {collection_name}")
            
            # Chunk the content
            logging.info(f"Chunking content of length {len(content)}")
            chunks = self.chunk_text(content)
            logging.info(f"Created {len(chunks)} chunks")
            
            if not chunks:
                raise ValueError("No chunks created from content")
            
            # Generate embeddings
            logging.info("Generating embeddings for chunks")
            try:
                embeddings = self.generate_embeddings(chunks)
                logging.info(f"Generated {len(embeddings)} embeddings")
            except Exception as e:
                logging.error(f"Failed to generate embeddings: {str(e)}")
                raise ValueError(f"Failed to generate embeddings: {str(e)}")
            
            # Generate unique IDs
            content_id = str(uuid.uuid4())
            chunk_ids = [f"{content_id}_chunk_{i}" for i in range(len(chunks))]
            logging.info(f"Generated content ID: {content_id}")
            
            # Prepare metadata
            metadatas = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "content_id": content_id,
                    "source": source,
                    "content_type": content_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_length": len(chunk)
                }
                metadatas.append(metadata)
            
            # Add to collection
            logging.info("Adding chunks to vector store")
            try:
                collection.add(
                    ids=chunk_ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )
                logging.info(f"Successfully added {len(chunks)} chunks to vector store")
            except Exception as e:
                logging.error(f"Failed to add chunks to collection: {str(e)}")
                raise ValueError(f"Failed to add chunks to vector store: {str(e)}")
            
            logging.info(f"Document addition completed successfully for {source}")
            return content_id
            
        except Exception as e:
            logging.error(f"Error adding document for user {user_id}: {str(e)}")
            raise
    
    def search_relevant_chunks(self, user_id: str, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant chunks in user's collection"""
        try:
            collection = self.get_user_collection(user_id)
            
            # Generate query embedding
            query_embeddings = self.generate_embeddings([query])
            
            # Search collection
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k
            )
            
            # Format results
            relevant_chunks = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    chunk_data = {
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if results['distances'] else 0
                    }
                    relevant_chunks.append(chunk_data)
            
            return relevant_chunks
            
        except Exception as e:
            logging.error(f"Error searching chunks for user {user_id}: {str(e)}")
            return []
    
    def generate_rag_response(self, query: str, user_id: str) -> Tuple[str, List[Dict]]:
        """Generate RAG response using user's documents"""
        try:
            # First check if user has any documents
            try:
                collection = self.get_user_collection(user_id)
                if collection.count() == 0:
                    logging.info(f"No documents found for user {user_id}, falling back to general response")
                    return self.generate_general_response(query), []
            except Exception as e:
                logging.warning(f"Could not access user collection for {user_id}: {str(e)}")
                return self.generate_general_response(query), []
            
            # Search for relevant chunks
            relevant_chunks = self.search_relevant_chunks(user_id, query)
            
            if not relevant_chunks:
                # No relevant content found, fallback to general response
                logging.info(f"No relevant chunks found for query: {query}")
                return self.generate_general_response(query), []
            
            # Prepare context from relevant chunks (limit to avoid token limits)
            context_parts = []
            sources = []
            max_context_length = 2000  # Limit context to avoid token limits
            
            current_length = 0
            for chunk in relevant_chunks:
                if current_length + len(chunk['content']) > max_context_length:
                    break
                context_parts.append(chunk['content'])
                sources.append({
                    "source": chunk['metadata']['source'],
                    "content_type": chunk['metadata']['content_type'],
                    "relevance_score": 1 - chunk['distance']  # Convert distance to relevance
                })
                current_length += len(chunk['content'])
            
            if not context_parts:
                return self.generate_general_response(query), []
            
            context = "\n\n".join(context_parts)
            
            # Generate response using context
            prompt = f"""Based on the following context from the user's documents, answer the query. If the context doesn't contain enough information to answer the query, say so and provide a general response.

Context:
{context}

Query: {query}

Please provide a helpful response based on the context above. If you reference specific information, mention which source it came from."""

            response = self.gemini_model.generate_content(prompt)
            
            return response.text, sources
            
        except Exception as e:
            logging.error(f"Error generating RAG response: {str(e)}")
            # Fallback to general response with error info
            general_response = self.generate_general_response(query)
            if "quota" in str(e).lower():
                general_response += "\n\nNote: Document-based responses are temporarily unavailable due to API limits."
            return general_response, []
    
    def generate_general_response(self, query: str) -> str:
        """Generate general response using Gemini with comprehensive error handling"""
        try:
            response = self.gemini_model.generate_content(query)
            return response.text
        except Exception as e:
            logging.error(f"Error generating general response: {str(e)}")
            if "API key not valid" in str(e):
                return "I'm sorry, but there's an issue with the AI service configuration. Please check the API key."
            elif "quota" in str(e).lower() or "429" in str(e):
                return "I'm having trouble processing your request right now. Please try again shortly."
            elif "404" in str(e):
                return "I'm experiencing a temporary service issue. Please try again in a few moments."
            elif "timeout" in str(e).lower():
                return "The request timed out. Please try again with a shorter query."
            else:
                return f"I encountered an error: {str(e)[:100]}... Please try again."
    
    def delete_document(self, user_id: str, content_id: str):
        """Delete a document from user's collection"""
        try:
            collection = self.get_user_collection(user_id)
            
            # Get all chunks for this content_id
            results = collection.get(where={"content_id": content_id})
            
            if results['ids']:
                collection.delete(ids=results['ids'])
                
        except Exception as e:
            logging.error(f"Error deleting document {content_id} for user {user_id}: {str(e)}")
            raise
    
    def get_collection_stats(self, user_id: str) -> Dict:
        """Get statistics about user's collection"""
        try:
            collection = self.get_user_collection(user_id)
            count = collection.count()
            
            # Get unique content IDs
            results = collection.get()
            content_ids = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    content_ids.add(metadata['content_id'])
            
            return {
                "total_chunks": count,
                "unique_documents": len(content_ids)
            }
            
        except Exception as e:
            logging.error(f"Error getting collection stats for user {user_id}: {str(e)}")
            return {"total_chunks": 0, "unique_documents": 0}
