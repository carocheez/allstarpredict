import GameLogTable from './GameLogTable'
import CareerStatsTable from './CareerStatsTable'
import PredictionDisplay from './PredictionDisplay'
import './Results.css'

export default function Results({ data }) {
  const { intent, player, results, count, analysis, message } = data

  return (
    <div className="results">
      <div className="results-header">
        <h2 className="player-name">{player}</h2>
        {intent === 'game_log_filter' && (
          <span className="results-count">{count} game{count !== 1 ? 's' : ''}</span>
        )}
      </div>

      {intent === 'game_log_filter' && (
        results.length === 0
          ? <p className="no-results">{message || 'No matching games found.'}</p>
          : <GameLogTable rows={results} />
      )}

      {intent === 'career_stats' && (
        results.length === 0
          ? <p className="no-results">No career stats found.</p>
          : <CareerStatsTable rows={results} />
      )}

      {intent === 'prediction' && <PredictionDisplay text={analysis} />}
    </div>
  )
}
