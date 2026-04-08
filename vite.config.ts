import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// ─── Shared SSE streaming helper ─────────────────────────────────────────────
async function streamOllama(
  ollamaUrl: string,
  ollamaModel: string,
  systemPrompt: string,
  messages: { role: string; content: string }[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  res: any,
) {
  const ollamaRes = await fetch(`${ollamaUrl}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: ollamaModel,
      messages: [{ role: 'system', content: systemPrompt }, ...messages],
      stream: true,
    }),
  })

  if (!ollamaRes.ok) throw new Error(`Ollama error ${ollamaRes.status} — is Ollama running? Try: ollama serve`)

  const reader = ollamaRes.body!.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6)
      if (data === '[DONE]') break
      try {
        const chunk = JSON.parse(data)
        const text = chunk.choices?.[0]?.delta?.content
        if (text) res.write(`data: ${JSON.stringify({ text })}\n\n`)
      } catch { /* partial chunk */ }
    }
  }
}

async function streamAnthropic(
  apiKey: string,
  systemPrompt: string,
  messages: { role: string; content: string }[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  res: any,
) {
  const { default: Anthropic } = await import('@anthropic-ai/sdk')
  const client = new Anthropic({ apiKey })

  const stream = client.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    system: systemPrompt,
    messages: messages as Parameters<typeof client.messages.stream>[0]['messages'],
  })

  for await (const event of stream) {
    if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
      res.write(`data: ${JSON.stringify({ text: event.delta.text })}\n\n`)
    }
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // ── Config from .env ───────────────────────────────────────────────────────
  const defaultBackend = (env.BACKEND || 'anthropic') as 'anthropic' | 'ollama'
  const ollamaModel    = env.OLLAMA_MODEL || 'llama3.2'
  const ollamaUrl      = env.OLLAMA_URL   || 'http://localhost:11434'
  const anthropicKey   = env.ANTHROPIC_API_KEY || ''

  return {
    plugins: [
      react(),
      {
        name: 'ading-api',
        configureServer(server) {

          // ── /api/status ─────────────────────────────────────────────────────
          server.middlewares.use('/api/status', (_req, res) => {
            res.writeHead(200, { 'Content-Type': 'application/json' })
            res.end(JSON.stringify({
              backend:        defaultBackend,
              ollamaModel,
              ollamaUrl,
              hasAnthropicKey: !!anthropicKey,
            }))
          })

          // ── Chat handler factory ─────────────────────────────────────────────
          async function handleChat(
            backend: 'anthropic' | 'ollama',
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            req: any,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            res: any,
          ) {
            if (req.method !== 'POST') { res.writeHead(405); res.end(); return }

            let body = ''
            req.on('data', (chunk: Buffer) => { body += chunk.toString() })
            req.on('end', async () => {
              try {
                const { messages } = JSON.parse(body)
                const { readFileSync } = await import('fs')
                const { resolve }      = await import('path')
                const systemPrompt = readFileSync(resolve('./prompt.md'), 'utf-8')

                res.writeHead(200, {
                  'Content-Type':  'text/event-stream',
                  'Cache-Control': 'no-cache',
                  'Connection':    'keep-alive',
                  'X-Backend':     backend,
                })

                if (backend === 'ollama') {
                  await streamOllama(ollamaUrl, ollamaModel, systemPrompt, messages, res)
                } else {
                  if (!anthropicKey) throw new Error('ANTHROPIC_API_KEY not set in .env')
                  await streamAnthropic(anthropicKey, systemPrompt, messages, res)
                }

                res.write('data: [DONE]\n\n')
                res.end()
              } catch (err) {
                console.error('[Ading API]', err)
                if (!res.headersSent) res.writeHead(500, { 'Content-Type': 'application/json' })
                res.end(JSON.stringify({ error: String(err) }))
              }
            })
          }

          // ── /api/chat/anthropic — always Anthropic ───────────────────────────
          server.middlewares.use('/api/chat/anthropic', (req, res) => {
            handleChat('anthropic', req, res)
          })

          // ── /api/chat/ollama — always Ollama ─────────────────────────────────
          server.middlewares.use('/api/chat/ollama', (req, res) => {
            handleChat('ollama', req, res)
          })

          // ── /api/chat — uses BACKEND from .env ───────────────────────────────
          server.middlewares.use('/api/chat', (req, res) => {
            handleChat(defaultBackend, req, res)
          })
        },
      },
    ],
  }
})
