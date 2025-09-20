import { useState, useEffect } from 'react'
import Head from 'next/head'

export default function SimpleChat() {
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!message.trim() || isLoading) return

    setIsLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/chat/general', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ message })
      })
      
      const data = await res.json()
      setResponse(data.response)
    } catch (error) {
      setResponse('Error: ' + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <Head>
        <title>RAG Chatbot - Simple</title>
        <meta name="description" content="AI-powered chatbot" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">RAG Chatbot</h1>
        
        <div className="max-w-2xl mx-auto">
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Chat with AI</h2>
            
            <form onSubmit={sendMessage} className="space-y-4">
              <div>
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ask me anything..."
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                />
              </div>
              
              <button
                type="submit"
                disabled={isLoading || !message.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-lg transition-colors"
              >
                {isLoading ? 'Sending...' : 'Send Message'}
              </button>
            </form>

            {response && (
              <div className="mt-6 p-4 bg-gray-700 rounded-lg">
                <h3 className="font-semibold mb-2">AI Response:</h3>
                <p className="text-gray-300 whitespace-pre-wrap">{response}</p>
              </div>
            )}
          </div>

          <div className="text-center text-gray-400">
            <p>Backend: http://localhost:8000</p>
            <p>Simple version - No authentication required</p>
          </div>
        </div>
      </div>
    </div>
  )
}


