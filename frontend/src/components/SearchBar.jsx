import { useState } from 'react'
import './SearchBar.css'

const EXAMPLES = [
  'Steph Curry 50 point games',
  "Predict Jalen Johnson's first All-Star selection",
  'LeBron James career stats',
  'Nikola Jokić triple doubles 2023-24',
]

export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('')

  function submit(e) {
    e.preventDefault()
    const q = query.trim()
    if (q) onSearch(q)
  }

  return (
    <div className="search-wrapper">
      <form className="search-form" onSubmit={submit}>
        <input
          className="search-input"
          type="text"
          placeholder="Ask about any NBA player or stat…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button className="search-btn" type="submit" disabled={loading || !query.trim()}>
          {loading ? '…' : 'Search'}
        </button>
      </form>

      <div className="examples">
        {EXAMPLES.map(ex => (
          <button
            key={ex}
            className="example-chip"
            onClick={() => { setQuery(ex); onSearch(ex) }}
            disabled={loading}
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  )
}
