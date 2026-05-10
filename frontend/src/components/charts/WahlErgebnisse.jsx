import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'

const PARTY_HEX = {
  cdu_csu: '#E8E8E8',
  spd:     '#E3000F',
  gruene:  '#1AA037',
  fdp:     '#FFED00',
  afd:     '#009EE0',
  linke:   '#BE3075',
}

const PARTIES = ['cdu_csu', 'spd', 'gruene', 'fdp', 'afd', 'linke']

const CAT_LABELS = {
  welfare:            'Wohlfahrt',
  economy:            'Wirtschaft',
  external_relations: 'Außenpolitik',
  political_system:   'Polit. System',
  fabric_of_society:  'Gesellschaft',
  social_groups:      'Soziale Gruppen',
  freedom_democracy:  'Demokratie',
}

const ELECTION_YEARS = [2005, 2009, 2013, 2017, 2021, 2025]
const SHORT = { cdu_csu: 'CDU/CSU', spd: 'SPD', gruene: 'Grüne', fdp: 'FDP', afd: 'AfD', linke: 'Linke' }

const S_LABEL = {
  fontFamily: 'var(--font-mono)',
  fontSize: 'var(--text-xs)',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  marginBottom: 'var(--space-3)',
}

function BarTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ ...TOOLTIP_STYLE, padding: 'var(--space-2) var(--space-3)', lineHeight: 1.8 }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
        Bundestagswahl {label}
      </div>
      {[...payload].sort((a, b) => (b.value ?? 0) - (a.value ?? 0)).map(p => (
        p.value != null && (
          <div key={p.dataKey} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <div style={{ width: '8px', height: '8px', background: PARTY_HEX[p.dataKey], flexShrink: 0 }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
              {SHORT[p.dataKey]}: {p.value.toFixed(1)}%
            </span>
          </div>
        )
      ))}
    </div>
  )
}

function YearButtons({ years, active, onChange }) {
  return (
    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: 'var(--space-3)' }}>
      {years.map(y => (
        <button
          key={y}
          onClick={() => onChange(y)}
          style={{
            padding: '3px 10px',
            background: 'none',
            border: 'none',
            borderBottom: active === y ? '2px solid var(--signal)' : '2px solid transparent',
            color: active === y ? 'var(--text-primary)' : 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            cursor: 'pointer',
            transition: 'color 150ms, border-color 150ms',
          }}
        >
          {y}
        </button>
      ))}
    </div>
  )
}

export default function WahlErgebnisse({ data, selectedYear }) {
  const [chartType, setChartType] = useState('bar')
  const [focusParty, setFocusParty] = useState(null)
  const [themesYear, setThemesYear] = useState(selectedYear)

  if (!data?.election_results) return (
    <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      Keine Wahldaten
    </div>
  )

  const results = data.election_results

  const barData = ELECTION_YEARS.map(y => {
    const row = { year: y }
    PARTIES.forEach(p => { row[p] = results[String(y)]?.[p] ?? null })
    return row
  })

  const pieData = PARTIES
    .map(p => ({ name: SHORT[p], value: results[String(selectedYear)]?.[p] ?? 0, id: p }))
    .filter(d => d.value > 0)

  const emphasis = data.category_analysis?.policy_emphasis?.[String(themesYear)] ?? {}

  const radarData = Object.entries(CAT_LABELS).map(([key, label]) => {
    const entry = { category: label }
    PARTIES.forEach(p => { entry[p] = emphasis[p]?.[key] ?? 0 })
    return entry
  })

  const hasEmphasis = Object.keys(emphasis).length > 0

  const radarOpacity = (party) => focusParty === null ? 1 : focusParty === party ? 1 : 0.15

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

      {/* ── Vote share chart ──────────────────────── */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
          <div style={S_LABEL}>Wahlergebnisse Bundestagswahl 2005–2025 (%)</div>
          <div style={{ display: 'flex', gap: '1px', background: 'var(--border)' }}>
            {[['bar', '▬'], ['pie', '◔']].map(([type, icon]) => (
              <button
                key={type}
                onClick={() => setChartType(type)}
                style={{
                  padding: '3px 10px',
                  background: chartType === type ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                  border: 'none',
                  color: chartType === type ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                {icon}
              </button>
            ))}
          </div>
        </div>

        {chartType === 'bar' ? (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }} barCategoryGap="22%">
              <XAxis dataKey="year"
                tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#52504E' }}
                axisLine={{ stroke: '#2C2E32' }} tickLine={false} />
              <YAxis tickFormatter={v => `${v}%`}
                tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#52504E' }}
                axisLine={{ stroke: '#2C2E32' }} tickLine={false} width={36} />
              <Tooltip content={<BarTooltip />} />
              {PARTIES.map(p => (
                <Bar key={p} dataKey={p} fill={PARTY_HEX[p]} maxBarSize={14} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                strokeWidth={0}
                label={({ name, percent }) => percent > 0.04 ? `${name} ${(percent * 100).toFixed(1)}%` : ''}
                labelLine={false}
              >
                {pieData.map(d => (
                  <Cell key={d.id} fill={PARTY_HEX[d.id]} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v.toFixed(1)}%`]} />
              <Legend iconType="square" wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Radar: policy emphasis ─────────────────── */}
      {hasEmphasis && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
            <div style={S_LABEL}>Themenschwerpunkte {themesYear} — ManifestoBERTa (%)</div>
            <YearButtons years={ELECTION_YEARS} active={themesYear} onChange={setThemesYear} />
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-6)', alignItems: 'flex-start' }}>
            <ResponsiveContainer width="100%" height={340}>
              <RadarChart data={radarData} margin={{ top: 8, right: 32, bottom: 8, left: 32 }}>
                <PolarGrid stroke="#2C2E32" />
                <PolarAngleAxis dataKey="category"
                  tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#8A8885' }} />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(v, name) => [`${(v ?? 0).toFixed(1)}%`, SHORT[name] ?? name]} />
                {PARTIES.filter(p => Object.values(emphasis[p] ?? {}).some(v => v > 0)).map(p => (
                  <Radar key={p} name={p} dataKey={p}
                    stroke={PARTY_HEX[p]} fill={PARTY_HEX[p]}
                    fillOpacity={0.07 * radarOpacity(p)}
                    strokeOpacity={radarOpacity(p)}
                    strokeWidth={1.5} />
                ))}
              </RadarChart>
            </ResponsiveContainer>

            {/* Party selection buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flexShrink: 0, paddingTop: 'var(--space-8)' }}>
              <button
                onClick={() => setFocusParty(null)}
                style={{
                  padding: '4px 10px',
                  background: focusParty === null ? 'var(--bg-elevated)' : 'none',
                  border: '1px solid var(--border)',
                  color: focusParty === null ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  cursor: 'pointer',
                  transition: 'all 150ms',
                }}
              >
                Alle
              </button>
              {PARTIES.map(p => (
                <button
                  key={p}
                  onClick={() => setFocusParty(prev => prev === p ? null : p)}
                  style={{
                    padding: '4px 10px',
                    background: focusParty === p ? `${PARTY_HEX[p]}22` : 'none',
                    border: `1px solid ${focusParty === p ? PARTY_HEX[p] : 'var(--border)'}`,
                    color: focusParty === p ? PARTY_HEX[p] : 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: 'var(--text-xs)',
                    cursor: 'pointer',
                    transition: 'all 150ms',
                  }}
                >
                  {SHORT[p]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Top-3 Themenschwerpunkte ──────────────── */}
      {Object.keys(emphasis).length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
            <div style={S_LABEL}>Top-3 Themenschwerpunkte je Partei</div>
            <YearButtons years={ELECTION_YEARS} active={themesYear} onChange={setThemesYear} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)' }}>
            {PARTIES.map(p => {
              const cats = Object.entries(emphasis[p] ?? {})
                .sort((a, b) => b[1] - a[1])
                .slice(0, 3)
              return (
                <div key={p} style={{ background: 'var(--bg-surface)', border: `1px solid ${PARTY_HEX[p]}30`, padding: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                    <div style={{ width: '8px', height: '8px', background: PARTY_HEX[p], flexShrink: 0 }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: PARTY_HEX[p] }}>
                      {SHORT[p]}
                    </span>
                  </div>
                  {cats.map(([cat, pct]) => (
                    <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                        {CAT_LABELS[cat] ?? cat}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                        {(pct ?? 0).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        </div>
      )}

    </div>
  )
}
