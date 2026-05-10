import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOverview } from '../api/client'
import { BIAS_COLORS } from '../constants/colors'

const SOURCE_BIAS = {
  taz: 'left',
  spiegel: 'left-liberal', zeit: 'left-liberal', sz: 'left-liberal', stern: 'left-liberal',
  tagesschau: 'neutral', zdf: 'neutral', dw: 'neutral',
  faz: 'conservative-liberal', cicero: 'conservative-liberal', nzz: 'conservative-liberal',
  welt: 'right-conservative', focus: 'right-conservative', ntv: 'right-conservative',
  junge_freiheit: 'far-right', tichys: 'far-right', achgut: 'far-right',
  handelsblatt: 'economic-liberal',
  bild: 'populist-mixed',
}

const TOPICS = [
  {
    id: 'migration',
    label: 'Migration & Asylpolitik',
    description: 'Einwanderung, Asylrecht und Integration — eines der polarisierendsten Themen Deutschlands.',
  },
  {
    id: 'energy_transition',
    label: 'Energiewende',
    description: 'Atomkraft, erneuerbare Energien und Klimapolitik — zwischen Versorgungssicherheit und Wandel.',
  },
  {
    id: 'retirement',
    label: 'Rente & Altersvorsorge',
    description: 'Rentenpolitik und Generationengerechtigkeit als gesellschaftliche Dauerdebatte.',
  },
  {
    id: 'digitalization',
    label: 'Digitale Transformation & KI',
    description: 'Digitalisierung, Künstliche Intelligenz und gesellschaftlicher Wandel durch Technologie.',
  },
  {
    id: 'work_transition',
    label: 'Arbeit im Wandel',
    description: 'Zukunft der Arbeit, Mindestlohn, Fachkräftemangel und Transformation durch Digitalisierung.',
  },
  {
    id: 'defense',
    label: 'Verteidigung & Militär',
    description: 'Bundeswehr, NATO, Wehrpflicht und Sicherheitspolitik in einer veränderten Welt.',
  },
  {
    id: 'family_children',
    label: 'Für Familien & Kinder',
    description: 'Kindergeld, Kita-Ausbau, Elterngeld und Vereinbarkeit von Familie und Beruf.',
  },
  {
    id: 'education',
    label: 'Bildung & lebenslanges Lernen',
    description: 'Schule, Hochschule, Ausbildung und Weiterbildung als Schlüssel zur gesellschaftlichen Teilhabe.',
  },
]

export default function Home() {
  const navigate = useNavigate()
  const [bySource, setBySource] = useState([])

  useEffect(() => {
    getOverview().then(d => { if (d?.by_source) setBySource(d.by_source) }).catch(() => {})
  }, [])

  return (
    <div style={{ maxWidth: '960px' }}>

      {/* ── Hero ──────────────────────────────────── */}
      <div className="fade-up" style={{ marginBottom: 'var(--space-16)', paddingTop: 'var(--space-12)' }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--signal)',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          marginBottom: 'var(--space-4)',
        }}>
          Dimension I — Medienspiegel
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(32px, 5vw, 52px)',
          fontWeight: 700,
          color: 'var(--text-primary)',
          lineHeight: 1.15,
          letterSpacing: '-0.02em',
          marginBottom: 'var(--space-6)',
          maxWidth: '680px',
        }}>
          Wie berichtet Deutschland<br />über sich selbst?
        </h1>
        <p style={{
          fontSize: 'var(--text-lg)',
          color: 'var(--text-secondary)',
          lineHeight: 1.7,
          maxWidth: '560px',
        }}>
          19 deutsche Medien. 8 politische Themen. Täglich aktualisiert.
          Wo gibt es Konsens — und wo beginnt der Diskurs?
        </p>
      </div>

      {/* ── Divider ───────────────────────────────── */}
      <div style={{
        height: '1px',
        background: `linear-gradient(to right, var(--border), transparent)`,
        marginBottom: 'var(--space-8)',
      }} />

      {/* ── Media Overview ───────────────────────── */}
      {bySource.length > 0 && (
        <div style={{ marginBottom: 'var(--space-8)' }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            color: 'var(--text-secondary)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 'var(--space-4)',
          }}>
            19 deutsche Medien — analysiert seit März 2026
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px' }}>
            {bySource.map(({ source, count }) => {
              const bias = SOURCE_BIAS[source] || 'neutral'
              const color = BIAS_COLORS[bias] || 'var(--text-muted)'
              return (
                <div
                  key={source}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    padding: '4px 10px',
                    background: 'var(--bg-surface)',
                    border: `1px solid ${color}30`,
                  }}
                >
                  <div style={{ width: '6px', height: '6px', background: color, flexShrink: 0 }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-secondary)' }}>
                    {source}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>
                    {count.toLocaleString()}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Topic List ────────────────────────────── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {TOPICS.map((topic, i) => (
          <TopicRow
            key={topic.id}
            topic={topic}
            index={i + 1}
            onClick={() => navigate(`/medienspiegel/${topic.id}`)}
            delay={i}
          />
        ))}
      </div>

      {/* ── Dimension II Teaser ───────────────────── */}
      <div style={{ marginTop: 'var(--space-8)', marginBottom: 'var(--space-4)' }}>
        <div
          onClick={() => navigate('/parteienspiegel')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            padding: '10px var(--space-4)',
            border: '1px solid var(--border)',
            cursor: 'pointer',
            transition: 'border-color 150ms ease, background 150ms ease',
            fontSize: 'var(--text-sm)',
            color: 'var(--text-secondary)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = 'var(--signal)'
            e.currentTarget.style.color = 'var(--text-primary)'
            e.currentTarget.style.background = 'var(--signal-subtle)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = 'var(--border)'
            e.currentTarget.style.color = 'var(--text-secondary)'
            e.currentTarget.style.background = 'transparent'
          }}
        >
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--signal)' }}>
            II
          </span>
          zu Dimension II Parteienspiegel
          <span style={{ color: 'var(--text-muted)' }}>→</span>
        </div>
      </div>

      {/* ── Footer ────────────────────────────────── */}
      <p style={{
        marginTop: 'var(--space-8)',
        paddingTop: 'var(--space-8)',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: 'var(--text-xs)',
        color: 'var(--text-muted)',
        lineHeight: 1.8,
      }}>
        Inspired by Taiwan's{' '}
        <a href="https://info.vtaiwan.tw/" target="_blank" rel="noopener noreferrer"
          style={{ color: 'var(--text-secondary)', textDecoration: 'underline', textUnderlineOffset: '3px' }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
        >vTaiwan</a>{' '}
        and the{' '}
        <a href="https://pol.is" target="_blank" rel="noopener noreferrer"
          style={{ color: 'var(--text-secondary)', textDecoration: 'underline', textUnderlineOffset: '3px' }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
        >Pol.is</a>{' '}
        bridging algorithm.{' '}
        <a href="https://www.plurality.net/" target="_blank" rel="noopener noreferrer"
          style={{ color: 'var(--text-secondary)', textDecoration: 'underline', textUnderlineOffset: '3px' }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
        >Plurality</a>{' '}
        by Audrey Tang & E. Glen Weyl.
      </p>
    </div>
  )
}

function TopicRow({ topic, index, onClick, delay }) {
  return (
    <div
      className={`fade-up fade-up-delay-${delay + 1}`}
      onClick={onClick}
      style={{
        display: 'grid',
        gridTemplateColumns: '32px 1fr auto',
        alignItems: 'center',
        gap: 'var(--space-6)',
        padding: 'var(--space-4) var(--space-3)',
        cursor: 'pointer',
        borderBottom: '1px solid var(--border-subtle)',
        transition: 'background 150ms ease',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-elevated)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <span style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--text-xs)',
        color: 'var(--text-secondary)',
        textAlign: 'right',
      }}>
        {String(index).padStart(2, '0')}
      </span>

      <div>
        <div style={{
          fontSize: 'var(--text-base)',
          fontWeight: 500,
          color: 'var(--text-primary)',
          marginBottom: '2px',
          letterSpacing: '-0.01em',
        }}>
          {topic.label}
        </div>
        <div style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
        }}>
          {topic.description}
        </div>
      </div>

      <span style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--text-sm)',
        color: 'var(--text-muted)',
        transition: 'color 150ms ease, transform 150ms ease',
      }}>
        →
      </span>
    </div>
  )
}
