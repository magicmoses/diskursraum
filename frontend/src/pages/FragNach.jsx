import { useState, useRef, useCallback } from 'react'
import { PARTY_COLORS, PARTY_NAMES } from '../constants/colors'
import { searchManifestos } from '../api/client'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const PARTY_ORDER = ['linke', 'gruene', 'spd', 'fdp', 'cdu_csu', 'afd']
const PARTY_SHORT  = {
  cdu_csu: 'CDU/CSU', spd: 'SPD', gruene: 'Grüne',
  fdp: 'FDP', afd: 'AfD', linke: 'Linke',
}
const YEARS = [2005, 2009, 2013, 2017, 2021, 2025]
const MAX_DEEP_DIVES = 10

const S = {
  label: {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--text-xs)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--text-secondary)',
    marginBottom: 'var(--space-3)',
  },
}

function filterBtn(active, partyColor) {
  return {
    background: active ? 'var(--bg-elevated)' : 'transparent',
    border: '1px solid var(--border)',
    borderBottom: active ? '2px solid var(--signal)' : '1px solid var(--border)',
    borderLeft: partyColor ? `3px solid ${partyColor}` : undefined,
    color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
    fontFamily: 'var(--font-body)',
    fontSize: 'var(--text-sm)',
    padding: '6px var(--space-3)',
    cursor: 'pointer',
    transition: 'all 120ms ease',
    whiteSpace: 'nowrap',
  }
}

function primaryBtn(disabled, accent) {
  return {
    background: disabled ? 'transparent' : (accent ? 'var(--signal-subtle)' : 'var(--bg-elevated)'),
    border: `1px solid ${disabled ? 'var(--border)' : (accent ? 'var(--signal)' : 'var(--border-hover)')}`,
    color: disabled ? 'var(--text-muted)' : 'var(--text-primary)',
    fontFamily: 'var(--font-body)',
    fontSize: 'var(--text-sm)',
    fontWeight: 500,
    padding: '8px var(--space-6)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 120ms ease',
  }
}

function ReferenceRow({ result }) {
  const color = PARTY_COLORS[result.party_id] || 'var(--signal)'
  return (
    <div style={{
      borderLeft: `2px solid ${color}`,
      paddingLeft: 'var(--space-3)',
      paddingTop: 'var(--space-2)',
      paddingBottom: 'var(--space-2)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: 'var(--text-xs)', fontWeight: 500, color: 'var(--text-secondary)' }}>
          {PARTY_NAMES[result.party_id] ?? result.party} · {result.year}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          {Math.round(result.relevance_score * 100)}%
        </span>
      </div>
      <p style={{
        fontSize: 'var(--text-sm)',
        color: 'var(--text-muted)',
        lineHeight: 1.5,
        overflow: 'hidden',
        display: '-webkit-box',
        WebkitLineClamp: 3,
        WebkitBoxOrient: 'vertical',
        margin: 0,
      }}>
        {result.text}
      </p>
    </div>
  )
}

export default function FragNach() {
  const [query, setQuery]             = useState('')
  const [selectedParties, setParties] = useState([])
  const [selectedYears, setYears]     = useState([])
  const [searchResults, setResults]   = useState([])
  const [deepDiveAnswer, setAnswer]   = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [deepDiveCount, setCount]     = useState(0)
  const [error, setError]             = useState(null)
  const [hasSearched, setHasSearched] = useState(false)
  const sessionId = useRef(crypto.randomUUID())

  const toggleParty = (id) =>
    setParties(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id])

  const toggleYear = (y) =>
    setYears(prev => prev.includes(y) ? prev.filter(yr => yr !== y) : [...prev, y])

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return
    setIsSearching(true)
    setError(null)
    setAnswer('')
    setHasSearched(true)
    try {
      const data = await searchManifestos(query.trim(), selectedParties, selectedYears)
      setResults(data.results || [])
    } catch {
      setError('Suche fehlgeschlagen — Backend erreichbar?')
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }, [query, selectedParties, selectedYears])

  const handleDeepDive = useCallback(async () => {
    if (!query.trim() || deepDiveCount >= MAX_DEEP_DIVES || isStreaming) return
    setIsStreaming(true)
    setAnswer('')
    setResults([])
    setCount(c => c + 1)
    setError(null)
    setHasSearched(true)

    // fetch references in parallel — populate collapsible while answer streams
    searchManifestos(query.trim(), selectedParties, selectedYears)
      .then(data => setResults(data.results || []))
      .catch(() => {})

    try {
      const res = await fetch(`${API_BASE}/frag-nach/deep-dive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          parties: selectedParties,
          years: selectedYears,
          session_id: sessionId.current,
        }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      outer: while (true) {
        const { done, value } = await reader.read()
        if (done) break
        for (const line of decoder.decode(value).split('\n')) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6).trim()
          if (payload === '[DONE]') break outer
          try {
            const { token } = JSON.parse(payload)
            if (token) setAnswer(prev => prev + token)
          } catch {}
        }
      }
    } catch {
      setError('Deep-Dive fehlgeschlagen — Backend erreichbar?')
    } finally {
      setIsStreaming(false)
    }
  }, [query, selectedParties, selectedYears, deepDiveCount, isStreaming])

  const handleKeyDown = (e) => { if (e.key === 'Enter') handleSearch() }

  const remaining = MAX_DEEP_DIVES - deepDiveCount
  const depleted  = deepDiveCount >= MAX_DEEP_DIVES

  return (
    <div style={{ maxWidth: '900px', paddingBottom: 'var(--space-24)' }}>

      {/* ── Header ─────────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ ...S.label, color: 'var(--signal)', marginBottom: 'var(--space-3)' }}>
          Dimension III — Frag nach.
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(22px, 4vw, 38px)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          lineHeight: 1.2,
          marginBottom: 'var(--space-3)',
        }}>
          Stell deine Frage. Die Wahlprogramme antworten.
        </h1>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
        }}>
          6 Bundestagswahlen · 6 Parteien · semantische Suche in Wahlprogrammen
        </div>
      </div>

      {/* ── Search Input ────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Wonach suchst du? z.B. Klimaschutz, Rente, Migration ..."
          style={{
            width: '100%',
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-body)',
            fontSize: 'var(--text-base)',
            padding: 'var(--space-4) var(--space-6)',
            outline: 'none',
            transition: 'border-color 150ms ease',
            boxSizing: 'border-box',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--signal)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
      </div>

      {/* ── Party Filter ────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <div style={S.label}>Parteien</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <button onClick={() => setParties([])} style={filterBtn(selectedParties.length === 0, null)}>
            Alle
          </button>
          {PARTY_ORDER.map(id => (
            <button
              key={id}
              onClick={() => toggleParty(id)}
              style={filterBtn(selectedParties.includes(id), PARTY_COLORS[id])}
            >
              {PARTY_SHORT[id]}
            </button>
          ))}
        </div>
      </div>

      {/* ── Year Filter ─────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={S.label}>Jahre</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <button onClick={() => setYears([])} style={filterBtn(selectedYears.length === 0, null)}>
            Alle
          </button>
          {YEARS.map(y => (
            <button
              key={y}
              onClick={() => toggleYear(y)}
              style={filterBtn(selectedYears.includes(y), null)}
            >
              {y}
            </button>
          ))}
        </div>
      </div>

      {/* ── Actions ─────────────────────────────────── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-4)',
        marginBottom: 'var(--space-8)',
        flexWrap: 'wrap',
      }}>
        <button
          onClick={handleSearch}
          disabled={!query.trim() || isSearching}
          style={primaryBtn(!query.trim() || isSearching, false)}
        >
          {isSearching ? 'Suche läuft...' : 'Schnellsuche'}
        </button>
        <button
          onClick={handleDeepDive}
          disabled={!query.trim() || depleted || isStreaming}
          style={primaryBtn(!query.trim() || depleted || isStreaming, true)}
        >
          {isStreaming ? 'Analysiere...' : '▶ Deep-Dive'}
        </button>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: depleted ? 'var(--amber)' : 'var(--text-muted)',
        }}>
          {depleted ? 'Session-Limit erreicht' : `${remaining} von ${MAX_DEEP_DIVES} Deep-Dives verfügbar`}
        </span>
      </div>

      {/* ── Error ───────────────────────────────────── */}
      {error && (
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-sm)',
          color: 'var(--amber)',
          marginBottom: 'var(--space-6)',
        }}>
          {error}
        </div>
      )}

      {/* ── Deep-Dive Answer ────────────────────────── */}
      {(deepDiveAnswer || isStreaming) && (
        <p style={{
          fontSize: 'var(--text-base)',
          color: 'var(--text-primary)',
          lineHeight: 1.8,
          marginBottom: 'var(--space-6)',
        }}>
          {deepDiveAnswer}
          {isStreaming && (
            <span style={{
              display: 'inline-block',
              width: '2px',
              height: '1em',
              background: 'var(--signal)',
              marginLeft: '2px',
              verticalAlign: 'text-bottom',
              animation: 'blink 1s step-end infinite',
            }} />
          )}
        </p>
      )}

      {/* ── References / Results ────────────────────── */}
      {searchResults.length > 0 && (
        <details style={{ marginBottom: 'var(--space-6)' }}>
          <summary style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            userSelect: 'none',
            paddingBottom: 'var(--space-3)',
            listStyle: 'none',
          }}>
            ▸ Quellen — {searchResults.length} Treffer
          </summary>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            paddingTop: 'var(--space-2)',
            borderTop: '1px solid var(--border)',
          }}>
            {searchResults.map((result, i) => (
              <ReferenceRow key={i} result={result} />
            ))}
          </div>
        </details>
      )}

      {/* ── Empty State ─────────────────────────────── */}
      {hasSearched && searchResults.length === 0 && !isSearching && !deepDiveAnswer && !isStreaming && (
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-muted)',
          textAlign: 'center',
          padding: 'var(--space-16) 0',
        }}>
          Keine Treffer — anderen Suchbegriff oder Filter versuchen.
        </div>
      )}

    </div>
  )
}
