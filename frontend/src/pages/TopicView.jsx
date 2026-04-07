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

// ── Loading State ─────────────────────────────────
function LoadingState() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-gray-500 text-sm">Lade Analyse...</p>
    </div>
  )
}

// ── Empty State ───────────────────────────────────
function EmptyState({ onBack }) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-6 text-center px-4">
      <div className="text-5xl">🔄</div>
      <div>
        <p className="text-white font-semibold text-lg mb-2">Analyse noch nicht verfügbar</p>
        <p className="text-gray-400 text-sm max-w-sm">
          Dieses Thema wird beim nächsten täglichen ML-Run analysiert.
          Schau später nochmal vorbei.
        </p>
      </div>
      <button
        onClick={onBack}
        className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
      >
        ← Zurück zur Übersicht
      </button>
    </div>
  )
}

// ── Bridging Card ─────────────────────────────────
function BridgingCard({ article, rank }) {
  const bias = BIAS_COLORS[article.bias] || BIAS_COLORS['neutral']
  const scorePercent = Math.min(article.bridging_score * 300, 100)

  return (
    <article className="group bg-gray-900/60 border border-gray-800 rounded-2xl p-5 hover:border-gray-600 hover:bg-gray-900 transition-all duration-200">
      <div className="flex gap-4">

        {/* Rank */}
        <div className="shrink-0 w-8 pt-0.5">
          <span className="text-xl font-bold text-gray-700 group-hover:text-gray-500 transition-colors">
            {rank}
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-white font-medium leading-snug mb-3 group-hover:text-blue-100 transition-colors">
            {article.title}
          </h3>

          {/* Meta row */}
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md font-medium"
              style={{ background: bias.bg, color: bias.text }}
            >
              {bias.label}
            </span>
            <span className="text-gray-500 text-xs">{article.source}</span>
            {article.emotion && article.emotion !== 'neutral' && (
              <span className="text-gray-500 text-xs">
                {EMOTION_EMOJI[article.emotion] || ''} {article.emotion}
              </span>
            )}
            {article.url && (

              <button
                onClick={() => window.open(article.url, '_blank')}
                className="text-xs text-blue-500 hover:text-blue-400 transition-colors ml-auto"
              >
                Lesen →
              </button>
            )}
          </div>

          {/* Score bar */}
          <div className="mt-3 flex items-center gap-3">
            <div className="flex-1 bg-gray-800 rounded-full h-1">
              <div
                className="h-1 rounded-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-500"
                style={{ width: `${scorePercent}%` }}
              />
            </div>
            <span className="text-blue-400 text-xs font-mono shrink-0">
              {(article.bridging_score * 100).toFixed(1)}
            </span>
          </div>
        </div>

      </div>
    </article >
  )
}

// ── Cluster Card ──────────────────────────────────
function ClusterCard({ cluster }) {
  const bias = BIAS_COLORS[cluster.bias] || BIAS_COLORS['neutral']
  const sources = Object.entries(cluster.sources || {})

  return (
    <div
      className="rounded-2xl p-5 border"
      style={{ borderColor: bias.bg, background: `${bias.bg}18` }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full shrink-0"
            style={{ background: bias.text }}
          />
          <span className="font-semibold text-white">{bias.label}</span>
        </div>
        <span className="text-xs font-mono" style={{ color: bias.text }}>
          {cluster.article_count} Artikel
        </span>
      </div>

      {/* Sources */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {sources.map(([sourceId, articles]) => (
          <span
            key={sourceId}
            className="text-xs px-2 py-1 rounded-lg"
            style={{ background: `${bias.bg}60`, color: bias.text }}
          >
            {articles[0]?.source} · {articles.length}
          </span>
        ))}
      </div>

      {/* Sample titles */}
      <div className="space-y-1.5 border-t border-white/5 pt-3">
        {cluster.sample_titles?.slice(0, 3).map((title, i) => (
          <p key={i} className="text-xs text-gray-400 truncate leading-relaxed">
            <span className="text-gray-600 mr-1.5">·</span>{title}
          </p>
        ))}
      </div>
    </div>
  )
}

// ── Spectrum Bar ──────────────────────────────────
function SpectrumBar({ clusters }) {
  const total = Object.values(clusters).reduce((s, c) => s + c.article_count, 0)
  if (total === 0) return null

  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">
        Politisches Spektrum
      </p>
      <div className="flex rounded-full overflow-hidden h-3 gap-px">
        {BIAS_SPECTRUM.filter(b => clusters[b]).map(b => {
          const cluster = clusters[b]
          const pct = (cluster.article_count / total * 100).toFixed(1)
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
    </div>
  )
}

// ── Main Component ────────────────────────────────
export default function TopicView() {
  const { topicId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('bridging')

  useEffect(() => {
    setLoading(true)
    setData(null)
    getTopicAnalysis(topicId)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [topicId])

  if (loading) return <LoadingState />

  if (!data || data.error) return <EmptyState onBack={() => navigate('/')} />

  const clusters = data.bias_clusters || {}
  const orderedClusters = BIAS_SPECTRUM
    .filter(b => clusters[b])
    .map(b => clusters[b])

  const tabs = [
    { id: 'bridging', label: '🌉 Bridging' },
    { id: 'clusters', label: '🗂 Cluster' },
  ]

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-16">

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
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{data.article_count} Artikel</span>
          <span>·</span>
          <span>{Object.keys(clusters).length} Bias-Gruppen</span>
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
      <SpectrumBar clusters={clusters} />

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

      {/* Tab: Bridging Statements */}
      {activeTab === 'bridging' && (
        <div className="space-y-3">
          <p className="text-gray-500 text-sm leading-relaxed">
            Aussagen die über ideologisch unterschiedliche Gruppen hinweg Zustimmung finden —
            nicht nur innerhalb der eigenen Echo-Kammer.
          </p>
          {data.top_bridging_statements?.length > 0
            ? data.top_bridging_statements.map((article, i) => (
              <BridgingCard key={i} article={article} rank={i + 1} />
            ))
            : (
              <div className="text-center py-12 text-gray-500">
                Keine Bridging Statements gefunden.
              </div>
            )
          }
        </div>
      )}

      {/* Tab: Bias Clusters */}
      {activeTab === 'clusters' && (
        <div className="space-y-3">
          <p className="text-gray-500 text-sm leading-relaxed">
            Wie verschiedene Medien-Bias-Gruppen dieses Thema behandeln.
            Geordnet von links nach rechts auf dem politischen Spektrum.
          </p>
          {orderedClusters.length > 0
            ? orderedClusters.map(cluster => (
              <ClusterCard key={cluster.bias} cluster={cluster} />
            ))
            : (
              <div className="text-center py-12 text-gray-500">
                Keine Cluster-Daten verfügbar.
              </div>
            )
          }
        </div>
      )}

    </div>
  )
}