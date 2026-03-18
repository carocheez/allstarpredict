import './PredictionDisplay.css'

export default function PredictionDisplay({ text }) {
  // Convert Gemini markdown-ish output into readable paragraphs
  const lines = text.split('\n').filter(l => l.trim())

  return (
    <div className="prediction">
      {lines.map((line, i) => {
        if (line.startsWith('## ')) {
          return <h3 key={i} className="pred-h2">{line.slice(3)}</h3>
        }
        if (line.startsWith('# ')) {
          return <h2 key={i} className="pred-h1">{line.slice(2)}</h2>
        }
        if (line.startsWith('**') && line.endsWith('**')) {
          return <p key={i} className="pred-bold">{line.slice(2, -2)}</p>
        }
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return <li key={i} className="pred-li">{line.slice(2)}</li>
        }
        return <p key={i} className="pred-p">{line}</p>
      })}
    </div>
  )
}
