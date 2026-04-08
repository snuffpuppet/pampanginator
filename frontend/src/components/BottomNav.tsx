import { NavLink, useLocation } from 'react-router-dom'
import { navigation } from '../config/ui'

const NAV_ICONS: Record<string, React.ReactNode> = {
  home: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9.5L10 3l7 6.5V17a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/>
      <path d="M7.5 18V12h5v6"/>
    </svg>
  ),
  chat: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 10c0 4-3.6 7-8 7a9.2 9.2 0 01-4-.9L2 17l1-3.5A6.8 6.8 0 012 10C2 6 5.6 3 10 3s8 3 8 7z"/>
    </svg>
  ),
  translate: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 5h8M7 3v2M11 5c0 3-3 5.5-6 6.5"/>
      <path d="M9 11.5c1.5.5 3 1.5 3.5 3M12 9l4 8M14 9l-2 0"/>
    </svg>
  ),
  grammar: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="14" height="14" rx="2"/>
      <path d="M7 7h6M7 10h6M7 13h3"/>
    </svg>
  ),
  vocabulary: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19V5a2 2 0 012-2h10a1 1 0 011 1v13"/>
      <path d="M4 19h13M4 19a1 1 0 01-1-1V8"/>
      <path d="M8 7h5M8 10h3"/>
    </svg>
  ),
}

export default function BottomNav() {
  const location = useLocation()

  return (
    <nav className="bottom-nav">
      <div style={{ display: 'flex', width: '100%' }}>
        {navigation.map((tab) => {
          const isActive = tab.to === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(tab.to)

          return (
            <NavLink
              key={tab.to}
              to={tab.to}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '2px',
                padding: '6px 4px',
                textDecoration: 'none',
                color: isActive ? 'var(--amber)' : 'var(--text-dim)',
                transition: 'color 0.15s ease',
                fontSize: '0.65rem',
                fontWeight: isActive ? 600 : 400,
                letterSpacing: '0.02em',
              }}
            >
              <span style={{ opacity: isActive ? 1 : 0.6, transition: 'opacity 0.15s ease' }}>
                {NAV_ICONS[tab.icon]}
              </span>
              {tab.label}
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
