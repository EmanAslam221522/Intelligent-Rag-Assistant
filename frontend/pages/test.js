import { useState } from 'react'

export default function TestPage() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-4">React Test Page</h1>
        <p className="text-slate-300 mb-4">If you can see this, React is working correctly!</p>
        <div className="space-y-4">
          <p className="text-white">Count: {count}</p>
          <button
            onClick={() => setCount(count + 1)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
          >
            Increment
          </button>
          <button
            onClick={() => setCount(0)}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded ml-2"
          >
            Reset
          </button>
        </div>
        <div className="mt-8">
          <a 
            href="/" 
            className="text-blue-400 hover:text-blue-300 underline"
          >
            ← Back to Chat
          </a>
        </div>
      </div>
    </div>
  )
}

