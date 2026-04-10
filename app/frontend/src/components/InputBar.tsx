import { useState, useRef, useEffect } from 'react'

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
  placeholder?: string
}

export default function ChatInput({ onSend, disabled, placeholder = 'Ask Ading anything…' }: Props) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px'
  }, [text])

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      display: 'flex',
      gap: '0.5rem',
      alignItems: 'flex-end',
      padding: '0.75rem 1rem',
      background: 'var(--bg-1)',
      borderTop: '1px solid var(--border)',
    }}>
      <textarea
        ref={textareaRef}
        className="input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={disabled}
        style={{
          flex: 1,
          resize: 'none',
          lineHeight: '1.5',
          overflow: 'hidden',
          minHeight: '42px',
          maxHeight: '140px',
          paddingTop: '0.6rem',
          paddingBottom: '0.6rem',
        }}
      />
      <button
        className="btn-amber"
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        style={{ height: 42, paddingLeft: '1rem', paddingRight: '1rem', flexShrink: 0 }}
        aria-label="Send"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M1.5 1.5l13 6.5-13 6.5V9.5L10 8 1.5 6.5V1.5z"/>
        </svg>
      </button>
    </div>
  )
}
