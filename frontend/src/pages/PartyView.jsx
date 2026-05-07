import { useEffect, useState } from 'react'
import { getHistoricalAnalysis } from '../api/client'
import { Loader } from '../components/ui'
import {
  ForceGraph, Heatmap, TimelineSlider,
  PCAScatter, BridgingTimeline, WahlErgebnisse,
} from '../components/charts'

const YEARS        = [2005, 2009, 2013, 2017, 2021, 2025]
const DEFAULT_YEAR = 2025

const TABS = [
  { id: 'positionen',  label: 'Positionen' },
  { id: 'entwicklung', label: 'Entwicklung' },
  { id: 'wahlen',      label: 'Wahlen & Programme' },
]

const S = {
  sectionLabel: {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--text-xs)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--text-muted)',
    marginBottom: 'var(--space-3)',
  },
  subhead: {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--text-sm)',
    color: 'var(--text-secondary)',
    lineHeight: 1.7,
    maxWidth: '640px',
    marginBottom: 'var(--space-6)',
  },
}

export default function PartyView() {
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(false)
  const [activeTab, setTab]     = useState('positionen')
  const [selectedYear, setYear] = useState(DEFAULT_YEAR)

  useEffect(() => {
    getHistoricalAnalysis()
      .then(d => { setData(d); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
  }, [])

  if (loading) return <Loader text="Lade Parteiprogramm-Analyse..." />

  if (error || !data) return (
    <div style={{ padding: 'var(--space-16)', textAlign: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      Analyse nicht verfügbar — Backend erreichbar?
    </div>
  )

  const yearCount  = data.years_analyzed?.length ?? 0
  const partyCount = Object.keys(data.pca_trajectories?.trajectories ?? {}).length

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
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', display: 'flex', gap: 'var(--space-4)' }}>
          <span>{yearCount} Wahljahre analysiert</span>
          <span>·</span>
          <span>{partyCount} Parteien</span>
          <span>·</span>
          <span>ManifestoBERTa + E5-Embeddings</span>
        </div>
      </div>

      {/* ── Timeline Slider — always visible ─────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <TimelineSlider
          years={YEARS}
          selectedYear={selectedYear}
          onChange={setYear}
          events={data.historical_events ?? []}
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
              color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
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

      {/* ── Tab: Positionen ──────────────────────────── */}
      {activeTab === 'positionen' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>
          <p style={S.subhead}>
            Der Bridging-Score misst, wie zentral eine Partei im semantischen Netzwerk liegt —
            wie viel sie inhaltlich mit anderen Parteien teilt. Dicke Kanten bedeuten hohe Ähnlichkeit
            in den Wahlprogrammen. Die Knotenknoten-Größe spiegelt Betweenness-Zentralität wider.
          </p>

          <div>
            <div style={S.sectionLabel}>Ähnlichkeitsnetzwerk {selectedYear}</div>
            <ForceGraph data={data} year={selectedYear} />
          </div>

          <div>
            <div style={S.sectionLabel}>Paarweise Ähnlichkeitsmatrix {selectedYear}</div>
            <Heatmap data={data} year={selectedYear} />
          </div>
        </div>
      )}

      {/* ── Tab: Entwicklung ─────────────────────────── */}
      {activeTab === 'entwicklung' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>
          <div>
            <div style={S.sectionLabel}>Semantische Trajektorien (PCA) — {selectedYear} hervorgehoben</div>
            <PCAScatter data={data} selectedYear={selectedYear} />
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-3)' }}>
              Einzelner PCA-Raum über alle Jahre — Positionen direkt vergleichbar.
              PC1 + PC2 erklären {((data.pca_trajectories?.explained_variance ?? [0, 0]).reduce((a, b) => a + b, 0) * 100).toFixed(1)}% der Varianz.
            </div>
          </div>

          <div>
            <div style={S.sectionLabel}>Bridging-Score im Zeitverlauf 2005–2025</div>
            <BridgingTimeline data={data} />
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-3)' }}>
              AfD gestrichelt — nur ab 2013 im Datensatz. Stable set: 5 Parteien für Vergleichbarkeit.
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Wahlen & Programme ───────────────────── */}
      {activeTab === 'wahlen' && (
        <WahlErgebnisse data={data} selectedYear={selectedYear} />
      )}

    </div>
  )
}
