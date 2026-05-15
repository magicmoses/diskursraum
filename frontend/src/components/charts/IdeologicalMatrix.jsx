import { useEffect, useMemo, useState } from 'react'
import { TOOLTIP_STYLE } from '../../constants/colors'
import { getCategoryDistribution } from '../../api/client'
import InfoIcon from '../ui/InfoIcon'

const YEARS   = [2005, 2009, 2013, 2017, 2021, 2025]
const PARTIES = ['cdu_csu', 'spd', 'gruene', 'fdp', 'afd', 'linke']

const PARTY_HEX = {
  cdu_csu: '#2C2C2C', spd: '#E3000F', gruene: '#64A12D',
  fdp: '#FFCC00', afd: '#009EE0', linke: '#BE3075',
}
const SHORT = {
  cdu_csu: 'CDU/CSU', spd: 'SPD', gruene: 'Grüne',
  fdp: 'FDP', afd: 'AfD', linke: 'Linke',
}

// ManifestoBERTa code → axis weights
const WEIGHTS = {
  // Economy left (-1)
  '403': { x: -1 }, '404': { x: -1 }, '405': { x: -1 }, '406': { x: -1 },
  '408': { x: -1 }, '503': { x: -1 }, '504': { x: -1 }, '506': { x: -1 },
  '701': { x: -1 },
  // Economy right (+1)
  '401': { x: 1 }, '402': { x: 1 }, '407': { x: 1 }, '409': { x: 1 },
  '410': { x: 1 }, '505': { x: 1 }, '702': { x: 1 },
  // Society progressive (+1)
  '201': { y: 1 }, '202': { y: 1 }, '204': { y: 1 }, '501': { y: 1 },
  '602': { y: 1 }, '604': { y: 1 }, '704': { y: 1 }, '705': { y: 1 }, '706': { y: 1 },
  // Society conservative (-1)
  '601': { y: -1 }, '603': { y: -1 }, '605': { y: -1 }, '607': { y: -1 }, '608': { y: -1 },
  // External relations
  '104': { x: 1, y: -1 }, '101': { x: 1 },
  '105': { y: 1 }, '107': { y: 1 }, '108': { y: 1 },
  '102': { y: 1 }, '103': { y: 1 },
}

function extractCode(key) {
  const m = key.match(/^(\d+)/)
  return m ? m[1] : null
}

function computeScore(distribution) {
  let x = 0, y = 0
  if (!distribution) return { x: 0, y: 0 }
  for (const [key, val] of Object.entries(distribution)) {
    const code = extractCode(key)
    if (!code) continue
    const w = WEIGHTS[code]
    if (!w) continue
    const pct = val.pct ?? 0
    x += (w.x ?? 0) * pct
    y += (w.y ?? 0) * pct
  }
  return { x, y }
}

const W = 680, H = 420
const PAD = { top: 36, right: 90, bottom: 48, left: 90 }
const plotW = W - PAD.left - PAD.right
const plotH = H - PAD.top - PAD.bottom

function toSVG(nx, ny) {
  return [
    PAD.left + ((nx + 1) / 2) * plotW,
    PAD.top  + ((1 - ny) / 2) * plotH,
  ]
}

export default function IdeologicalMatrix() {
  const [catData, setCatData] = useState({})
  const [viewYear, setViewYear] = useState(2025)
  const [tooltip, setTooltip] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    Promise.all(YEARS.map(y =>
      getCategoryDistribution(y)
        .then(d => ({ year: y, d }))
        .catch(() => ({ year: y, d: null }))
    )).then(results => {
      const map = {}
      results.forEach(({ year, d }) => { if (d) map[year] = d })
      setCatData(map)
      setReady(true)
    })
  }, [])

  const scores = useMemo(() => {
    const result = {}
    YEARS.forEach(y => {
      result[y] = {}
      const yd = catData[y]
      if (!yd) return
      PARTIES.forEach(p => {
        const dist = yd.parties?.[p]?.distribution?.distribution
        result[y][p] = computeScore(dist)
      })
    })
    return result
  }, [catData])

  // Min-max normalise across all parties × all years
  const allX = PARTIES.flatMap(p => YEARS.map(y => scores[y]?.[p]?.x ?? null)).filter(v => v !== null)
  const allY = PARTIES.flatMap(p => YEARS.map(y => scores[y]?.[p]?.y ?? null)).filter(v => v !== null)
  const xMin = allX.length ? Math.min(...allX) : -1
  const xMax = allX.length ? Math.max(...allX) :  1
  const yMin = allY.length ? Math.min(...allY) : -1
  const yMax = allY.length ? Math.max(...allY) :  1
  const xRange = xMax - xMin || 1
  const yRange = yMax - yMin || 1

  function norm(score) {
    return {
      nx: ((score.x - xMin) / xRange) * 2 - 1,
      ny: ((score.y - yMin) / yRange) * 2 - 1,
    }
  }

  const presentParties = PARTIES.filter(p => !(p === 'afd' && viewYear < 2013))
  const yearScores = scores[viewYear] ?? {}

  return (
    <div>
      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: 'var(--space-3)', alignItems: 'center' }}>
        {YEARS.map(y => (
          <button
            key={y}
            onClick={() => setViewYear(y)}
            style={{
              padding: '3px 10px', background: 'none', border: 'none',
              borderBottom: viewYear === y ? '2px solid var(--signal)' : '2px solid transparent',
              color: viewYear === y ? 'var(--text-primary)' : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
              cursor: 'pointer', transition: 'color 150ms, border-color 150ms',
            }}
          >
            {y}
          </button>
        ))}
        <InfoIcon text="Berechnet aus der Verteilung politischer Themenschwerpunkte in den Wahlprogrammen gemäß ManifestoBERTa-Klassifikation. Je weiter rechts eine Partei, desto stärker marktwirtschaftlich orientiert. Je weiter oben, desto progressiver in gesellschaftlichen Fragen." />
      </div>

      {!ready ? (
        <div style={{ height: '420px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
          Lade Kategoriedaten…
        </div>
      ) : (
        <div style={{ position: 'relative' }}>
          <svg
            viewBox={`0 0 ${W} ${H}`}
            style={{ width: '100%', height: 'auto', display: 'block', background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
          >
            {/* Grid lines */}
            <line x1={PAD.left} y1={PAD.top + plotH / 2} x2={W - PAD.right} y2={PAD.top + plotH / 2}
              stroke="#D8D0C4" strokeDasharray="4 4" />
            <line x1={PAD.left + plotW / 2} y1={PAD.top} x2={PAD.left + plotW / 2} y2={H - PAD.bottom}
              stroke="#D8D0C4" strokeDasharray="4 4" />

            {/* Axes */}
            <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom} stroke="#C8BFB0" />
            <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={H - PAD.bottom} stroke="#C8BFB0" />

            {/* Axis labels */}
            <text x={W / 2} y={H - 6} textAnchor="middle" fill="#7A6E64" fontFamily="var(--font-mono)" fontSize="10">
              ← Staatlich/Sozial — Marktwirtschaftlich →
            </text>
            <text x={10} y={H / 2} textAnchor="middle" fill="#7A6E64" fontFamily="var(--font-mono)" fontSize="10"
              transform={`rotate(-90, 10, ${H / 2})`}>
              ← Konservativ — Progressiv →
            </text>

            {/* Dots + labels */}
            {presentParties.map(p => {
              const score = yearScores[p]
              if (!score) return null
              const { nx, ny } = norm(score)
              const [sx, sy] = toSVG(nx, ny)
              const labelX = sx + 12
              const labelY = sy + 4
              return (
                <g key={p}>
                  <circle cx={sx} cy={sy} r={9} fill={PARTY_HEX[p]} fillOpacity={0.9}
                    stroke="#C8BFB0" strokeWidth={1.5} style={{ cursor: 'default' }}
                    onMouseEnter={e => setTooltip({ x: e.clientX, y: e.clientY, p, score })}
                    onMouseMove={e => setTooltip(t => t ? { ...t, x: e.clientX, y: e.clientY } : null)}
                    onMouseLeave={() => setTooltip(null)}
                  />
                  <text x={labelX} y={labelY} fill={PARTY_HEX[p]}
                    fontFamily="var(--font-mono)" fontSize="11" fillOpacity={0.9}>
                    {SHORT[p]}
                  </text>
                </g>
              )
            })}
          </svg>

          {tooltip && (
            <div style={{
              ...TOOLTIP_STYLE, position: 'fixed',
              left: tooltip.x + 12, top: tooltip.y - 8,
              padding: 'var(--space-2) var(--space-3)',
              pointerEvents: 'none', zIndex: 200,
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', lineHeight: 1.7,
            }}>
              {SHORT[tooltip.p]} — {viewYear}<br />
              Wirtschaft: {tooltip.score.x.toFixed(1)}<br />
              Gesellschaft: {tooltip.score.y.toFixed(1)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
