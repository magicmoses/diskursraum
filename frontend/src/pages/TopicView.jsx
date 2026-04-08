import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTopicAnalysis } from '../api/client'

// ── Constants ─────────────────────────────────────
const BIAS_COLORS = {
  'left': { bg: '#1e3a8a', text: '#93c5fd', label: 'Links' },
  'left-liberal': { bg: '#1d4ed8', text: '#bfdbfe', label: 'Links-Liberal' },
  'neutral': { bg: '#374151', text: '#d1d5db', label: 'Neutral' },
  'conservative-liberal': { bg: '#92400e', text: '#fcd34d', label: 'Konservativ-Liberal' },
  'economic-liberal': { bg: '#713f12', text: '#fde68a', label: 'Wirtschaftsliberal' },
  'right-conservative': { bg: '#991b1b', text: '#fca5a5', label: 'Rechts-Konservativ' },
  'populist-mixed': { bg: '#581c87', text: '#d8b4fe', label: 'Populistisch' },
  'far-right': { bg: '#450a0a', text: '#fecaca', label: 'Rechtsaußen' },
}

const BIAS_SPECTRUM = [
  'left', 'left-liberal', 'neutral',
  'conservative-liberal', 'economic-liberal',
  'right-conservative', 'populist-mixed', 'far-right',
]

const EMOTION_EMOJI = {
  neutral: '😐', curiosity: '🤔', optimism: '🌟',
  annoyance: '😤', confusion: '😕', admiration: '✨',
  excitement: '⚡', amusement: '😄', fear: '😨',
  sadness: '😢', anger: '🔥', disapproval: '👎',
  approval: '👍', disgust: '🤢', surprise: '😲',
  disappointment: '😞', joy: '🎉', grief: '💔',
}

// ── Helpers ───────────────────────────────────────
function getBiasForSource(sourceId) {
  const map = {
    taz: 'left',
    spiegel: 'left-liberal', zeit: 'left-liberal',
    sz: 'left-liberal', stern: 'left-liberal',
    tagesschau: 'neutral', zdf: 'neutral', dw: 'neutral',
    faz: 'conservative-liberal', cicero: 'conservative-liberal',
    welt: 'right-conservative', focus: 'right-conservative',
    junge_freiheit: 'far-right',
    handelsblatt: 'economic-liberal',
    bild: 'populist-mixed',
  }
  return map[sourceId] || 'neutral'
}

// ── Sub-components ────────────────────────────────
function LoadingState() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-gray-500 text-sm">Lade Analyse...</p>
    </div>
  )
}

function EmptyState({ onBack, topicId }) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-6 text-center px-4">
      <div className="text-5xl">🔄</div>
      <div>
        <p className="text-white font-semibold text-lg mb-2">Analyse noch nicht verfügbar</p>
        <p className="text-gray-400 text-sm max-w-sm">
          Dieses Thema wird beim nächsten täglichen ML-Run analysiert.
        </p>
      </div>
      <button onClick={onBack} className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
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
    <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">
        Politisches Spektrum der Berichterstattung
      </p>
      <div className="flex rounded-full overflow-hidden h-3 gap-px">
        {ordered.map(b => {
          const pct = (biasDistribution[b] / total * 100).toFixed(1)
          const bias = BIAS_COLORS[b]
          return (
            <div
              key={b}
              title={`${bias.label}: ${pct}%`}
              style={{ width: `${pct}%`, background: bias.text }}
              className="transition-all duration-300 cursor-pointer hover:opacity-80"
            />
          )
        })}
      </div>
      <div className="flex justify-between mt-1.5">
        <span className="text-xs text-blue-400">Links</span>
        <span className="text-xs text-red-400">Rechts</span>
      </div>
      <div className="flex flex-wrap gap-2 mt-3">
        {ordered.map(b => {
          const pct = (biasDistribution[b] / total * 100).toFixed(0)
          const bias = BIAS_COLORS[b]
          return (
            <span
              key={b}
              className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: bias.bg, color: bias.text }}
            >
              {bias.label} {pct}%
            </span>
          )
        })}
      </div>
    </div>
  )
}

function SynthesisCard({ shared, controversial }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="bg-blue-950/40 border border-blue-800/40 rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">🤝</span>
          <span className="text-sm font-semibold text-blue-300">Gemeinsame Perspektiven</span>
        </div>
        <p className="text-gray-300 text-sm leading-relaxed">{shared}</p>
      </div>
      <div className="bg-red-950/30 border border-red-800/30 rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">⚡</span>
          <span className="text-sm font-semibold text-red-300">Kontroverse Punkte</span>
        </div>
        <p className="text-gray-300 text-sm leading-relaxed">{controversial}</p>
      </div>
    </div>
  )
}

function OutletCard({ outlet }) {
  const bias = BIAS_COLORS[outlet.bias] || BIAS_COLORS['neutral']
  const emotion = outlet.dominant_emotion

  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 hover:border-gray-600 transition-colors">

      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{ background: bias.text }}
          />
          <span className="font-semibold text-white text-sm">{outlet.source}</span>
        </div>
        <div className="flex items-center gap-2">
          {emotion && emotion !== 'neutral' && (
            <span className="text-xs text-gray-500">
              {EMOTION_EMOJI[emotion] || ''} {emotion}
            </span>
          )}
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: bias.bg, color: bias.text }}
          >
            {outlet.article_count} Art.
          </span>
        </div>
      </div>

      {/* Sample titles */}
      <div className="space-y-1.5">
        {outlet.sample_titles?.slice(0, 3).map((title, i) => (
          <p
            key={i}
            className="text-xs text-gray-400 leading-relaxed line-clamp-2"
            style={{ borderLeft: `2px solid ${bias.bg}`, paddingLeft: '8px' }}
          >
            {title}
          </p>
        ))}
      </div>

    </div>
  )
}

// ── Main Component ────────────────────────────────
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

  if (loading) return <LoadingState />
  if (!data || data.error) return <EmptyState onBack={() => navigate('/')} topicId={topicId} />

  const outlets = data.outlets || {}
  const outletList = Object.values(outlets)

  // Group outlets by bias spectrum order
  const outletsByBias = {}
  outletList.forEach(outlet => {
    const bias = outlet.bias || getBiasForSource(outlet.source_id)
    if (!outletsByBias[bias]) outletsByBias[bias] = []
    outletsByBias[bias].push(outlet)
  })

  const tabs = [
    { id: 'overview', label: '📊 Überblick' },
    { id: 'outlets', label: '🗞 Medienhäuser' },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">

      {/* Back */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-white transition-colors"
      >
        ← Themenübersicht
      </button>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">{data.topic_label}</h1>
        <div className="flex items-center gap-3 text-xs text-gray-500 flex-wrap">
          <span>{data.article_count} relevante Artikel</span>
          <span>·</span>
          <span>{outletList.length} Medienhäuser</span>
          <span>·</span>
          <span>
            Stand: {data.cached_at
              ? new Date(data.cached_at).toLocaleDateString('de-DE', {
                day: '2-digit', month: '2-digit', year: 'numeric'
              })
              : '—'}
          </span>
        </div>
      </div>

      {/* Spectrum Bar */}
      {data.bias_distribution && (
        <SpectrumBar biasDistribution={data.bias_distribution} />
      )}

      {/* Synthesis */}
      {data.shared_perspectives && data.controversial_points && (
        <SynthesisCard
          shared={data.shared_perspectives}
          controversial={data.controversial_points}
        />
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900/60 border border-gray-800 rounded-xl p-1">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-150 ${activeTab === tab.id
              ? 'bg-gray-700 text-white shadow-sm'
              : 'text-gray-400 hover:text-white'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Überblick */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          <p className="text-gray-500 text-sm leading-relaxed">
            Wie viel berichtet jede politische Gruppe über dieses Thema?
          </p>
          {BIAS_SPECTRUM.filter(b => outletsByBias[b]).map(b => {
            const bias = BIAS_COLORS[b]
            const groupOutlets = outletsByBias[b]
            const groupTotal = groupOutlets.reduce((s, o) => s + o.article_count, 0)

            return (
              <div
                key={b}
                className="rounded-xl p-4 border"
                style={{ borderColor: `${bias.bg}80`, background: `${bias.bg}18` }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: bias.text }} />
                    <span className="font-semibold text-white text-sm">{bias.label}</span>
                    <span className="text-xs text-gray-500">
                      ({groupOutlets.map(o => o.source).join(', ')})
                    </span>
                  </div>
                  <span className="text-xs font-mono" style={{ color: bias.text }}>
                    {groupTotal} Artikel
                  </span>
                </div>

                {/* Top titles from this group */}
                <div className="space-y-1">
                  {groupOutlets.flatMap(o => o.sample_titles || []).slice(0, 3).map((title, i) => (
                    <p key={i} className="text-xs text-gray-400 truncate">
                      <span className="text-gray-600 mr-1.5">·</span>{title}
                    </p>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Tab: Medienhäuser */}
      {activeTab === 'outlets' && (
        <div className="space-y-3">
          <p className="text-gray-500 text-sm leading-relaxed">
            Detailansicht pro Medienhaus — Artikel-Anzahl, dominante Emotion und Beispiel-Titel.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {BIAS_SPECTRUM.flatMap(b =>
              (outletsByBias[b] || []).map(outlet => (
                <OutletCard key={outlet.source_id} outlet={outlet} />
              ))
            )}
          </div>
        </div>
      )}

    </div>
  )
}