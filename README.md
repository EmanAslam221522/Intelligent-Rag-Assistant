# 🤖 NexusAI - Intelligent RAG Chatbot

A powerful **Retrieval-Augmented Generation (RAG)** chatbot powered by **Google Gemini AI** and **LangChain**. Upload documents, add URLs, and get intelligent responses based on your content.

![NexusAI](https://img.shields.io/badge/NexusAI-RAG%20Chatbot-blue?style=for-the-badge&logo=robot)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black?style=for-the-badge&logo=next.js)
![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-orange?style=for-the-badge&logo=google)

## ✨ Features

### 🧠 **AI-Powered Chat**
- **Real Google Gemini AI** integration for intelligent conversations
- **Fallback system** ensures reliability even during API issues
- **Context-aware responses** based on uploaded documents

### 📄 **Document Processing**
- **Multiple formats supported**: PDF, DOCX, CSV, TXT
- **Automatic text extraction** and intelligent chunking
- **Vector embeddings** for semantic search
- **Persistent storage** with ChromaDB

### 🌐 **URL Content Extraction**
- **Web scraping** capabilities with BeautifulSoup
- **Automatic content processing** from any URL
- **Real-time content fetching** and indexing

### 🔐 **Secure Authentication**
- **JWT-based authentication** system
- **Password hashing** with salt
- **User session management**
- **Rate limiting** for security

### 🎯 **RAG (Retrieval-Augmented Generation)**
- **Vector similarity search** for relevant content
- **Context-aware responses** from your documents
- **Intelligent fallback** to general AI when no relevant content found
- **Source attribution** showing which documents were used

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **Google Gemini API Key** (Get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/EmanAslam221522/Intelligent-Rag-Assistant.git
cd Intelligent-Rag-Assistant/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp env.example .env
# Edit .env and add your Google Gemini API key
```

5. **Start the backend**
```bash
python main.py
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start the development server**
```bash
npm run dev
```

4. **Open your browser**
Visit `http://localhost:3000`

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Chat & AI
- `POST /api/chat/general` - General AI chat
- `POST /api/chat/rag` - RAG-powered chat with documents

### Document Management
- `POST /api/upload` - Upload documents (PDF, DOCX, CSV, TXT)
- `GET /api/content/list` - List uploaded content
- `DELETE /api/content/{filename}` - Delete specific content
- `POST /api/content/url` - Add URL content

### Health Check
- `GET /api/health` - API health status

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • React UI      │    │ • REST API      │    │ • Google Gemini │
│ • Auth Context  │    │ • JWT Auth      │    │ • ChromaDB      │
│ • File Upload   │    │ • Document      │    │ • Vector Store  │
│ • Chat Interface│    │   Processing    │    │ • Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# JWT Secret (Generate a strong secret)
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# Database Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### Security Features

- ✅ **API Key Protection** - Environment variables for sensitive data
- ✅ **JWT Authentication** - Secure token-based auth
- ✅ **Password Hashing** - Salted password storage
- ✅ **Rate Limiting** - Protection against abuse
- ✅ **CORS Configuration** - Secure cross-origin requests
- ✅ **Input Validation** - Sanitized file uploads

## 📊 Supported File Types

| Format | Extension | Processing Method |
|--------|-----------|-------------------|
| **PDF** | `.pdf` | PyPDF2 text extraction |
| **Word** | `.docx` | python-docx parsing |
| **CSV** | `.csv` | CSV reader with text conversion |
| **Text** | `.txt` | Direct text reading |

## 🎯 Usage Examples

### Upload a Document
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf"
```

### Chat with Documents
```bash
curl -X POST "http://localhost:8000/api/chat/rag" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "message=What is the main topic of my document?"
```

### Add URL Content
```bash
curl -X POST "http://localhost:8000/api/content/url" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "url=https://example.com/article"
```

## 🛠️ Development

### Project Structure
```
Intelligent-Rag-Assistant/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables
│   ├── env.example         # Environment template
│   └── chroma_db_*/        # Vector databases (auto-generated)
├── frontend/
│   ├── components/          # React components
│   ├── contexts/           # React contexts
│   ├── pages/              # Next.js pages
│   ├── styles/             # CSS styles
│   └── package.json        # Node dependencies
└── README.md               # This file
```

### Key Technologies

**Backend:**
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM application framework
- **Google Generative AI** - Gemini API integration
- **ChromaDB** - Vector database for embeddings
- **JWT** - Authentication tokens
- **PyPDF2** - PDF processing
- **python-docx** - Word document processing

**Frontend:**
- **Next.js** - React framework
- **React** - UI library
- **Axios** - HTTP client
- **Context API** - State management

## 🚨 Troubleshooting

### Common Issues

1. **"Invalid API key" Error**
   - Ensure your Gemini API key is correctly set in `.env`
   - Check if the API key has proper permissions

2. **"401 Invalid token" Error**
   - Clear browser localStorage and re-login
   - Check if JWT_SECRET_KEY is consistent

3. **Document Upload Fails**
   - Verify file format is supported
   - Check file size limits
   - Ensure backend is running

4. **RAG Not Working**
   - Verify ChromaDB is properly initialized
   - Check if documents were processed successfully
   - Review backend logs for errors

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for powerful language model capabilities
- **LangChain** for RAG framework and document processing
- **FastAPI** for excellent Python web framework
- **Next.js** for modern React development
- **ChromaDB** for vector storage and similarity search

## 📞 Support

If you encounter any issues or have questions:

1. **Check the troubleshooting section** above
2. **Review the logs** in your browser console and backend terminal
3. **Open an issue** on GitHub with detailed error information
4. **Contact the maintainer** for urgent issues

---

<div align="center">

**⭐ Star this repository if you found it helpful!**

Made with ❤️ by [Eman Aslam](https://github.com/EmanAslam221522)

</div>