import { useNavigate } from 'react-router-dom'

// 8-pointed star (parol) — computed coordinates
// Center (100,100), outer R=80, inner r=34
const PAROL_POINTS = '100,20 113,68.6 156.6,43.4 131.4,87 180,100 131.4,113 156.6,156.6 113,131.4 100,180 87,131.4 43.4,156.6 68.6,113 20,100 68.6,87 43.4,43.4 87,68.6'

function ParolSVG() {
  return (
    <svg
      viewBox="0 0 200 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="parol-sway"
      style={{ width: '100%', height: '100%' }}
      aria-hidden
    >
      <defs>
        <radialGradient id="pg" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#f5a623" stopOpacity="0.18" />
          <stop offset="70%" stopColor="#f5a623" stopOpacity="0.04" />
          <stop offset="100%" stopColor="#f5a623" stopOpacity="0" />
        </radialGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <filter id="softglow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>

      {/* Ambient glow */}
      <circle cx="100" cy="100" r="85" fill="url(#pg)" />

      {/* Outer ring */}
      <circle cx="100" cy="100" r="88" stroke="#f5a623" strokeWidth="0.4" opacity="0.15" />
      <circle cx="100" cy="100" r="72" stroke="#f5a623" strokeWidth="0.4" opacity="0.12" />

      {/* 8-pointed star */}
      <polygon
        points={PAROL_POINTS}
        stroke="#f5a623"
        strokeWidth="1.2"
        fill="rgba(245,166,35,0.04)"
        filter="url(#glow)"
      />

      {/* Inner octagon */}
      <polygon
        points="100,45 126,55 140,81 130,107 100,120 70,107 60,81 74,55"
        stroke="#f5a623"
        strokeWidth="0.7"
        fill="none"
        opacity="0.35"
      />

      {/* Center circle */}
      <circle cx="100" cy="100" r="18" stroke="#f5a623" strokeWidth="0.9" fill="rgba(245,166,35,0.07)" filter="url(#glow)" />
      <circle cx="100" cy="100" r="5" fill="#f5a623" opacity="0.5" filter="url(#softglow)" />

      {/* Radiating spokes */}
      {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
        const rad = (deg * Math.PI) / 180
        return (
          <line
            key={deg}
            x1={100 + 18 * Math.cos(rad)}
            y1={100 + 18 * Math.sin(rad)}
            x2={100 + 68 * Math.cos(rad)}
            y2={100 + 68 * Math.sin(rad)}
            stroke="#f5a623"
            strokeWidth="0.5"
            opacity="0.18"
          />
        )
      })}

      {/* Diagonal spokes (between main spokes) */}
      {[22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5].map((deg) => {
        const rad = (deg * Math.PI) / 180
        return (
          <line
            key={deg}
            x1={100 + 18 * Math.cos(rad)}
            y1={100 + 18 * Math.sin(rad)}
            x2={100 + 50 * Math.cos(rad)}
            y2={100 + 50 * Math.sin(rad)}
            stroke="#f5a623"
            strokeWidth="0.35"
            opacity="0.12"
          />
        )
      })}

      {/* Star tip dots */}
      {['100,20', '156.6,43.4', '180,100', '156.6,156.6', '100,180', '43.4,156.6', '20,100', '43.4,43.4'].map((pt, i) => {
        const [x, y] = pt.split(',').map(Number)
        return <circle key={i} cx={x} cy={y} r="2.5" fill="#f5a623" opacity="0.55" filter="url(#glow)" />
      })}

      {/* Hanging tassels (parol detail) */}
      <line x1="92" y1="180" x2="85" y2="196" stroke="#f5a623" strokeWidth="0.7" opacity="0.4" />
      <line x1="100" y1="180" x2="100" y2="196" stroke="#f5a623" strokeWidth="0.7" opacity="0.4" />
      <line x1="108" y1="180" x2="115" y2="196" stroke="#f5a623" strokeWidth="0.7" opacity="0.4" />
      <circle cx="85" cy="197" r="2" fill="#f5a623" opacity="0.4" />
      <circle cx="100" cy="197" r="2" fill="#f5a623" opacity="0.4" />
      <circle cx="115" cy="197" r="2" fill="#f5a623" opacity="0.4" />
    </svg>
  )
}

const QUICK_ACTIONS = [
  {
    to: '/chat',
    icon: '◎',
    title: 'Talk with Ading',
    desc: 'Open conversation — ask anything about Kapampangan.',
    accent: 'var(--amber)',
  },
  {
    to: '/translate',
    icon: '⇄',
    title: 'Translate',
    desc: 'English ↔ Kapampangan with usage notes.',
    accent: 'var(--terra-light)',
  },
  {
    to: '/grammar',
    icon: '∂',
    title: 'Grammar Explorer',
    desc: 'Verb focus, aspects, pronouns, particles & more.',
    accent: 'var(--forest-light, #3d8a65)',
  },
  {
    to: '/vocabulary',
    icon: '◈',
    title: 'Vocabulary & Drill',
    desc: 'Browse all categories. Drill with flashcards.',
    accent: 'var(--amber-light)',
  },
  {
    to: '/chat',
    icon: '✦',
    title: 'Check My Kapampangan',
    desc: 'Paste a sentence for Ading\'s gentle correction.',
    accent: 'var(--terra)',
    state: { mode: 'correction' },
  },
  {
    to: '/chat',
    icon: '⬡',
    title: 'Scenario Practice',
    desc: 'Family dinner, market, office — roleplay with Ading.',
    accent: '#9b6a9b',
    state: { mode: 'scenario' },
  },
  {
    to: '/compare',
    icon: '⇌',
    title: 'Compare LLMs',
    desc: 'Claude vs local model — same question, side by side.',
    accent: '#6a8fc1',
  },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="page parol-bg page-enter" style={{ overflowY: 'auto' }}>
      {/* Hero */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '2rem 1.25rem 1rem',
        textAlign: 'center',
        position: 'relative',
      }}>
        {/* Parol */}
        <div style={{ width: 160, height: 160, marginBottom: '-0.5rem', position: 'relative' }}>
          <ParolSVG />
        </div>

        {/* Wordmark */}
        <h1 className="font-display" style={{
          fontSize: 'clamp(2.2rem, 8vw, 3.2rem)',
          fontWeight: 700,
          color: 'var(--text)',
          letterSpacing: '-0.01em',
          lineHeight: 1,
          marginBottom: '0.4rem',
        }}>
          Kapilator
        </h1>

        {/* Kapampangan greeting */}
        <p className="font-display" style={{
          fontSize: 'clamp(1.05rem, 4vw, 1.3rem)',
          fontStyle: 'italic',
          color: 'var(--amber)',
          fontWeight: 500,
          marginBottom: '0.5rem',
          textShadow: '0 0 24px rgba(245,166,35,0.3)',
        }}>
          Mayap a abak — learn Kapampangan with Ading
        </p>

        <p style={{
          fontSize: '0.82rem',
          color: 'var(--text-muted)',
          maxWidth: 300,
          lineHeight: 1.6,
        }}>
          The language of Pampanga, Philippines —<br />warm, patient, and always encouraging.
        </p>
      </div>

      {/* Quick Actions */}
      <div style={{ padding: '0.75rem 1rem 1.5rem', maxWidth: 680, margin: '0 auto' }}>
        <p style={{
          fontSize: '0.7rem',
          color: 'var(--text-dim)',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          fontWeight: 600,
          marginBottom: '0.75rem',
          paddingLeft: '0.25rem',
        }}>
          Where would you like to start?
        </p>

        <div className="stagger" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '0.65rem',
        }}>
          {QUICK_ACTIONS.map((action, idx) => (
            <button
              key={action.title}
              className="card-interactive"
              onClick={() => navigate(action.to, { state: action.state })}
              style={{
                padding: '0.9rem',
                textAlign: 'left',
                background: 'var(--bg-2)',
                cursor: 'pointer',
                border: '1px solid var(--border)',
                gridColumn: idx === QUICK_ACTIONS.length - 1 && QUICK_ACTIONS.length % 2 !== 0 ? 'span 2' : undefined,
              }}
            >
              <div style={{
                fontSize: '1.2rem',
                color: action.accent,
                marginBottom: '0.35rem',
                lineHeight: 1,
              }}>
                {action.icon}
              </div>
              <div style={{
                fontFamily: '"Cormorant Garamond", serif',
                fontSize: '1rem',
                fontWeight: 600,
                color: 'var(--text)',
                marginBottom: '0.2rem',
                lineHeight: 1.2,
              }}>
                {action.title}
              </div>
              <div style={{
                fontSize: '0.73rem',
                color: 'var(--text-muted)',
                lineHeight: 1.45,
              }}>
                {action.desc}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Cultural note footer */}
      <div style={{
        margin: '0 1rem 2rem',
        padding: '0.85rem 1rem',
        borderRadius: 12,
        background: 'rgba(42,24,16,0.5)',
        border: '1px solid var(--border)',
        maxWidth: 680,
        marginLeft: 'auto',
        marginRight: 'auto',
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'flex-start',
      }}>
        <span style={{ fontSize: '1.1rem', flexShrink: 0, marginTop: '0.1rem' }}>🏮</span>
        <div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.6, margin: 0 }}>
            <span style={{ color: 'var(--amber-light)', fontWeight: 600 }}>Did you know? </span>
            Pampanga is the culinary capital of the Philippines. Saying{' '}
            <em className="kap">Mangan ta na!</em> (Let's eat!) is both an invitation and an expression of warmth.
          </p>
        </div>
      </div>
    </div>
  )
}
