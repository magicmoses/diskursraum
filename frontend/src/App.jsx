import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Analytics from './pages/Analytics'
import Home from './pages/Home'
import TopicView from './pages/TopicView'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">

        {/* Navbar */}
        <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-8">
          <span className="text-xl font-bold text-white">
            🦞 ConsensusAgent
          </span>
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive ? "text-white font-medium" : "text-gray-400 hover:text-white"
            }
          >
            Topics
          </NavLink>
          <NavLink
            to="/analytics"
            className={({ isActive }) =>
              isActive ? "text-white font-medium" : "text-gray-400 hover:text-white"
            }
          >
            Data Analytics
          </NavLink>
        </nav>

        <main className="px-6 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/topic/:topicId" element={<TopicView />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  )
}

export default App