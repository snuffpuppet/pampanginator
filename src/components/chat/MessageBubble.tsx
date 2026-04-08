import type { Message } from '../../store/conversation'

// Minimal markdown renderer: bold, italic (→ kap style), headers, lists, hr, line breaks
function renderMarkdown(text: string): string {
  return text
    // Tables: leave as simple text for now, handled by CSS
    // Headers
    .replace(/^### (.+)$/gm, '<h4 style="font-family:\'Cormorant Garamond\',serif;font-size:1.05em;color:var(--amber-light);margin:0.5rem 0 0.25rem;font-weight:600;">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 style="font-family:\'Cormorant Garamond\',serif;font-size:1.2em;color:var(--amber-light);margin:0.5rem 0 0.3rem;font-weight:600;">$1</h3>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic → Kapampangan style
    .replace(/\*(.+?)\*/g, '<em class="kap">$1</em>')
    // Horizontal rule
    .replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid var(--border);margin:0.6rem 0;" />')
    // Unordered lists
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul style="padding-left:1.2rem;margin:0.3rem 0;">${match}</ul>`)
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p style="margin-bottom:0.45rem;">')
    // Single newline
    .replace(/\n/g, '<br />')
}

interface Props {
  message: Message
  isStreaming?: boolean
}

export default function MessageBubble({ message, isStreaming }: Props) {
  const isAding = message.role === 'assistant'

  const html = renderMarkdown(message.content)

  return (
    <div
      className="msg-enter"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isAding ? 'flex-start' : 'flex-end',
        gap: '0.25rem',
      }}
    >
      {isAding && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', maxWidth: '90%' }}>
          {/* Ading avatar */}
          <div style={{
            width: 28, height: 28, borderRadius: '50%', flexShrink: 0, marginTop: 2,
            background: 'var(--bg-3)', border: '1px solid var(--border-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.65rem', color: 'var(--amber)',
          }}>
            ◎
          </div>
          <div
            className="bubble-ading msg-content"
            dangerouslySetInnerHTML={{
              __html: `<p style="margin-bottom:0.45rem;">${html}</p>`,
            }}
          />
        </div>
      )}

      {!isAding && (
        <div
          className="bubble-user"
          style={{ color: 'var(--text)', fontSize: '0.9rem' }}
        >
          <p style={{ margin: 0 }}>{message.content}</p>
        </div>
      )}

      {isStreaming && isAding && (
        <span style={{
          fontSize: '0.7rem', color: 'var(--text-dim)', marginLeft: '2.2rem',
        }}>
          Ading is writing…
        </span>
      )}
    </div>
  )
}
