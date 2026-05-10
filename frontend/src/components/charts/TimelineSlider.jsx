import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import { TOOLTIP_STYLE } from '../../constants/colors'

const EVENT_COLORS = {
  politics: 'var(--signal)',
  economy:  'var(--amber)',
  energy:   'var(--patina)',
  climate:  'var(--patina-light)',
  foreign:  'var(--text-secondary)',
  migration:'var(--amber-light)',
  health:   'var(--text-muted)',
  digital:  'var(--signal-light)',
}

const PARTY_HEX = {
  cdu_csu: '#E8E8E8',
  spd:     '#E3000F',
  gruene:  '#1AA037',
  fdp:     '#FFED00',
  afd:     '#009EE0',
  linke:   '#BE3075',
}

const PARTY_SHORT = { cdu_csu: 'CDU/CSU', spd: 'SPD', gruene: 'Grüne', fdp: 'FDP', afd: 'AfD', linke: 'Linke' }

const COALITIONS = [
  { from: 2005, to: 2009, label: 'Groko',        parties: ['cdu_csu', 'spd'] },
  { from: 2009, to: 2013, label: 'Schwarz-Gelb', parties: ['cdu_csu', 'fdp'] },
  { from: 2013, to: 2017, label: 'Groko',        parties: ['cdu_csu', 'spd'] },
  { from: 2017, to: 2021, label: 'Groko',        parties: ['cdu_csu', 'spd'] },
  { from: 2021, to: 2025, label: 'Ampel',        parties: ['spd', 'gruene', 'fdp'] },
  { from: 2025, to: null, label: 'Groko',        parties: ['cdu_csu', 'spd'] },
]

const ALL_PARTIES = ['cdu_csu', 'spd', 'gruene', 'fdp', 'afd', 'linke']
const ELECTION_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]

function ElectionTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ ...TOOLTIP_STYLE, padding: 'var(--space-2) var(--space-3)', lineHeight: 1.8 }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
        Wahl {label}
      </div>
      {[...payload].sort((a, b) => (b.value ?? 0) - (a.value ?? 0)).map(p => (
        p.value != null && (
          <div key={p.dataKey} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <div style={{ width: '8px', height: '2px', background: PARTY_HEX[p.dataKey], flexShrink: 0 }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              {PARTY_SHORT[p.dataKey]}: {p.value.toFixed(1)}%
            </span>
          </div>
        )
      ))}
    </div>
  )
}

export default function TimelineSlider({ years, selectedYear, onChange, events, electionResults }) {
  const [activeEvent, setActiveEvent] = useState(null)

  const min = years[0]
  const max = years[years.length - 1]
  const pct = y => ((y - min) / (max - min)) * 100

  const byYear = {}
  events?.forEach(ev => {
    ;(byYear[ev.year] ??= []).push(ev)
  })

  // Build line chart data from electionResults
  const hasResults = electionResults && Object.keys(electionResults).length > 0
  const lineData = hasResults
    ? ELECTION_YEARS.map(y => {
        const row = { year: y }
        ALL_PARTIES.forEach(p => { row[p] = electionResults[String(y)]?.[p] ?? null })
        return row
      })
    : []

  return (
    <div style={{ display: 'flex', gap: 'var(--space-6)', alignItems: 'flex-start' }}>

      {/* ── Main timeline block ──────────────────── */}
      <div style={{ flex: 1, padding: 'var(--space-4) var(--space-6)', background: 'var(--bg-surface)', border: '1px solid var(--border)' }}>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-4)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          <span style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>Bundestagswahl</span>
          <span style={{ color: 'var(--signal)' }}>{selectedYear}</span>
        </div>

        {/* Election results mini line chart */}
        {hasResults && (
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <ResponsiveContainer width="100%" height={80}>
              <LineChart data={lineData} margin={{ top: 4, right: 4, bottom: 4, left: 24 }}>
                <XAxis dataKey="year" hide />
                <YAxis tickFormatter={v => `${v}%`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--text-secondary)' }} axisLine={false} tickLine={false} width={28} />
                <Tooltip content={<ElectionTooltip />} />
                {ALL_PARTIES.map(p => (
                  <Line key={p} type="monotone" dataKey={p}
                    stroke={PARTY_HEX[p]} strokeWidth={1.2}
                    dot={false} connectNulls={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Track + year dots */}
        <div style={{ position: 'relative', height: '28px', marginBottom: 'var(--space-2)' }}>
          <div style={{
            position: 'absolute', top: '50%', left: 0, right: 0,
            height: '1px', background: 'var(--border-hover)', transform: 'translateY(-50%)',
          }} />

          {years.map(y => {
            const isSel = y === selectedYear
            return (
              <div
                key={y}
                onClick={() => onChange(y)}
                style={{
                  position: 'absolute', left: `${pct(y)}%`, top: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: isSel ? '12px' : '8px',
                  height: isSel ? '12px' : '8px',
                  background: isSel ? 'var(--signal)' : 'var(--bg-elevated)',
                  border: `1px solid ${isSel ? 'var(--signal)' : 'var(--border-hover)'}`,
                  cursor: 'pointer',
                  transition: 'all 150ms',
                  zIndex: 2,
                }}
              />
            )
          })}

          <input
            type="range" min={min} max={max} value={selectedYear}
            onChange={e => {
              const v = Number(e.target.value)
              onChange(years.reduce((a, b) => Math.abs(b - v) < Math.abs(a - v) ? b : a))
            }}
            style={{ position: 'absolute', inset: 0, width: '100%', opacity: 0, cursor: 'pointer', margin: 0, padding: 0 }}
          />
        </div>

        {/* Year labels */}
        <div style={{ position: 'relative', height: '18px', marginBottom: 'var(--space-4)' }}>
          {years.map(y => (
            <span
              key={y}
              onClick={() => onChange(y)}
              style={{
                position: 'absolute', left: `${pct(y)}%`, transform: 'translateX(-50%)',
                fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
                color: y === selectedYear ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor: 'pointer', transition: 'color 150ms',
              }}
            >
              {y}
            </span>
          ))}
        </div>

        {/* Coalition bars */}
        <div style={{ position: 'relative', height: '28px', marginBottom: 'var(--space-2)' }}>
          {COALITIONS.map((c, i) => {
            const fromPct  = pct(c.from)
            const toPct    = c.to ? pct(c.to) : 100
            const widthPct = toPct - fromPct
            return (
              <div key={i} style={{
                position: 'absolute',
                left: `${fromPct}%`,
                width: `${widthPct}%`,
                top: 0,
                paddingRight: '1px',
              }}>
                <div style={{ display: 'flex', height: '8px', marginBottom: '3px' }}>
                  {c.parties.map(p => (
                    <div key={p} style={{ flex: 1, background: PARTY_HEX[p], opacity: 0.65 }} />
                  ))}
                </div>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '8px',
                  color: 'var(--text-muted)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  display: 'block',
                  opacity: 0.75,
                }}>
                  {c.label}
                </span>
              </div>
            )
          })}
        </div>

        {/* Event strip */}
        <div style={{ position: 'relative', height: '20px' }}>
          <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: '1px', background: 'var(--border-subtle)' }} />

          {Object.entries(byYear).map(([evYear, evs]) => (
            <div
              key={evYear}
              style={{ position: 'absolute', left: `${pct(Number(evYear))}%`, top: 0, height: '100%', transform: 'translateX(-50%)', zIndex: 1, display: 'flex', gap: '1px' }}
              onMouseEnter={() => setActiveEvent({ year: Number(evYear), events: evs })}
            >
              {evs.map((ev, i) => (
                <div key={i} style={{ width: '3px', height: '100%', background: EVENT_COLORS[ev.category] ?? 'var(--text-muted)', opacity: 0.85, cursor: 'pointer' }} />
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* ── Persistent info panel ────────────────── */}
      <div style={{
        width: '200px',
        flexShrink: 0,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        padding: 'var(--space-3)',
        minHeight: '80px',
        alignSelf: 'stretch',
      }}>
        {activeEvent ? (
          <>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--signal)', marginBottom: 'var(--space-2)' }}>
              {activeEvent.year}
            </div>
            {activeEvent.events.map((ev, i) => (
              <div key={i} style={{ marginBottom: i < activeEvent.events.length - 1 ? 'var(--space-3)' : 0 }}>
                <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: ev.description ? '4px' : 0 }}>
                  <div style={{ width: '6px', height: '6px', flexShrink: 0, marginTop: '3px', background: EVENT_COLORS[ev.category] ?? 'var(--text-muted)' }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-primary)', lineHeight: 1.5, fontWeight: 500 }}>
                    {ev.label}
                  </span>
                </div>
                {ev.description && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', color: 'var(--text-secondary)', lineHeight: 1.5, paddingLeft: '14px' }}>
                    {ev.description}
                  </div>
                )}
              </div>
            ))}
          </>
        ) : (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>
            Über ein Ereignis hovern
          </span>
        )}
      </div>
    </div>
  )
}
