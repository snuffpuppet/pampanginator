import { useState, useEffect, useRef } from 'react'
import { VOCAB_CATEGORIES } from '../data/vocabulary'
import type { VocabEntry } from '../data/vocabulary'
import { useVocabulary } from '../store/vocabulary'
import type { VocabSearchResult, AddVocabRequest } from '../services/api'

// ─── Constants ────────────────────────────────────────────────────────────────

// Similarity above this is shown as a strong match; below = near-miss
const NEAR_MISS_THRESHOLD = 0.72

const AUTHORITY_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: 'Native', color: 'var(--amber)' },
  2: { label: 'Academic', color: '#7eb8c9' },
  3: { label: 'Community', color: 'var(--text-muted)' },
  4: { label: 'Inferred', color: 'var(--text-dim)' },
}

const POS_OPTIONS = ['verb', 'noun', 'adjective', 'adverb', 'phrase', 'particle', 'pronoun']
const SOURCE_OPTIONS = [
  { value: 'native_speaker', label: 'Native speaker' },
  { value: 'reference', label: 'Reference source' },
  { value: 'inferred', label: 'Inferred / unsure' },
]

// ─── Small shared pieces ───────────────────────────────────────────────────────

function AuthorityBadge({ level }: { level: number }) {
  const meta = AUTHORITY_LABELS[level] ?? AUTHORITY_LABELS[4]
  return (
    <span style={{
      fontSize: '0.64rem',
      fontWeight: 700,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
      color: meta.color,
      border: `1px solid ${meta.color}`,
      borderRadius: 3,
      padding: '0.1rem 0.35rem',
      opacity: 0.85,
      whiteSpace: 'nowrap',
      flexShrink: 0,
    }}>
      {meta.label}
    </span>
  )
}

function AspectForms({ forms, term }: { forms: Record<string, string>; term: string }) {
  const [open, setOpen] = useState(false)
  const aspects = Object.entries(forms).filter(([, v]) => v)
  if (aspects.length === 0) return null
  return (
    <div style={{ marginTop: '0.4rem' }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          fontSize: '0.7rem', color: 'var(--text-muted)',
          display: 'flex', alignItems: 'center', gap: '0.3rem', padding: 0,
        }}
      >
        <span style={{
          display: 'inline-block',
          transition: 'transform 0.2s',
          transform: open ? 'rotate(90deg)' : 'rotate(0deg)',
        }}>▶</span>
        Aspect forms
      </button>
      {open && (
        <div style={{
          marginTop: '0.35rem',
          paddingLeft: '0.75rem',
          borderLeft: '2px solid var(--border)',
          display: 'flex', flexDirection: 'column', gap: '0.2rem',
          animation: 'pageEnter 0.2s ease forwards',
        }}>
          {aspects.map(([aspect, form]) => (
            <div key={aspect} style={{ display: 'flex', gap: '0.5rem', fontSize: '0.78rem' }}>
              <span style={{ color: 'var(--text-dim)', width: 90, flexShrink: 0, textTransform: 'capitalize' }}>
                {aspect}
              </span>
              <span className="font-display" style={{ fontStyle: 'italic', color: 'var(--amber-light)', fontWeight: 500 }}>
                {form}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function VocabResultCard({ result, isNearMiss = false }: { result: VocabSearchResult; isNearMiss?: boolean }) {
  return (
    <div style={{
      padding: '0.85rem 1rem',
      borderBottom: '1px solid var(--border)',
      opacity: isNearMiss ? 0.8 : 1,
      animation: 'pageEnter 0.25s ease forwards',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.5rem' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span className="font-display" style={{
              fontStyle: 'italic', color: 'var(--amber)',
              fontSize: '1.15rem', fontWeight: 500, lineHeight: 1.2,
            }}>
              {result.term}
            </span>
            {result.part_of_speech && (
              <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                {result.part_of_speech}
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text)', marginTop: '0.2rem', lineHeight: 1.5 }}>
            {result.meaning}
          </p>
          {result.usage_notes && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem', fontStyle: 'italic' }}>
              {result.usage_notes}
            </p>
          )}
          {result.aspect_forms && Object.keys(result.aspect_forms).length > 0 && (
            <AspectForms forms={result.aspect_forms} term={result.term} />
          )}
          {result.examples && result.examples.length > 0 && (
            <div style={{ marginTop: '0.45rem', paddingLeft: '0.75rem', borderLeft: '2px solid var(--border)' }}>
              {result.examples.slice(0, 1).map((ex, i) => (
                <div key={i}>
                  <p className="font-display" style={{
                    fontStyle: 'italic', color: 'var(--amber-light)',
                    fontSize: '0.85rem', fontWeight: 500, margin: 0,
                  }}>
                    {ex.kapampangan}
                  </p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
                    {ex.english}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
        <AuthorityBadge level={result.authority_level} />
      </div>
    </div>
  )
}

// ─── Search Tab ───────────────────────────────────────────────────────────────

function SearchTab({ onAddRequest }: { onAddRequest: (term: string) => void }) {
  const [inputValue, setInputValue] = useState('')
  const { vocabularyResults, isSearching, lastQuery, searchError, searchVocabulary } = useVocabulary()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      if (inputValue.trim()) searchVocabulary(inputValue.trim())
    }, 300)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [inputValue, searchVocabulary])

  const strongMatches = vocabularyResults.filter((r) => r.similarity_score >= NEAR_MISS_THRESHOLD)
  const nearMisses = vocabularyResults.filter((r) => r.similarity_score < NEAR_MISS_THRESHOLD)
  const hasResults = vocabularyResults.length > 0
  const hasSearched = lastQuery.length > 0

  return (
    <div>
      {/* Search input */}
      <div style={{ padding: '0.75rem 1rem' }}>
        <div style={{ position: 'relative' }}>
          <input
            className="input"
            type="search"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Search Kapampangan or English…"
            style={{ fontSize: '0.9rem', paddingRight: '2.5rem' }}
            autoFocus
          />
          {isSearching && (
            <span style={{
              position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)',
              fontSize: '0.75rem', color: 'var(--text-dim)',
            }}>
              ◌
            </span>
          )}
        </div>
        <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.35rem' }}>
          Searches by meaning — try "how to say I'm hungry" or just "eat"
        </p>
      </div>

      {/* Error */}
      {searchError && (
        <div style={{ padding: '0.75rem 1rem', color: 'var(--terra-light)', fontSize: '0.8rem' }}>
          {searchError}
        </div>
      )}

      {/* Results */}
      {hasResults && (
        <div>
          {/* Strong matches */}
          {strongMatches.length > 0 && (
            <div>
              {strongMatches.map((r) => (
                <VocabResultCard key={r.id ?? r.term} result={r} />
              ))}
            </div>
          )}

          {/* Near-miss section */}
          {nearMisses.length > 0 && (
            <div>
              {strongMatches.length === 0 && (
                <div style={{
                  padding: '0.6rem 1rem',
                  fontSize: '0.78rem', color: 'var(--text-muted)',
                  borderBottom: '1px solid var(--border)',
                }}>
                  No exact match for <em style={{ color: 'var(--amber-dim)' }}>"{lastQuery}"</em>
                </div>
              )}
              <div style={{
                padding: '0.4rem 1rem 0.2rem',
                fontSize: '0.68rem', fontWeight: 700,
                letterSpacing: '0.1em', textTransform: 'uppercase',
                color: 'var(--text-dim)',
              }}>
                Related entries
              </div>
              {nearMisses.map((r) => (
                <VocabResultCard key={r.id ?? r.term} result={r} isNearMiss />
              ))}
            </div>
          )}

          {/* Add button when no strong matches */}
          {strongMatches.length === 0 && (
            <div style={{ padding: '0.75rem 1rem' }}>
              <button
                className="btn-ghost"
                onClick={() => onAddRequest(lastQuery)}
                style={{ fontSize: '0.8rem', width: '100%', justifyContent: 'center' }}
              >
                + Add "{lastQuery}" to vocabulary
              </button>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!hasResults && !isSearching && !hasSearched && (
        <div style={{ padding: '2.5rem 1.5rem', textAlign: 'center' }}>
          <div className="font-display" style={{
            fontSize: '2.5rem', fontStyle: 'italic', color: 'var(--border-light)',
            lineHeight: 1.2, marginBottom: '0.5rem',
          }}>
            Nanu ya?
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
            What are you looking for?
          </p>
        </div>
      )}

      {!hasResults && !isSearching && hasSearched && (
        <div style={{ padding: '1.5rem 1rem', textAlign: 'center' }}>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            Nothing found for "{lastQuery}"
          </p>
          <button
            className="btn-ghost"
            onClick={() => onAddRequest(lastQuery)}
            style={{ fontSize: '0.8rem' }}
          >
            + Add it to vocabulary
          </button>
        </div>
      )}
    </div>
  )
}

// ─── Add Entry Tab ────────────────────────────────────────────────────────────

function AddEntryTab({ prefillTerm = '' }: { prefillTerm?: string }) {
  const { isAdding, addedEntry, addError, addVocabularyEntry, clearAddedEntry } = useVocabulary()

  const [term, setTerm] = useState(prefillTerm)
  const [meaning, setMeaning] = useState('')
  const [pos, setPos] = useState('')
  const [progressive, setProgressive] = useState('')
  const [completed, setCompleted] = useState('')
  const [contemplated, setContemplated] = useState('')
  const [exampleKap, setExampleKap] = useState('')
  const [exampleEn, setExampleEn] = useState('')
  const [usageNotes, setUsageNotes] = useState('')
  const [source, setSource] = useState('inferred')

  useEffect(() => {
    setTerm(prefillTerm)
  }, [prefillTerm])

  const isVerb = pos === 'verb'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!term.trim() || !meaning.trim()) return

    const entry: AddVocabRequest = {
      term: term.trim(),
      meaning: meaning.trim(),
      part_of_speech: pos || undefined,
      usage_notes: usageNotes.trim() || undefined,
      source,
      authority_level: source === 'native_speaker' ? 1 : source === 'reference' ? 2 : 3,
    }

    if (isVerb && (progressive || completed || contemplated)) {
      entry.aspect_forms = {}
      if (progressive) entry.aspect_forms.progressive = progressive.trim()
      if (completed) entry.aspect_forms.completed = completed.trim()
      if (contemplated) entry.aspect_forms.contemplated = contemplated.trim()
    }

    if (exampleKap.trim()) {
      entry.examples = [{ kapampangan: exampleKap.trim(), english: exampleEn.trim() }]
    }

    await addVocabularyEntry(entry)
  }

  if (addedEntry) {
    return (
      <div style={{
        padding: '2rem 1rem', textAlign: 'center',
        animation: 'pageEnter 0.3s ease forwards',
      }}>
        <div style={{ fontSize: '1.5rem', marginBottom: '0.75rem' }}>✓</div>
        <p className="font-display" style={{
          fontSize: '1.4rem', fontStyle: 'italic', color: 'var(--amber)',
          marginBottom: '0.25rem',
        }}>
          {addedEntry.term}
        </p>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          {addedEntry.meaning}
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '1.25rem' }}>
          Entry added and immediately searchable.
        </p>
        <button className="btn-ghost" onClick={clearAddedEntry} style={{ fontSize: '0.8rem' }}>
          Add another
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} style={{ padding: '0 1rem 2rem' }}>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', padding: '0.75rem 0 1rem' }}>
        Entries are embedded immediately and searchable without a restart.
      </p>

      {/* Term + Meaning */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <div>
          <label style={labelStyle}>Kapampangan term *</label>
          <input
            className="input"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="e.g. mangan"
            required
            style={{ fontFamily: "'Cormorant Garamond', Georgia, serif", fontStyle: 'italic', fontSize: '1rem' }}
          />
        </div>
        <div>
          <label style={labelStyle}>English meaning *</label>
          <input
            className="input"
            value={meaning}
            onChange={(e) => setMeaning(e.target.value)}
            placeholder="e.g. to eat"
            required
          />
        </div>
      </div>

      {/* Part of speech */}
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={labelStyle}>Part of speech</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {POS_OPTIONS.map((p) => (
            <button
              key={p}
              type="button"
              className={`tab-pill${pos === p ? ' active' : ''}`}
              onClick={() => setPos(pos === p ? '' : p)}
              style={{ fontSize: '0.75rem' }}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Aspect forms — verb only */}
      {isVerb && (
        <div style={{
          marginBottom: '0.75rem', padding: '0.75rem',
          background: 'var(--bg-2)', borderRadius: 8, border: '1px solid var(--border)',
          animation: 'pageEnter 0.2s ease forwards',
        }}>
          <label style={{ ...labelStyle, marginBottom: '0.6rem', display: 'block' }}>Aspect forms</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
            {[
              { label: 'Progressive', val: progressive, set: setProgressive },
              { label: 'Completed', val: completed, set: setCompleted },
              { label: 'Contemplated', val: contemplated, set: setContemplated },
            ].map(({ label, val, set }) => (
              <div key={label}>
                <label style={{ ...labelStyle, fontSize: '0.65rem' }}>{label}</label>
                <input
                  className="input"
                  value={val}
                  onChange={(e) => set(e.target.value)}
                  placeholder="—"
                  style={{ fontFamily: "'Cormorant Garamond', Georgia, serif", fontStyle: 'italic', fontSize: '0.9rem' }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Example sentence */}
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={labelStyle}>Example sentence</label>
        <input
          className="input"
          value={exampleKap}
          onChange={(e) => setExampleKap(e.target.value)}
          placeholder="Kapampangan sentence…"
          style={{ marginBottom: '0.4rem', fontFamily: "'Cormorant Garamond', Georgia, serif", fontStyle: 'italic', fontSize: '0.95rem' }}
        />
        <input
          className="input"
          value={exampleEn}
          onChange={(e) => setExampleEn(e.target.value)}
          placeholder="English translation…"
        />
      </div>

      {/* Usage notes */}
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={labelStyle}>Usage notes / cultural context</label>
        <textarea
          className="input"
          value={usageNotes}
          onChange={(e) => setUsageNotes(e.target.value)}
          placeholder="Any context or notes on usage…"
          rows={2}
          style={{ resize: 'vertical', fontSize: '0.85rem' }}
        />
      </div>

      {/* Source */}
      <div style={{ marginBottom: '1.25rem' }}>
        <label style={labelStyle}>Source</label>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {SOURCE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`tab-pill${source === opt.value ? ' active' : ''}`}
              onClick={() => setSource(opt.value)}
              style={{ fontSize: '0.75rem' }}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {source === 'native_speaker' && (
          <p style={{ fontSize: '0.7rem', color: 'var(--amber)', marginTop: '0.35rem' }}>
            Native speaker entries are saved at authority level 1.
          </p>
        )}
      </div>

      {addError && (
        <p style={{ fontSize: '0.8rem', color: 'var(--terra-light)', marginBottom: '0.75rem' }}>
          {addError}
        </p>
      )}

      <button
        type="submit"
        className="btn-amber"
        disabled={isAdding || !term.trim() || !meaning.trim()}
        style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}
      >
        {isAdding ? 'Saving…' : 'Add to vocabulary'}
      </button>
    </form>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.7rem',
  fontWeight: 700,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  color: 'var(--text-dim)',
  marginBottom: '0.3rem',
}

// ─── Flashcard Drill ──────────────────────────────────────────────────────────

function FlashcardDrill({ entries, onExit }: { entries: VocabEntry[]; onExit: () => void }) {
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [known, setKnown] = useState<number[]>([])
  const [unknown, setUnknown] = useState<number[]>([])

  const current = entries[index]
  const isDone = index >= entries.length

  if (isDone) {
    return (
      <div style={{
        height: '100%', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', padding: '2rem',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🏮</div>
        <h2 className="font-display" style={{ fontSize: '1.6rem', color: 'var(--amber)', marginBottom: '0.5rem' }}>
          Dakal a salamat!
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          {known.length} known · {unknown.length} to review
        </p>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn-amber" onClick={() => { setIndex(0); setFlipped(false); setKnown([]); setUnknown([]) }}>
            Drill again
          </button>
          <button className="btn-ghost" onClick={onExit}>Back to list</button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '1rem', gap: '1rem' }}>
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
          <span>{index + 1} / {entries.length}</span>
          <button onClick={onExit} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.75rem' }}>
            Exit ✕
          </button>
        </div>
        <div style={{ height: 3, background: 'var(--bg-3)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ height: '100%', borderRadius: 2, background: 'var(--amber)', width: `${(index / entries.length) * 100}%`, transition: 'width 0.3s ease' }} />
        </div>
      </div>

      <div className="flashcard-scene" style={{ width: '100%', maxWidth: 400, height: 220, cursor: 'pointer', flex: '0 0 220px' }} onClick={() => setFlipped((f) => !f)}>
        <div className={`flashcard-inner${flipped ? ' flipped' : ''}`}>
          <div className="flashcard-face" style={{ background: 'var(--bg-2)', border: '1px solid var(--border-light)', flexDirection: 'column', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>Kapampangan</span>
            <span className="font-display" style={{ fontSize: 'clamp(1.3rem,5vw,1.8rem)', color: 'var(--amber)', fontStyle: 'italic', textAlign: 'center', padding: '0 1rem', lineHeight: 1.3 }}>{current.kap}</span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>tap to flip</span>
          </div>
          <div className="flashcard-face flashcard-back" style={{ background: 'var(--bg-3)', border: '1px solid var(--amber-dim)', flexDirection: 'column', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>English</span>
            <span style={{ fontSize: 'clamp(1rem,4vw,1.4rem)', color: 'var(--text)', textAlign: 'center', padding: '0 1rem', lineHeight: 1.4, fontWeight: 500 }}>{current.en}</span>
            {current.note && <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center', padding: '0 1rem' }}>{current.note}</span>}
          </div>
        </div>
      </div>

      {flipped && (
        <div style={{ display: 'flex', gap: '0.75rem', animation: 'pageEnter 0.2s ease forwards' }}>
          <button className="btn-ghost" onClick={() => { setUnknown((u) => [...u, index]); setFlipped(false); setIndex((i) => i + 1) }}
            style={{ flex: 1, justifyContent: 'center', borderColor: 'var(--terra)', color: 'var(--terra-light)' }}>
            Not yet
          </button>
          <button className="btn-amber" onClick={() => { setKnown((k) => [...k, index]); setFlipped(false); setIndex((i) => i + 1) }}
            style={{ flex: 1, justifyContent: 'center' }}>
            Got it ✓
          </button>
        </div>
      )}
    </div>
  )
}

function DrillTab() {
  const [activeCategory, setActiveCategory] = useState(VOCAB_CATEGORIES[0].id)
  const [drillMode, setDrillMode] = useState(false)

  const category = VOCAB_CATEGORIES.find((c) => c.id === activeCategory)!

  if (drillMode) {
    return <FlashcardDrill entries={category.entries} onExit={() => setDrillMode(false)} />
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: '0.4rem', overflowX: 'auto', padding: '0.75rem 1rem', scrollbarWidth: 'none' }}>
        {VOCAB_CATEGORIES.map((cat) => (
          <button key={cat.id} className={`tab-pill${activeCategory === cat.id ? ' active' : ''}`} onClick={() => setActiveCategory(cat.id)}>
            {cat.label}
          </button>
        ))}
      </div>
      <div style={{ padding: '0 1rem 0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          {category.entries.length} entries in {category.label}
        </span>
        <button className="btn-amber" onClick={() => setDrillMode(true)} style={{ fontSize: '0.78rem', padding: '0.4rem 0.9rem' }}>
          Drill ◈
        </button>
      </div>
      <div style={{ margin: '0 1rem 2rem', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
        <table className="vocab-table">
          <thead><tr><th style={{ width: '50%' }}>Kapampangan</th><th>English</th></tr></thead>
          <tbody>
            {category.entries.map((entry, i) => (
              <tr key={i}>
                <td><span className="font-display" style={{ fontStyle: 'italic', color: 'var(--amber)', fontSize: '0.95rem', fontWeight: 500 }}>{entry.kap}</span></td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  {entry.en}
                  {entry.note && <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.1rem' }}>{entry.note}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

type Tab = 'search' | 'add' | 'drill'

export default function Vocabulary() {
  const [activeTab, setActiveTab] = useState<Tab>('search')
  const [addPrefill, setAddPrefill] = useState('')

  const handleAddRequest = (term: string) => {
    setAddPrefill(term)
    setActiveTab('add')
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: 'search', label: 'Search' },
    { id: 'add', label: '+ Add' },
    { id: 'drill', label: 'Drill ◈' },
  ]

  return (
    <div className="page page-enter" style={{ overflowY: 'auto' }}>
      <div style={{ maxWidth: 680, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ padding: '1.25rem 1rem 0.5rem' }}>
          <h1 className="section-heading">Vocabulary</h1>
        </div>

        {/* Tab bar */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0 1rem' }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                padding: '0.6rem 0.9rem',
                fontSize: '0.82rem', fontWeight: 600,
                color: activeTab === tab.id ? 'var(--amber)' : 'var(--text-dim)',
                borderBottom: activeTab === tab.id ? '2px solid var(--amber)' : '2px solid transparent',
                marginBottom: -1,
                transition: 'color 0.15s',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div key={activeTab} style={{ animation: 'pageEnter 0.2s ease forwards' }}>
          {activeTab === 'search' && <SearchTab onAddRequest={handleAddRequest} />}
          {activeTab === 'add' && <AddEntryTab prefillTerm={addPrefill} />}
          {activeTab === 'drill' && <DrillTab />}
        </div>
      </div>
    </div>
  )
}
