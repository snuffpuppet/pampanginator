/**
 * Fetches the Kapampangan vocabulary from kaikki.org (sourced from Wiktionary)
 * and writes a compact, lookup-ready JSON to src/data/kaikki.json.
 *
 * Run once: npm run fetch-vocab
 * Re-run to refresh (kaikki.org updates weekly).
 *
 * Source:  https://kaikki.org/dictionary/Kapampangan/
 * License: CC-BY-SA (Wiktionary)
 */

import { writeFile } from 'fs/promises'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUTPUT = resolve(__dirname, '../src/data/kaikki.json')
const JSONL_URL = 'https://kaikki.org/dictionary/Kapampangan/kaikki.org-dictionary-Kapampangan.jsonl'

// POS labels to make output human-readable
const POS_LABELS = {
  verb: 'verb', noun: 'noun', adj: 'adjective', adv: 'adverb',
  prep: 'preposition', conj: 'conjunction', intj: 'interjection',
  particle: 'particle', pron: 'pronoun', num: 'numeral', det: 'determiner',
  name: 'proper noun', prefix: 'prefix', suffix: 'suffix',
}

function processEntry(raw) {
  const senses = raw.senses ?? []

  // Collect all glosses, skip meta-only entries like "Alternative form of X"
  const glosses = senses
    .flatMap(s => s.glosses ?? s.raw_glosses ?? [])
    .filter(g => g && !g.startsWith('Alternative form') && !g.startsWith('Misspelling'))
    .slice(0, 5)

  if (glosses.length === 0) return null

  // Best IPA
  const ipa = raw.sounds?.find(s => s.ipa)?.ipa ?? null

  // Usage examples (text + translation, max 2)
  const examples = senses
    .flatMap(s => s.examples ?? [])
    .filter(e => e.text && (e.translation || e.english))
    .slice(0, 2)
    .map(e => ({ kap: e.text, en: e.translation ?? e.english }))

  // Inflected forms — strip the canonical form, keep useful ones
  const forms = (raw.forms ?? [])
    .filter(f => f.form && f.form !== raw.word && !f.tags?.includes('canonical') && !f.tags?.includes('table-tags'))
    .map(f => ({ form: f.form, tags: (f.tags ?? []).filter(t => !['romanization', 'table-tags'].includes(t)) }))
    .slice(0, 10)

  // Etymology — first sentence only to save tokens
  const etymology = raw.etymology_text
    ? raw.etymology_text.split(/[.;]/)[0].trim()
    : null

  // Synonyms
  const synonyms = senses
    .flatMap(s => s.synonyms ?? [])
    .map(s => s.word)
    .filter(Boolean)
    .slice(0, 4)

  return {
    word: raw.word,
    pos: POS_LABELS[raw.pos] ?? raw.pos ?? 'word',
    glosses,
    ipa,
    examples,
    forms,
    etymology,
    synonyms: synonyms.length ? synonyms : undefined,
  }
}

async function main() {
  console.log('⬇  Downloading Kapampangan vocabulary from kaikki.org…')
  console.log(`   Source: ${JSONL_URL}\n`)

  const response = await fetch(JSONL_URL)
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`)

  const text = await response.text()
  const lines = text.trim().split('\n').filter(Boolean)

  console.log(`   ${lines.length} raw entries received`)

  const entries = []
  let skipped = 0

  for (const line of lines) {
    try {
      const raw = JSON.parse(line)
      const entry = processEntry(raw)
      if (entry) {
        entries.push(entry)
      } else {
        skipped++
      }
    } catch {
      skipped++
    }
  }

  console.log(`   ${entries.length} usable entries (${skipped} skipped — no glosses or alternative-form-only)`)

  const json = JSON.stringify(entries)
  await writeFile(OUTPUT, json, 'utf-8')

  const kb = (json.length / 1024).toFixed(1)
  console.log(`\n✓  Written to src/data/kaikki.json (${kb} KB)`)
  console.log(`   POS breakdown:`)

  const byPos = {}
  for (const e of entries) byPos[e.pos] = (byPos[e.pos] ?? 0) + 1
  for (const [pos, count] of Object.entries(byPos).sort((a, b) => b[1] - a[1])) {
    console.log(`     ${pos.padEnd(14)} ${count}`)
  }
}

main().catch(err => {
  console.error('\n✗  Error:', err.message)
  process.exit(1)
})
