import { useState } from 'react'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'

const PARTY_HEX = {
  cdu_csu: '#E8E8E8',
  spd:     '#E3000F',
  gruene:  '#1AA037',
  fdp:     '#FFED00',
  afd:     '#009EE0',
  linke:   '#BE3075',
}

const PARTIES = ['cdu_csu', 'spd', 'gruene', 'fdp', 'linke', 'afd']

const W = 680, H = 420
const PAD = { top: 28, right: 64, bottom: 44, left: 48 }
const plotW = W - PAD.left - PAD.right
const plotH = H - PAD.top - PAD.bottom

const DOMAIN = [-1.15, 1.15]

function toSVG(x, y) {
  const sx = PAD.left + ((x - DOMAIN[0]) / (DOMAIN[1] - DOMAIN[0])) * plotW
  const sy = PAD.top  + ((DOMAIN[1] - y) / (DOMAIN[1] - DOMAIN[0])) * plotH
  return [sx, sy]
}

export default function PCAScatter({ data, viewYear }) {
  const [tooltip, setTooltip] = useState(null)

  if (!data?.pca_trajectories?.trajectories) return (
    <div style={{ height: '420px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      Keine PCA-Daten
    </div>
  )

  const { trajectories, explained_variance } = data.pca_trajectories
  const [ev1, ev2] = explained_variance ?? [0, 0]

  const ticks = [-1, -0.5, 0, 0.5, 1]
  const [ox, oy] = toSVG(0, 0)

  return (
    <div style={{ position: 'relative' }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: '100%', height: 'auto', display: 'block', background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
      >
        {/* Grid */}
        <line x1={PAD.left} y1={oy} x2={W - PAD.right} y2={oy} stroke="#2C2E32" strokeDasharray="4 4" />
        <line x1={ox} y1={PAD.top} x2={ox} y2={H - PAD.bottom} stroke="#2C2E32" strokeDasharray="4 4" />

        {/* Axes */}
        <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom} stroke="#2C2E32" />
        <line x1={PAD.left} y1={PAD.top}         x2={PAD.left}      y2={H - PAD.bottom} stroke="#2C2E32" />

        {/* X ticks + labels */}
        {ticks.map(t => {
          const [sx] = toSVG(t, 0)
          return (
            <g key={`xt-${t}`}>
              <line x1={sx} y1={H - PAD.bottom} x2={sx} y2={H - PAD.bottom + 4} stroke="#52504E" />
              <text x={sx} y={H - PAD.bottom + 14} textAnchor="middle" fill="#52504E" fontFamily="var(--font-mono)" fontSize="10">{t}</text>
            </g>
          )
        })}

        {/* Y ticks + labels */}
        {ticks.map(t => {
          const [, sy] = toSVG(0, t)
          return (
            <g key={`yt-${t}`}>
              <line x1={PAD.left - 4} y1={sy} x2={PAD.left} y2={sy} stroke="#52504E" />
              <text x={PAD.left - 6} y={sy + 4} textAnchor="end" fill="#52504E" fontFamily="var(--font-mono)" fontSize="10">{t}</text>
            </g>
          )
        })}

        {/* Axis labels */}
        <text x={W / 2} y={H - 4} textAnchor="middle" fill="#52504E" fontFamily="var(--font-mono)" fontSize="11">
          {`PC1 (${(ev1 * 100).toFixed(1)}%)`}
        </text>
        <text x={12} y={H / 2} textAnchor="middle" fill="#52504E" fontFamily="var(--font-mono)" fontSize="11"
          transform={`rotate(-90, 12, ${H / 2})`}>
          {`PC2 (${(ev2 * 100).toFixed(1)}%)`}
        </text>

        {/* Trajectory lines */}
        {PARTIES.map(party => {
          const pts = trajectories[party]
          if (!pts || pts.length < 2) return null
          const d = pts.map((p, i) => {
            const [sx, sy] = toSVG(p.x, p.y)
            return `${i === 0 ? 'M' : 'L'}${sx},${sy}`
          }).join(' ')
          return (
            <path key={`l-${party}`} d={d} fill="none"
              stroke={PARTY_HEX[party]} strokeWidth="1" strokeOpacity="0.22" />
          )
        })}

        {/* Dots */}
        {PARTIES.map(party => {
          const pts = trajectories[party]
          if (!pts) return null
          return pts.map(p => {
            const [sx, sy] = toSVG(p.x, p.y)
            const isSel = viewYear !== null && p.year === viewYear
            const isAll = viewYear === null
            const opacity = isAll ? 0.55 : (isSel ? 1 : 0.22)
            const radius  = isAll ? 5 : (isSel ? 8 : 4)
            return (
              <circle
                key={`d-${party}-${p.year}`}
                cx={sx} cy={sy}
                r={radius}
                fill={PARTY_HEX[party]}
                fillOpacity={opacity}
                stroke={PARTY_HEX[party]}
                strokeWidth={isSel ? 2 : 0.5}
                style={{ cursor: 'default' }}
                onMouseEnter={e => setTooltip({ x: e.clientX, y: e.clientY, party, year: p.year, px: p.x, py: p.y })}
                onMouseMove={e => setTooltip(t => t ? { ...t, x: e.clientX, y: e.clientY } : null)}
                onMouseLeave={() => setTooltip(null)}
              />
            )
          })
        })}

        {/* Labels at selected year or all years */}
        {PARTIES.map(party => {
          const pts = trajectories[party]
          const targetYear = viewYear ?? Math.max(...(pts?.map(p => p.year) ?? []))
          const p = pts?.find(pp => pp.year === targetYear)
          if (!p) return null
          const [sx, sy] = toSVG(p.x, p.y)
          const short = party === 'cdu_csu' ? 'CDU/CSU' : party === 'gruene' ? 'Grüne' : party === 'linke' ? 'Linke' : party.toUpperCase()
          return (
            <text key={`lbl-${party}`} x={sx + 11} y={sy + 4}
              fill={PARTY_HEX[party]} fontFamily="var(--font-mono)" fontSize="11"
              fillOpacity={viewYear === null ? 0.7 : 0.9}>
              {short}
            </text>
          )
        })}
      </svg>

      {tooltip && (
        <div style={{
          ...TOOLTIP_STYLE,
          position: 'fixed',
          left: tooltip.x + 12, top: tooltip.y - 8,
          padding: 'var(--space-2) var(--space-3)',
          pointerEvents: 'none', zIndex: 200,
          fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', lineHeight: 1.7,
        }}>
          {PARTY_NAMES[tooltip.party]} — {tooltip.year}<br />
          x: {tooltip.px.toFixed(3)}, y: {tooltip.py.toFixed(3)}
        </div>
      )}
    </div>
  )
}
