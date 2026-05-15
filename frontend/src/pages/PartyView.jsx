import { useEffect, useMemo, useState } from 'react'
import { getHistoricalAnalysis, getHohenheimData } from '../api/client'
import { Loader, InfoIcon } from '../components/ui'
import {
  ForceGraph, Heatmap, TimelineSlider,
  BridgingTimeline, WahlErgebnisse,
  IdeologicalMatrix, PartyDistanceView, PartyTrajectory,
} from '../components/charts'

const YEARS        = [2005, 2009, 2013, 2017, 2021, 2025]
const DEFAULT_YEAR = 2025

const TABS = [
  { id: 'positionen', label: 'Positionen & Entwicklung' },
  { id: 'wahlen',     label: 'Wahlen & Programme' },
]

const SHORT = {
  cdu_csu: 'CDU/CSU', spd: 'SPD', gruene: 'Grüne',
  fdp: 'FDP', afd: 'AfD', linke: 'Linke',
}

const CAT_LABELS = {
  welfare:            'Wohlfahrt',
  economy:            'Wirtschaft',
  external_relations: 'Außenpolitik',
  political_system:   'Polit. System',
  fabric_of_society:  'Gesellschaft',
  social_groups:      'Soziale Gruppen',
  freedom_democracy:  'Demokratie',
}

const PREV_YEAR = { 2009: 2005, 2013: 2009, 2017: 2013, 2021: 2017, 2025: 2021 }

const S = {
  sectionLabel: {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--text-xs)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--text-secondary)',
    marginBottom: 'var(--space-3)',
  },
}

const PARTY_HEX = {
  cdu_csu: '#2C2C2C', spd: '#E3000F', gruene: '#64A12D',
  fdp: '#FFCC00', afd: '#009EE0', linke: '#BE3075',
}

const PARTIES = ['cdu_csu', 'spd', 'gruene', 'fdp', 'afd', 'linke']

export default function PartyView() {
  const [data, setData]               = useState(null)
  const [hohenheimData, setHohenheim] = useState(null)
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(false)
  const [activeTab, setTab]           = useState('positionen')
  const [selectedYear, setYear]       = useState(DEFAULT_YEAR)
  const [driftParty, setDriftParty]   = useState('cdu_csu')

  useEffect(() => {
    getHistoricalAnalysis()
      .then(d => { setData(d); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
    getHohenheimData()
      .then(d => setHohenheim(d))
      .catch(() => {})
  }, [])

  const driftStatement = useMemo(() => {
    const prev = PREV_YEAR[selectedYear]
    if (!prev || !data) return null
    const pe = data?.category_analysis?.policy_emphasis
    const curr = pe?.[String(selectedYear)]?.[driftParty]
    const prevData = pe?.[String(prev)]?.[driftParty]
    if (!curr || !prevData) return null

    const diffs = Object.keys(curr)
      .map(cat => ({ cat, delta: (curr[cat] ?? 0) - (prevData[cat] ?? 0) }))
      .sort((a, b) => b.delta - a.delta)

    const grew   = diffs.slice(0, 2)
    const shrunk = diffs.slice(-2).reverse()
    const grewStr   = grew.map(d => `${CAT_LABELS[d.cat] ?? d.cat} (+${d.delta.toFixed(1)}%)`).join(', ')
    const shrunkStr = shrunk.map(d => `${CAT_LABELS[d.cat] ?? d.cat} (${d.delta.toFixed(1)}%)`).join(', ')

    return `${SHORT[driftParty]} ${selectedYear} vs. ${prev}: Stärker betont → ${grewStr} · Weniger betont → ${shrunkStr}`
  }, [data, selectedYear, driftParty])

  if (loading) return <Loader text="Lade Parteiprogramm-Analyse..." />

  if (error || !data) return (
    <div style={{ padding: 'var(--space-16)', textAlign: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      Analyse nicht verfügbar — Backend erreichbar?
    </div>
  )

  return (
    <div style={{ maxWidth: '900px', paddingBottom: 'var(--space-24)' }}>

      {/* ── Header ──────────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ ...S.sectionLabel, color: 'var(--signal)', marginBottom: 'var(--space-3)' }}>
          Dimension II — Parteiprogramme
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(22px, 4vw, 38px)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          lineHeight: 1.2,
          marginBottom: 'var(--space-3)',
        }}>
          Wie haben sich Parteipositionen entwickelt?
        </h1>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
          marginBottom: 'var(--space-2)',
        }}>
          6 Bundestagswahlen · 6 Parteien · 8 Themen · Wer sind die Brückenbauer?
        </div>
      </div>

      {/* ── Timeline Slider — always visible ─────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <TimelineSlider
          years={YEARS}
          selectedYear={selectedYear}
          onChange={setYear}
          events={data.historical_events ?? []}
          electionResults={data.election_results}
        />
      </div>

      {/* ── Tab bar ──────────────────────────────────── */}
      <div style={{
        display: 'flex', gap: '1px',
        background: 'var(--border)',
        borderBottom: '1px solid var(--border)',
        marginBottom: 'var(--space-8)',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setTab(tab.id)}
            style={{
              padding: 'var(--space-3) var(--space-6)',
              background: activeTab === tab.id ? 'var(--bg-surface)' : 'var(--bg-primary)',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid var(--signal)' : '2px solid transparent',
              color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              fontSize: 'var(--text-sm)',
              fontFamily: 'var(--font-body)',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              fontWeight: activeTab === tab.id ? 500 : 400,
              letterSpacing: '0.01em',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Positionen & Entwicklung ────────────── */}
      {activeTab === 'positionen' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-10)' }}>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
              Ideologische Verortung
              <InfoIcon text="Wirtschaftsachse (links–rechts) und Gesellschaftsachse (progressiv–konservativ) aus ManifestoBERTa-Kategoriencodes. Normiert über alle Wahljahre." />
            </div>
            <IdeologicalMatrix data={data} />

            {/* Programm-Drift Statement */}
            {driftStatement && (
              <div style={{ marginTop: 'var(--space-4)' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: 'var(--space-2)' }}>
                  {PARTIES.map(p => (
                    <button
                      key={p}
                      onClick={() => setDriftParty(p)}
                      style={{
                        padding: '2px 8px',
                        background: driftParty === p ? `${PARTY_HEX[p]}22` : 'none',
                        border: `1px solid ${driftParty === p ? PARTY_HEX[p] : 'var(--border)'}`,
                        color: driftParty === p ? PARTY_HEX[p] : 'var(--text-muted)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '10px',
                        cursor: 'pointer',
                        transition: 'all 120ms',
                      }}
                    >
                      {SHORT[p]}
                    </button>
                  ))}
                </div>
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-muted)',
                  padding: 'var(--space-3) var(--space-4)',
                  background: 'var(--bg-elevated)',
                  borderLeft: '2px solid var(--border)',
                  lineHeight: 1.6,
                }}>
                  {driftStatement}
                </div>
              </div>
            )}
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
              Inhaltliche Distanz zur Partei
              <InfoIcon text="Die Abstände zeigen wie ähnlich sich die Parteien in ihren Wahlprogrammen sind — berechnet aus semantischer Nähe und inhaltlichen Schwerpunkten." />
            </div>
            <PartyDistanceView data={data} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
              Distanzentwicklung im Zeitverlauf 2005–2025
              <InfoIcon text="Wie hat sich die inhaltliche Distanz zwischen Parteien von Wahl zu Wahl verändert? Basis: ManifestoBERTa-Ähnlichkeiten aus Wahlprogrammen." />
            </div>
            <PartyTrajectory data={data} selectedYear={selectedYear} />
          </div>

          <div>
            <div style={S.sectionLabel}>Bridging-Score im Zeitverlauf 2005–2025</div>
            <BridgingTimeline data={data} />
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: 'var(--space-3)' }}>
              AfD erst ab 2013 im Bundestag — Wahlprogramm 2013 umfasste nur wenige Seiten (Partei im selben Jahr gegründet).
            </div>
          </div>

          <div>
            <div style={S.sectionLabel}>Paarweise Ähnlichkeitsmatrix</div>
            <Heatmap data={data} year={selectedYear} />
          </div>

          <div>
            <div style={S.sectionLabel}>Ähnlichkeitsnetzwerk {selectedYear}</div>
            <ForceGraph data={data} year={selectedYear} />
          </div>

        </div>
      )}

      {/* ── Tab: Wahlen & Programme ───────────────────── */}
      {activeTab === 'wahlen' && (
        <WahlErgebnisse data={data} selectedYear={selectedYear} hohenheimData={hohenheimData} />
      )}

    </div>
  )
}
