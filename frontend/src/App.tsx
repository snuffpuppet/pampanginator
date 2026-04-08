import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import BottomNav from './components/BottomNav'
import Home from './components/Home'
import Chat from './components/Chat'
import Translate from './components/Translate'
import Grammar from './components/Grammar'
import Vocabulary from './components/Vocabulary'
import Compare from './components/Compare'

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
