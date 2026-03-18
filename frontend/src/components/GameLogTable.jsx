import './Table.css'

const HEADERS = {
  GAME_DATE: 'Date',
  MATCHUP: 'Matchup',
  WL: 'W/L',
  MIN: 'MIN',
  PTS: 'PTS',
  AST: 'AST',
  REB: 'REB',
  STL: 'STL',
  BLK: 'BLK',
  FG3M: '3PM',
  FG3A: '3PA',
  FG_PCT: 'FG%',
  FG3_PCT: '3P%',
  FT_PCT: 'FT%',
}

function fmt(key, val) {
  if (val == null) return '—'
  if (['FG_PCT', 'FG3_PCT', 'FT_PCT'].includes(key)) {
    return (val * 100).toFixed(1) + '%'
  }
  if (key === 'MIN') return typeof val === 'string' ? val.split(':')[0] : val
  return val
}

export default function GameLogTable({ rows }) {
  if (!rows.length) return null
  const keys = Object.keys(HEADERS).filter(k => k in rows[0])

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
            <tr key={i} className={row.WL === 'W' ? 'win' : 'loss'}>
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
