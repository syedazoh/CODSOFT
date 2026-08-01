import React, { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => setApiStatus(data.status))
      .catch((err) => {
        setError(err.message)
        setApiStatus('error')
      })
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Startup Simulator</h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Development Status</h2>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <span>Backend API</span>
            <span className={`px-3 py-1 rounded text-white ${apiStatus === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'}`}>
              {apiStatus}
            </span>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App