import { sidebarPanels } from '../config/ui'

interface Props {
  activePanel?: string | null
  onPanelChange?: (panel: string) => void
  grammarContent?: string | null
  vocabularyContent?: string | null
}

const PANEL_LABELS: Record<string, string> = {
  grammar_notes: 'Grammar',
  vocabulary_cards: 'Vocabulary',
}

export default function SidePanel({ activePanel, onPanelChange, grammarContent, vocabularyContent }: Props) {
  const currentPanel = activePanel ?? sidebarPanels[0]

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      borderLeft: '1px solid var(--border)',
      background: 'var(--bg-1)',
    }}>
      {/* Panel tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
      }}>
        {sidebarPanels.map((panel) => {
          const isActive = panel === currentPanel
          return (
            <button
              key={panel}
              onClick={() => onPanelChange?.(panel)}
              style={{
                flex: 1,
                padding: '0.6rem 0.5rem',
                border: 'none',
                borderBottom: `2px solid ${isActive ? 'var(--amber)' : 'transparent'}`,
                background: 'transparent',
                color: isActive ? 'var(--amber)' : 'var(--text-dim)',
                fontSize: '0.72rem',
                fontWeight: isActive ? 600 : 400,
                cursor: 'pointer',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                transition: 'all 0.15s ease',
              }}
            >
              {PANEL_LABELS[panel] ?? panel}
            </button>
          )
        })}
      </div>

      {/* Panel content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
        {currentPanel === 'grammar_notes' && (
          grammarContent ? (
            <div style={{ fontSize: '0.82rem', color: 'var(--text)', lineHeight: 1.7 }}>
              {grammarContent}
            </div>
          ) : (
            <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
              Grammar notes will appear here as you chat with Ading.
            </p>
          )
        )}

        {currentPanel === 'vocabulary_cards' && (
          vocabularyContent ? (
            <div style={{ fontSize: '0.82rem', color: 'var(--text)', lineHeight: 1.7 }}>
              {vocabularyContent}
            </div>
          ) : (
            <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
              Vocabulary encountered in your conversation will appear here.
            </p>
          )
        )}
      </div>
    </div>
  )
}
