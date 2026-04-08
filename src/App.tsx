import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import BottomNav from './components/layout/BottomNav'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Translate from './pages/Translate'
import Grammar from './pages/Grammar'
import Vocabulary from './pages/Vocabulary'
import Compare from './pages/Compare'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100svh', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
        <main style={{ flex: 1, overflow: 'hidden' }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/translate" element={<Translate />} />
            <Route path="/grammar" element={<Grammar />} />
            <Route path="/vocabulary" element={<Vocabulary />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}
