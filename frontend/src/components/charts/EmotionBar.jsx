import { EMOTION_COLORS } from '../../constants/colors'

export default function EmotionBar({ emotion, pct }) {
  const color = EMOTION_COLORS[emotion] || 'var(--text-muted)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
      <span style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--text-secondary)',
        width: '120px',
        flexShrink: 0,
      }}>
        {emotion}
      </span>
      <div style={{ flex: 1, height: '3px', background: 'var(--bg-elevated)' }}>
        <div style={{
          height: '3px',
          width: `${pct}%`,
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
