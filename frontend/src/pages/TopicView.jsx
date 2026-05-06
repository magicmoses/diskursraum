import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTopicAnalysis } from '../api/client'
import { Loader } from '../components/ui'
import { BIAS_COLORS, BIAS_LABELS } from '../constants/colors'

// ── Bias config for TopicView ─────────────────────
// Extended with bg/text for inline spectrum display
const BIAS_DISPLAY = {
  'left': { bg: '#1A2A3A', text: '#6B9AB8', label: 'Links' },
  'left-liberal': { bg: '#1A2535', text: '#8B9BAF', label: 'Links-Liberal' },
  'neutral': { bg: '#1E2023', text: '#8A8885', label: 'Neutral' },
  'conservative-liberal': { bg: '#2A1F0E', text: '#C4781A', label: 'Konservativ-Liberal' },
  'economic-liberal': { bg: '#2A1E0A', text: '#E8A84A', label: 'Wirtschaftsliberal' },
  'right-conservative': { bg: '#2A1010', text: '#B85C38', label: 'Rechts-Konservativ' },
  'populist-mixed': { bg: '#221A10', text: '#8B7355', label: 'Populistisch' },
  'far-right': { bg: '#1F0A0A', text: '#7A3B2E', label: 'Rechtsaußen' },
}

const BIAS_SPECTRUM = [
  'left', 'left-liberal', 'neutral',
  'conservative-liberal', 'economic-liberal',
  'right-conservative', 'populist-mixed', 'far-right',
]

const SOURCE_BIAS_MAP = {
  taz: 'left',
  spiegel: 'left-liberal', zeit: 'left-liberal',
  sz: 'left-liberal', stern: 'left-liberal',
  tagesschau: 'neutral', zdf: 'neutral', dw: 'neutral',
  faz: 'conservative-liberal', cicero: 'conservative-liberal',
  nzz: 'conservative-liberal',
  welt: 'right-conservative', focus: 'right-conservative', ntv: 'right-conservative',
  junge_freiheit: 'far-right', tichys: 'far-right', achgut: 'far-right',
  handelsblatt: 'economic-liberal',
  bild: 'populist-mixed',
}

// ── Shared style ──────────────────────────────────
const S = {
  label: {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--text-xs)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--text-muted)',
  },
  dot: (color) => ({
    width: '8px',
    height: '8px',
    background: color,
    flexShrink: 0,
  }),
}

// ── Sub-components ────────────────────────────────
function EmptyState({ onBack }) {
  return (
    <div style={{
      minHeight: '60vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 'var(--space-6)',
      textAlign: 'center',
    }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--text-xs)',
        color: 'var(--amber)',
        letterSpacing: '0.10em',
        textTransform: 'uppercase',
      }}>
        Analyse ausstehend
      </div>
      <p style={{ fontSize: 'var(--text-base)', color: 'var(--text-secondary)', maxWidth: '360px', lineHeight: 1.6 }}>
        Dieses Thema wird beim nächsten täglichen ML-Run analysiert.
      </p>
      <button
        onClick={onBack}
        style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--signal)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'var(--font-body)',
        }}
      >
        ← Zurück zur Übersicht
      </button>
    </div>
  )
}

function SpectrumBar({ biasDistribution }) {
  const total = Object.values(biasDistribution).reduce((s, c) => s + c, 0)
  if (total === 0) return null
  const ordered = BIAS_SPECTRUM.filter(b => biasDistribution[b])

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      padding: 'var(--space-4) var(--space-6)',
    }}>
      <div style={{ ...S.label, marginBottom: 'var(--space-3)' }}>
        Politisches Spektrum der Berichterstattung
      </div>
      <div style={{ display: 'flex', height: '4px', gap: '1px' }}>
        {ordered.map(b => {
          const pct = (biasDistribution[b] / total * 100).toFixed(1)
          const d = BIAS_DISPLAY[b]
          return (
            <div
              key={b}
              title={`${d?.label}: ${pct}%`}
              style={{
                width: `${pct}%`,
                background: d?.text || 'var(--text-muted)',
                transition: 'opacity 150ms ease',
                cursor: 'default',
              }}
            />
          )
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-2)' }}>
        <span style={{ ...S.label, color: '#6B9AB8' }}>Links</span>
        <span style={{ ...S.label, color: '#7A3B2E' }}>Rechts</span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
        {ordered.map(b => {
          const pct = (biasDistribution[b] / total * 100).toFixed(0)
          const d = BIAS_DISPLAY[b]
          return (
            <span key={b} style={{
              fontSize: 'var(--text-xs)',
              fontFamily: 'var(--font-mono)',
              padding: '2px 8px',
              background: d?.bg,
              color: d?.text,
              border: `1px solid ${d?.text}30`,
            }}>
              {d?.label} {pct}%
            </span>
          )
        })}
      </div>
    </div>
  )
}

function SynthesisCard({ shared, controversial }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
      {[
        { label: 'Gemeinsame Perspektiven', text: shared, accent: 'var(--patina)', bg: 'var(--patina-subtle)' },
        { label: 'Kontroverse Punkte', text: controversial, accent: 'var(--amber)', bg: 'var(--amber-subtle)' },
      ].map(({ label, text, accent, bg }) => (
        <div key={label} style={{
          background: bg,
          border: `1px solid ${accent}30`,
          padding: 'var(--space-6)',
        }}>
          <div style={{ ...S.label, color: accent, marginBottom: 'var(--space-3)' }}>
            {label}
          </div>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
            {text}
          </p>
        </div>
      ))}
    </div>
  )
}

function OutletCard({ outlet }) {
  const bias = BIAS_DISPLAY[outlet.bias || SOURCE_BIAS_MAP[outlet.source_id]] || BIAS_DISPLAY['neutral']

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      padding: 'var(--space-4)',
      transition: 'border-color 150ms ease',
    }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-hover)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <div style={S.dot(bias.text)} />
          <span style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-primary)' }}>
            {outlet.source}
          </span>
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: bias.text,
          background: bias.bg,
          padding: '2px 6px',
          border: `1px solid ${bias.text}30`,
        }}>
          {outlet.article_count} Art.
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {outlet.sample_titles?.slice(0, 3).map((title, i) => (
          <p key={i} style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
            paddingLeft: 'var(--space-3)',
            borderLeft: `2px solid ${bias.text}40`,
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}>
            {title}
          </p>
        ))}
      </div>
    </div>
  )
}

// ── Tab Bar ───────────────────────────────────────
function TabBar({ tabs, active, onChange }) {
  return (
    <div style={{
      display: 'flex',
      gap: '1px',
      background: 'var(--border)',
      borderBottom: '1px solid var(--border)',
    }}>
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          style={{
            padding: 'var(--space-3) var(--space-6)',
            background: active === tab.id ? 'var(--bg-surface)' : 'var(--bg-primary)',
            border: 'none',
            borderBottom: active === tab.id ? '2px solid var(--signal)' : '2px solid transparent',
            color: active === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
            fontSize: 'var(--text-sm)',
            fontFamily: 'var(--font-body)',
            cursor: 'pointer',
            transition: 'all 150ms ease',
            fontWeight: active === tab.id ? 500 : 400,
            letterSpacing: '0.01em',
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

// ── Main ──────────────────────────────────────────
export default function TopicView() {
  const { topicId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    setLoading(true)
    setData(null)
    getTopicAnalysis(topicId)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [topicId])

  if (loading) return <Loader text="Lade Analyse..." />
  if (!data || data.error) return <EmptyState onBack={() => navigate('/')} />

  const outlets = data.outlets || {}
  const outletList = Object.values(outlets)

  const outletsByBias = {}
  outletList.forEach(outlet => {
    const bias = outlet.bias || SOURCE_BIAS_MAP[outlet.source_id] || 'neutral'
    if (!outletsByBias[bias]) outletsByBias[bias] = []
    outletsByBias[bias].push(outlet)
  })

  const tabs = [
    { id: 'overview', label: 'Überblick' },
    { id: 'outlets', label: 'Medienhäuser' },
  ]

  return (
    <div style={{ maxWidth: '880px', paddingBottom: 'var(--space-16)' }}>

      {/* ── Back ──────────────────────────────────── */}
      <button
        onClick={() => navigate('/medienspiegel')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-muted)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'var(--font-body)',
          padding: 'var(--space-8) 0 var(--space-6)',
          transition: 'color 150ms ease',
        }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
      >
        ← Themenübersicht
      </button>

      {/* ── Header ────────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ ...S.label, color: 'var(--signal)', marginBottom: 'var(--space-3)' }}>
          Dimension I — Medienspiegel
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(24px, 4vw, 40px)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          marginBottom: 'var(--space-3)',
        }}>
          {data.topic_label}
        </h1>
        <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          <span>{data.article_count} Artikel</span>
          <span>·</span>
          <span>{outletList.length} Medienhäuser</span>
          <span>·</span>
          <span>
            {data.cached_at
              ? new Date(data.cached_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
              : '—'}
          </span>
        </div>
      </div>

      {/* ── Spectrum ──────────────────────────────── */}
      {data.bias_distribution && (
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <SpectrumBar biasDistribution={data.bias_distribution} />
        </div>
      )}

      {/* ── Synthesis ─────────────────────────────── */}
      {data.shared_perspectives && data.controversial_points && (
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <SynthesisCard shared={data.shared_perspectives} controversial={data.controversial_points} />
        </div>
      )}

      {/* ── Tabs ──────────────────────────────────── */}
      <TabBar tabs={tabs} active={activeTab} onChange={setActiveTab} />

      <div style={{ paddingTop: 'var(--space-6)' }}>

        {/* Overview */}
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {BIAS_SPECTRUM.filter(b => outletsByBias[b]).map(b => {
              const d = BIAS_DISPLAY[b]
              const groupOutlets = outletsByBias[b]
              const groupTotal = groupOutlets.reduce((s, o) => s + o.article_count, 0)
              return (
                <div key={b} style={{
                  background: d.bg,
                  border: `1px solid ${d.text}20`,
                  padding: 'var(--space-4) var(--space-6)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <div style={S.dot(d.text)} />
                      <span style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-primary)' }}>
                        {d.label}
                      </span>
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {groupOutlets.map(o => o.source).join(', ')}
                      </span>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: d.text }}>
                      {groupTotal} Art.
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {groupOutlets.flatMap(o => o.sample_titles || []).slice(0, 3).map((title, i) => (
                      <p key={i} style={{
                        fontSize: 'var(--text-xs)',
                        color: 'var(--text-secondary)',
                        paddingLeft: 'var(--space-3)',
                        borderLeft: `1px solid ${d.text}40`,
                        lineHeight: 1.5,
                      }}>
                        {title}
                      </p>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Outlets */}
        {activeTab === 'outlets' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
            {BIAS_SPECTRUM.flatMap(b =>
              (outletsByBias[b] || []).map(outlet => (
                <OutletCard key={outlet.source_id} outlet={outlet} />
              ))
            )}
          </div>
        )}

      </div>
    </div>
  )
}
