import { useEffect, useState } from 'react'
import {
  getOverview, getArticlesPerDay,
  getTrendingTopics, getPublishingTimes, getWeekdayActivity,
  getSourceDetails, getEmotionsPerBias,
} from '../api/client'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell,
} from 'recharts'
import { KpiCard, Section, Loader, InfoIcon } from '../components/ui'
import { EmotionBar } from '../components/charts'
import {
  BIAS_COLORS, BIAS_LABELS, EMOTION_COLORS,
  TOOLTIP_STYLE, WEEKDAYS,
} from '../constants/colors'

const DEUTSCHLAND_KW = [
  'deutschland', 'deutsch', 'bundesregierung', 'bundestag', 'berlin',
  'cdu', 'spd', 'grüne', 'fdp', 'afd', 'merz', 'scholz', 'bundesrat',
  'baden-württemberg', 'bayern', 'brandenburg', 'bremen', 'hamburg',
  'hessen', 'mecklenburg-vorpommern', 'niedersachsen', 'nordrhein-westfalen',
  'rheinland-pfalz', 'saarland', 'sachsen', 'sachsen-anhalt',
  'schleswig-holstein', 'thüringen',
]

function isGermanyTopic(topic) {
  const lower = (topic ?? '').toLowerCase()
  return DEUTSCHLAND_KW.some(kw => lower.includes(kw))
}

// ── Main ──────────────────────────────────────────
export default function Analytics() {
  const [overview, setOverview]               = useState(null)
  const [articlesPerDay, setArticlesPerDay]   = useState([])
  const [trendingTopics, setTrendingTopics]   = useState({ deutschland: [], international: [] })
  const [publishingTimes, setPublishingTimes] = useState([])
  const [weekdayActivity, setWeekdayActivity] = useState([])
  const [sourceDetails, setSourceDetails]     = useState([])
  const [emotionsPerBias, setEmotionsPerBias] = useState({})
  const [loading, setLoading]                 = useState(true)
  const [trendTab, setTrendTab]               = useState('de')

  useEffect(() => {
    Promise.all([
      getOverview(), getArticlesPerDay(),
      getPublishingTimes(), getWeekdayActivity(), getSourceDetails(),
      getEmotionsPerBias(),
    ]).then(([ov, apd, pt, wa, sd, epb]) => {
      setOverview(ov)
      setArticlesPerDay(apd)
      setPublishingTimes(pt)
      setWeekdayActivity(wa)
      setSourceDetails(sd)
      setEmotionsPerBias(epb)
      setLoading(false)
    })
    getTrendingTopics(7, 20).then(tt => {
      if (!tt) return
      if (tt.deutschland || tt.international) {
        setTrendingTopics(tt)
      } else if (Array.isArray(tt)) {
        setTrendingTopics({
          deutschland: tt.filter(t => isGermanyTopic(t.topic)),
          international: tt,
        })
      }
    })
  }, [])

  if (loading) return <Loader text="Lade Analytics..." />

  const weekdayTotals = WEEKDAYS.map(day => ({
    day,
    count: weekdayActivity.filter(r => r.weekday === day).reduce((s, r) => s + r.count, 0)
  }))

  const hourTotals = Array.from({ length: 24 }, (_, localH) => ({
    hour: `${localH}h`,
    count: publishingTimes.filter(r => r.hour === (localH - 2 + 24) % 24).reduce((s, r) => s + r.count, 0)
  }))

  const weeksInDataset = Math.max(1, Math.round(articlesPerDay.length / 7))

  const shownTopics = trendTab === 'de'
    ? (trendingTopics.deutschland || [])
    : (trendingTopics.international || [])
  const maxVal = shownTopics[0]?.article_count || shownTopics[0]?.relevanz || 1

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
          Diskursraum-Analytics
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(28px, 4vw, 40px)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          marginBottom: 'var(--space-2)',
        }}>
          Diskursraum-Analytics
        </h1>
      </div>

      {/* ── KPIs ────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1px', background: 'var(--border)' }}>
        <KpiCard label="Artikel gesamt" value={overview.total_articles.toLocaleString()} />
        <KpiCard label="Quellen" value="19" />
        <KpiCard label="Letzter inkludierter Crawl" mono value={
          overview.last_crawl.crawled_at
            ? new Date(overview.last_crawl.crawled_at).toLocaleDateString('de-DE', {
                day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'Europe/Berlin',
              })
            : '—'
        } />
      </div>

      {/* ── Trending Topics ──────────────────────── */}
      <Section title="Was bewegt Deutschland?" subtitle="Meistdiskutierte Themen in deutschen Medien der letzten 7 Tage">
        <div style={{ display: 'flex', gap: '1px', background: 'var(--border)', marginBottom: 'var(--space-4)' }}>
          {[
            { id: 'de',   label: 'Innerhalb Deutschlands' },
            { id: 'intl', label: 'International' },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTrendTab(t.id)}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                background: trendTab === t.id ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                border: 'none',
                borderBottom: trendTab === t.id ? '2px solid var(--signal)' : '2px solid transparent',
                color: trendTab === t.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontSize: 'var(--text-sm)',
                fontFamily: 'var(--font-body)',
                cursor: 'pointer',
                transition: 'all 150ms ease',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {shownTopics.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
            {!trendingTopics.deutschland?.length && !trendingTopics.international?.length
              ? 'Wird geladen...'
              : 'Keine Treffer'}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {shownTopics.slice(0, 5).map((topic, i) => {
              const val = topic.article_count ?? topic.relevanz ?? 0
              const pct = (val / maxVal * 100).toFixed(0)
              return (
                <div key={topic.topic} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', width: '16px' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)', width: '220px', flexShrink: 0 }}>
                    {topic.topic}
                  </span>
                  <div style={{ flex: 1, height: '3px', background: 'var(--bg-elevated)' }}>
                    <div style={{ height: '3px', width: `${pct}%`, background: 'var(--signal)', transition: 'width 700ms ease' }} />
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', width: '60px', textAlign: 'right' }}>
                    {topic.article_count != null ? `${topic.article_count} Art.` : `${(topic.relevanz * 100).toFixed(0)}%`}
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
            <YAxis type="category" dataKey="source" width={190} stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [`${v} Artikel`]} />
            <Bar dataKey="count" radius={[0, 1, 1, 0]}>
              {(overview.by_source ?? []).map(entry => {
                const sd = sourceDetails.find(s => s.source === entry.source)
                return (
                  <Cell key={entry.source} fill={BIAS_COLORS[sd?.bias] || 'var(--signal)'} />
                )
              })}
            </Bar>
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
              label={({ bias, percent }) => percent > 0.04 ? `${BIAS_LABELS[bias] || bias} ${(percent * 100).toFixed(0)}%` : ''}
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

      {/* ── Emotionsanalyse ──────────────────────── */}
      <Section
        title={
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            Emotionsanalyse
            <InfoIcon text="Das Modell klassifiziert Texte in 28 Emotionskategorien basierend auf dem GoEmotions-Datensatz. Neutral-Klasse wird ausgeblendet." />
          </span>
        }
        subtitle="Ermittelt mit AnasAlokla/multilingual_go_emotions_V1.2"
      >
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
                    {BIAS_LABELS[bias] || bias}
                  </span>
                </div>
                <EmotionBar emotions={emotions} />
              </div>
            ))
          }
        </div>
      </Section>

      {/* ── Veröffentlichungszeiten ──────────────── */}
      <Section title="Veröffentlichungszeiten" subtitle="Wann werden Artikel publiziert? (Deutsche Zeit)">
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
      <Section title="Aktivität nach Wochentagen">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={weekdayTotals}>
            <XAxis dataKey="day" stroke="var(--border)" tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
            <YAxis stroke="var(--border)" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null
                const count = payload[0]?.value ?? 0
                const avg = (count / weeksInDataset).toFixed(1)
                return (
                  <div style={{ ...TOOLTIP_STYLE, padding: 'var(--space-2) var(--space-3)', lineHeight: 1.7 }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>{label}</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>{count} Artikel gesamt</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>∅ Artikel/Tag: {avg}</div>
                  </div>
                )
              }}
            />
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

    </div>
  )
}
