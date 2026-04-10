import { useState } from 'react'
import type { Message } from '../store/conversation'
import { submitFeedback } from '../services/api'

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

type FeedbackState = 'idle' | 'thumbs_up' | 'correcting' | 'submitting' | 'done'

interface CorrectionForm {
  correction_kapampangan: string
  correction_english: string
  correction_note: string
  corrected_by: string
  authority_level: number
}

const EMPTY_FORM: CorrectionForm = {
  correction_kapampangan: '',
  correction_english: '',
  correction_note: '',
  corrected_by: '',
  authority_level: 3,
}

interface Props {
  message: Message
  isStreaming?: boolean
}

export default function MessageBubble({ message, isStreaming }: Props) {
  const isAding = message.role === 'assistant'
  const [feedbackState, setFeedbackState] = useState<FeedbackState>('idle')
  const [form, setForm] = useState<CorrectionForm>(EMPTY_FORM)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const html = renderMarkdown(message.content)

  async function handleThumbsUp() {
    setFeedbackState('thumbs_up')
    try {
      await submitFeedback({
        interaction_id: message.interactionId,
        rating: 'thumbs_up',
      })
      setFeedbackState('done')
    } catch {
      // Non-critical — feedback failure should not surface as an error
      setFeedbackState('idle')
    }
  }

  async function handleSubmitCorrection() {
    setFeedbackState('submitting')
    setSubmitError(null)
    try {
      await submitFeedback({
        interaction_id: message.interactionId,
        rating: 'thumbs_down',
        correction_kapampangan: form.correction_kapampangan || undefined,
        correction_english: form.correction_english || undefined,
        correction_note: form.correction_note || undefined,
        corrected_by: form.corrected_by || undefined,
        authority_level: form.authority_level,
      })
      setFeedbackState('done')
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Could not submit feedback')
      setFeedbackState('correcting')
    }
  }

  const showControls = isAding && !isStreaming && message.id !== 'welcome'

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

      {/* ── Feedback controls ─────────────────────────────────────────────── */}
      {showControls && feedbackState === 'idle' && (
        <div style={{ marginLeft: '2.2rem', display: 'flex', gap: '0.35rem' }}>
          <button
            onClick={handleThumbsUp}
            title="Helpful"
            style={{
              background: 'none', border: '1px solid var(--border)', borderRadius: 4,
              color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.75rem',
              padding: '0.15rem 0.45rem', lineHeight: 1.4,
              transition: 'border-color 0.15s, color 0.15s',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--amber)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--amber)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-dim)' }}
          >
            👍
          </button>
          <button
            onClick={() => setFeedbackState('correcting')}
            title="Incorrect — suggest a correction"
            style={{
              background: 'none', border: '1px solid var(--border)', borderRadius: 4,
              color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.75rem',
              padding: '0.15rem 0.45rem', lineHeight: 1.4,
              transition: 'border-color 0.15s, color 0.15s',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = '#c0392b'; (e.currentTarget as HTMLButtonElement).style.color = '#c0392b' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-dim)' }}
          >
            👎
          </button>
        </div>
      )}

      {showControls && feedbackState === 'thumbs_up' && (
        <span style={{ marginLeft: '2.2rem', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
          Sending…
        </span>
      )}

      {showControls && feedbackState === 'done' && (
        <span style={{ marginLeft: '2.2rem', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
          Feedback recorded — thank you.
        </span>
      )}

      {/* ── Inline correction form ────────────────────────────────────────── */}
      {showControls && (feedbackState === 'correcting' || feedbackState === 'submitting') && (
        <div style={{
          marginLeft: '2.2rem', marginTop: '0.4rem',
          background: 'var(--bg-2)', border: '1px solid var(--border)',
          borderRadius: 8, padding: '0.85rem 1rem', maxWidth: 480,
          display: 'flex', flexDirection: 'column', gap: '0.55rem',
        }}>
          <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--text-dim)' }}>
            What's wrong? All fields are optional.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
              Correct Kapampangan
            </label>
            <input
              className="input"
              placeholder="e.g. E ku pa mangan."
              value={form.correction_kapampangan}
              onChange={e => setForm(f => ({ ...f, correction_kapampangan: e.target.value }))}
              style={{ fontSize: '0.88rem' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
              English gloss of correction
            </label>
            <input
              className="input"
              placeholder="e.g. I haven't eaten yet."
              value={form.correction_english}
              onChange={e => setForm(f => ({ ...f, correction_english: e.target.value }))}
              style={{ fontSize: '0.88rem' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
              Note about the error
            </label>
            <input
              className="input"
              placeholder="e.g. Should be contemplated aspect, not completed."
              value={form.correction_note}
              onChange={e => setForm(f => ({ ...f, correction_note: e.target.value }))}
              style={{ fontSize: '0.88rem' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Your name (optional)
              </label>
              <input
                className="input"
                placeholder="e.g. Manang Rosa"
                value={form.corrected_by}
                onChange={e => setForm(f => ({ ...f, corrected_by: e.target.value }))}
                style={{ fontSize: '0.88rem' }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Authority
              </label>
              <select
                className="input"
                value={form.authority_level}
                onChange={e => setForm(f => ({ ...f, authority_level: Number(e.target.value) }))}
                style={{ fontSize: '0.85rem', width: 'auto' }}
              >
                <option value={1}>1 — Native speaker</option>
                <option value={2}>2 — Academic source</option>
                <option value={3}>3 — Community</option>
                <option value={4}>4 — Inference</option>
              </select>
            </div>
          </div>

          {submitError && (
            <p style={{ margin: 0, fontSize: '0.72rem', color: '#c0392b' }}>{submitError}</p>
          )}

          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <button
              className="btn-ghost"
              onClick={() => { setFeedbackState('idle'); setForm(EMPTY_FORM) }}
              disabled={feedbackState === 'submitting'}
              style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}
            >
              Cancel
            </button>
            <button
              className="btn-amber"
              onClick={handleSubmitCorrection}
              disabled={feedbackState === 'submitting'}
              style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}
            >
              {feedbackState === 'submitting' ? 'Sending…' : 'Submit'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
