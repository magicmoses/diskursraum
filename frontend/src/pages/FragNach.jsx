import { useState, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { PARTY_COLORS, PARTY_NAMES } from '../constants/colors'
import { searchManifestos } from '../api/client'

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8001').replace(/\/$/, '')

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
  const { t } = useTranslation()
  const [query, setQuery]             = useState('')
  const [selectedParty, setParty]     = useState(null)
  const [selectedYear, setYear]       = useState(null)
  const [searchResults, setResults]   = useState([])
  const [deepDiveAnswer, setAnswer]   = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [deepDiveCount, setCount]     = useState(0)
  const [error, setError]             = useState(null)
  const sessionId = useRef(crypto.randomUUID())

  const handleDeepDive = useCallback(async () => {
    if (!query.trim() || deepDiveCount >= MAX_DEEP_DIVES || isStreaming) return
    setIsStreaming(true)
    setAnswer('')
    setResults([])
    setCount(c => c + 1)
    setError(null)

    const parties = selectedParty ? [selectedParty] : []
    const years   = selectedYear  ? [selectedYear]  : []

    searchManifestos(query.trim(), parties, years)
      .then(data => setResults(data.results || []))
      .catch(() => {})

    try {
      const res = await fetch(`${API_BASE}/frag-nach/deep-dive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          parties,
          years,
          session_id: sessionId.current,
        }),
      })

      const contentType = res.headers.get('content-type') ?? ''
      if (!contentType.includes('text/event-stream')) {
        const errData = await res.json().catch(() => ({}))
        setError(errData.message || errData.error || 'Deep-Dive aktuell nicht verfügbar — Versuche es später nochmal')
        return
      }

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
  }, [query, selectedParty, selectedYear, deepDiveCount, isStreaming])

  const handleKeyDown = (e) => { if (e.key === 'Enter') handleDeepDive() }

  const remaining = MAX_DEEP_DIVES - deepDiveCount
  const depleted  = deepDiveCount >= MAX_DEEP_DIVES

  return (
    <div style={{ maxWidth: '900px', paddingBottom: 'var(--space-24)' }}>

      {/* ── Header ─────────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ ...S.label, color: 'var(--signal)', marginBottom: 'var(--space-3)' }}>
          {t('frag_nach.eyebrow')}
        </div>
        <h1 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'clamp(22px, 4vw, 38px)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          lineHeight: 1.2,
          marginBottom: 'var(--space-3)',
        }}>
          {t('frag_nach.subheadline')}
        </h1>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-secondary)',
        }}>
          {t('frag_nach.meta')}
        </div>
      </div>

      {/* ── Search Input ────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('frag_nach.placeholder')}
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

      {/* ── Party Filter ─────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <div style={S.label}>{t('frag_nach.party_label')}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <button onClick={() => setParty(null)} style={filterBtn(selectedParty === null, null)}>
            {t('frag_nach.all')}
          </button>
          {PARTY_ORDER.map(id => (
            <button
              key={id}
              onClick={() => setParty(prev => prev === id ? null : id)}
              style={filterBtn(selectedParty === id, PARTY_COLORS[id])}
            >
              {PARTY_SHORT[id]}
            </button>
          ))}
        </div>
      </div>

      {/* ── Year Filter ──────────────────────────────── */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={S.label}>{t('frag_nach.year_label')}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <button onClick={() => setYear(null)} style={filterBtn(selectedYear === null, null)}>
            {t('frag_nach.all')}
          </button>
          {YEARS.map(y => (
            <button
              key={y}
              onClick={() => setYear(prev => prev === y ? null : y)}
              style={filterBtn(selectedYear === y, null)}
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
          onClick={handleDeepDive}
          disabled={!query.trim() || depleted || isStreaming}
          style={primaryBtn(!query.trim() || depleted || isStreaming, true)}
        >
          {isStreaming ? t('frag_nach.button_loading') : t('frag_nach.button_idle')}
        </button>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: depleted ? 'var(--amber)' : 'var(--text-muted)',
        }}>
          {depleted
            ? t('frag_nach.limit_reached')
            : t('frag_nach.counter', { remaining, max: MAX_DEEP_DIVES })}
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

      {/* ── Deep-Dive Answer Box ────────────────────── */}
      {(deepDiveAnswer || isStreaming) && (
        <div style={{ border: '1px solid var(--signal)', marginBottom: 'var(--space-6)' }}>

          <div style={{
            background: 'var(--signal)',
            color: 'white',
            padding: 'var(--space-2) var(--space-4)',
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}>
            {t('frag_nach.answer_label')}
          </div>

          <div style={{ padding: 'var(--space-6)', background: 'var(--bg-surface)' }}>
            <p style={{
              fontSize: 'var(--text-base)',
              color: 'var(--text-primary)',
              lineHeight: 1.8,
              margin: 0,
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

            {searchResults.length > 0 && (
              <details style={{ marginTop: 'var(--space-4)', borderTop: '1px solid var(--border-subtle)', paddingTop: 'var(--space-4)' }}>
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
                  ▸ {t('frag_nach.sources_label', { count: searchResults.length })}
                </summary>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', paddingTop: 'var(--space-2)' }}>
                  {searchResults.map((result, i) => (
                    <ReferenceRow key={i} result={result} />
                  ))}
                </div>
              </details>
            )}
          </div>

        </div>
      )}

    </div>
  )
}
