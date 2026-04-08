import { useNavigate } from 'react-router-dom'
import ChatWindow from '../components/chat/ChatWindow'
import { useConversation } from '../store/conversation'

export default function Chat() {
  const navigate = useNavigate()
  const { clearConversation } = useConversation()

  return (
    <div className="page page-enter" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1rem',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-1)',
        flexShrink: 0,
      }}>
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.35rem',
            fontSize: '0.82rem', padding: '0.25rem',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="M9 2L4 7l5 5"/>
          </svg>
          Home
        </button>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span className="font-display" style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text)' }}>
            Ading
          </span>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>
            Kapampangan companion
          </span>
        </div>

        <button
          onClick={() => {
            if (window.confirm('Clear this conversation and start fresh?')) clearConversation()
          }}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-dim)', fontSize: '0.75rem', padding: '0.25rem',
          }}
          title="Clear session"
        >
          Clear
        </button>
      </div>

      {/* Chat */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <ChatWindow mode="chat" placeholder="Ask Ading anything about Kapampangan…" />
      </div>
    </div>
  )
}
