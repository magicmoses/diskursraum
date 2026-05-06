export default function Section({ title, subtitle, label, children }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      padding: 'var(--space-6)',
    }}>
      <div style={{ marginBottom: 'var(--space-6)' }}>
        {label && (
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            color: 'var(--signal)',
            letterSpacing: '0.10em',
            textTransform: 'uppercase',
            marginBottom: 'var(--space-2)',
          }}>
            {label}
          </div>
        )}
        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: 'var(--text-xl)',
          fontWeight: 600,
          color: 'var(--text-primary)',
          letterSpacing: '-0.01em',
          marginBottom: subtitle ? 'var(--space-1)' : 0,
        }}>
          {title}
        </h2>
        {subtitle && (
          <p style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
          }}>
            {subtitle}
          </p>
        )}
      </div>
      {children}
    </div>
  )
}
