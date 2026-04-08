/**
 * ChatWindow — pure display component.
 *
 * Renders the message list from the store. Passes sendMessage to ChatInput.
 * Contains no API calls and no business logic.
 */

import { useEffect, useRef } from 'react'
import { useConversation } from '../../store/conversation'
import type { Mode } from '../../services/api'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import ChatInput from './ChatInput'

interface Props {
  mode?: Mode
  scenarioName?: string
  placeholder?: string
}

export default function ChatWindow({ mode = 'chat', scenarioName, placeholder }: Props) {
  const { messages, isStreaming, streamingText, sourcesUsed, sendMessage } = useConversation()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, streamingText])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}>
        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'assistant'}
          />
        ))}

        {isStreaming && streamingText && (
          <MessageBubble
            message={{ id: 'streaming', role: 'assistant', content: streamingText, timestamp: Date.now() }}
            isStreaming
          />
        )}

        {isStreaming && !streamingText && <TypingIndicator />}

        <div ref={bottomRef} />
      </div>

      {/* Source attribution */}
      {sourcesUsed && !isStreaming && (
        <div style={{
          padding: '0.3rem 1rem',
          fontSize: '0.68rem',
          color: 'var(--text-dim)',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-1)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
        }}>
          <span style={{ color: 'var(--forest)', fontSize: '0.75rem' }}>◉</span>
          Grounded with kaikki.org / Wiktionary reference data
        </div>
      )}

      <ChatInput
        onSend={(text) => sendMessage(text, mode, scenarioName)}
        disabled={isStreaming}
        placeholder={placeholder}
      />
    </div>
  )
}
