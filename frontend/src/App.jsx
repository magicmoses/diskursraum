import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Analytics from './pages/Analytics'
import Home from './pages/Home'
import TopicView from './pages/TopicView'
import PartyView from './pages/PartyView'
import FragNach from './pages/FragNach'
import Landing from './pages/Landing'

function LanguageToggle() {
  const { i18n } = useTranslation()
  const isDE = i18n.language === 'de'

  const toggle = () => {
    const next = isDE ? 'en' : 'de'
    i18n.changeLanguage(next)
    localStorage.setItem('diskursraum_lang', next)
  }

  return (
    <button
      onClick={toggle}
      style={{
        background: 'none',
        border: '1px solid var(--border)',
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--text-xs)',
        color: 'var(--text-secondary)',
        letterSpacing: '0.08em',
        cursor: 'pointer',
        padding: '3px 10px',
        transition: 'all 150ms ease',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'var(--signal)'
        e.currentTarget.style.color = 'var(--text-primary)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--border)'
        e.currentTarget.style.color = 'var(--text-secondary)'
      }}
    >
      {isDE ? 'EN' : 'DE'}
    </button>
  )
}

function AppShell() {
  const location = useLocation()
  const { t } = useTranslation()
  const isLanding = location.pathname === '/'

  const NAV_LINKS = [
    { to: '/medienspiegel',   label: t('nav.medienspiegel') },
    { to: '/parteienspiegel', label: t('nav.parteienspiegel') },
    { to: '/frag-nach',       label: t('nav.frag_nach') },
    { to: '/project',         label: t('nav.analytics') },
  ]

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)' }}>

      {!isLanding && (
        <nav style={{
          borderBottom: '1px solid var(--border)',
          padding: '0 var(--space-12)',
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          backgroundColor: 'var(--bg-primary)',
          backdropFilter: 'blur(8px)',
        }}>
          <NavLink to="/" style={{ textDecoration: 'none' }}>
            <span style={{
              fontFamily: 'var(--font-display)',
              fontSize: '18px',
              fontWeight: 600,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
            }}>
              Diskursraum
            </span>
          </NavLink>

          <div style={{ display: 'flex', gap: 'var(--space-8)', alignItems: 'center' }}>
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                style={({ isActive }) => ({
                  textDecoration: 'none',
                  fontSize: 'var(--text-sm)',
                  fontWeight: isActive ? 500 : 400,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  letterSpacing: '0.01em',
                  transition: 'color 150ms ease',
                  paddingBottom: '2px',
                  borderBottom: isActive ? '1px solid var(--signal)' : '1px solid transparent',
                })}
              >
                {label}
              </NavLink>
            ))}
            <LanguageToggle />
          </div>
        </nav>
      )}

      <main style={{
        padding: isLanding ? 0 : 'var(--space-12)',
        maxWidth: isLanding ? 'none' : '1200px',
        margin: '0 auto',
      }}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/medienspiegel" element={<Home />} />
          <Route path="/medienspiegel/:topicId" element={<TopicView />} />
          <Route path="/parteienspiegel" element={<PartyView />} />
          <Route path="/frag-nach" element={<FragNach />} />
          <Route path="/project" element={<Analytics />} />
        </Routes>
      </main>

    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
