import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'
import InfoIcon from '../ui/InfoIcon'

const PARTY_HEX = {
  cdu_csu: '#E8E8E8',
  spd:     '#E3000F',
  gruene:  '#1AA037',
  fdp:     '#FFED00',
  afd:     '#009EE0',
  linke:   '#BE3075',
}

const STABLE = ['cdu_csu', 'spd', 'gruene', 'fdp', 'linke']
const YEARS  = [2005, 2009, 2013, 2017, 2021, 2025]

const EVENT_STROKE = {
  politics: '#8B9BAF', economy: '#C4781A', energy: '#4A7C6F',
  climate: '#6BA898', foreign: '#8A8885', migration: '#E8A84A',
  health: '#52504E', digital: '#B8C4D0',
}

const SHORT = { cdu_csu: 'CDU/CSU', spd: 'SPD', gruene: 'Grüne', fdp: 'FDP', linke: 'Linke', afd: 'AfD' }

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ ...TOOLTIP_STYLE, padding: 'var(--space-2) var(--space-3)', lineHeight: 1.8 }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginBottom: '4px' }}>
        Wahl {label}
      </div>
      {[...payload].sort((a, b) => (b.value ?? 0) - (a.value ?? 0)).map(p => (
        <div key={p.dataKey} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <div style={{ width: '8px', height: '2px', background: PARTY_HEX[p.dataKey], flexShrink: 0 }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
            {SHORT[p.dataKey]}: {p.value?.toFixed(4) ?? '—'}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function BridgingTimeline({ data }) {
  if (!data?.bridging_timeseries) return (
    <div style={{ height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      Keine Zeitreihe
    </div>
  )

  const { stable_parties, afd } = data.bridging_timeseries

  const chartData = YEARS.map(y => {
    const row = { year: y }
    STABLE.forEach(p => { row[p] = stable_parties[p]?.[String(y)] ?? null })
    row.afd = afd?.[String(y)] ?? null
    return row
  })

  const allVals = chartData.flatMap(r => [...STABLE, 'afd'].map(p => r[p]).filter(v => v != null))
  const yMin = (Math.min(...allVals) - 0.0015).toFixed(4)
  const yMax = (Math.max(...allVals) + 0.0015).toFixed(4)

  const electionEvents = (data.historical_events ?? []).filter(e => YEARS.includes(e.year))

  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 24, left: 12 }}>
          <XAxis
            dataKey="year"
            tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-secondary)' }}
            axisLine={{ stroke: '#2C2E32' }} tickLine={false}
          />
          <YAxis
            domain={[Number(yMin), Number(yMax)]}
            tickFormatter={v => v.toFixed(3)}
            tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--text-secondary)' }}
            axisLine={{ stroke: '#2C2E32' }} tickLine={false} width={52}
          />
          <Tooltip content={<CustomTooltip />} />

          {electionEvents.map((ev, i) => (
            <ReferenceLine key={i} x={ev.year}
              stroke={EVENT_STROKE[ev.category] ?? '#2C2E32'}
              strokeOpacity={0.3} strokeDasharray="3 3" />
          ))}

          {STABLE.map(p => (
            <Line key={p} type="monotone" dataKey={p}
              stroke={PARTY_HEX[p]} strokeWidth={1.5}
              dot={{ r: 3, fill: PARTY_HEX[p], strokeWidth: 0 }}
              activeDot={{ r: 5 }} connectNulls={false} />
          ))}
          <Line type="monotone" dataKey="afd"
            stroke={PARTY_HEX.afd} strokeWidth={1.5}
            dot={{ r: 3, fill: PARTY_HEX.afd, strokeWidth: 0 }}
            activeDot={{ r: 5 }} connectNulls={false} />
        </LineChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-3)', justifyContent: 'center', marginTop: 'var(--space-2)' }}>
        {[...STABLE, 'afd'].map(p => (
          <div key={p} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
            <svg width="20" height="10">
              <line x1="0" y1="5" x2="20" y2="5" stroke={PARTY_HEX[p]} strokeWidth="1.5" />
            </svg>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              {SHORT[p]}
            </span>
            {p === 'afd' && (
              <InfoIcon text="Die AfD weist in allen analysierten Jahren den niedrigsten Brückenwert auf — programmatisch am stärksten isoliert vom übrigen Parteienspektrum." />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
