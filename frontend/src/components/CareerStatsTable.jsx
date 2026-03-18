import './Table.css'

const HEADERS = {
  SEASON_ID: 'Season',
  TEAM_ABBREVIATION: 'Team',
  GP: 'GP',
  GS: 'GS',
  MIN: 'MIN',
  PTS: 'PTS',
  REB: 'REB',
  AST: 'AST',
  STL: 'STL',
  BLK: 'BLK',
  TOV: 'TOV',
  FG_PCT: 'FG%',
  FG3_PCT: '3P%',
  FT_PCT: 'FT%',
}

function fmt(key, val) {
  if (val == null) return '—'
  if (['FG_PCT', 'FG3_PCT', 'FT_PCT'].includes(key)) {
    return (val * 100).toFixed(1) + '%'
  }
  if (['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'MIN'].includes(key)) {
    return typeof val === 'number' ? val.toFixed(1) : val
  }
  return val
}

export default function CareerStatsTable({ rows }) {
  if (!rows.length) return null
  const keys = Object.keys(rows[0]).filter(k => k in HEADERS)

  return (
    <div className="table-scroll">
      <table className="stats-table">
        <thead>
          <tr>
            {keys.map(k => <th key={k}>{HEADERS[k]}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {keys.map(k => (
                <td key={k} className={k === 'PTS' ? 'highlight' : ''}>
                  {fmt(k, row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
