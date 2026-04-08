import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GRAMMAR_SECTIONS } from '../data/grammar'
import type { GrammarSection } from '../data/grammar'

function GrammarCard({ section }: { section: GrammarSection }) {
  const [expanded, setExpanded] = useState(false)
  const navigate = useNavigate()

  const handleAskAding = () => {
    // Store the prompt and navigate to chat
    sessionStorage.setItem('ading-prefill', section.examplePrompt)
    navigate('/chat')
  }

  return (
    <div
      className="card"
      style={{ overflow: 'hidden', transition: 'all 0.2s ease' }}
    >
      {/* Card header — always visible */}
      <button
        onClick={() => setExpanded((v) => !v)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.9rem 1rem',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          gap: '0.75rem',
        }}
      >
        <div style={{ flex: 1 }}>
          <div className="font-display" style={{
            fontSize: '1.1rem', fontWeight: 600, color: 'var(--text)',
            lineHeight: 1.2, marginBottom: '0.15rem',
          }}>
            {section.title}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {section.subtitle}
          </div>
        </div>
        <div style={{
          color: 'var(--amber-dim)',
          fontSize: '0.75rem',
          flexShrink: 0,
          transform: expanded ? 'rotate(180deg)' : 'none',
          transition: 'transform 0.2s ease',
        }}>
          ▾
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div style={{ padding: '0 1rem 1rem', animation: 'pageEnter 0.22s ease forwards' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.65, marginBottom: '0.85rem' }}>
            {section.summary}
          </p>

          {/* Rules */}
          {section.rules && section.rules.length > 0 && (
            <div style={{ marginBottom: '0.85rem' }}>
              {section.rules.map((rule, i) => (
                <div key={i} style={{
                  display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
                  marginBottom: '0.35rem',
                }}>
                  <span style={{ color: 'var(--amber-dim)', flexShrink: 0, marginTop: '0.05em', fontSize: '0.8rem' }}>
                    {rule.startsWith('✅') || rule.startsWith('❌') || rule.startsWith('⚠️') ? '' : '·'}
                  </span>
                  <span style={{
                    fontSize: '0.82rem',
                    color: rule.startsWith('❌') ? 'var(--terra-light)' :
                           rule.startsWith('✅') ? '#3d8a65' :
                           rule.startsWith('⚠️') ? 'var(--amber-light)' : 'var(--text-muted)',
                    lineHeight: 1.5,
                    fontFamily: rule.includes('→') || rule.match(/[a-z]\./) ? '"Cormorant Garamond", serif' : 'inherit',
                    fontStyle: rule.includes('→') || rule.match(/[A-Z][a-z]+ [a-z]/) ? 'italic' : 'normal',
                  }}>
                    {rule}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Table */}
          {section.table && (
            <div style={{ overflowX: 'auto', marginBottom: '0.85rem', borderRadius: 8, border: '1px solid var(--border)' }}>
              <table className="vocab-table" style={{ fontSize: '0.78rem' }}>
                <thead>
                  <tr>
                    {section.table.headers.map((h) => (
                      <th key={h} style={{ whiteSpace: 'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {section.table.rows.map((row, i) => (
                    <tr key={i}>
                      {row.map((cell, j) => (
                        <td key={j} style={{
                          color: j === 0 ? 'var(--text)' : j === 2 ? 'var(--amber)' : 'var(--text-muted)',
                          fontFamily: j === 2 || (j === 3 && cell.includes('('))
                            ? '"Cormorant Garamond", serif'
                            : 'inherit',
                          fontStyle: j === 2 ? 'italic' : 'normal',
                          fontWeight: j === 0 ? 500 : 400,
                          whiteSpace: j === 2 ? 'nowrap' : 'normal',
                        }}>
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Ask Ading */}
          <button
            className="btn-ghost"
            onClick={handleAskAding}
            style={{ width: '100%', justifyContent: 'center', gap: '0.5rem' }}
          >
            <span style={{ color: 'var(--amber)', fontSize: '0.85rem' }}>◎</span>
            Show me an example with Ading
          </button>
        </div>
      )}
    </div>
  )
}

export default function Grammar() {
  return (
    <div className="page page-enter" style={{ overflowY: 'auto' }}>
      <div className="page-padded">
        <div style={{ marginBottom: '1.25rem' }}>
          <h1 className="section-heading" style={{ marginBottom: '0.25rem' }}>Grammar Explorer</h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Tap any section to expand. Ask Ading for live examples.
          </p>
        </div>

        <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {GRAMMAR_SECTIONS.map((section) => (
            <GrammarCard key={section.id} section={section} />
          ))}
        </div>

        {/* Footer note */}
        <div style={{
          marginTop: '1.5rem', padding: '0.75rem 1rem',
          background: 'var(--bg-2)', borderRadius: 10,
          border: '1px solid var(--border)',
        }}>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.6, margin: 0 }}>
            <span style={{ color: 'var(--amber-light)', fontWeight: 600 }}>Note on Tagalog: </span>
            Kapampangan verb aspects look similar to Tagalog but mean the opposite.{' '}
            <em className="kap">Susulat</em> = "is writing" in Kapampangan, but "will write" in Tagalog.
            Always verify with Ading if unsure.
          </p>
        </div>
      </div>
    </div>
  )
}
