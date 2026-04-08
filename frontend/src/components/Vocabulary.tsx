import { useState } from 'react'
import { VOCAB_CATEGORIES } from '../data/vocabulary'
import type { VocabEntry } from '../data/vocabulary'

// ─── Flashcard Drill ─────────────────────────────────────────────────────────

function FlashcardDrill({ entries, onExit }: { entries: VocabEntry[]; onExit: () => void }) {
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [known, setKnown] = useState<number[]>([])
  const [unknown, setUnknown] = useState<number[]>([])

  const current = entries[index]
  const remaining = entries.length - index
  const isDone = index >= entries.length

  const handleFlip = () => setFlipped((f) => !f)

  const handleKnow = () => {
    setKnown((k) => [...k, index])
    setFlipped(false)
    setIndex((i) => i + 1)
  }

  const handleDontKnow = () => {
    setUnknown((u) => [...u, index])
    setFlipped(false)
    setIndex((i) => i + 1)
  }

  if (isDone) {
    return (
      <div style={{
        height: '100%', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', padding: '2rem',
        textAlign: 'center', animation: 'pageEnter 0.3s ease forwards',
      }}>
        <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🏮</div>
        <h2 className="font-display" style={{ fontSize: '1.6rem', color: 'var(--amber)', marginBottom: '0.5rem' }}>
          Dakal a salamat!
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          You finished the set — {known.length} known, {unknown.length} to review.
        </p>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            className="btn-amber"
            onClick={() => { setIndex(0); setFlipped(false); setKnown([]); setUnknown([]) }}
          >
            Drill again
          </button>
          <button className="btn-ghost" onClick={onExit}>Back to list</button>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', padding: '1rem', gap: '1rem',
    }}>
      {/* Progress */}
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem',
        }}>
          <span>{index + 1} / {entries.length}</span>
          <button
            onClick={onExit}
            style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.75rem' }}
          >
            Exit drill ✕
          </button>
        </div>
        <div style={{ height: 3, background: 'var(--bg-3)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            height: '100%', borderRadius: 2,
            background: 'var(--amber)',
            width: `${((index) / entries.length) * 100}%`,
            transition: 'width 0.3s ease',
          }} />
        </div>
      </div>

      {/* Card */}
      <div
        className="flashcard-scene"
        style={{ width: '100%', maxWidth: 400, height: 220, cursor: 'pointer', flex: '0 0 220px' }}
        onClick={handleFlip}
      >
        <div className={`flashcard-inner${flipped ? ' flipped' : ''}`}>
          {/* Front — Kapampangan */}
          <div
            className="flashcard-face"
            style={{ background: 'var(--bg-2)', border: '1px solid var(--border-light)', flexDirection: 'column', gap: '0.75rem' }}
          >
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>
              Kapampangan
            </span>
            <span className="font-display" style={{ fontSize: 'clamp(1.3rem, 5vw, 1.8rem)', color: 'var(--amber)', fontStyle: 'italic', textAlign: 'center', padding: '0 1rem', lineHeight: 1.3 }}>
              {current.kap}
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>tap to flip</span>
          </div>
          {/* Back — English */}
          <div
            className="flashcard-face flashcard-back"
            style={{ background: 'var(--bg-3)', border: '1px solid var(--amber-dim)', flexDirection: 'column', gap: '0.75rem' }}
          >
            <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>
              English
            </span>
            <span style={{ fontSize: 'clamp(1rem, 4vw, 1.4rem)', color: 'var(--text)', textAlign: 'center', padding: '0 1rem', lineHeight: 1.4, fontWeight: 500 }}>
              {current.en}
            </span>
            {current.note && (
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center', padding: '0 1rem' }}>
                {current.note}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Hint */}
      {!flipped && (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', margin: 0 }}>
          Do you know this one?
        </p>
      )}

      {/* Response buttons */}
      {flipped && (
        <div style={{ display: 'flex', gap: '0.75rem', animation: 'pageEnter 0.2s ease forwards' }}>
          <button
            className="btn-ghost"
            onClick={handleDontKnow}
            style={{ flex: 1, justifyContent: 'center', borderColor: 'var(--terra)', color: 'var(--terra-light)' }}
          >
            Not yet
          </button>
          <button
            className="btn-amber"
            onClick={handleKnow}
            style={{ flex: 1, justifyContent: 'center' }}
          >
            Got it ✓
          </button>
        </div>
      )}

      {/* Remaining */}
      <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: 'auto' }}>
        {remaining - 1} card{remaining - 1 !== 1 ? 's' : ''} remaining
      </p>
    </div>
  )
}

// ─── Main Vocabulary Page ─────────────────────────────────────────────────────

export default function Vocabulary() {
  const [activeCategory, setActiveCategory] = useState(VOCAB_CATEGORIES[0].id)
  const [search, setSearch] = useState('')
  const [drillMode, setDrillMode] = useState(false)

  const category = VOCAB_CATEGORIES.find((c) => c.id === activeCategory)!

  const filteredEntries = search.trim()
    ? category.entries.filter(
        (e) =>
          e.kap.toLowerCase().includes(search.toLowerCase()) ||
          e.en.toLowerCase().includes(search.toLowerCase())
      )
    : category.entries

  if (drillMode) {
    return (
      <div className="page page-enter" style={{ display: 'flex', flexDirection: 'column' }}>
        <FlashcardDrill entries={filteredEntries} onExit={() => setDrillMode(false)} />
      </div>
    )
  }

  return (
    <div className="page page-enter" style={{ overflowY: 'auto' }}>
      <div style={{ maxWidth: 680, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ padding: '1.25rem 1rem 0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
            <h1 className="section-heading">Vocabulary</h1>
            <button
              className="btn-amber"
              onClick={() => setDrillMode(true)}
              style={{ fontSize: '0.78rem', padding: '0.4rem 0.9rem' }}
            >
              Drill ◈
            </button>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {filteredEntries.length} entries in {category.label}
          </p>
        </div>

        {/* Category tabs */}
        <div style={{
          display: 'flex', gap: '0.4rem', overflowX: 'auto',
          padding: '0 1rem 0.75rem', scrollbarWidth: 'none',
        }}>
          {VOCAB_CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              className={`tab-pill${activeCategory === cat.id ? ' active' : ''}`}
              onClick={() => { setActiveCategory(cat.id); setSearch('') }}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div style={{ padding: '0 1rem 0.75rem' }}>
          <input
            className="input"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${category.label.toLowerCase()}…`}
            style={{ fontSize: '0.85rem' }}
          />
        </div>

        {/* Table */}
        <div style={{ margin: '0 1rem 2rem', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden' }}>
          <table className="vocab-table">
            <thead>
              <tr>
                <th style={{ width: '50%' }}>Kapampangan</th>
                <th>English</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.length > 0 ? filteredEntries.map((entry, i) => (
                <tr key={i}>
                  <td>
                    <span className="font-display" style={{
                      fontStyle: 'italic', color: 'var(--amber)',
                      fontSize: '0.95rem', fontWeight: 500,
                    }}>
                      {entry.kap}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    {entry.en}
                    {entry.note && (
                      <span style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.1rem' }}>
                        {entry.note}
                      </span>
                    )}
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={2} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '1.5rem' }}>
                    No entries match "{search}"
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
