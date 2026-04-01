import { useEffect, useState } from 'react'
import { getOverview, getArticlesPerDay, getBiasOverTime, getCrawlHistory } from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
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

export default function Analytics() {
  const [overview, setOverview] = useState(null)
  const [articlesPerDay, setArticlesPerDay] = useState([])
  const [biasOverTime, setBiasOverTime] = useState([])
  const [crawlHistory, setCrawlHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getOverview(),
      getArticlesPerDay(),
      getBiasOverTime(),
      getCrawlHistory(),
    ]).then(([ov, apd, bot, ch]) => {
      setOverview(ov)
      setArticlesPerDay(apd)
      setBiasOverTime(bot)
      setCrawlHistory(ch.slice(0, 20).reverse())
      setLoading(false)
    })
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-400">
      Loading analytics...
    </div>
  )

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
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={overview.by_source} layout="vertical">
            <XAxis type="number" stroke="#6b7280" />
            <YAxis type="category" dataKey="source" width={160} stroke="#6b7280" tick={{ fontSize: 12 }} />
            <Tooltip contentStyle={{ background: '#1f2937', border: 'none' }} />
            <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* Bias Distribution */}
      <Section title="Bias Distribution">
        <div className="flex flex-col md:flex-row items-center gap-8">
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
        </div>
      </Section>

      {/* Articles per Day */}
      <Section title="Articles Collected per Day">
        <ResponsiveContainer width="100%" height={250}>
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
        <ResponsiveContainer width="100%" height={250}>
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