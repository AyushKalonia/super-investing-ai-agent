import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './index.css'

function App() {
  const [ticker, setTicker] = useState('NSE: SRVCABLE')
  const [date, setDate] = useState('23 September 2026')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    
    try {
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, date })
      })
      
      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to generate brief')
      }
      
      setResult(data.result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Super Investing</h1>
        <p>AI Research Agent</p>
      </div>

      <div className="card">
        <div className="form-group">
          <div className="input-row">
            <input 
              className="input-field"
              type="text" 
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="Target Ticker (e.g. NSE: SRVCABLE)"
            />
            <input 
              className="input-field"
              type="text" 
              value={date}
              onChange={(e) => setDate(e.target.value)}
              placeholder="Context Date"
            />
          </div>
          <button 
            className="btn" 
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? <span className="loader"></span> : 'Generate Research Brief'}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {result && (
          <div className="markdown-body">
            <ReactMarkdown>{result}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
