import { scenarios } from '../config/ui'
import type { Scenario } from '../config/ui'

interface Props {
  activeId: string | null
  onSelect: (scenario: Scenario) => void
}

export default function ScenarioSelector({ activeId, onSelect }: Props) {
  return (
    <div style={{
      display: 'flex',
      gap: '0.5rem',
      flexWrap: 'wrap',
      padding: '0.75rem 1rem',
      borderBottom: '1px solid var(--border)',
    }}>
      {scenarios.map((scenario) => {
        const isActive = scenario.id === activeId
        return (
          <button
            key={scenario.id}
            onClick={() => onSelect(scenario)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.3rem 0.7rem',
              borderRadius: 20,
              border: `1px solid ${isActive ? 'var(--amber)' : 'var(--border)'}`,
              background: isActive ? 'rgba(245,166,35,0.12)' : 'transparent',
              color: isActive ? 'var(--amber)' : 'var(--text-dim)',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              fontWeight: isActive ? 600 : 400,
            }}
          >
            <span>{scenario.icon}</span>
            <span>{scenario.label}</span>
          </button>
        )
      })}
    </div>
  )
}
