import { useState, useRef, useEffect } from 'react'
import { streamChat, getBackendStatus } from '../services/api'
import type { BackendStatus } from '../services/api'

interface PanelState {
  text: string
  status: 'idle' | 'streaming' | 'done' | 'error'
  elapsedMs: number | null
  error: string | null
}

const EMPTY_PANEL: PanelState = { text: '', status: 'idle', elapsedMs: null, error: null }

const SAMPLE_PROMPTS = [
  'How do I say "I miss you" in Kapampangan?',
  'Explain the difference between sinulat and sumulat.',
  'Translate: "Good morning, have you eaten yet?"',
  'What does "Kaluguran da ka" mean?',
  'How do I conjugate the verb "mangan" in all three aspects?',
]

export default function Compare() {
  const [query, setQuery]         = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [anthropic, setAnthropic] = useState<PanelState>(EMPTY_PANEL)
  const [ollama, setOllama]       = useState<PanelState>(EMPTY_PANEL)
  const [status, setStatus]       = useState<BackendStatus | null>(null)
  const anthropicRef              = useRef<HTMLDivElement>(null)
  const ollamaRef                 = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getBackendStatus().then(setStatus).catch(() => null)
  }, [])

  async function runComparison() {
    if (!query.trim() || isRunning) return
    setIsRunning(true)
    setAnthropic({ text: '', status: 'streaming', elapsedMs: null, error: null })
    setOllama({ text: '', status: 'streaming', elapsedMs: null, error: null })

    const messages = [{ role: 'user' as const, content: query }]

    async function runPanel(
      endpoint: string,
      setter: React.Dispatch<React.SetStateAction<PanelState>>,
    ) {
      const t0 = Date.now()
      try {
        await streamChat(
          messages,
          (chunk) => setter(prev => ({ ...prev, text: prev.text + chunk })),
          'chat',
          undefined,
          endpoint,
        )
        setter(prev => ({ ...prev, status: 'done', elapsedMs: Date.now() - t0 }))
      } catch (err) {
        setter(prev => ({
          ...prev,
          status: 'error',
          elapsedMs: Date.now() - t0,
          error: err instanceof Error ? err.message : String(err),
        }))
      }
    }

    await Promise.allSettled([
      runPanel('/api/chat/anthropic', setAnthropic),
      runPanel('/api/chat/ollama', setOllama),
    ])

    setIsRunning(false)
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runComparison() }
  }

  const ollamaLabel = status ? status.ollamaModel : 'ollama'

  return (
    <div className="page page-enter" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{ padding: '1.1rem 1.25rem 0.75rem', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.6rem', marginBottom: '0.15rem' }}>
          <h1 className="font-display" style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text)', margin: 0 }}>
            Compare
          </h1>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            Claude vs Local LLM
          </span>
        </div>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0 }}>
          Same question, both backends — side by side.
        </p>
      </div>

      {/* Status pills */}
      {status && (
        <div style={{ padding: '0.6rem 1.25rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', flexShrink: 0 }}>
          <span style={{
            fontSize: '0.7rem',
            padding: '0.2rem 0.6rem',
            borderRadius: 20,
            background: status.hasAnthropicKey ? 'rgba(61,138,101,0.18)' : 'rgba(193,68,14,0.18)',
            border: `1px solid ${status.hasAnthropicKey ? 'rgba(61,138,101,0.4)' : 'rgba(193,68,14,0.4)'}`,
            color: status.hasAnthropicKey ? '#6ecf9f' : '#e07050',
          }}>
            {status.hasAnthropicKey ? '● Claude (Anthropic)' : '○ Claude — no API key'}
          </span>
          <span style={{
            fontSize: '0.7rem',
            padding: '0.2rem 0.6rem',
            borderRadius: 20,
            background: 'rgba(245,166,35,0.1)',
            border: '1px solid rgba(245,166,35,0.25)',
            color: 'var(--amber)',
          }}>
            ◉ {ollamaLabel} (local)
          </span>
          <span style={{
            fontSize: '0.7rem',
            padding: '0.2rem 0.6rem',
            borderRadius: 20,
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid var(--border)',
            color: 'var(--text-dim)',
          }}>
            default: {status.backend}
          </span>
        </div>
      )}

      {/* Sample prompts */}
      <div style={{ padding: '0 1.25rem 0.6rem', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {SAMPLE_PROMPTS.map(p => (
            <button
              key={p}
              onClick={() => setQuery(p)}
              style={{
                fontSize: '0.68rem',
                padding: '0.2rem 0.55rem',
                borderRadius: 12,
                border: '1px solid var(--border)',
                background: query === p ? 'rgba(245,166,35,0.12)' : 'transparent',
                color: query === p ? 'var(--amber)' : 'var(--text-dim)',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div style={{ padding: '0 1.25rem 0.85rem', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-end' }}>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask something about Kapampangan…"
            rows={2}
            disabled={isRunning}
            style={{
              flex: 1,
              background: 'var(--bg-2)',
              border: '1px solid var(--border)',
              borderRadius: 10,
              padding: '0.65rem 0.85rem',
              color: 'var(--text)',
              fontSize: '0.9rem',
              resize: 'none',
              fontFamily: 'inherit',
              outline: 'none',
            }}
          />
          <button
            onClick={runComparison}
            disabled={!query.trim() || isRunning}
            style={{
              padding: '0.65rem 1.1rem',
              borderRadius: 10,
              background: query.trim() && !isRunning ? 'var(--amber)' : 'var(--bg-3)',
              color: query.trim() && !isRunning ? '#1a0e00' : 'var(--text-dim)',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: query.trim() && !isRunning ? 'pointer' : 'not-allowed',
              transition: 'all 0.15s',
              flexShrink: 0,
              height: 'fit-content',
            }}
          >
            {isRunning ? '…' : 'Compare'}
          </button>
        </div>
      </div>

      {/* Panels */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '0',
        overflow: 'hidden',
        borderTop: '1px solid var(--border)',
      }}>
        <Panel
          label="Claude"
          sublabel="Anthropic"
          accentColor="var(--forest-light, #3d8a65)"
          state={anthropic}
          ref={anthropicRef}
          isRunning={isRunning}
        />
        <div style={{ borderLeft: '1px solid var(--border)', overflow: 'hidden' }}>
          <Panel
            label={ollamaLabel}
            sublabel="Local · Ollama"
            accentColor="var(--amber)"
            state={ollama}
            ref={ollamaRef}
            isRunning={isRunning}
          />
        </div>
      </div>
    </div>
  )
}

interface PanelProps {
  label: string
  sublabel: string
  accentColor: string
  state: PanelState
  isRunning: boolean
  ref: React.RefObject<HTMLDivElement | null>
}

function Panel({ label, sublabel, accentColor, state, isRunning, ref }: PanelProps) {
  // Auto-scroll as content streams in
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [state.text, ref])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Panel header */}
      <div style={{
        padding: '0.55rem 0.9rem',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
        background: 'rgba(0,0,0,0.12)',
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
          <span style={{ fontFamily: '"Cormorant Garamond", serif', fontWeight: 700, fontSize: '1rem', color: accentColor }}>
            {label}
          </span>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {sublabel}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {state.status === 'streaming' && (
            <span style={{ display: 'flex', gap: 3 }}>
              {[0, 1, 2].map(i => (
                <span key={i} style={{
                  width: 4, height: 4, borderRadius: '50%', background: accentColor,
                  animation: `typing-dot 1s ease-in-out ${i * 0.2}s infinite`,
                  opacity: 0.7,
                }} />
              ))}
            </span>
          )}
          {state.elapsedMs !== null && (
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>
              {(state.elapsedMs / 1000).toFixed(1)}s
            </span>
          )}
          {state.status === 'done' && (
            <span style={{ fontSize: '0.65rem', color: accentColor }}>✓</span>
          )}
          {state.status === 'error' && (
            <span style={{ fontSize: '0.65rem', color: 'var(--terra)' }}>✗</span>
          )}
        </div>
      </div>

      {/* Content */}
      <div
        ref={ref}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.9rem',
          fontSize: '0.84rem',
          lineHeight: 1.7,
          color: 'var(--text)',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {state.status === 'idle' && !isRunning && (
          <span style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: '0.78rem' }}>
            Waiting for a query…
          </span>
        )}
        {state.status === 'error' && (
          <div>
            <div style={{
              padding: '0.65rem 0.85rem',
              borderRadius: 8,
              background: 'rgba(193,68,14,0.12)',
              border: '1px solid rgba(193,68,14,0.3)',
              color: '#e07050',
              fontSize: '0.78rem',
              lineHeight: 1.6,
            }}>
              <strong>Error</strong><br />
              {state.error}
              {state.error?.includes('Ollama') && (
                <div style={{ marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                  Make sure Ollama is running: <code style={{ color: 'var(--amber)' }}>ollama serve</code>
                </div>
              )}
            </div>
          </div>
        )}
        {state.text && (
          <ResponseText text={state.text} />
        )}
      </div>
    </div>
  )
}

function ResponseText({ text }: { text: string }) {
  // Render *kapampangan* in italic amber (same as MessageBubble)
  const parts = text.split(/(\*[^*]+\*)/)
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith('*') && part.endsWith('*') && part.length > 2
          ? <em key={i} className="kap">{part.slice(1, -1)}</em>
          : <span key={i}>{part}</span>
      )}
    </>
  )
}
