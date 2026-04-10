import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SYSTEM_PROMPT_PATH = join(__dirname, '../config/system_prompt.md')

// ─── OpenRouter SSE streaming helper ─────────────────────────────────────────
async function streamOpenRouter(
  apiKey: string,
  model: string,
  systemPrompt: string,
  messages: { role: string; content: string }[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  res: any,
) {
  if (!apiKey) throw new Error('OPENROUTER_API_KEY not set in .env')

  const orRes = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'system', content: systemPrompt }, ...messages],
      stream: true,
    }),
  })

  if (!orRes.ok) throw new Error(`OpenRouter error ${orRes.status} — check your OPENROUTER_API_KEY`)

  const reader = orRes.body!.getReader()
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

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // ── Config from .env ───────────────────────────────────────────────────────
  const defaultBackend = env.BACKEND || 'openrouter'
  const openRouterKey  = env.OPENROUTER_API_KEY || ''
  const modelA         = env.OPENROUTER_MODEL_A || 'anthropic/claude-sonnet-4-6'
  const modelB         = env.OPENROUTER_MODEL_B || 'meta-llama/llama-3.1-8b-instruct'
  // Active model: explicit override, else model A default
  const activeModel    = env.OPENROUTER_MODEL || modelA

  return {
    build: { outDir: '../app/frontend' },
    plugins: [
      react(),
      {
        name: 'ading-api',
        configureServer(server) {

          // ── /api/status ─────────────────────────────────────────────────────
          server.middlewares.use('/api/status', (_req, res) => {
            res.writeHead(200, { 'Content-Type': 'application/json' })
            res.end(JSON.stringify({
              backend:          defaultBackend,
              modelA,
              modelB,
              hasOpenRouterKey: !!openRouterKey,
            }))
          })

          // ── Chat handler factory ─────────────────────────────────────────────
          async function handleChat(
            model: string,
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
                const systemPrompt = readFileSync(SYSTEM_PROMPT_PATH, 'utf-8')

                res.writeHead(200, {
                  'Content-Type':  'text/event-stream',
                  'Cache-Control': 'no-cache',
                  'Connection':    'keep-alive',
                  'X-Model':       model,
                })

                await streamOpenRouter(openRouterKey, model, systemPrompt, messages, res)

                res.write('data: [DONE]\n\n')
                res.end()
              } catch (err) {
                console.error('[Ading API]', err)
                if (!res.headersSent) res.writeHead(500, { 'Content-Type': 'application/json' })
                res.end(JSON.stringify({ error: String(err) }))
              }
            })
          }

          // ── /api/chat/model-a — always model A ───────────────────────────────
          server.middlewares.use('/api/chat/model-a', (req, res) => {
            handleChat(modelA, req, res)
          })

          // ── /api/chat/model-b — always model B ───────────────────────────────
          server.middlewares.use('/api/chat/model-b', (req, res) => {
            handleChat(modelB, req, res)
          })

          // ── /api/chat — uses active model from .env ───────────────────────────
          server.middlewares.use('/api/chat', (req, res) => {
            handleChat(activeModel, req, res)
          })
        },
      },
    ],
  }
})
