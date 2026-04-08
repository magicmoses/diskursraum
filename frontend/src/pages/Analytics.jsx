import { useEffect, useState } from 'react'
import {
  getOverview, getArticlesPerDay, getCrawlHistory,
  getTrendingTopics, getPublishingTimes, getWeekdayActivity,
  getSourceDetails, getEmotionsPerBias, getEditorialProfiles,
} from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts'

// ── Constants ─────────────────────────────────────
const BIAS_COLORS = {
  'neutral': '#6b7280',
  'left-liberal': '#3b82f6',
  'left': '#1d4ed8',
  'conservative-liberal': '#f97316',
  'right-conservative': '#ef4444',
  'far-right': '#7f1d1d',
  'populist-mixed': '#a855f7',
  'economic-liberal': '#eab308',
}

const EMOTION_COLORS = {
  curiosity: '#60a5fa',
  optimism: '#34d399',
  annoyance: '#f97316',
  admiration: '#a78bfa',
  excitement: '#fbbf24',
  fear: '#f87171',
  sadness: '#94a3b8',
  anger: '#ef4444',
  disapproval: '#fb923c',
  approval: '#4ade80',
  confusion: '#c084fc',
  amusement: '#facc15',
  disappointment: '#64748b',
  surprise: '#38bdf8',
  joy: '#86efac',
  grief: '#475569',
}

const EMOTION_EMOJI = {
  curiosity: '🤔', optimism: '🌟', annoyance: '😤',
  admiration: '✨', excitement: '⚡', fear: '😨',
  sadness: '😢', anger: '🔥', disapproval: '👎',
  approval: '👍', confusion: '😕', amusement: '😄',
  disappointment: '😞', surprise: '😲', joy: '🎉',
  grief: '💔',
}

const WEEKDAYS = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']

// ── Sub-components ────────────────────────────────
function KpiCard({ label, value }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-gray-400 text-sm mb-1">{label}</div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}

function Section({ title, subtitle, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-200">{title}</h2>
        {subtitle && <p className="text-gray-500 text-sm mt-1">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

function EmotionBar({ emotion, pct, count }) {
  const color = EMOTION_COLORS[emotion] || '#6b7280'
  const emoji = EMOTION_EMOJI[emotion] || ''
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400 w-28 shrink-0 truncate">
        {emoji} {emotion}
      </span>
      <div className="flex-1 bg-gray-800 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs text-gray-500 w-10 text-right shrink-0">
        {pct}%
      </span>
    </div>
  )
}

function EditorialComparisonChart({ profiles }) {
  if (!profiles || Object.keys(profiles).length === 0) return (
    <div className="text-gray-500 text-sm text-center py-8">Keine Daten verfügbar</div>
  )

  const SOURCE_STYLE = {
    taz: { color: '#3bf63b', label: 'taz' },
    welt: { color: '#4744ef', label: 'Die Welt' },
    junge_freiheit: { color: '#7f1d1d', label: 'Junge Freiheit' },
  }

  // Find emotions present in at least 2 of 3 sources
  const emotionSets = Object.entries(SOURCE_STYLE).map(([sourceId]) => {
    const profile = profiles[sourceId]
    if (!profile || profile.error) return new Set()
    return new Set(profile.top_emotions?.map(e => e.emotion) || [])
  })

  const sharedEmotions = [...new Set([...emotionSets[0], ...emotionSets[1], ...emotionSets[2]])]
    .filter(emotion => emotionSets.filter(s => s.has(emotion)).length >= 2)
    .slice(0, 8)

  // Build chart data
  const chartData = sharedEmotions.map(emotion => {
    const point = {
      emotion: `${EMOTION_EMOJI[emotion] || ''} ${emotion}`,
    }
    Object.entries(SOURCE_STYLE).forEach(([sourceId]) => {
      const profile = profiles[sourceId]
      if (!profile || profile.error) { point[sourceId] = 0; return }
      const found = profile.top_emotions?.find(e => e.emotion === emotion)
      point[sourceId] = found ? found.pct : 0
    })
    return point
  })

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
        <XAxis
          dataKey="emotion"
          stroke="#6b7280"
          tick={{ fontSize: 11, fill: '#9ca3af' }}
        />
        <YAxis
          stroke="#6b7280"
          tick={{ fontSize: 11 }}
          unit="%"
        />
        <Tooltip
          contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }}
          formatter={(v, name) => [`${v}%`, SOURCE_STYLE[name]?.label || name]}
        />
        <Legend
          iconType="circle"
          wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }}
          formatter={name => SOURCE_STYLE[name]?.label || name}
        />
        {Object.entries(SOURCE_STYLE).map(([sourceId, style]) => (
          <Bar
            key={sourceId}
            dataKey={sourceId}
            name={sourceId}
            fill={style.color}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Main Component ────────────────────────────────
export default function Analytics() {
  const [overview, setOverview] = useState(null)
  const [articlesPerDay, setArticlesPerDay] = useState([])
  const [crawlHistory, setCrawlHistory] = useState([])
  const [trendingTopics, setTrendingTopics] = useState([])
  const [publishingTimes, setPublishingTimes] = useState([])
  const [weekdayActivity, setWeekdayActivity] = useState([])
  const [sourceDetails, setSourceDetails] = useState([])
  const [emotionsPerBias, setEmotionsPerBias] = useState({})
  const [editorialProfiles, setEditorialProfiles] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getOverview(),
      getArticlesPerDay(),
      getCrawlHistory(),
      getPublishingTimes(),
      getWeekdayActivity(),
      getSourceDetails(),
      getEmotionsPerBias(),
      getEditorialProfiles(14),
    ]).then(([ov, apd, ch, pt, wa, sd, epb, ep]) => {
      setOverview(ov)
      setArticlesPerDay(apd)
      setCrawlHistory(ch.slice(0, 20).reverse())
      setPublishingTimes(pt)
      setWeekdayActivity(wa)
      setSourceDetails(sd)
      setEmotionsPerBias(epb)
      console.log('emotionsPerBias:', epb)
      setEditorialProfiles(ep)
      setLoading(false)
    })

    // Trending Topics lazy — lädt nach
    getTrendingTopics(7, 5).then(tt => setTrendingTopics(tt))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-400">
      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-3" />
      Lade Analytics...
    </div>
  )

  // ── Data prep ──────────────────────────────────
  const weekdayTotals = WEEKDAYS.map(day => ({
    day,
    count: weekdayActivity
      .filter(r => r.weekday === day)
      .reduce((s, r) => s + r.count, 0)
  }))

  const hourTotals = Array.from({ length: 24 }, (_, h) => ({
    hour: `${h}`,
    count: publishingTimes
      .filter(r => r.hour === h)
      .reduce((s, r) => s + r.count, 0)
  }))

  const profileEntries = Object.values(editorialProfiles).filter(p => !p.error)

  const PROFILE_LABELS = {
    taz: { label: 'taz', bias: 'left', color: '#1d4ed8' },
    welt: { label: 'Die Welt', bias: 'right-conservative', color: '#ef4444' },
    junge_freiheit: { label: 'Junge Freiheit', bias: 'far-right', color: '#7f1d1d' },
  }

  return (
    <div className="space-y-8 pb-16">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-1">Data Analytics</h1>
        <p className="text-gray-400 text-sm">
          {overview.total_articles.toLocaleString()} Artikel · 15 Quellen · Live
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Artikel gesamt" value={overview.total_articles.toLocaleString()} />
        <KpiCard label="Quellen" value="15" />
        <KpiCard label="Letzter Crawl" value={
          overview.last_crawl.crawled_at
            ? new Date(overview.last_crawl.crawled_at).toLocaleTimeString('de-DE', {
              hour: '2-digit', minute: '2-digit'
            })
            : '—'
        } />
        <KpiCard label="Neu (letzter Crawl)" value={overview.last_crawl.new_articles} />
      </div>

      {/* Trending Topics — Top 5 */}
      <Section
        title="Trending Topics"
        subtitle="Meistdiskutierte Themen der letzten 7 Tage"
      >
        {trendingTopics.length === 0 ? (
          <div className="text-gray-500 text-sm">Wird geladen...</div>
        ) : (
          <div className="space-y-2">
            {trendingTopics.slice(0, 5).map((topic, i) => {
              const max = trendingTopics[0]?.article_count || 1
              const pct = (topic.article_count / max * 100).toFixed(0)
              return (
                <div key={topic.topic} className="flex items-center gap-3">
                  <span className="text-gray-600 font-mono text-sm w-4">{i + 1}</span>
                  <span className="text-white text-sm w-40 shrink-0">{topic.topic}</span>
                  <div className="flex-1 bg-gray-800 rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-blue-500 transition-all duration-700"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-gray-500 text-xs w-16 text-right shrink-0">
                    {topic.article_count} Art.
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </Section>

      {/* Articles per Source */}
      <Section title="Artikel pro Quelle">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={overview.by_source} layout="vertical">
            <XAxis type="number" stroke="#6b7280" tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="source" width={170} stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }}
              formatter={(v, name, props) => [
                `${v} Artikel/Tag · ${props.payload.active_days} Tage gecrawlt`
              ]}
            />
            <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Avg Articles per Day */}
      <Section
        title="Durchschnittliche Artikel pro Tag"
        subtitle="Pro Medienhaus — Farbe zeigt politische Ausrichtung · Hover für Details"
      >
        <ResponsiveContainer width="100%" height={420}>
          <BarChart data={sourceDetails} layout="vertical">
            <XAxis type="number" stroke="#6b7280" tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="source" width={170} stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }}
              formatter={v => [`${v} Artikel/Tag`]}
            />
            <Bar dataKey="avg_per_day" radius={[0, 4, 4, 0]}>
              {sourceDetails.map(entry => (
                <Cell key={entry.source} fill={BIAS_COLORS[entry.bias] || '#6b7280'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Bias Distribution */}
      <Section title="Bias-Verteilung" subtitle="Politische Ausrichtung aller Artikel">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={overview.by_bias}
              dataKey="count"
              nameKey="bias"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={({ bias, percent }) =>
                percent > 0.04 ? `${bias} ${(percent * 100).toFixed(0)}%` : ''
              }
              labelLine={false}
            >
              {overview.by_bias.map(entry => (
                <Cell key={entry.bias} fill={BIAS_COLORS[entry.bias] || '#6b7280'} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }} />
          </PieChart>
        </ResponsiveContainer>
      </Section>

      {/* Emotional Tone per Bias */}
      <Section
        title="Emotionaler Ton per politischer Ausrichtung"
        subtitle="Dominant-Emotionen ohne Neutral — zeigt den emotionalen Subtext des Diskurses"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(emotionsPerBias)
            .filter(([, emotions]) => Array.isArray(emotions) && emotions.length > 0)
            .sort((a, b) => {
              const order = ['left', 'left-liberal', 'neutral', 'conservative-liberal', 'economic-liberal', 'right-conservative', 'populist-mixed', 'far-right']
              return order.indexOf(a[0]) - order.indexOf(b[0])
            })
            .map(([bias, emotions]) => (
              <div key={bias} className="space-y-2">
                <div className="flex items-center gap-2 mb-3">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: BIAS_COLORS[bias] || '#6b7280' }}
                  />
                  <span className="text-sm font-medium text-gray-300 capitalize">
                    {bias}
                    <span className="text-gray-600 font-normal text-xs ml-1">
                      ({({
                        'left': 'taz',
                        'left-liberal': 'Spiegel, Zeit, SZ, Stern',
                        'neutral': 'Tagesschau, ZDF, DW',
                        'conservative-liberal': 'FAZ, Cicero',
                        'right-conservative': 'WELT, Focus',
                        'far-right': 'Junge Freiheit',
                        'economic-liberal': 'Handelsblatt',
                        'populist-mixed': 'BILD',
                      }[bias] || bias)})
                    </span>
                  </span>
                </div>
                {emotions.map(e => (
                  <EmotionBar key={e.emotion} emotion={e.emotion} pct={e.pct} count={e.count} />
                ))}
              </div>
            ))
          }
        </div>
      </Section>

      {/* GroupedBar Chart — taz vs WELT vs Junge Freiheit */}
      <Section
        title="Emotionaler Vergleich — Links vs. Rechts"
        subtitle="taz · Die Welt · Junge Freiheit — Emotionen die bei mindestens 2 Quellen in den Top 5 sind"
      >
        <EditorialComparisonChart profiles={editorialProfiles} />
      </Section>

      {/* Publishing Hours */}
      <Section
        title="Veröffentlichungszeiten (UTC)"
        subtitle="Wann werden Artikel publiziert?"
      >
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={hourTotals}>
            <XAxis dataKey="hour" stroke="#6b7280" tick={{ fontSize: 10 }}
              tickFormatter={h => `${h}h`}
            />
            <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }}
              formatter={v => [`${v} Artikel`]}
              labelFormatter={h => `${h}:00 UTC`}
            />
            <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Weekday Activity */}
      <Section
        title="Aktivität nach Wochentag"
        subtitle="Wann wird am meisten publiziert?"
      >
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={weekdayTotals}>
            <XAxis dataKey="day" stroke="#6b7280" tick={{ fontSize: 12 }} />
            <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }}
              formatter={v => [`${v} Artikel`]}
            />
            <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Articles per Day */}
      <Section title="Artikel pro Tag" subtitle="Wachstum der Datenbasis">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={articlesPerDay}>
            <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }} />
            <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      {/* Crawl History */}
      <Section title="Crawl-Aktivität" subtitle="Letzte 20 Crawl-Runs">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={crawlHistory}>
            <XAxis
              dataKey="crawled_at"
              stroke="#6b7280"
              tick={{ fontSize: 10 }}
              tickFormatter={v => new Date(v).toLocaleTimeString('de-DE', {
                hour: '2-digit', minute: '2-digit'
              })}
            />
            <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px' }}
              labelFormatter={v => new Date(v).toLocaleString('de-DE')}
            />
            <Bar dataKey="articles_new" fill="#10b981" name="Neue Artikel" radius={[4, 4, 0, 0]} />
            <Bar dataKey="articles_found" fill="#374151" name="Gefunden" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

    </div>
  )
}