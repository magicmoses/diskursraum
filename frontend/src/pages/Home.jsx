import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
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

const TOPIC_IDS = [
  'energy_transition', 'digitalization', 'work_transition', 'migration',
  'retirement', 'defense', 'family_children', 'education',
]

const ICON_PATHS = {
  megaphone: 'M18 3v2c2.21 1.1 3.5 3.37 3.5 6s-1.29 4.9-3.5 6v2c3.32-1.26 5.5-4.37 5.5-8s-2.18-6.74-5.5-8zM5 9H1v6h4l6 6V3L5 9zm10 3c0-1.77-1.02-3.29-2.5-4.03v8.05C13.98 15.29 15 13.77 15 12z',
  newspaper: 'M20 4H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H4V6h16v14zM8 8h10v2H8zm0 4h10v2H8zm0 4h7v2H8zM4 8h2v2H4zm0 4h2v2H4zm0 4h2v2H4z',
  pen:       'M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z',
}

const DECO = [
  { icon: 'megaphone', top:  50,  side: 'right', offset: -16, rotate:  14, size: 70, opacity: 0.085 },
  { icon: 'newspaper', top: 200,  side: 'left',  offset: -12, rotate:  -8, size: 78, opacity: 0.075 },
  { icon: 'pen',       top: 420,  side: 'right', offset:  20, rotate: -24, size: 60, opacity: 0.090 },
  { icon: 'megaphone', top: 640,  side: 'left',  offset:  10, rotate:  22, size: 54, opacity: 0.075 },
  { icon: 'newspaper', top: 860,  side: 'right', offset:   0, rotate:   9, size: 74, opacity: 0.080 },
  { icon: 'pen',       top:1080,  side: 'left',  offset:   5, rotate: -17, size: 62, opacity: 0.075 },
]

export default function Home() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [bySource, setBySource] = useState([])

  const TOPICS = TOPIC_IDS.map(id => ({
    id,
    label: t(`home.topics.${id}.label`),
    description: t(`home.topics.${id}.description`),
  }))

  useEffect(() => {
    getOverview().then(d => { if (d?.by_source) setBySource(d.by_source) }).catch(() => {})
  }, [])

  return (
    <div style={{ maxWidth: '960px', position: 'relative' }}>

      {/* ── Medien-Icons — dekorativer Hintergrund ── */}
      <div aria-hidden style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        {DECO.map((d, i) => (
          <div key={i} style={{
            position: 'absolute',
            top: d.top,
            [d.side]: d.offset,
            transform: `rotate(${d.rotate}deg)`,
            color: '#1A1410',
            opacity: d.opacity,
          }}>
            <svg viewBox="0 0 24 24" width={d.size} height={d.size} fill="currentColor">
              <path d={ICON_PATHS[d.icon]} />
            </svg>
          </div>
        ))}
      </div>

      {/* ── Content ── */}
      <div style={{ position: 'relative', zIndex: 1 }}>

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
          {t('home.eyebrow')}
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
          whiteSpace: 'pre-line',
        }}>
          {t('home.headline')}
        </h1>
        <p style={{
          fontSize: 'var(--text-lg)',
          color: 'var(--text-secondary)',
          lineHeight: 1.7,
          maxWidth: '560px',
        }}>
          {t('home.description')}
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
            {t('home.media_intro')}
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
          {t('home.dim2_button')}
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
