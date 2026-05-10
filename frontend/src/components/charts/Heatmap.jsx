import { useState } from 'react'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'

const PARTIES = ['cdu_csu', 'spd', 'gruene', 'fdp', 'afd', 'linke']

const YEARS = [2005, 2009, 2013, 2017, 2021, 2025]

const TOPIC_LABELS = {
  migration:        'Migration',
  energy_transition:'Energiewende',
  retirement:       'Rente',
  digitalization:   'Digitalisierung',
  work_transition:  'Arbeit',
  defense:          'Verteidigung',
  family_children:  'Familie',
  education:        'Bildung',
}

const SHORT = {
  cdu_csu: 'CDU',
  spd:     'SPD',
  gruene:  'Grüne',
  fdp:     'FDP',
  afd:     'AfD',
  linke:   'Linke',
}

// distance_matrices keys are sorted "p1__p2"
function pairKey(a, b) { return [a, b].sort().join('__') }

function buildMatrix(dist, parties) {
  return parties.map(r => parties.map(c => r === c ? 1.0 : (dist[pairKey(r, c)] ?? null)))
}

// Interpolates patina (low) → signal (high) similarity
function cellBg(val, min, max) {
  if (val === null) return 'transparent'
  if (val === 1.0)  return 'var(--bg-elevated)'
  const t = (val - min) / (max - min || 1)
  // amber-subtle at t=0, patina-subtle at t=1
  const r = Math.round(74  + (196 - 74)  * (1 - t))
  const g = Math.round(124 + (120 - 124) * (1 - t))
  const b = Math.round(111 + (26  - 111) * (1 - t))
  return `rgba(${r},${g},${b},${0.12 + t * 0.48})`
}

export default function Heatmap({ data, year: initialYear = 2025 }) {
  const [hovered, setHovered]   = useState(null)
  const [tooltip, setTooltip]   = useState(null)
  const [activeTopic, setTopic] = useState(null)
  const [year, setYear]         = useState(initialYear)

  const yearKey = String(year)

  const presentParties = PARTIES.filter(p => !(p === 'afd' && year < 2013))

  let dist = data?.distance_matrices?.[yearKey] ?? {}

  if (activeTopic) {
    const sub = data?.graphs_by_year?.[yearKey]?.topic_subgraphs?.[activeTopic]
    if (sub?.edges) {
      dist = {}
      sub.edges.forEach(e => { dist[pairKey(e.source, e.target)] = e.weight })
    }
  }

  const matrix   = buildMatrix(dist, presentParties)
  const allVals  = matrix.flat().filter(v => v !== null && v !== 1.0)
  const rangeMin = allVals.length ? Math.min(...allVals) : 0.94
  const rangeMax = allVals.length ? Math.max(...allVals) : 1.0

  const CELL = 68
  const LABEL_W = 78

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: '4px', marginBottom: 'var(--space-3)', flexWrap: 'wrap' }}>
        {YEARS.map(y => (
          <button
            key={y}
            onClick={() => setYear(y)}
            style={{
              padding: '3px 10px', background: 'none', border: 'none',
              borderBottom: year === y ? '2px solid var(--signal)' : '2px solid transparent',
              color: year === y ? 'var(--text-primary)' : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
              cursor: 'pointer', transition: 'color 150ms, border-color 150ms',
            }}
          >
            {y}
          </button>
        ))}
      </div>
      {/* Topic switcher */}
      <div style={{ display: 'flex', gap: '1px', marginBottom: 'var(--space-3)', background: 'var(--border)', flexWrap: 'wrap' }}>
        {[{ id: null, label: 'Gesamt' }, ...Object.entries(TOPIC_LABELS).map(([id, label]) => ({ id, label }))].map(({ id, label }) => (
          <button
            key={id ?? 'all'}
            onClick={() => setTopic(id)}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: activeTopic === id ? 'var(--bg-elevated)' : 'var(--bg-surface)',
              border: 'none',
              color: activeTopic === id ? 'var(--text-primary)' : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--text-xs)',
              cursor: 'pointer',
              transition: 'background 100ms',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div style={{ overflowX: 'auto' }}>
        {/* Column headers */}
        <div style={{ display: 'flex', paddingLeft: `${LABEL_W}px`, marginBottom: '2px' }}>
          {presentParties.map(p => (
            <div key={p} style={{
              width: `${CELL}px`, flexShrink: 0, textAlign: 'center',
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)',
              paddingBottom: 'var(--space-1)',
            }}>
              {SHORT[p]}
            </div>
          ))}
        </div>

        {/* Rows */}
        {presentParties.map((row, ri) => (
          <div key={row} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{
              width: `${LABEL_W}px`, flexShrink: 0, textAlign: 'right',
              paddingRight: 'var(--space-2)',
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            }}>
              {SHORT[row]}
            </div>
            {presentParties.map((col, ci) => {
              const val = matrix[ri][ci]
              const isHighlighted = hovered && (hovered[0] === ri || hovered[1] === ci)
              return (
                <div
                  key={col}
                  onMouseEnter={e => {
                    setHovered([ri, ci])
                    if (val !== null && val !== 1.0) {
                      setTooltip({ x: e.clientX, y: e.clientY, row, col, val })
                    }
                  }}
                  onMouseMove={e => setTooltip(t => t ? { ...t, x: e.clientX, y: e.clientY } : null)}
                  onMouseLeave={() => { setHovered(null); setTooltip(null) }}
                  style={{
                    width: `${CELL}px`, height: `${CELL}px`, flexShrink: 0,
                    background: cellBg(val, rangeMin, rangeMax),
                    border: `1px solid ${isHighlighted ? 'var(--border-hover)' : 'var(--border-subtle)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontFamily: 'var(--font-mono)', fontSize: '10px',
                    color: val === 1.0 ? 'var(--text-muted)' : 'var(--text-secondary)',
                    transition: 'border-color 80ms',
                    cursor: 'default',
                  }}
                >
                  {val !== null ? val.toFixed(3) : '—'}
                </div>
              )
            })}
          </div>
        ))}
      </div>

      {tooltip?.val != null && (
        <div style={{
          ...TOOLTIP_STYLE,
          position: 'fixed',
          left: tooltip.x + 12, top: tooltip.y - 8,
          padding: 'var(--space-2) var(--space-3)',
          pointerEvents: 'none', zIndex: 200,
          lineHeight: 1.6,
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
            {PARTY_NAMES[tooltip.row]} – {PARTY_NAMES[tooltip.col]}<br />
            Ähnlichkeit: {tooltip.val.toFixed(4)}
          </span>
        </div>
      )}
    </div>
  )
}
