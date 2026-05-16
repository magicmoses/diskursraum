import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getTopicAnalysis } from '../api/client'
import { Loader } from '../components/ui'
import { BIAS_COLORS } from '../constants/colors'

const DEUTSCHLAND_KW = [
  'deutschland', 'deutsch', 'bundesregierung', 'bundestag', 'berlin',
  'cdu', 'spd', 'grüne', 'fdp', 'afd', 'merz', 'scholz', 'bundesrat',
  'baden-württemberg', 'bayern', 'brandenburg', 'bremen', 'hamburg',
  'hessen', 'mecklenburg-vorpommern', 'niedersachsen', 'nordrhein-westfalen',
  'rheinland-pfalz', 'saarland', 'sachsen', 'sachsen-anhalt',
  'schleswig-holstein', 'thüringen',
]

function isGermanyTitle(title) {
  const lower = title.toLowerCase()
  return DEUTSCHLAND_KW.some(kw => lower.includes(kw))
}

const BIAS_DISPLAY_COLORS = {
  'left':                 { bg: '#E8F0F5', text: '#1A5276' },
  'left-liberal':         { bg: '#EBF0F5', text: '#2E6B8A' },
  'neutral':              { bg: '#F0EFED', text: '#5A5550' },
  'conservative-liberal': { bg: '#FDF5E8', text: '#9A6010' },
  'economic-liberal':     { bg: '#FDF8E8', text: '#B8860B' },
  'right-conservative':   { bg: '#FDF0EC', text: '#8B3520' },
  'populist-mixed':       { bg: '#F5F0E8', text: '#7A5A30' },
  'far-right':            { bg: '#FAF0EC', text: '#6B2A1E' },
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

const S = {
  label: {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--text-xs)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--text-secondary)',
  },
  dot: (color) => ({
    width: '8px',
    height: '8px',
    background: color,
    flexShrink: 0,
  }),
}

function EmptyState({ onBack }) {
  const { t } = useTranslation()
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
        {t('topicview.pending')}
      </div>
      <p style={{ fontSize: 'var(--text-base)', color: 'var(--text-secondary)', maxWidth: '360px', lineHeight: 1.6 }}>
        {t('topicview.pending_desc')}
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
        {t('topicview.back')}
      </button>
    </div>
  )
}

function SpectrumBar({ biasDistribution, biasDisplay }) {
  const { t } = useTranslation()
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
        {t('topicview.spectrum_label')}
      </div>
      <div style={{ display: 'flex', height: '4px', gap: '1px' }}>
        {ordered.map(b => {
          const pct = (biasDistribution[b] / total * 100).toFixed(1)
          const d = biasDisplay[b]
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
        <span style={{ ...S.label, color: '#1A5276' }}>{t('topicview.spectrum_left')}</span>
        <span style={{ ...S.label, color: '#6B2A1E' }}>{t('topicview.spectrum_right')}</span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
        {ordered.map(b => {
          const pct = (biasDistribution[b] / total * 100).toFixed(0)
          const d = biasDisplay[b]
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
  const { t } = useTranslation()
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
      {[
        { label: t('topicview.shared'),      text: shared,      accent: 'var(--patina)', bg: 'var(--patina-subtle)' },
        { label: t('topicview.controversial'), text: controversial, accent: 'var(--amber)',  bg: 'var(--amber-subtle)' },
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

function OutletCard({ outlet, biasDisplay }) {
  const colors = BIAS_DISPLAY_COLORS[outlet.bias || SOURCE_BIAS_MAP[outlet.source_id]] || BIAS_DISPLAY_COLORS['neutral']
  const label = biasDisplay[outlet.bias || SOURCE_BIAS_MAP[outlet.source_id]]?.label || outlet.bias || ''

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
          <div style={S.dot(colors.text)} />
          <span style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--text-primary)' }}>
            {outlet.source}
          </span>
        </div>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: colors.text,
          background: colors.bg,
          padding: '2px 6px',
          border: `1px solid ${colors.text}30`,
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
            borderLeft: `2px solid ${colors.text}40`,
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}>
            {title}
          </p>
        ))}
      </div>
      {label && (
        <div style={{ marginTop: 'var(--space-2)', fontSize: 'var(--text-xs)', color: colors.text, fontFamily: 'var(--font-mono)' }}>
          {label}
        </div>
      )}
    </div>
  )
}

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
            color: active === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
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

export default function TopicView() {
  const { topicId } = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  const biasDisplay = Object.fromEntries(
    BIAS_SPECTRUM.map(b => [b, { ...BIAS_DISPLAY_COLORS[b], label: t(`bias.${b}`) }])
  )

  const tabs = [
    { id: 'overview', label: t('topicview.tab_overview') },
    { id: 'outlets',  label: t('topicview.tab_outlets') },
  ]

  useEffect(() => {
    setLoading(true)
    setData(null)
    getTopicAnalysis(topicId)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [topicId])

  if (loading) return <Loader text={t('common.loading')} />
  if (!data || data.error) return <EmptyState onBack={() => navigate('/')} />

  const outlets = data.outlets || {}
  const outletList = Object.values(outlets)

  const outletsByBias = {}
  outletList.forEach(outlet => {
    const bias = outlet.bias || SOURCE_BIAS_MAP[outlet.source_id] || 'neutral'
    if (!outletsByBias[bias]) outletsByBias[bias] = []
    outletsByBias[bias].push(outlet)
  })

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
          color: 'var(--text-secondary)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'var(--font-body)',
          padding: 'var(--space-8) 0 var(--space-6)',
          transition: 'color 150ms ease',
        }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
      >
        {t('topicview.back')}
      </button>

      {/* ── Header ────────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ ...S.label, color: 'var(--signal)', marginBottom: 'var(--space-3)' }}>
          {t('home.eyebrow')}
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
        <div style={{ display: 'flex', gap: 'var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
          <span>{t('topicview.article_count', { count: data.article_count })}</span>
          <span>·</span>
          <span>{t('topicview.outlet_count', { count: outletList.length })}</span>
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
          <SpectrumBar biasDistribution={data.bias_distribution} biasDisplay={biasDisplay} />
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

        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {BIAS_SPECTRUM.filter(b => outletsByBias[b]).map(b => {
              const d = biasDisplay[b]
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
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                        {groupOutlets.map(o => o.source).join(', ')}
                      </span>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: d.text }}>
                      {groupTotal} Art.
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {groupOutlets.flatMap(o => (o.sample_titles || []).filter(isGermanyTitle)).slice(0, 3).map((title, i) => (
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

        {activeTab === 'outlets' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
            {BIAS_SPECTRUM.flatMap(b =>
              (outletsByBias[b] || []).map(outlet => (
                <OutletCard key={outlet.source_id} outlet={outlet} biasDisplay={biasDisplay} />
              ))
            )}
          </div>
        )}

      </div>
    </div>
  )
}
