interface Props {
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg'
}

export default function KapampanganText({ children, size = 'md' }: Props) {
  const sizes = { sm: '0.95em', md: '1.08em', lg: '1.2em' }
  return (
    <em style={{
      fontFamily: '"Cormorant Garamond", Georgia, serif',
      fontStyle: 'italic',
      color: 'var(--amber)',
      fontSize: sizes[size],
      fontWeight: 500,
    }}>
      {children}
    </em>
  )
}
