export default function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', padding: '0.25rem 0' }}>
      {/* Ading avatar dot */}
      <div style={{
        width: 28, height: 28, borderRadius: '50%', flexShrink: 0, marginTop: 2,
        background: 'var(--bg-3)', border: '1px solid var(--border-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.65rem', color: 'var(--amber)',
      }}>
        ◎
      </div>
      <div className="bubble-ading" style={{ padding: '0.6rem 0.9rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', height: '18px' }}>
          {[0, 1, 2].map(i => (
            <span
              key={i}
              className="typing-dot"
              style={{
                display: 'inline-block',
                width: 6, height: 6, borderRadius: '50%',
                background: 'var(--amber-dim)',
                animationDelay: `${i * 0.18}s`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
