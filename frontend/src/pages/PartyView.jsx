import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getHistoricalAnalysis, getHohenheimData } from '../api/client'
import { Loader, InfoIcon } from '../components/ui'
import {
  ForceGraph, Heatmap, TimelineSlider,
  BridgingTimeline, WahlErgebnisse,
  IdeologicalMatrix, PartyDistanceView,
} from '../components/charts'

const YEARS        = [2005, 2009, 2013, 2017, 2021, 2025]
const DEFAULT_YEAR = 2025

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

export default function PartyView() {
  const [data, setData]               = useState(null)
  const [hohenheimData, setHohenheim] = useState(null)
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(false)
  const [activeTab, setTab]           = useState('verortung')
  const [selectedYear, setYear]       = useState(DEFAULT_YEAR)
  const { t } = useTranslation()

  const TABS = [
    { id: 'verortung',     label: t('partyview.tab_verortung') },
    { id: 'distanz',       label: t('partyview.tab_distanz') },
    { id: 'brueckenbauer', label: t('partyview.tab_brueckenbauer') },
    { id: 'wahlen',        label: t('partyview.tab_wahlen') },
  ]

  useEffect(() => {
    getHistoricalAnalysis()
      .then(d => { setData(d); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
    getHohenheimData()
      .then(d => setHohenheim(d))
      .catch(() => {})
  }, [])

  if (loading) return <Loader text={t('partyview.loading')} />

  if (error || !data) return (
    <div style={{ padding: 'var(--space-16)', textAlign: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      {t('partyview.error')}
    </div>
  )

  return (
    <div style={{ maxWidth: '900px', paddingTop: 'var(--space-12)', paddingBottom: 'var(--space-24)' }}>

      {/* ── Header ──────────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ ...S.sectionLabel, color: 'var(--signal)', marginBottom: 'var(--space-3)' }}>
          {t('partyview.eyebrow')}
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(22px, 4vw, 38px)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          lineHeight: 1.2,
          marginBottom: 'var(--space-3)',
        }}>
          {t('partyview.headline')}
        </h1>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
          marginBottom: 'var(--space-2)',
        }}>
          {t('partyview.subtitle')}
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
        marginBottom: 'var(--space-10)',
        flexWrap: 'wrap',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setTab(tab.id)}
            style={{
              padding: 'var(--space-3) var(--space-5)',
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
              whiteSpace: 'nowrap',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab 1: Ideologische Verortung ───────────── */}
      {activeTab === 'verortung' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
            {t('partyview.verortung_label')}
            <InfoIcon text="Wirtschaftsachse (links–rechts) und Gesellschaftsachse (progressiv–konservativ) aus ManifestoBERTa-Kategoriencodes. Normiert über alle Wahljahre." />
          </div>
          <IdeologicalMatrix data={data} />
        </div>
      )}

      {/* ── Tab 2: Nähe & Distanz ─────────────────── */}
      {activeTab === 'distanz' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
              {t('partyview.distanz_label')}
              <InfoIcon text="Die Abstände zeigen wie ähnlich sich die Parteien in ihren Wahlprogrammen sind — berechnet aus semantischer Nähe und inhaltlichen Schwerpunkten." />
            </div>
            <PartyDistanceView data={data} />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
              {t('partyview.heatmap_label')}
              <InfoIcon text="Technisch: Kosinus-Ähnlichkeit zwischen ManifestoBERTa-Embeddings der Wahlprogramme. Skala 0–1, wobei 1 = inhaltlich identisch. Typische Werte im Datensatz: 0,23 (sehr verschieden) bis 0,55 (sehr ähnlich)." />
            </div>
            <Heatmap data={data} year={selectedYear} />
          </div>

        </div>
      )}

      {/* ── Tab 3: Brückenbauer ──────────────────── */}
      {activeTab === 'brueckenbauer' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-16)' }}>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
              {t('partyview.bridging_label')}
              <InfoIcon text="Technisch: Mittelwert der Kosinus-Ähnlichkeiten einer Partei zu allen anderen, min-max-normiert auf 0–1 über alle Wahljahre. Wert 1 = programmatisch nächste Partei zum Feld, Wert 0 = am weitesten entfernt." />
            </div>
            <BridgingTimeline data={data} />

            <div style={{
              marginTop: 'var(--space-6)',
              padding: 'var(--space-4) var(--space-5)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderLeft: '3px solid var(--signal)',
            }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--signal)', marginBottom: 'var(--space-2)' }}>
                {t('partyview.bridging_hintergrund')}
              </div>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                {t('partyview.bridging_text')}
              </p>
            </div>

            <div style={{
              marginTop: 'var(--space-3)',
              padding: 'var(--space-4) var(--space-5)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderLeft: '3px solid var(--amber)',
            }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--amber)', marginBottom: 'var(--space-2)' }}>
                {t('partyview.bridging_erkenntnisse')}
              </div>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                {t('partyview.bridging_findings')}
              </p>
            </div>
          </div>

          <div>
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 'var(--space-4)', maxWidth: '680px' }}>
              {t('partyview.network_desc', { year: selectedYear })}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', ...S.sectionLabel }}>
              {t('partyview.network_label')}
              <InfoIcon text="Technisch: Knoten-Größe = Brückenbauer-Score (normiert). Kantendicke = Kosinus-Ähnlichkeit der Wahlprogramme. Themenfilter begrenzen auf Teilgraphen einzelner ManifestoBERTa-Kategorien." />
            </div>
            <ForceGraph data={data} year={selectedYear} />
          </div>

        </div>
      )}

      {/* ── Tab 4: Wahlen & Programme ─────────────── */}
      {activeTab === 'wahlen' && (
        <WahlErgebnisse data={data} selectedYear={selectedYear} hohenheimData={hohenheimData} />
      )}

    </div>
  )
}
