export default function Loader({ text = 'Laden...' }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '240px',
      gap: 'var(--space-3)',
      color: 'var(--text-muted)',
      fontFamily: 'var(--font-mono)',
      fontSize: 'var(--text-sm)',
    }}>
      <div style={{
        width: '16px',
        height: '16px',
        border: '1px solid var(--signal)',
        borderTopColor: 'transparent',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      {text}
    </div>
  )
}
