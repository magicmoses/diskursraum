import { useState } from 'react'

export default function InfoIcon({ text }) {
  const [show, setShow] = useState(false)
  return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      <span
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          cursor: 'help',
          userSelect: 'none',
          lineHeight: 1,
        }}
      >
        ⓘ
      </span>
      {show && (
        <div style={{
          position: 'absolute',
          bottom: 'calc(100% + 6px)',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          padding: '8px 12px',
          fontSize: '12px',
          fontFamily: 'var(--font-body)',
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
          maxWidth: '320px',
          whiteSpace: 'normal',
          zIndex: 300,
          pointerEvents: 'none',
        }}>
          {text}
        </div>
      )}
    </span>
  )
}
