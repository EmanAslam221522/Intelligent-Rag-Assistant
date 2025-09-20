import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function TestAuth() {
  const { user, isAuthenticated, getAuthHeaders, login, logout } = useAuth()
  const [email, setEmail] = useState('test@example.com')
  const [password, setPassword] = useState('testpass123')
  const [testResult, setTestResult] = useState('')

  const handleLogin = async () => {
    const result = await login(email, password)
    setTestResult(result.success ? 'Login successful!' : 'Login failed: ' + result.error)
  }

  const testUpload = async () => {
    try {
      const headers = getAuthHeaders()
      console.log('Auth headers:', headers)
      
      if (!headers.Authorization) {
        setTestResult('No token available!')
        return
      }

      // Create a test file
      const testFile = new File(['Test content'], 'test.txt', { type: 'text/plain' })
      const formData = new FormData()
      formData.append('file', testFile)

      const response = await fetch('http://localhost:8000/api/content/upload', {
        method: 'POST',
        body: formData,
        headers: headers
      })

      if (response.ok) {
        const data = await response.json()
        setTestResult(`Upload successful: ${JSON.stringify(data)}`)
      } else {
        const error = await response.json()
        setTestResult(`Upload failed: ${error.detail}`)
      }
    } catch (error) {
      setTestResult(`Error: ${error.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8">Authentication Test</h1>
      
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Current Status</h2>
          <p>Authenticated: {isAuthenticated ? 'Yes' : 'No'}</p>
          <p>User: {user ? user.username : 'None'}</p>
          <p>Token: {getAuthHeaders().Authorization ? 'Present' : 'Missing'}</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Login Test</h2>
          <div className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
            <div className="flex space-x-4">
              <button
                onClick={handleLogin}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg"
              >
                Login
              </button>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Upload Test</h2>
          <button
            onClick={testUpload}
            className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg"
          >
            Test Upload
          </button>
        </div>

        {testResult && (
          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Test Result</h2>
            <pre className="text-sm text-gray-300 whitespace-pre-wrap">{testResult}</pre>
          </div>
        )}
      </div>
    </div>
  )
}


