/**
 * All HTTP calls in one place — Decision 10.
 *
 * Nothing outside this file calls fetch(). Components and the store
 * import from here; if the backend URL or request format changes,
 * one file changes.
 */

import { buildVocabContext } from '../lib/lookup'

// ─── Types ────────────────────────────────────────────────────────────────────

export type Mode =
  | 'chat'
  | 'translation-en-kp'
  | 'translation-kp-en'
  | 'correction'
  | 'scenario'

export interface ApiMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface BackendStatus {
  backend: 'anthropic' | 'ollama'
  ollamaModel: string
  ollamaUrl: string
  hasAnthropicKey: boolean
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

const LOOKUP_MODES: Mode[] = ['translation-en-kp', 'translation-kp-en', 'correction']

function buildUserContent(
  text: string,
  mode: Mode,
  vocabContext: string,
  scenarioName?: string,
): string {
  const ref = vocabContext ? `${vocabContext}\n\n` : ''
  switch (mode) {
    case 'translation-en-kp':
      return `${ref}[TRANSLATION: EN→KP] Translate to Kapampangan and provide a brief usage note: "${text}"`
    case 'translation-kp-en':
      return `${ref}[TRANSLATION: KP→EN] Translate this Kapampangan to English and note any grammar of interest: "${text}"`
    case 'correction':
      return `${ref}[ERROR CORRECTION MODE] Apply your five-step correction protocol to this Kapampangan sentence the learner wrote: "${text}"`
    case 'scenario':
      return `${ref}[SCENARIO: ${scenarioName ?? 'Conversation Practice'}] ${text}`
    default:
      return `${ref}${text}`
  }
}

async function readStream(
  body: ReadableStream<Uint8Array>,
  onChunk: (text: string) => void,
): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6)
      if (data === '[DONE]') return
      try {
        const { text } = JSON.parse(data)
        if (text) onChunk(text)
      } catch { /* partial chunk — skip */ }
    }
  }
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Stream a chat response from Ading.
 *
 * Enriches the last user message with authoritative vocabulary context and the
 * appropriate mode prefix, then opens an SSE connection and calls onChunk for
 * each text delta received.
 *
 * Returns { sourcesUsed: true } if kaikki.org reference data was injected.
 */
export async function streamChat(
  messages: ApiMessage[],
  onChunk: (text: string) => void,
  mode: Mode = 'chat',
  scenarioName?: string,
  endpoint = '/api/chat',
): Promise<{ sourcesUsed: boolean }> {
  const userText = messages[messages.length - 1]?.content ?? ''
  const shouldLookup = LOOKUP_MODES.includes(mode) || userText.length < 200
  const vocabContext = shouldLookup ? await buildVocabContext(userText) : ''

  const processedMessages = messages.map((msg, i) =>
    i === messages.length - 1 && msg.role === 'user'
      ? { ...msg, content: buildUserContent(msg.content, mode, vocabContext, scenarioName) }
      : msg,
  )

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: processedMessages }),
  })

  if (!response.ok) throw new Error(`API error: ${response.status}`)
  if (!response.body) throw new Error('No response body')

  await readStream(response.body, onChunk)

  return { sourcesUsed: !!vocabContext }
}

/**
 * Fetch the current backend configuration from the dev server.
 */
export async function getBackendStatus(): Promise<BackendStatus> {
  const res = await fetch('/api/status')
  if (!res.ok) throw new Error('Could not reach /api/status')
  return res.json() as Promise<BackendStatus>
}
