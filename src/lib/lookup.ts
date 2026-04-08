/**
 * Vocabulary lookup against the kaikki.org / Wiktionary dataset.
 *
 * Given a user's query string, finds relevant Kapampangan dictionary entries
 * and returns them formatted as an authoritative context block to prepend
 * to the API message.
 *
 * Populate the database first:  npm run fetch-vocab
 */

export interface KaikkiEntry {
  word: string
  pos: string
  glosses: string[]
  ipa: string | null
  examples: { kap: string; en: string }[]
  forms: { form: string; tags: string[] }[]
  etymology: string | null
  synonyms?: string[]
}

// Lazy-loaded on first call — avoids impacting initial bundle parse time
let _entries: KaikkiEntry[] | null = null
let _formIndex: Map<string, KaikkiEntry> | null = null   // form → entry
let _glossIndex: Map<string, KaikkiEntry[]> | null = null // gloss word → entries

async function load(): Promise<KaikkiEntry[]> {
  if (_entries !== null) return _entries

  try {
    const mod = await import('../data/kaikki.json', { assert: { type: 'json' } })
    _entries = (mod.default ?? mod) as KaikkiEntry[]
  } catch {
    // File not yet generated — run `npm run fetch-vocab`
    _entries = []
  }

  // Build indexes for fast lookup
  _formIndex = new Map()
  _glossIndex = new Map()

  for (const entry of _entries) {
    // Form index: every inflected form → its entry
    for (const f of entry.forms ?? []) {
      if (f.form) _formIndex.set(f.form.toLowerCase(), entry)
    }
    // Gloss index: each individual word in every gloss → entries that contain it
    for (const gloss of entry.glosses) {
      const words = gloss.toLowerCase().replace(/[^\w\s]/g, ' ').split(/\s+/).filter(w => w.length > 2)
      for (const word of words) {
        if (!_glossIndex.has(word)) _glossIndex.set(word, [])
        _glossIndex.get(word)!.push(entry)
      }
    }
  }

  return _entries
}

// English stop words — not useful as gloss-match candidates
const STOP_WORDS = new Set([
  'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her',
  'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how',
  'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'did', 'its',
  'let', 'put', 'say', 'she', 'too', 'use', 'that', 'this', 'with',
  'have', 'from', 'they', 'will', 'been', 'than', 'what', 'when', 'which',
  'would', 'there', 'their', 'about', 'into', 'more', 'some', 'make',
  'like', 'just', 'also', 'know', 'take', 'than', 'only', 'over', 'such',
  'even', 'most', 'after', 'also', 'many', 'does', 'mean', 'said', 'each',
  'word', 'want', 'tell', 'help', 'please', 'show', 'give', 'need', 'ask',
  'translate', 'translation', 'kapampangan', 'english', 'language', 'using',
  'explain', 'example', 'sentence', 'meaning', 'phrase', 'word', 'form',
  'say', 'speak', 'write', 'learn', 'practice', 'correct', 'wrong',
])

function tokenise(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2 && !STOP_WORDS.has(w))
}

interface ScoredEntry { entry: KaikkiEntry; score: number }

/**
 * Find dictionary entries relevant to the given query text.
 * Returns up to `limit` entries sorted by relevance score.
 */
async function findRelevant(text: string, limit = 6): Promise<KaikkiEntry[]> {
  const entries = await load()
  if (entries.length === 0) return []

  const tokens = tokenise(text)
  if (tokens.length === 0) return []

  const scored = new Map<string, ScoredEntry>()

  const score = (entry: KaikkiEntry, points: number) => {
    const key = entry.word
    const current = scored.get(key)
    if (!current || current.score < points) {
      scored.set(key, { entry, score: (current?.score ?? 0) + points })
    } else {
      current.score += points
    }
  }

  for (const token of tokens) {
    // 1. Exact word match (highest priority — user typed a Kapampangan word)
    const exact = entries.find(e => e.word.toLowerCase() === token)
    if (exact) { score(exact, 12); continue }

    // 2. Inflected form match (e.g. "sinulat" → entry for "sulat")
    const byForm = _formIndex?.get(token)
    if (byForm) { score(byForm, 9); continue }

    // 3. Word starts with token (partial stem match, e.g. "mang" → "mangan")
    if (token.length >= 4) {
      for (const e of entries) {
        if (e.word.toLowerCase().startsWith(token)) score(e, 5)
      }
    }

    // 4. English gloss word match (user is describing an English concept)
    const byGloss = _glossIndex?.get(token) ?? []
    for (const e of byGloss) score(e, 3)
  }

  return Array.from(scored.values())
    .filter(s => s.score >= 3)          // minimum relevance threshold
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(s => s.entry)
}

/**
 * Main export. Given a user query string, returns a formatted authoritative
 * context block to prepend to the API message, or an empty string if no
 * relevant entries were found.
 */
export async function buildVocabContext(userText: string): Promise<string> {
  const matches = await findRelevant(userText)
  if (matches.length === 0) return ''

  const lines: string[] = [
    '[AUTHORITATIVE VOCABULARY REFERENCE — kaikki.org / Wiktionary CC-BY-SA]',
    'The following verified dictionary entries are relevant to this query.',
    'Treat these as ground truth for word meanings and forms.',
    '',
  ]

  for (const entry of matches) {
    // Heading: word (pos) — up to 3 glosses
    const glossStr = entry.glosses.slice(0, 3).join('; ')
    lines.push(`${entry.word} (${entry.pos}) — ${glossStr}`)

    if (entry.ipa) {
      lines.push(`  Pronunciation: ${entry.ipa}`)
    }

    if (entry.forms.length > 0) {
      // Group forms by their first meaningful tag
      const formStr = entry.forms
        .slice(0, 6)
        .map(f => {
          const tag = f.tags.find(t => !['positive', 'form-of'].includes(t))
          return tag ? `${f.form} (${tag})` : f.form
        })
        .join(', ')
      if (formStr) lines.push(`  Forms: ${formStr}`)
    }

    if (entry.examples.length > 0) {
      const ex = entry.examples[0]
      lines.push(`  Example: "${ex.kap}" → "${ex.en}"`)
    }

    if (entry.etymology) {
      lines.push(`  Etymology: ${entry.etymology}`)
    }

    if (entry.synonyms?.length) {
      lines.push(`  See also: ${entry.synonyms.join(', ')}`)
    }

    lines.push('')
  }

  lines.push('[End of authoritative reference]')
  lines.push('---')
  return lines.join('\n')
}

/**
 * Returns true if the kaikki database has been populated.
 * Use to show a warning in the UI if the user hasn't run fetch-vocab yet.
 */
export async function isDatabaseLoaded(): Promise<boolean> {
  const entries = await load()
  return entries.length > 0
}

/**
 * Returns the number of entries in the loaded database.
 */
export async function getDatabaseSize(): Promise<number> {
  const entries = await load()
  return entries.length
}
