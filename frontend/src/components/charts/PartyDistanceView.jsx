import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'
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

const TOPIC_IDS = ['migration', 'energy_transition', 'retirement', 'digitalization', 'work_transition', 'defense', 'family_children', 'education']

function pairKey(a, b) { return [a, b].sort().join('__') }

function getPairScore(data, year, topic, a, b) {
  const yk = String(year)
  const key = pairKey(a, b)
  if (topic) {
    const edges = data?.graphs_by_year?.[yk]?.topic_subgraphs?.[topic]?.edges
    if (edges) {
      const edge = edges.find(e => pairKey(e.source, e.target) === key)
      if (edge != null) return edge.weight
    }
  }
  return data?.distance_matrices?.[yk]?.[key] ?? 0
}

const W = 640, H = 400
const cx = W / 2, cy = H / 2
const MAX_R = 155

export default function PartyDistanceView({ data }) {
  const { t } = useTranslation()
  const [center, setCenter] = useState('cdu_csu')
  const [year, setYear]     = useState(2025)
  const [topic, setTopic]   = useState(null)
  const [tooltip, setTooltip] = useState(null)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    if (!playing) return
    let idx = YEARS.indexOf(year)
    const timer = setInterval(() => {
      idx = (idx + 1) % YEARS.length
      setYear(YEARS[idx])
      if (idx === YEARS.length - 1) setPlaying(false)
    }, 2500)
    return () => clearInterval(timer)
  }, [playing, year])

  const others = PARTIES.filter(p => {
    if (p === center) return false
    if (p === 'afd' && year < 2013) return false
    return true
  })

  const positions = others.map((p, i) => {
    const score = getPairScore(data, year, topic, center, p)
    const dist  = 1 - score
    const angle = (2 * Math.PI * i / others.length) - Math.PI / 2
    return {
      id: p,
      x: cx + dist * MAX_R * Math.cos(angle),
      y: cy + dist * MAX_R * Math.sin(angle),
      score,
    }
  })

  return (
    <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'flex-start' }}>
      {/* Party selector */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flexShrink: 0, paddingTop: 'var(--space-2)' }}>
        {PARTIES.map(p => (
          <button
            key={p}
            onClick={() => setCenter(p)}
            style={{
              padding: '5px 10px',
              background: center === p ? `${PARTY_HEX[p]}22` : 'none',
              border: `1px solid ${center === p ? PARTY_HEX[p] : 'var(--border)'}`,
              color: center === p ? PARTY_HEX[p] : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
              cursor: 'pointer', transition: 'all 150ms', whiteSpace: 'nowrap',
            }}
          >
            {SHORT[p]}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Controls */}
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
          <div style={{ display: 'flex', gap: '4px' }}>
            {YEARS.map(y => (
              <button
                key={y}
                onClick={() => { setPlaying(false); setYear(y) }}
                style={{
                  padding: '3px 8px', background: 'none', border: 'none',
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
          <button
            onClick={() => { setPlaying(p => !p); if (!playing) setYear(YEARS[0]) }}
            style={{
              padding: '3px 10px',
              background: playing ? 'var(--bg-elevated)' : 'none',
              border: '1px solid var(--border)',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
              cursor: 'pointer',
            }}
          >
            {playing ? t('distance.stop') : t('distance.play')}
          </button>
        </div>

        {/* Topic filter */}
        <div style={{ display: 'flex', gap: '1px', marginBottom: 'var(--space-3)', background: 'var(--border)', flexWrap: 'wrap' }}>
          {[{ id: null, label: t('topic.all') }, ...TOPIC_IDS.map(id => ({ id, label: t(`topic.${id}`) }))].map(({ id, label }) => (
            <button
              key={id ?? 'all'}
              onClick={() => setTopic(id)}
              style={{
                padding: '3px var(--space-3)',
                background: topic === id ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                border: 'none',
                color: topic === id ? 'var(--text-primary)' : 'var(--text-muted)',
                fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
                cursor: 'pointer', transition: 'background 100ms',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* SVG */}
        <div style={{ position: 'relative' }}>
          <svg
            viewBox={`0 0 ${W} ${H}`}
            style={{ width: '100%', height: 'auto', display: 'block', background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
          >
            {/* Distance rings */}
            {[0.33, 0.67, 1].map(t => (
              <circle key={t} cx={cx} cy={cy} r={t * MAX_R}
                fill="none" stroke="#D8D0C4" strokeWidth={1} opacity={0.6} />
            ))}

            {/* Connector lines */}
            {positions.map(pos => (
              <line key={pos.id}
                x1={cx} y1={cy} x2={pos.x} y2={pos.y}
                stroke={PARTY_HEX[pos.id]} strokeWidth={1 + pos.score * 3}
                strokeOpacity={0.25}
              />
            ))}

            {/* Other party nodes */}
            {positions.map(pos => (
              <g key={pos.id}>
                <circle cx={pos.x} cy={pos.y} r={12}
                  fill={PARTY_HEX[pos.id]} fillOpacity={0.9}
                  stroke="#C8BFB0" strokeWidth={1.5}
                  style={{ cursor: 'default' }}
                  onMouseEnter={e => setTooltip({ x: e.clientX, y: e.clientY, id: pos.id, score: pos.score })}
                  onMouseMove={e => setTooltip(t => t ? { ...t, x: e.clientX, y: e.clientY } : null)}
                  onMouseLeave={() => setTooltip(null)}
                />
                <text x={pos.x} y={pos.y + 26} textAnchor="middle"
                  fill={PARTY_HEX[pos.id]} fontFamily="var(--font-mono)" fontSize="10">
                  {SHORT[pos.id]}
                </text>
              </g>
            ))}

            {/* Center party */}
            <circle cx={cx} cy={cy} r={20}
              fill={PARTY_HEX[center]} fillOpacity={0.95}
              stroke="#C8BFB0" strokeWidth={2}
            />
            <text x={cx} y={cy + 5} textAnchor="middle"
              fill="#F5F0E8" fontFamily="var(--font-mono)" fontSize="11" fontWeight="bold">
              {SHORT[center]}
            </text>

            {/* Legend */}
            <text x={8} y={H - 8}
              fill="#7A6E64" fontFamily="var(--font-mono)" fontSize="9">
              {t('distance.closer')}
            </text>
          </svg>

          {tooltip && (
            <div style={{
              ...TOOLTIP_STYLE, position: 'fixed',
              left: tooltip.x + 12, top: tooltip.y - 8,
              padding: 'var(--space-2) var(--space-3)',
              pointerEvents: 'none', zIndex: 200,
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', lineHeight: 1.7,
            }}>
              {SHORT[center]} – {SHORT[tooltip.id]}<br />
              {t('distance.similarity')}: {tooltip.score.toFixed(3)}<br />
              <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                {topic ? t(`topic.${topic}`) : t('topic.all')} · {year}
              </span>
            </div>
          )}
        </div>

        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
          <InfoIcon text="Die Abstände zeigen wie ähnlich sich die Parteien in ihren Wahlprogrammen zu diesem Thema sind — berechnet aus semantischer Nähe und inhaltlichen Schwerpunkten." />
          <span>{t('distance.caption')}</span>
        </div>
      </div>
    </div>
  )
}
