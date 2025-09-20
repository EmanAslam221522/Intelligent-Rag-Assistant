import { useState, useRef, useEffect } from 'react'
import Head from 'next/head'
import { useAuth } from '../contexts/AuthContext'
import { Send, User, Bot, FileText, Globe, Trash2, Upload, Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import AuthModal from '../components/Auth/AuthModal'
import ContentManagement from '../components/Content/ContentManagement'

export default function Home() {
  const { user, isAuthenticated, getAuthHeaders, logout } = useAuth()
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showContentManagement, setShowContentManagement] = useState(false)
  const [chatMode, setChatMode] = useState('general') // 'general' or 'documents'
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    setIsTyping(true)

    try {
      let response
      
      if (chatMode === 'general') {
        // General chat - no authentication required
        response = await fetch('/api/chat/general', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: `message=${encodeURIComponent(inputMessage)}`
        })
      } else {
        // RAG chat - requires authentication
        const headers = await getAuthHeaders()
        response = await fetch('/api/chat/rag', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            ...headers
          },
          body: `message=${encodeURIComponent(inputMessage)}`
        })
      }

      // Simulate typing delay for better UX
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Failed to get response')
      }

      // Extract the actual response text properly
      const responseText = data.response || data.answer || data.content || data.message || JSON.stringify(data)

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: responseText,
        source: data.source || 'general',
        sources: data.sources || [],
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      
      // Extract the actual error message
      let errorMessage = 'Sorry, I encountered an error. Please try again.'
      
      if (error.message) {
        errorMessage = error.message
      } else if (error.response) {
        errorMessage = error.response.message || errorMessage
      }
      
      toast.error(errorMessage)
      
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: errorMessage,
        source: 'error',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
    } finally {
      setIsLoading(false)
      setIsTyping(false)
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  return (
    <>
      <Head>
        <title>Dynamic RAG Chatbot</title>
        <meta name="description" content="AI-powered chatbot with document analysis capabilities" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-slate-900">
        {/* Header */}
        <header className="header-glass sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-3">
                  <Bot className="h-8 w-8 text-blue-400" />
                  <h1 className="text-xl font-bold text-white">RAG Chatbot</h1>
                </div>
                
                {isAuthenticated && (
                  <div className="hidden md:flex items-center space-x-2">
                    <button
                      onClick={() => setChatMode('general')}
                      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                        chatMode === 'general'
                          ? 'bg-blue-900 text-white shadow-md'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      General
                    </button>
                    <button
                      onClick={() => setChatMode('documents')}
                      className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                        chatMode === 'documents'
                          ? 'bg-blue-900 text-white shadow-md'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      Documents
                    </button>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-4">
                {isAuthenticated ? (
                  <>
                    <button
                      onClick={() => setShowContentManagement(true)}
                      className="btn-ghost flex items-center space-x-2"
                    >
                      <FileText className="h-4 w-4" />
                      <span className="hidden sm:inline">Manage Content</span>
                    </button>
                    
                    <div className="flex items-center space-x-3">
                      <span className="text-sm text-slate-300 font-medium">Welcome, {user?.username}</span>
                      <button
                        onClick={logout}
                        className="btn-secondary text-sm"
                      >
                        Logout
                      </button>
                    </div>
                  </>
                ) : (
                  <button
                    onClick={() => setShowAuthModal(true)}
                    className="btn-primary"
                  >
                    Login / Register
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card min-h-[600px] flex flex-col">
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 chat-container">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <Bot className="h-16 w-16 text-blue-400 mb-4" />
                  <h2 className="text-xl font-semibold text-white mb-2">
                    Welcome to RAG Chatbot
                  </h2>
                  <p className="text-slate-300 max-w-md">
                    {isAuthenticated 
                      ? "Ask me anything! I can help with general questions or analyze your uploaded documents."
                      : "Ask me anything! For general questions, no login required. Login to upload documents for personalized responses."
                    }
                  </p>
                  {!isAuthenticated && (
                    <div className="mt-4 p-4 bg-blue-900/20 rounded-lg border border-blue-600/50 backdrop-blur-sm">
                      <p className="text-sm text-blue-300">
                        💡 Login to upload documents and get personalized responses based on your content!
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} message-enter`}
                  >
                    <div className={`message-bubble ${message.type === 'user' ? 'message-user' : message.source === 'documents' ? 'message-ai-document' : 'message-ai'}`}>
                      <div className="flex items-start space-x-2">
                        {message.type === 'ai' && (
                          <Bot className="h-5 w-5 mt-1 flex-shrink-0" />
                        )}
                        {message.type === 'user' && (
                          <User className="h-5 w-5 mt-1 flex-shrink-0" />
                        )}
                        <div className="flex-1">
                          <div className="whitespace-pre-wrap">{message.content}</div>
                          
                          {message.source === 'documents' && message.sources && message.sources.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-blue-200">
                              <p className="text-xs text-blue-700 font-medium mb-2">Sources:</p>
                              <div className="space-y-1">
                                {message.sources.map((source, index) => (
                                  <div key={index} className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                    {source.source} ({source.content_type})
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          <div className="message-timestamp">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {isTyping && (
                <div className="flex justify-start message-enter">
                  <div className="message-bubble message-ai">
                    <div className="flex items-center space-x-2">
                      <Bot className="h-5 w-5 text-blue-400" />
                      <div className="typing-indicator">
                        <span className="text-sm text-slate-300">AI is typing</span>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className="border-t border-gray-200 p-4">
              <form onSubmit={sendMessage} className="flex space-x-4">
                <div className="flex-1">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder={isAuthenticated 
                      ? `Ask me anything${chatMode === 'documents' ? ' about your documents' : ''}...`
                      : "Ask me anything..."
                    }
                    className="input-field"
                    disabled={isLoading}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || isLoading}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <Send className="h-4 w-4" />
                  <span>Send</span>
                </button>
              </form>
              
              {messages.length > 0 && (
                <div className="mt-3 flex justify-end">
                  <button
                    onClick={clearChat}
                    className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    Clear chat
                  </button>
                </div>
              )}
            </div>
          </div>
        </main>

        {/* Modals */}
        <AuthModal 
          isOpen={showAuthModal} 
          onClose={() => setShowAuthModal(false)} 
        />
        
        <ContentManagement 
          isOpen={showContentManagement} 
          onClose={() => setShowContentManagement(false)} 
        />
      </div>
    </>
  )
}
