import { useEffect, useState } from 'react'
import {
  getOverview, getArticlesPerDay, getCrawlHistory,
  getTrendingTopics, getPublishingTimes, getWeekdayActivity,
  getSourceDetails, getSentimentPerSource, getSentimentPerBias,
  getLeftRightComparison, getNeutralityCheck
} from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, Legend
} from 'recharts'

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

const SENTIMENT_COLORS = {
  'positive': '#10b981',
  'negative': '#ef4444',
  'neutral': '#6b7280',
}

const WEEKDAYS = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']

export default function Analytics() {
  const [overview, setOverview] = useState(null)
  const [articlesPerDay, setArticlesPerDay] = useState([])
  const [crawlHistory, setCrawlHistory] = useState([])
  const [trendingTopics, setTrendingTopics] = useState([])
  const [publishingTimes, setPublishingTimes] = useState([])
  const [weekdayActivity, setWeekdayActivity] = useState([])
  const [sourceDetails, setSourceDetails] = useState([])
  const [sentimentPerSource, setSentimentPerSource] = useState([])
  const [sentimentPerBias, setSentimentPerBias] = useState([])
  const [leftRightComparison, setLeftRightComparison] = useState(null)
  const [neutralityCheck, setNeutralityCheck] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Schnelle Endpoints zuerst
    Promise.all([
      getOverview(),
      getArticlesPerDay(),
      getCrawlHistory(),
      getPublishingTimes(),
      getWeekdayActivity(),
      getSourceDetails(),
      getSentimentPerSource(),
      getSentimentPerBias(),
      getLeftRightComparison(14),
      getNeutralityCheck(),
    ]).then(([ov, apd, ch, pt, wa, sd, sps, spb, lrc, nc]) => {
      setOverview(ov)
      setArticlesPerDay(apd)
      setCrawlHistory(ch.slice(0, 20).reverse())
      setPublishingTimes(pt)
      setWeekdayActivity(wa)
      setSourceDetails(sd)
      setSentimentPerSource(sps)
      setSentimentPerBias(spb)
      setLeftRightComparison(lrc)
      setNeutralityCheck(nc)
      setLoading(false)
    })

    // Trending Topics separat — lädt nach
    getTrendingTopics(7, 20).then(tt => setTrendingTopics(tt))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-400">
      Loading analytics...
    </div>
  )

  // ── Data prep ────────────────────────────────
  // Sentiment per bias — pivot
  const biasGroups = [...new Set(sentimentPerBias.map(r => r.bias))]
  const sentimentByBias = biasGroups.map(bias => {
    const rows = sentimentPerBias.filter(r => r.bias === bias)
    const total = rows.reduce((s, r) => s + r.count, 0)
    const obj = { bias }
    rows.forEach(r => {
      obj[r.sentiment] = Math.round(r.count * 100 / total)
    })
    return obj
  })

  // Weekday activity — aggregate
  const weekdayTotals = WEEKDAYS.map((day, idx) => ({
    day,
    count: weekdayActivity
      .filter(r => r.weekday === day)
      .reduce((s, r) => s + r.count, 0)
  }))

  // Publishing hours — aggregate all sources
  const hourTotals = Array.from({ length: 24 }, (_, h) => ({
    hour: `${h}:00`,
    count: publishingTimes
      .filter(r => r.hour === h)
      .reduce((s, r) => s + r.count, 0)
  }))

  return (
    <div className="space-y-10">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-1">Data Analytics</h1>
        <p className="text-gray-400">
          Live stats from {overview.total_articles.toLocaleString()} articles
          across 15 German news sources
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Total Articles" value={overview.total_articles.toLocaleString()} />
        <KpiCard label="News Sources" value="15" />
        <KpiCard label="Last Crawl" value={
          overview.last_crawl.crawled_at
            ? new Date(overview.last_crawl.crawled_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
            : '—'
        } />
        <KpiCard label="New (last crawl)" value={overview.last_crawl.new_articles} />
      </div>

      {/* Articles per Source */}
      <Section title="Articles per Source">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={overview.by_source} layout="vertical">
            <XAxis type="number" stroke="#6b7280" />
            <YAxis type="category" dataKey="source" width={170} stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none' }} />
            <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Avg Articles per Day per Source */}
      <Section title="Avg. Articles per Day per Source">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={sourceDetails} layout="vertical">
            <XAxis type="number" stroke="#6b7280" />
            <YAxis type="category" dataKey="source" width={170} stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: 'none' }}
              formatter={(v, n) => [v, n === 'avg_per_day' ? 'Avg/Day' : n]}
            />
            <Bar dataKey="avg_per_day" radius={[0, 4, 4, 0]}>
              {sourceDetails.map((entry) => (
                <Cell key={entry.source} fill={BIAS_COLORS[entry.bias] || '#6b7280'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Bias Distribution */}
      <Section title="Bias Distribution">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={overview.by_bias}
              dataKey="count"
              nameKey="bias"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={({ bias, percent }) => `${bias} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {overview.by_bias.map((entry) => (
                <Cell key={entry.bias} fill={BIAS_COLORS[entry.bias] || '#6b7280'} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none' }} />
          </PieChart>
        </ResponsiveContainer>
      </Section>

      {/* Sentiment per Bias */}
      <Section title="Sentiment Distribution per Bias Group">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sentimentByBias}>
            <XAxis dataKey="bias" stroke="#6b7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6b7280" unit="%" />
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none' }} />
            <Legend />
            <Bar dataKey="positive" stackId="a" fill={SENTIMENT_COLORS.positive} name="Positiv" />
            <Bar dataKey="neutral" stackId="a" fill={SENTIMENT_COLORS.neutral} name="Neutral" />
            <Bar dataKey="negative" stackId="a" fill={SENTIMENT_COLORS.negative} name="Negativ" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Neutrality Check */}
      <Section title="Neutralitäts-Check — Wie neutral sind die neutralen Quellen?">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="text-left py-2">Bias</th>
                <th className="text-right py-2">Positiv %</th>
                <th className="text-right py-2">Neutral %</th>
                <th className="text-right py-2">Negativ %</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(
                neutralityCheck.reduce((acc, row) => {
                  if (!acc[row.bias]) acc[row.bias] = {}
                  acc[row.bias][row.sentiment] = row.percentage
                  return acc
                }, {})
              ).map(([bias, sentiments]) => (
                <tr key={bias} className="border-b border-gray-800">
                  <td className="py-2">
                    <span
                      className="px-2 py-0.5 rounded text-xs text-white"
                      style={{ background: BIAS_COLORS[bias] || '#6b7280' }}
                    >
                      {bias}
                    </span>
                  </td>
                  <td className="text-right py-2 text-green-400">{sentiments.positive || 0}%</td>
                  <td className="text-right py-2 text-gray-400">{sentiments.neutral || 0}%</td>
                  <td className="text-right py-2 text-red-400">{sentiments.negative || 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* Left vs Right Comparison */}
      {leftRightComparison && (
        <Section title="Links vs. Rechts — taz vs. Junge Freiheit vs. Die Welt">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.values(leftRightComparison).map(source => (
              source.error ? null :
                <div key={source.source_id} className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span
                      className="px-2 py-0.5 rounded text-xs text-white"
                      style={{ background: BIAS_COLORS[source.bias] || '#6b7280' }}
                    >
                      {source.bias}
                    </span>
                    <span className="font-medium text-white capitalize">{source.source_id}</span>
                  </div>
                  <div className="text-gray-400 text-sm">{source.total_articles} Artikel</div>

                  {/* Sentiment bars */}
                  <div className="space-y-1">
                    {['positive', 'negative', 'neutral'].map(s => (
                      <div key={s} className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-14">{s}</span>
                        <div className="flex-1 bg-gray-800 rounded-full h-2">
                          <div
                            className="h-2 rounded-full"
                            style={{
                              width: `${source.sentiment_pct[s] || 0}%`,
                              background: SENTIMENT_COLORS[s]
                            }}
                          />
                        </div>
                        <span className="text-xs text-gray-400 w-8">{source.sentiment_pct[s] || 0}%</span>
                      </div>
                    ))}
                  </div>

                  {/* Top keywords */}
                  <div className="flex flex-wrap gap-1 mt-2">
                    {source.top_keywords?.slice(0, 8).map(kw => (
                      <span key={kw.keyword} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">
                        {kw.keyword}
                      </span>
                    ))}
                  </div>
                </div>
            ))}
          </div>
        </Section>
      )}

      {/* Publishing Hours */}
      <Section title="Publishing Activity by Hour (UTC)">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={hourTotals}>
            <XAxis dataKey="hour" stroke="#6b7280" tick={{ fontSize: 10 }} />
            <YAxis stroke="#6b7280" />
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none' }} />
            <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Weekday Activity */}
      <Section title="Publishing Activity by Weekday">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={weekdayTotals}>
            <XAxis dataKey="day" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none' }} />
            <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Articles per Day */}
      <Section title="Articles Collected per Day">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={articlesPerDay}>
            <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 11 }} />
            <YAxis stroke="#6b7280" />
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none' }} />
            <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      {/* Crawl History */}
      <Section title="Recent Crawl Activity (last 20)">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={crawlHistory}>
            <XAxis dataKey="crawled_at" stroke="#6b7280" tick={{ fontSize: 10 }}
              tickFormatter={(v) => new Date(v).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
            />
            <YAxis stroke="#6b7280" />
            <Tooltip
              contentStyle={{ background: '#1f2937', border: 'none' }}
              labelFormatter={(v) => new Date(v).toLocaleString('de-DE')}
            />
            <Bar dataKey="articles_new" fill="#10b981" name="New Articles" radius={[4, 4, 0, 0]} />
            <Bar dataKey="articles_found" fill="#374151" name="Total Found" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Trending Topics */}
      <Section title="Trending Topics (letzte 7 Tage)">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {trendingTopics.map(topic => (
            <div key={topic.topic} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
              <div className="font-medium text-white text-sm mb-1">{topic.topic}</div>
              <div className="text-gray-400 text-xs">{topic.article_count} Artikel</div>
              <div className="text-gray-500 text-xs">{topic.source_count} Quellen</div>
              {topic.is_core && <div className="mt-1 text-xs text-blue-500">Kernthema</div>}
            </div>
          ))}
        </div>
      </Section>

    </div>
  )
}

function KpiCard({ label, value }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="text-gray-400 text-sm mb-1">{label}</div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4 text-gray-200">{title}</h2>
      {children}
    </div>
  )
}