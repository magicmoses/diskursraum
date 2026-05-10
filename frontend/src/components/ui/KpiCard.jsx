export default function KpiCard({ label, value, mono = false }) {
  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      padding: 'var(--space-4) var(--space-6)',
    }}>
      <div style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--text-secondary)',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        marginBottom: 'var(--space-2)',
        fontFamily: 'var(--font-mono)',
      }}>
        {label}
      </div>
      <div style={{
        fontSize: 'var(--text-2xl)',
        fontWeight: 600,
        color: 'var(--text-primary)',
        fontFamily: mono ? 'var(--font-mono)' : 'var(--font-display)',
        letterSpacing: '-0.02em',
        lineHeight: 1,
      }}>
        {value}
      </div>
    </div>
  )
}
