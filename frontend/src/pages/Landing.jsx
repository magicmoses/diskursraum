import { useNavigate } from 'react-router-dom'

const SECTIONS = [
  {
    route: '/medienspiegel',
    dim: 'I',
    title: 'Medienspiegel',
    subtitle: 'Wie berichten 19 deutsche Medien über gesellschaftliche Debatten?',
    body: 'Täglich aktualisiert. Acht politische Themen. Von links bis rechts — wo gibt es Konsens, wo beginnt der Diskurs?',
    meta: '19 Quellen · 8 Themen · täglich',
  },
  {
    route: '/parteienspiegel',
    dim: 'II',
    title: 'Parteienspiegel',
    subtitle: 'Wie haben sich Parteipositionen von 2005 bis 2025 entwickelt?',
    body: 'Semantische Analyse aller Bundestagswahlprogramme. Wer nähert sich an, wer entfernt sich — und was sagen die Wahlergebnisse dazu?',
    meta: '6 Parteien · 6 Wahlen · 2005–2025',
  },
]

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* ── Nav ───────────────────────────────────── */}
      <nav style={{
        padding: 'var(--space-6) var(--space-12)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: '18px',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: 'var(--text-primary)',
        }}>
          Diskursraum
        </span>
        <button
          onClick={() => navigate('/project')}
          style={{
            background: 'none',
            border: 'none',
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            color: 'var(--text-muted)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            cursor: 'pointer',
            transition: 'color 150ms ease',
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--text-secondary)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
        >
          Project ↗
        </button>
      </nav>

      {/* ── Hero ──────────────────────────────────── */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: 'var(--space-24) var(--space-12)',
        maxWidth: '960px',
        margin: '0 auto',
        width: '100%',
        position: 'relative',
        overflow: 'hidden',
      }}>

        {/* Deutschlandfahne — dekorativer Hintergrund */}
        <div style={{
          position: 'absolute',
          right: '-24px',
          top: '50%',
          transform: 'translateY(-50%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 300 180"
            width="360"
            height="216"
            style={{ opacity: 0.10, display: 'block', animation: 'flagWave 4s ease-in-out infinite' }}
          >
            <defs>
              <filter id="fw-l" x="-5%" y="-12%" width="115%" height="130%">
                <feTurbulence type="turbulence" baseFrequency="0.025 0.09" numOctaves="3" result="wave">
                  <animate attributeName="baseFrequency"
                    values="0.020 0.07;0.035 0.11;0.025 0.09;0.015 0.07;0.020 0.07"
                    dur="5s" repeatCount="indefinite" />
                </feTurbulence>
                <feDisplacementMap in="SourceGraphic" in2="wave" scale="16"
                  xChannelSelector="R" yChannelSelector="G" />
              </filter>
            </defs>
            <g filter="url(#fw-l)">
              <rect width="300" height="60"  fill="#1A1A1A" />
              <rect y="60"  width="300" height="60"  fill="#CC0000" />
              <rect y="120" width="300" height="60"  fill="#FFCC00" />
            </g>
          </svg>
        </div>

        {/* Eyebrow */}
        <div className="fade-up" style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--signal)',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          marginBottom: 'var(--space-6)',
        }}>
          Mapping Public Discourse in Germany
        </div>

        {/* Headline */}
        <h1 className="fade-up fade-up-delay-1" style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(40px, 7vw, 80px)',
          fontWeight: 700,
          letterSpacing: '-0.03em',
          lineHeight: 1.05,
          color: 'var(--text-primary)',
          marginBottom: 'var(--space-8)',
          maxWidth: '760px',
        }}>
          Der deutsche<br />Diskurs —<br />sichtbar gemacht.
        </h1>

        {/* Description */}
        <p className="fade-up fade-up-delay-2" style={{
          fontSize: 'var(--text-lg)',
          color: 'var(--text-secondary)',
          lineHeight: 1.7,
          maxWidth: '560px',
          marginBottom: 'var(--space-16)',
        }}>
          Zwei Dimensionen. Fünfzehn Medien. Sechs Parteien.
          Zwanzig Jahre Wahlprogramme. Wo konvergiert Deutschland —
          und wo spaltet es sich?
        </p>

        {/* ── Section Cards ────────────────────────── */}
        <div className="fade-up fade-up-delay-3" style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '1px',
          background: 'var(--border)',
          maxWidth: '720px',
        }}>
          {SECTIONS.map(({ route, dim, title, subtitle, body, meta }) => (
            <button
              key={route}
              onClick={() => navigate(route)}
              style={{
                background: 'var(--bg-surface)',
                border: 'none',
                padding: 'var(--space-8)',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'background 150ms ease',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-elevated)'}
              onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-surface)'}
            >
              {/* Dim label */}
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--text-xs)',
                color: 'var(--signal)',
                letterSpacing: '0.10em',
                textTransform: 'uppercase',
              }}>
                Dimension {dim}
              </div>

              {/* Title */}
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-xl)',
                fontWeight: 600,
                color: 'var(--text-primary)',
                letterSpacing: '-0.01em',
                lineHeight: 1.2,
              }}>
                {title}
              </div>

              {/* Subtitle */}
              <div style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
              }}>
                {subtitle}
              </div>

              {/* Body */}
              <div style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--text-secondary)',
                lineHeight: 1.6,
                marginTop: 'var(--space-1)',
              }}>
                {body}
              </div>

              {/* Meta + arrow */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginTop: 'var(--space-2)',
                paddingTop: 'var(--space-3)',
                borderTop: '1px solid var(--border-subtle)',
              }}>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--text-secondary)',
                  letterSpacing: '0.04em',
                }}>
                  {meta}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>→</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Footer ────────────────────────────────── */}
      <footer style={{
        padding: 'var(--space-6) var(--space-12)',
        borderTop: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <p style={{
          fontSize: 'var(--text-xs)',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          letterSpacing: '0.04em',
        }}>
          Inspired by{' '}
          <a href="https://info.vtaiwan.tw/" target="_blank" rel="noopener noreferrer"
            style={{ color: 'var(--text-secondary)', textDecoration: 'underline', textUnderlineOffset: '3px' }}
          >vTaiwan</a>
          {' '}·{' '}
          <a href="https://pol.is" target="_blank" rel="noopener noreferrer"
            style={{ color: 'var(--text-secondary)', textDecoration: 'underline', textUnderlineOffset: '3px' }}
          >Pol.is</a>
          {' '}·{' '}
          <a href="https://www.plurality.net/" target="_blank" rel="noopener noreferrer"
            style={{ color: 'var(--text-secondary)', textDecoration: 'underline', textUnderlineOffset: '3px' }}
          >Plurality</a>
        </p>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--text-muted)',
        }}>
          Taipei, 2026
        </span>
      </footer>

    </div>
  )
}