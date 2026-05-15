import { useState, useEffect, useRef, useCallback } from 'react'
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'
import { InfoIcon } from '../ui'

const PARTY_HEX = {
  cdu_csu: '#2C2C2C',
  spd:     '#E3000F',
  gruene:  '#64A12D',
  fdp:     '#FFCC00',
  afd:     '#009EE0',
  linke:   '#BE3075',
}

const PARTY_SHORT = {
  cdu_csu: 'CDU/CSU',
  spd:     'SPD',
  gruene:  'Grüne',
  fdp:     'FDP',
  afd:     'AfD',
  linke:   'Linke',
}

const PARTIES = ['cdu_csu', 'spd', 'gruene', 'fdp', 'linke', 'afd']
const YEARS   = [2005, 2009, 2013, 2017, 2021, 2025]

const TOPIC_OPTIONS = [
  { id: 'all',               label: 'Alle Themen' },
  { id: 'migration',         label: 'Migration' },
  { id: 'energy_transition', label: 'Energiewende' },
  { id: 'retirement',        label: 'Rente' },
  { id: 'digitalization',    label: 'Digitalisierung' },
  { id: 'work_transition',   label: 'Arbeit & Wandel' },
  { id: 'defense',           label: 'Verteidigung' },
  { id: 'family_children',   label: 'Familie & Kinder' },
  { id: 'education',         label: 'Bildung' },
]

function pairKey(a, b) {
  return [a, b].sort().join('__')
}

function getDistance(data, year, refParty, otherParty, topic) {
  if ((refParty === 'afd' || otherParty === 'afd') && year < 2013) return null
  const y = String(year)
  if (topic === 'all') {
    const sim = data.distance_matrices?.[y]?.[pairKey(refParty, otherParty)]
    return sim != null ? +(1 - sim).toFixed(3) : null
  }
  const edges = data.graphs_by_year?.[y]?.topic_subgraphs?.[topic]?.edges ?? []
  const edge  = edges.find(e =>
    (e.source === refParty && e.target === otherParty) ||
    (e.source === otherParty && e.target === refParty)
  )
  return edge != null ? +(1 - edge.weight).toFixed(3) : null
}

const selectStyle = {
  background:  'var(--bg-surface)',
  border:      '1px solid var(--border)',
  borderRadius:'4px',
  color:       'var(--text-primary)',
  fontFamily:  'var(--font-mono)',
  fontSize:    'var(--text-xs)',
  padding:     '4px 8px',
  cursor:      'pointer',
}

export default function PartyTrajectory({ data, selectedYear }) {
  const [refParty, setRefParty] = useState('spd')
  const [topic,    setTopic]    = useState('all')
  const [playing,  setPlaying]  = useState(false)
  const [activeYear, setActiveYear] = useState(selectedYear ?? 2025)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (selectedYear != null) setActiveYear(selectedYear)
  }, [selectedYear])

  const stopPlay = useCallback(() => {
    clearInterval(intervalRef.current)
    setPlaying(false)
  }, [])

  const startPlay = useCallback(() => {
    setPlaying(true)
    let idx = YEARS.indexOf(activeYear)
    intervalRef.current = setInterval(() => {
      idx = (idx + 1) % YEARS.length
      setActiveYear(YEARS[idx])
    }, 1500)
  }, [activeYear])

  useEffect(() => () => clearInterval(intervalRef.current), [])

  const others = PARTIES.filter(p => p !== refParty)

  const chartData = YEARS.map(year => {
    const point = { year }
    for (const p of others) {
      point[p] = getDistance(data, year, refParty, p, topic)
    }
    return point
  })

  const activeRow = chartData.find(r => r.year === activeYear) ?? {}
  const scored    = others.map(p => ({ p, d: activeRow[p] })).filter(x => x.d != null)
  const closest   = scored.length ? scored.reduce((a, b) => a.d < b.d ? a : b) : null
  const farthest  = scored.length ? scored.reduce((a, b) => a.d > b.d ? a : b) : null

  return (
    <div>
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-4)', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>Referenzpartei</span>
          <select value={refParty} onChange={e => { stopPlay(); setRefParty(e.target.value) }} style={selectStyle}>
            {PARTIES.map(p => <option key={p} value={p}>{PARTY_SHORT[p]}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>Thema</span>
          <select value={topic} onChange={e => { stopPlay(); setTopic(e.target.value) }} style={selectStyle}>
            {TOPIC_OPTIONS.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </div>
        <button
          onClick={playing ? stopPlay : startPlay}
          style={{ ...selectStyle, padding: '4px 12px', marginLeft: 'auto' }}
        >
          {playing ? '⏹ Stop' : '▶ Play'}
        </button>
        <InfoIcon text="Semantische Distanz zwischen zwei Parteien in ihren Wahlprogrammen — berechnet aus ManifestoBERTa-Embeddings. 0 = identische Positionen, 1 = maximale Distanz. AfD erst ab 2013 verfügbar." />
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 8, right: 20, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#D8D0C4" />
          <XAxis
            dataKey="year"
            type="number"
            domain={[2003, 2027]}
            ticks={YEARS}
            tick={{ fill: '#7A6E64', fontFamily: 'var(--font-mono)', fontSize: 11 }}
            axisLine={{ stroke: '#C8BFB0' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            tickCount={6}
            tickFormatter={v => v.toFixed(1)}
            tick={{ fill: '#7A6E64', fontFamily: 'var(--font-mono)', fontSize: 11 }}
            axisLine={{ stroke: '#C8BFB0' }}
            tickLine={false}
            label={{ value: 'Distanz', angle: -90, position: 'insideLeft', offset: 14, style: { fill: '#7A6E64', fontFamily: 'var(--font-mono)', fontSize: 10 } }}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(val, name) => [val != null ? val.toFixed(3) : '–', PARTY_SHORT[name] ?? name]}
            labelFormatter={y => `Wahl ${y}`}
          />
          <ReferenceLine x={activeYear} stroke="var(--signal)" strokeWidth={1.5} strokeDasharray="4 2" label={{ value: activeYear, position: 'top', style: { fill: 'var(--signal)', fontFamily: 'var(--font-mono)', fontSize: 10 } }} />
          {others.map(p => (
            <Line
              key={p}
              type="monotone"
              dataKey={p}
              stroke={PARTY_HEX[p]}
              strokeWidth={2}
              dot={{ r: 3, fill: PARTY_HEX[p], stroke: 'var(--bg-primary)', strokeWidth: 1 }}
              activeDot={{ r: 5 }}
              connectNulls={false}
              name={p}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', marginTop: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
        {others.map(p => (
          <div key={p} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: 14, height: 3, background: PARTY_HEX[p], borderRadius: 1 }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              {PARTY_SHORT[p]}
            </span>
          </div>
        ))}
      </div>

      {closest && farthest && closest.p !== farthest.p && (
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          {activeYear}: {PARTY_SHORT[refParty]} am nächsten zu{' '}
          <span style={{ color: PARTY_HEX[closest.p] }}>{PARTY_SHORT[closest.p]}</span>
          {' '}(Distanz {closest.d.toFixed(2)}), am weitesten von{' '}
          <span style={{ color: PARTY_HEX[farthest.p] }}>{PARTY_SHORT[farthest.p]}</span>
          {' '}(Distanz {farthest.d.toFixed(2)}).
        </div>
      )}
    </div>
  )
}
