import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
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

export default function WahlErgebnisse({ data, selectedYear }) {
  if (!data?.election_results) return (
    <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      Keine Wahldaten
    </div>
  )

  // historical_analysis.election_results is already the unwrapped results object
  const results = data.election_results

  const barData = ELECTION_YEARS.map(y => {
    const row = { year: y }
    PARTIES.forEach(p => { row[p] = results[String(y)]?.[p] ?? null })
    return row
  })

  // Radar: policy_emphasis[year][party] = { group: pct }
  const emphasis = data.category_analysis?.policy_emphasis?.[String(selectedYear)] ?? {}

  const radarData = Object.entries(CAT_LABELS).map(([key, label]) => {
    const entry = { category: label }
    PARTIES.forEach(p => { entry[p] = emphasis[p]?.[key] ?? 0 })
    return entry
  })

  const hasEmphasis = Object.keys(emphasis).length > 0

  const correlation = data.bridging_vote_correlation ?? {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>

      {/* Grouped bar: vote shares */}
      <div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)' }}>
          Zweitstimmen 2005–2025 (%)
        </div>
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
      </div>

      {/* Radar: policy emphasis */}
      {hasEmphasis && (
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)' }}>
            Themenschwerpunkte {selectedYear} — ManifestoBERTa (%)
          </div>
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
                  fillOpacity={0.07} strokeWidth={1.5} />
              ))}
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Bridging × vote correlation */}
      {Object.keys(correlation).length > 0 && (
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)' }}>
            Bridging-Score × Wahlergebnis — Pearson r
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
            {Object.entries(correlation).map(([pid, d]) => (
              <div key={pid} style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
                padding: 'var(--space-2) var(--space-3)',
                background: 'var(--bg-elevated)', border: '1px solid var(--border)',
              }}>
                <div style={{ width: '8px', height: '8px', background: PARTY_HEX[pid], flexShrink: 0 }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                  {SHORT[pid]}
                </span>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
                  color: d.pearson_correlation > 0.3 ? 'var(--patina-light)'
                       : d.pearson_correlation < -0.3 ? 'var(--amber-light)'
                       : 'var(--text-muted)',
                }}>
                  r = {d.pearson_correlation.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
