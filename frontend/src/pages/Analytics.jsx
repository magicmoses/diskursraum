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
import { KpiCard, Section, Loader } from '../components/ui'
import { EmotionBar } from '../components/charts'
import {
  BIAS_COLORS, BIAS_LABELS, EMOTION_COLORS,
  TOOLTIP_STYLE, WEEKDAYS,
} from '../constants/colors'

// ── EditorialComparisonChart ──────────────────────
// Analytics-spezifisch — bleibt hier
function EditorialComparisonChart({ profiles }) {
  if (!profiles || Object.keys(profiles).length === 0) return (
    <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: 'var(--space-8)' }}>
      Keine Daten verfügbar
    </div>
  )

  const SOURCE_STYLE = {
    taz: { color: '#4A7C9E', label: 'taz' },
    welt: { color: '#B85C38', label: 'Die Welt' },
    junge_freiheit: { color: '#7A3B2E', label: 'Junge Freiheit' },
  }

  const emotionSets = Object.entries(SOURCE_STYLE).map(([sourceId]) => {
    const profile = profiles[sourceId]
    if (!profile || profile.error) return new Set()
    return new Set(profile.top_emotions?.map(e => e.emotion) || [])
  })

  const sharedEmotions = [...new Set([...emotionSets[0], ...emotionSets[1], ...emotionSets[2]])]
    .filter(emotion => emotionSets.filter(s => s.has(emotion)).length >= 2)
    .slice(0, 8)

  const chartData = sharedEmotions.map(emotion => {
    const point = { emotion }
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
      <BarChart data={chartData} margin={{ top: 8, right: 16, bottom: 16, left: 0 }}>
        <XAxis dataKey="emotion" stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)', fontFamily: 'var(--font-body)' }} />
        <YAxis stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} unit="%" />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, name) => [`${v}%`, SOURCE_STYLE[name]?.label || name]} />
        <Legend iconType="square" wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }} formatter={name => SOURCE_STYLE[name]?.label || name} />
        {Object.entries(SOURCE_STYLE).map(([sourceId, style]) => (
          <Bar key={sourceId} dataKey={sourceId} name={sourceId} fill={style.color} radius={[1, 1, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Main ──────────────────────────────────────────
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
      getOverview(), getArticlesPerDay(), getCrawlHistory(),
      getPublishingTimes(), getWeekdayActivity(), getSourceDetails(),
      getEmotionsPerBias(), getEditorialProfiles(14),
    ]).then(([ov, apd, ch, pt, wa, sd, epb, ep]) => {
      setOverview(ov)
      setArticlesPerDay(apd)
      setCrawlHistory(ch.slice(0, 20).reverse())
      setPublishingTimes(pt)
      setWeekdayActivity(wa)
      setSourceDetails(sd)
      setEmotionsPerBias(epb)
      setEditorialProfiles(ep)
      setLoading(false)
    })
    getTrendingTopics(7, 5).then(tt => setTrendingTopics(tt))
  }, [])

  if (loading) return <Loader text="Lade Analytics..." />

  const weekdayTotals = WEEKDAYS.map(day => ({
    day,
    count: weekdayActivity.filter(r => r.weekday === day).reduce((s, r) => s + r.count, 0)
  }))

  const hourTotals = Array.from({ length: 24 }, (_, h) => ({
    hour: `${h}h`,
    count: publishingTimes.filter(r => r.hour === h).reduce((s, r) => s + r.count, 0)
  }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', paddingBottom: 'var(--space-16)' }}>

      {/* ── Header ──────────────────────────────── */}
      <div className="fade-up" style={{ paddingTop: 'var(--space-8)' }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--signal)',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          marginBottom: 'var(--space-3)',
        }}>
          Project Analytics
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(28px, 4vw, 40px)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          marginBottom: 'var(--space-2)',
        }}>
          Data Analytics
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
          {overview.total_articles.toLocaleString()} Artikel · 15 Quellen · Live
        </p>
      </div>

      {/* ── KPIs ────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1px', background: 'var(--border)' }}>
        <KpiCard label="Artikel gesamt" value={overview.total_articles.toLocaleString()} />
        <KpiCard label="Quellen" value="15" />
        <KpiCard label="Letzter Crawl" mono value={
          overview.last_crawl.crawled_at
            ? new Date(overview.last_crawl.crawled_at).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
            : '—'
        } />
        <KpiCard label="Neu (letzter Crawl)" mono value={overview.last_crawl.new_articles} />
      </div>

      {/* ── Trending Topics ──────────────────────── */}
      <Section label="Live" title="Trending Topics" subtitle="Meistdiskutierte Themen der letzten 7 Tage">
        {trendingTopics.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>Wird geladen...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {trendingTopics.slice(0, 5).map((topic, i) => {
              const max = trendingTopics[0]?.article_count || 1
              const pct = (topic.article_count / max * 100).toFixed(0)
              return (
                <div key={topic.topic} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', width: '16px' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)', width: '160px', flexShrink: 0 }}>
                    {topic.topic}
                  </span>
                  <div style={{ flex: 1, height: '3px', background: 'var(--bg-elevated)' }}>
                    <div style={{ height: '3px', width: `${pct}%`, background: 'var(--signal)', transition: 'width 700ms ease' }} />
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', width: '60px', textAlign: 'right' }}>
                    {topic.article_count} Art.
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </Section>

      {/* ── Artikel pro Quelle ───────────────────── */}
      <Section title="Artikel pro Quelle">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={overview.by_source} layout="vertical" margin={{ left: 8 }}>
            <XAxis type="number" stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <YAxis type="category" dataKey="source" width={170} stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v} Artikel`]} />
            <Bar dataKey="count" fill="var(--signal)" radius={[0, 1, 1, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* ── Durchschnitt pro Tag ─────────────────── */}
      <Section title="Durchschnittliche Artikel pro Tag" subtitle="Farbe zeigt politische Ausrichtung">
        <ResponsiveContainer width="100%" height={420}>
          <BarChart data={sourceDetails} layout="vertical" margin={{ left: 8 }}>
            <XAxis type="number" stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <YAxis type="category" dataKey="source" width={170} stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v} Artikel/Tag`]} />
            <Bar dataKey="avg_per_day" radius={[0, 1, 1, 0]}>
              {sourceDetails.map(entry => (
                <Cell key={entry.source} fill={BIAS_COLORS[entry.bias] || 'var(--text-muted)'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* ── Bias Verteilung ──────────────────────── */}
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
              strokeWidth={0}
              label={({ bias, percent }) => percent > 0.04 ? `${bias} ${(percent * 100).toFixed(0)}%` : ''}
              labelLine={false}
            >
              {overview.by_bias.map(entry => (
                <Cell key={entry.bias} fill={BIAS_COLORS[entry.bias] || 'var(--text-muted)'} />
              ))}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </PieChart>
        </ResponsiveContainer>
      </Section>

      {/* ── Emotionaler Ton ──────────────────────── */}
      <Section title="Emotionaler Ton" subtitle="Dominant-Emotionen ohne Neutral — emotionaler Subtext des Diskurses">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-8)' }}>
          {Object.entries(emotionsPerBias)
            .filter(([, emotions]) => Array.isArray(emotions) && emotions.length > 0)
            .sort((a, b) => {
              const order = ['left', 'left-liberal', 'neutral', 'conservative-liberal', 'economic-liberal', 'right-conservative', 'populist-mixed', 'far-right']
              return order.indexOf(a[0]) - order.indexOf(b[0])
            })
            .map(([bias, emotions]) => (
              <div key={bias}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
                  <div style={{ width: '8px', height: '8px', background: BIAS_COLORS[bias] || 'var(--text-muted)', flexShrink: 0 }} />
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)', fontWeight: 500 }}>
                    {bias}
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {BIAS_LABELS[bias] || ''}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {emotions.map(e => <EmotionBar key={e.emotion} emotion={e.emotion} pct={e.pct} />)}
                </div>
              </div>
            ))
          }
        </div>
      </Section>

      {/* ── Links vs. Rechts ─────────────────────── */}
      <Section title="Links vs. Rechts" subtitle="taz · Die Welt · Junge Freiheit — Emotionen in den Top 5 von mindestens 2 Quellen">
        <EditorialComparisonChart profiles={editorialProfiles} />
      </Section>

      {/* ── Veröffentlichungszeiten ──────────────── */}
      <Section title="Veröffentlichungszeiten (UTC)" subtitle="Wann werden Artikel publiziert?">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={hourTotals} margin={{ left: 0 }}>
            <XAxis dataKey="hour" stroke="var(--border)" tick={{ fontSize: 10, fill: 'var(--text-secondary)' }} />
            <YAxis stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v} Artikel`]} />
            <Bar dataKey="count" fill="var(--patina)" radius={[1, 1, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* ── Wochentag ────────────────────────────── */}
      <Section title="Aktivität nach Wochentag">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={weekdayTotals}>
            <XAxis dataKey="day" stroke="var(--border)" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
            <YAxis stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v} Artikel`]} />
            <Bar dataKey="count" fill="var(--amber)" radius={[1, 1, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      {/* ── Datenbasis-Wachstum ───────────────────── */}
      <Section title="Datenbasis-Wachstum" subtitle="Kumulierte Artikel pro Tag">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={articlesPerDay}>
            <XAxis dataKey="date" stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <YAxis stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Line type="monotone" dataKey="count" stroke="var(--signal)" strokeWidth={1.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      {/* ── Crawl History ────────────────────────── */}
      <Section title="Crawl-Aktivität" subtitle="Letzte 20 Runs">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={crawlHistory}>
            <XAxis
              dataKey="crawled_at"
              stroke="var(--border)"
              tick={{ fontSize: 10, fill: 'var(--text-secondary)' }}
              tickFormatter={v => new Date(v).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
            />
            <YAxis stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} labelFormatter={v => new Date(v).toLocaleString('de-DE')} />
            <Bar dataKey="articles_new" fill="var(--patina)" name="Neue Artikel" radius={[1, 1, 0, 0]} />
            <Bar dataKey="articles_found" fill="var(--bg-elevated)" name="Gefunden" radius={[1, 1, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

    </div>
  )
}
