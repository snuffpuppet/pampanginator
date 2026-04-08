import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '../../store/chatStore'
import { streamAdingResponse } from '../../lib/ading'
import type { Mode } from '../../lib/ading'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import ChatInput from './ChatInput'

interface Props {
  mode?: Mode
  scenarioName?: string
  placeholder?: string
}

export default function ChatWindow({ mode = 'chat', scenarioName, placeholder }: Props) {
  const { messages, isStreaming, streamingText, addUserMessage, appendStreaming, finalizeStream, setStreaming } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)
  const [lastUsedSources, setLastUsedSources] = useState(false)

  // Scroll to bottom on new messages or streaming
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, streamingText])

  const handleSend = async (text: string) => {
    if (isStreaming) return

    addUserMessage(text)
    setStreaming(true)

    const apiMessages = [
      ...messages.map((m) => ({ role: m.role, content: m.content })),
      { role: 'user' as const, content: text },
    ]

    try {
      const result = await streamAdingResponse(apiMessages, appendStreaming, mode, scenarioName)
      setLastUsedSources(result.sourcesUsed)
    } catch (err) {
      console.error(err)
      appendStreaming('\n\n*Pasensya na* — something went wrong. Please try again.')
    } finally {
      finalizeStream()
    }
  }

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

        {/* Streaming message */}
        {isStreaming && streamingText && (
          <MessageBubble
            message={{ id: 'streaming', role: 'assistant', content: streamingText, timestamp: Date.now() }}
            isStreaming
          />
        )}

        {/* Typing indicator (before first token arrives) */}
        {isStreaming && !streamingText && <TypingIndicator />}

        <div ref={bottomRef} />
      </div>

      {/* Source indicator */}
      {lastUsedSources && !isStreaming && (
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

      <ChatInput onSend={handleSend} disabled={isStreaming} placeholder={placeholder} />
    </div>
  )
}
