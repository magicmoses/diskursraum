import { useState } from 'react'
import { EMOTION_COLORS } from '../../constants/colors'

const EMOTION_LABELS = {
  curiosity:      'Neugierde',
  approval:       'Zustimmung',
  admiration:     'Bewunderung',
  disapproval:    'Ablehnung',
  annoyance:      'Verärgerung',
  anger:          'Ärger',
  joy:            'Freude',
  sadness:        'Trauer',
  fear:           'Angst',
  disgust:        'Ekel',
  surprise:       'Überraschung',
  optimism:       'Optimismus',
  love:           'Zuneigung',
  realization:    'Erkenntnis',
  excitement:     'Aufregung',
  gratitude:      'Dankbarkeit',
  caring:         'Fürsorge',
  relief:         'Erleichterung',
  confusion:      'Verwirrung',
  amusement:      'Belustigung',
  desire:         'Verlangen',
  pride:          'Stolz',
  remorse:        'Reue',
  grief:          'Tiefe Trauer',
  nervousness:    'Nervosität',
  embarrassment:  'Scham',
  disappointment: 'Enttäuschung',
  neutral:        'Neutral',
}

function EmotionRow({ emotion, pct }) {
  const color = EMOTION_COLORS[emotion] || 'var(--text-muted)'
  const label = EMOTION_LABELS[emotion] || emotion
  const barWidth = Math.min((pct / 50) * 100, 100)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
      <span style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--text-secondary)',
        width: '110px',
        flexShrink: 0,
      }}>
        {label}
      </span>
      <div style={{ flex: 1, height: '3px', background: 'var(--border-subtle)' }}>
        <div style={{
          height: '3px',
          width: `${barWidth}%`,
          background: color,
          transition: 'width 600ms ease',
        }} />
      </div>
      <span style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--text-muted)',
        width: '36px',
        textAlign: 'right',
        fontFamily: 'var(--font-mono)',
      }}>
        {pct}%
      </span>
    </div>
  )
}

export default function EmotionBar({ emotions }) {
  const [expanded, setExpanded] = useState(false)

  if (!emotions || emotions.length === 0) return null

  const top3 = emotions.slice(0, 3)
  const rest = emotions.slice(3)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      {top3.map(e => <EmotionRow key={e.emotion} emotion={e.emotion} pct={e.pct} />)}
      {rest.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(v => !v)}
            style={{
              alignSelf: 'flex-start',
              marginTop: '2px',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              letterSpacing: '0.04em',
            }}
          >
            {expanded ? '▲ weniger' : `▼ ${rest.length} weitere`}
          </button>
          {expanded && rest.map(e => <EmotionRow key={e.emotion} emotion={e.emotion} pct={e.pct} />)}
        </>
      )}
    </div>
  )
}
