import { useState } from 'react'
import SearchBar from './components/SearchBar'
import Results from './components/Results'
import './App.css'

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSearch(query) {
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const res = await fetch('http://localhost:5001/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Something went wrong')
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo-row">
          <span className="logo-ball">🏀</span>
          <span className="logo-text">
            AllStar<span className="logo-accent">Predict</span>
          </span>
        </div>
        <p className="tagline">Ask anything about NBA stats &amp; predictions</p>
      </header>

      <main className="main">
        <SearchBar onSearch={handleSearch} loading={loading} />

        {loading && (
          <div className="loading">
            <div className="spinner" />
            <p>Fetching NBA data…</p>
          </div>
        )}

        {error && (
          <div className="error-card">
            <span>⚠️</span> {error}
          </div>
        )}

        {results && !loading && <Results data={results} />}
      </main>
    </div>
  )
}
