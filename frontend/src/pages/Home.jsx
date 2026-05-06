import { useNavigate } from 'react-router-dom'

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
    id: 'wealth_tax',
    label: 'Vermögenssteuer & Umverteilung',
    description: 'Besteuerung großer Vermögen, Erbschaftssteuer und soziale Gerechtigkeit.',
  },
  {
    id: 'digitalization',
    label: 'Digitale Transformation & KI',
    description: 'Digitalisierung, Künstliche Intelligenz und gesellschaftlicher Wandel durch Technologie.',
  },
]

export default function Home() {
  const navigate = useNavigate()

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
          marginBottom: 'var(--space-8)',
        }}>
          15 deutsche Medien. 5 politische Themen. Täglich aktualisiert.
          Wo gibt es Konsens — und wo beginnt der Diskurs?
        </p>

        {/* Dimension II Teaser */}
        <div
          onClick={() => navigate('/parties')}
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
          Parteiprogramme 2005–2025 analysieren
          <span style={{ color: 'var(--text-muted)' }}>→</span>
        </div>
      </div>

      {/* ── Divider ───────────────────────────────── */}
      <div style={{
        height: '1px',
        background: `linear-gradient(to right, var(--border), transparent)`,
        marginBottom: 'var(--space-8)',
      }} />

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

      {/* ── Footer ────────────────────────────────── */}
      <p style={{
        marginTop: 'var(--space-16)',
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
      {/* Index */}
      <span style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--text-xs)',
        color: 'var(--text-muted)',
        textAlign: 'right',
      }}>
        {String(index).padStart(2, '0')}
      </span>

      {/* Content */}
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

      {/* Arrow */}
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