import { useState } from 'react'

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

export default function TimelineSlider({ years, selectedYear, onChange, events }) {
  const [expandedYear, setExpandedYear] = useState(null)

  const min = years[0]
  const max = years[years.length - 1]

  const pct = y => ((y - min) / (max - min)) * 100

  const byYear = {}
  events?.forEach(ev => {
    ;(byYear[ev.year] ??= []).push(ev)
  })

  return (
    <div style={{ padding: 'var(--space-4) var(--space-6)', background: 'var(--bg-surface)', border: '1px solid var(--border)' }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-4)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
        <span style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>Bundestagswahl</span>
        <span style={{ color: 'var(--signal)' }}>{selectedYear}</span>
      </div>

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

        {/* Invisible range input for keyboard nav + drag */}
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
      <div style={{ position: 'relative', height: '18px', marginBottom: 'var(--space-8)' }}>
        {years.map(y => (
          <span
            key={y}
            onClick={() => onChange(y)}
            style={{
              position: 'absolute', left: `${pct(y)}%`, transform: 'translateX(-50%)',
              fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
              color: y === selectedYear ? 'var(--text-primary)' : 'var(--text-muted)',
              cursor: 'pointer', transition: 'color 150ms',
            }}
          >
            {y}
          </span>
        ))}
      </div>

      {/* Event strip */}
      <div style={{ position: 'relative', height: '20px' }}>
        <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: '1px', background: 'var(--border-subtle)' }} />

        {Object.entries(byYear).map(([evYear, evs]) => {
          const isExpanded = expandedYear === Number(evYear)
          return (
            <div
              key={evYear}
              style={{ position: 'absolute', left: `${pct(Number(evYear))}%`, top: 0, transform: 'translateX(-50%)', zIndex: isExpanded ? 10 : 1 }}
              onMouseEnter={() => setExpandedYear(Number(evYear))}
              onMouseLeave={() => setExpandedYear(null)}
            >
              <div style={{ display: 'flex', gap: '2px', justifyContent: 'center', cursor: 'default' }}>
                {evs.map((ev, i) => (
                  <div key={i} style={{ width: '6px', height: '6px', background: EVENT_COLORS[ev.category] ?? 'var(--text-muted)' }} />
                ))}
              </div>

              {isExpanded && (
                <div style={{
                  position: 'absolute', top: '14px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  padding: 'var(--space-2) var(--space-3)',
                  minWidth: '180px',
                  transform: 'translateX(-50%)',
                  pointerEvents: 'none',
                }}>
                  {evs.map((ev, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: i < evs.length - 1 ? '4px' : 0 }}>
                      <div style={{ width: '6px', height: '6px', flexShrink: 0, background: EVENT_COLORS[ev.category] ?? 'var(--text-muted)' }} />
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                        {ev.year} — {ev.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
