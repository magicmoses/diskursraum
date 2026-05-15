import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Analytics from './pages/Analytics'
import Home from './pages/Home'
import TopicView from './pages/TopicView'
import PartyView from './pages/PartyView'
import FragNach from './pages/FragNach'
import Landing from './pages/Landing'

// Nav ausblenden auf Landing Page
function AppShell() {
  const location = useLocation()
  const isLanding = location.pathname === '/'

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
            {[
              { to: '/medienspiegel', label: 'Medienspiegel' },
              { to: '/parteienspiegel', label: 'Parteienspiegel' },
              { to: '/frag-nach', label: 'Frag nach.' },
              { to: '/project', label: 'Diskursraum-Analytics' },
            ].map(({ to, label }) => (
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