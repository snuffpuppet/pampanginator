import { useState, useEffect } from 'react'
import { streamAdingResponse } from '../lib/ading'
import type { Mode } from '../lib/ading'
import { isDatabaseLoaded, getDatabaseSize } from '../lib/lookup'

function renderTranslationHtml(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em class="kap">$1</em>')
    .replace(/\n\n/g, '</p><p style="margin-bottom:0.4rem;">')
    .replace(/\n/g, '<br />')
}

export default function Translate() {
  const [direction, setDirection] = useState<'en-kp' | 'kp-en'>('en-kp')
  const [input, setInput] = useState('')
  const [result, setResult] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sourcesUsed, setSourcesUsed] = useState(false)
  const [dbSize, setDbSize] = useState(0)

  useEffect(() => {
    isDatabaseLoaded().then(loaded => {
      if (loaded) getDatabaseSize().then(setDbSize)
    })
  }, [])

  const mode: Mode = direction === 'en-kp' ? 'translation-en-kp' : 'translation-kp-en'

  const handleTranslate = async () => {
    if (!input.trim() || isLoading) return
    setResult('')
    setSourcesUsed(false)
    setIsLoading(true)
    try {
      const res = await streamAdingResponse(
        [{ role: 'user', content: input.trim() }],
        (chunk) => setResult((r) => r + chunk),
        mode,
      )
      setSourcesUsed(res.sourcesUsed)
    } catch {
      setResult('*Pasensya na* — something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const sourceLang = direction === 'en-kp' ? 'English' : 'Kapampangan'
  const targetLang = direction === 'en-kp' ? 'Kapampangan' : 'English'

  return (
    <div className="page parol-bg page-enter" style={{ overflowY: 'auto' }}>
      <div className="page-padded">
        {/* Header */}
        <div style={{ marginBottom: '1.25rem' }}>
          <h1 className="section-heading" style={{ marginBottom: '0.25rem' }}>Translate</h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            Ading will translate and explain usage
          </p>
          {/* Database status */}
          {dbSize > 0 ? (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.3rem 0.7rem', borderRadius: 20,
              background: 'rgba(45,106,79,0.15)', border: '1px solid rgba(45,106,79,0.3)',
              fontSize: '0.72rem', color: '#3d8a65',
            }}>
              <span>◉</span>
              {dbSize.toLocaleString()} verified entries from kaikki.org / Wiktionary
            </div>
          ) : (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.3rem 0.7rem', borderRadius: 20,
              background: 'rgba(193,68,14,0.1)', border: '1px solid rgba(193,68,14,0.25)',
              fontSize: '0.72rem', color: 'var(--terra-light)',
            }}>
              <span>◌</span>
              No reference database — run <code style={{ fontFamily: 'monospace', background: 'rgba(0,0,0,0.3)', padding: '0 4px', borderRadius: 3 }}>npm run fetch-vocab</code> to enable
            </div>
          )}
        </div>

        {/* Direction toggle */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          marginBottom: '1rem',
          background: 'var(--bg-2)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '0.35rem',
        }}>
          {(['en-kp', 'kp-en'] as const).map((dir) => (
            <button
              key={dir}
              onClick={() => { setDirection(dir); setResult(''); setInput('') }}
              style={{
                flex: 1,
                padding: '0.45rem',
                borderRadius: 7,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
                transition: 'all 0.15s ease',
                background: direction === dir ? 'var(--bg-3)' : 'transparent',
                color: direction === dir ? 'var(--amber-light)' : 'var(--text-muted)',
                fontFamily: 'Sora, sans-serif',
              }}
            >
              {dir === 'en-kp' ? 'English → Kapampangan' : 'Kapampangan → English'}
            </button>
          ))}
        </div>

        {/* Input */}
        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.7rem',
            fontWeight: 600,
            color: 'var(--text-dim)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.4rem',
          }}>
            {sourceLang}
          </label>
          <textarea
            className="input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={direction === 'en-kp'
              ? 'Type English text to translate…'
              : 'Isulat ing Kapampangan…'}
            rows={3}
            style={{ resize: 'vertical', minHeight: 80 }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleTranslate()
            }}
          />
        </div>

        <button
          className="btn-amber"
          onClick={handleTranslate}
          disabled={isLoading || !input.trim()}
          style={{ width: '100%', marginBottom: '1.25rem', justifyContent: 'center' }}
        >
          {isLoading ? (
            <>
              <span style={{ opacity: 0.7 }}>Translating</span>
              <span style={{ opacity: 0.5 }}>…</span>
            </>
          ) : (
            <>
              Translate to {targetLang}
              <span style={{ fontSize: '0.9rem', opacity: 0.7 }}>⌘↵</span>
            </>
          )}
        </button>

        {/* Result */}
        {(result || isLoading) && (
          <div style={{ animation: 'pageEnter 0.28s ease forwards' }}>
            <label style={{
              display: 'block',
              fontSize: '0.7rem',
              fontWeight: 600,
              color: 'var(--text-dim)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '0.4rem',
            }}>
              {targetLang} — Ading's Response
            </label>
            <div
              className="card msg-content"
              style={{ padding: '1rem', minHeight: 60 }}
            >
              {result ? (
                <>
                  <div dangerouslySetInnerHTML={{ __html: `<p style="margin-bottom:0.4rem;">${renderTranslationHtml(result)}</p>` }} />
                  {sourcesUsed && (
                    <div style={{ marginTop: '0.6rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border)', fontSize: '0.68rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <span style={{ color: 'var(--forest)', fontSize: '0.75rem' }}>◉</span>
                      Grounded with kaikki.org / Wiktionary reference data
                    </div>
                  )}
                </>
              ) : (
                <div style={{ display: 'flex', gap: 5, alignItems: 'center', height: 24 }}>
                  {[0, 1, 2].map(i => (
                    <span key={i} className="typing-dot" style={{
                      display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
                      background: 'var(--amber-dim)', animationDelay: `${i * 0.18}s`,
                    }} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick-phrase shortcuts */}
        {!result && !isLoading && (
          <div style={{ marginTop: '1.5rem' }}>
            <p style={{
              fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase',
              letterSpacing: '0.08em', fontWeight: 600, marginBottom: '0.6rem',
            }}>
              Try these
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {(direction === 'en-kp'
                ? ["I haven't eaten yet.", "How are you?", "Let's go home.", "Thank you very much.", "I love you."]
                : ["Mangan ta na!", "Kaluguran da ka.", "Mayap a abak.", "Awa.", "Tara na."]
              ).map((phrase) => (
                <button
                  key={phrase}
                  onClick={() => { setInput(phrase); setResult('') }}
                  style={{
                    padding: '0.3rem 0.7rem',
                    background: 'var(--bg-2)',
                    border: '1px solid var(--border)',
                    borderRadius: 20,
                    color: 'var(--text-muted)',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    fontFamily: 'Sora, sans-serif',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--amber-dim)'
                    e.currentTarget.style.color = 'var(--text)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border)'
                    e.currentTarget.style.color = 'var(--text-muted)'
                  }}
                >
                  {phrase}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
