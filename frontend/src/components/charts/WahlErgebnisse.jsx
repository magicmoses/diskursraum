import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  PieChart, Pie, Cell, Legend,
  LineChart, Line, ReferenceLine,
} from 'recharts'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'
import { InfoIcon } from '../../components/ui'

const PARTY_HEX = {
  cdu_csu: '#2C2C2C',
  spd:     '#E3000F',
  gruene:  '#64A12D',
  fdp:     '#FFCC00',
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
const NLP_YEARS      = [2009, 2013, 2017, 2021, 2025]

const SHORT = {
  cdu_csu: 'CDU/CSU', spd: 'SPD', gruene: 'Grüne',
  fdp: 'FDP', afd: 'AfD', linke: 'Linke',
}

const S_LABEL = {
  fontFamily: 'var(--font-mono)',
  fontSize: 'var(--text-xs)',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  marginBottom: 'var(--space-3)',
}

const SOURCE_NOTE = {
  fontFamily: 'var(--font-mono)',
  fontSize: '10px',
  color: 'var(--text-muted)',
  marginTop: 'var(--space-2)',
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

export default function WahlErgebnisse({ data, selectedYear, hohenheimData }) {
  const [chartType, setChartType]     = useState('bar')
  const [focusParty, setFocusParty]   = useState(null)
  const [themesYear, setThemesYear]   = useState(selectedYear)
  const [comparePair, setComparePair] = useState(['cdu_csu', 'spd'])
  const [hixYear, setHixYear]         = useState(2025)
  const [topicsParty, setTopicsParty] = useState('cdu_csu')
  const [topicsYear, setTopicsYear]   = useState(selectedYear)

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
  const hasEmphasis = Object.keys(emphasis).length > 0

  const radarData = Object.entries(CAT_LABELS).map(([key, label]) => {
    const entry = { category: label }
    PARTIES.forEach(p => { entry[p] = emphasis[p]?.[key] ?? 0 })
    return entry
  })

  const radarOpacity = (party) => focusParty === null ? 1 : focusParty === party ? 1 : 0.15

  const wordCountData = NLP_YEARS.map(y => {
    const row = { year: y }
    PARTIES.forEach(p => { row[p] = hohenheimData?.years?.[String(y)]?.[p]?.word_count ?? null })
    return row
  })

  const hixBarData = PARTIES.map(p => ({
    party: SHORT[p], id: p,
    value: hohenheimData?.years?.[String(hixYear)]?.[p]?.hix ?? null,
  })).filter(d => d.value !== null)

  const toggleComparePair = (p) =>
    setComparePair(prev =>
      prev.includes(p) ? prev.filter(x => x !== p) :
      prev.length < 2  ? [...prev, p] : [prev[1], p]
    )

  const topicsEmphasis = data?.category_analysis?.policy_emphasis?.[String(topicsYear)]?.[topicsParty]
  const topicsData = topicsEmphasis
    ? Object.entries(topicsEmphasis)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([cat, pct]) => ({ topic: CAT_LABELS[cat] ?? cat, pct }))
    : null

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
              <XAxis dataKey="year" tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#7A6E64' }} axisLine={{ stroke: '#C8BFB0' }} tickLine={false} />
              <YAxis tickFormatter={v => `${v}%`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#7A6E64' }} axisLine={{ stroke: '#C8BFB0' }} tickLine={false} width={36} />
              <Tooltip content={<BarTooltip />} />
              {PARTIES.map(p => <Bar key={p} dataKey={p} fill={PARTY_HEX[p]} maxBarSize={14} />)}
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} strokeWidth={0}
                label={({ name, percent }) => percent > 0.04 ? `${name} ${(percent * 100).toFixed(1)}%` : ''} labelLine={false}>
                {pieData.map(d => <Cell key={d.id} fill={PARTY_HEX[d.id]} />)}
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
                <PolarGrid stroke="#D8D0C4" />
                <PolarAngleAxis dataKey="category" tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#7A6E64' }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, name) => [`${(v ?? 0).toFixed(1)}%`, SHORT[name] ?? name]} />
                {PARTIES.filter(p => Object.values(emphasis[p] ?? {}).some(v => v > 0)).map(p => (
                  <Radar key={p} name={p} dataKey={p} stroke={PARTY_HEX[p]} fill={PARTY_HEX[p]}
                    fillOpacity={0.07 * radarOpacity(p)} strokeOpacity={radarOpacity(p)} strokeWidth={1.5} />
                ))}
              </RadarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flexShrink: 0, paddingTop: 'var(--space-8)' }}>
              <button onClick={() => setFocusParty(null)} style={{
                padding: '4px 10px', background: focusParty === null ? 'var(--bg-elevated)' : 'none',
                border: '1px solid var(--border)', color: focusParty === null ? 'var(--text-primary)' : 'var(--text-muted)',
                fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', cursor: 'pointer', transition: 'all 150ms',
              }}>Alle</button>
              {PARTIES.map(p => (
                <button key={p} onClick={() => setFocusParty(prev => prev === p ? null : p)} style={{
                  padding: '4px 10px', background: focusParty === p ? `${PARTY_HEX[p]}22` : 'none',
                  border: `1px solid ${focusParty === p ? PARTY_HEX[p] : 'var(--border)'}`,
                  color: focusParty === p ? PARTY_HEX[p] : 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', cursor: 'pointer', transition: 'all 150ms',
                }}>{SHORT[p]}</button>
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
              const cats = Object.entries(emphasis[p] ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 3)
              return (
                <div key={p} style={{ background: 'var(--bg-surface)', border: `1px solid ${PARTY_HEX[p]}30`, padding: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
                    <div style={{ width: '8px', height: '8px', background: PARTY_HEX[p], flexShrink: 0 }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: PARTY_HEX[p] }}>{SHORT[p]}</span>
                  </div>
                  {cats.map(([cat, pct]) => (
                    <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>{CAT_LABELS[cat] ?? cat}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{(pct ?? 0).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Programmlänge im Zeitverlauf ─────────── */}
      {hohenheimData && (
        <div>
          <div style={{ ...S_LABEL, marginBottom: 'var(--space-3)' }}>Wie viel haben die Parteien geschrieben?</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: 'var(--space-3)' }}>
            {PARTIES.map(p => {
              const active = comparePair.includes(p)
              return (
                <button key={p} onClick={() => toggleComparePair(p)} style={{
                  padding: '3px 10px',
                  background: active ? `${PARTY_HEX[p]}22` : 'none',
                  border: `1px solid ${active ? PARTY_HEX[p] : 'var(--border)'}`,
                  color: active ? PARTY_HEX[p] : 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', cursor: 'pointer', transition: 'all 120ms',
                }}>{SHORT[p]}</button>
              )
            })}
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={wordCountData} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
              <XAxis dataKey="year" tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#7A6E64' }} axisLine={{ stroke: '#C8BFB0' }} tickLine={false} />
              <YAxis tickFormatter={v => `${Math.round(v / 1000)}k`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#7A6E64' }} axisLine={{ stroke: '#C8BFB0' }} tickLine={false} width={36} />
              <Tooltip content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                return (
                  <div style={{ ...TOOLTIP_STYLE, padding: 'var(--space-2) var(--space-3)', lineHeight: 1.8 }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>Bundestagswahl {label}</div>
                    {[...payload].filter(p => p.value != null).sort((a, b) => (b.value ?? 0) - (a.value ?? 0)).map(p => (
                      <div key={p.dataKey} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <div style={{ width: '8px', height: '8px', background: p.stroke, flexShrink: 0 }} />
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                          {SHORT[p.dataKey]}: {p.value?.toLocaleString('de-DE')} Wörter
                        </span>
                      </div>
                    ))}
                  </div>
                )
              }} />
              {PARTIES.map(p => {
                const inPair = comparePair.includes(p)
                return (
                  <Line key={p} type="monotone" dataKey={p} stroke={PARTY_HEX[p]}
                    strokeWidth={inPair ? 2 : 1} strokeOpacity={inPair ? 1 : 0.3}
                    strokeDasharray={inPair ? undefined : '4 3'} dot={inPair} connectNulls={false} />
                )
              })}
            </LineChart>
          </ResponsiveContainer>
          <div style={SOURCE_NOTE}>Quelle: Universität Hohenheim, Wahlprogramm-Check · komm.uni-hohenheim.de</div>
        </div>
      )}

      {/* ── Verständlichkeit (HIX) ────────────────── */}
      {hohenheimData && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S_LABEL }}>
            Wie verständlich schreiben die Parteien?
            <InfoIcon text="Der Hohenheimer Verständlichkeitsindex (HIX) misst die formale Verständlichkeit von Texten auf einer Skala von 0 bis 20. Zum Vergleich: Doktorarbeiten erreichen 1,2 Punkte, Bundestagsreden 15,0 Punkte, die Bild-Zeitung 16,8 Punkte." />
          </div>
          <YearButtons years={NLP_YEARS} active={hixYear} onChange={setHixYear} />
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={hixBarData} margin={{ top: 16, right: 80, bottom: 4, left: 0 }}>
              <XAxis dataKey="party" tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#7A6E64' }} axisLine={{ stroke: '#C8BFB0' }} tickLine={false} />
              <YAxis domain={[0, 20]} tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#7A6E64' }} axisLine={{ stroke: '#C8BFB0' }} tickLine={false} width={24} />
              <Tooltip content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                return (
                  <div style={{ ...TOOLTIP_STYLE, padding: 'var(--space-2) var(--space-3)' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                      {label} {hixYear}: {payload[0]?.value?.toFixed(1)} Punkte
                    </span>
                  </div>
                )
              }} />
              <ReferenceLine y={1.2} stroke="#7A6E64" strokeDasharray="4 2"
                label={{ value: 'Doktorarbeit', position: 'insideRight', offset: 8, fontSize: 9, fontFamily: 'var(--font-mono)', fill: '#7A6E64' }} />
              <ReferenceLine y={15.0} stroke="#7A6E64" strokeDasharray="4 2"
                label={{ value: 'Bundestag-Rede', position: 'insideRight', offset: 8, fontSize: 9, fontFamily: 'var(--font-mono)', fill: '#7A6E64' }} />
              <Bar dataKey="value" maxBarSize={40}>
                {hixBarData.map(d => <Cell key={d.id} fill={PARTY_HEX[d.id]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={SOURCE_NOTE}>Quelle: Universität Hohenheim, Wahlprogramm-Check · komm.uni-hohenheim.de</div>
        </div>
      )}

      {/* ── Was haben die Parteien betont? ─────────── */}
      <div>
        <div style={{ ...S_LABEL, marginBottom: 'var(--space-4)' }}>Was haben die Parteien betont?</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-3)', marginBottom: 'var(--space-3)', alignItems: 'center' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {PARTIES.map(p => (
              <button key={p} onClick={() => setTopicsParty(p)} style={{
                padding: '3px 10px',
                background: topicsParty === p ? `${PARTY_HEX[p]}22` : 'none',
                border: `1px solid ${topicsParty === p ? PARTY_HEX[p] : 'var(--border)'}`,
                color: topicsParty === p ? PARTY_HEX[p] : 'var(--text-muted)',
                fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', cursor: 'pointer', transition: 'all 120ms',
              }}>{SHORT[p]}</button>
            ))}
          </div>
          <YearButtons years={ELECTION_YEARS} active={topicsYear} onChange={setTopicsYear} />
        </div>

        {topicsData ? topicsData.map((item, i) => (
          <div key={i} style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderLeft: `3px solid ${PARTY_HEX[topicsParty]}`,
            padding: 'var(--space-4) var(--space-5)',
            marginBottom: 'var(--space-2)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            gap: 'var(--space-4)',
          }}>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
              {item.topic}
            </p>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
              {item.pct?.toFixed(1)}%
            </span>
          </div>
        )) : (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--text-muted)', padding: 'var(--space-6) 0', textAlign: 'center' }}>
            Keine Daten verfügbar.
          </div>
        )}
      </div>

    </div>
  )
}
