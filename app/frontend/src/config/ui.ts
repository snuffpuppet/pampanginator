/**
 * Typed mirror of frontend/config/ui.yaml.
 *
 * The yaml is the single source of truth — this file provides TypeScript types
 * and imports the parsed values so the rest of the app never reads yaml directly.
 */

export interface NavItem {
  to: string
  label: string
  icon: string
}

export interface QuickAction {
  to: string
  icon: string
  title: string
  desc: string
  accent: string
  state?: Record<string, string>
}

export interface Scenario {
  id: string
  label: string
  icon: string
  opening_prompt: string
}

export interface UiConfig {
  navigation: NavItem[]
  quick_actions: QuickAction[]
  scenarios: Scenario[]
  compare_sample_prompts: string[]
  sidebar_panels: string[]
}

// Vite resolves yaml imports via a plugin; until then, we duplicate the data
// here in typed form so the rest of the app imports from this module only.
// When a yaml loader is added, replace the const below with an import.

export const navigation: NavItem[] = [
  { to: '/', label: 'Home', icon: 'home' },
  { to: '/chat', label: 'Ading', icon: 'chat' },
  { to: '/translate', label: 'Translate', icon: 'translate' },
  { to: '/grammar', label: 'Grammar', icon: 'grammar' },
  { to: '/vocabulary', label: 'Vocab', icon: 'vocabulary' },
]

export const quickActions: QuickAction[] = [
  { to: '/chat', icon: '◎', title: 'Talk with Ading', desc: 'Open conversation — ask anything about Kapampangan.', accent: 'var(--amber)' },
  { to: '/translate', icon: '⇄', title: 'Translate', desc: 'English ↔ Kapampangan with usage notes.', accent: 'var(--terra-light)' },
  { to: '/grammar', icon: '∂', title: 'Grammar Explorer', desc: 'Verb focus, aspects, pronouns, particles & more.', accent: 'var(--forest-light, #3d8a65)' },
  { to: '/vocabulary', icon: '◈', title: 'Vocabulary & Drill', desc: 'Browse all categories. Drill with flashcards.', accent: 'var(--amber-light)' },
  { to: '/chat', icon: '✦', title: 'Check My Kapampangan', desc: "Paste a sentence for Ading's gentle correction.", accent: 'var(--terra)', state: { mode: 'correction' } },
  { to: '/chat', icon: '⬡', title: 'Scenario Practice', desc: 'Family dinner, market, office — roleplay with Ading.', accent: '#9b6a9b', state: { mode: 'scenario' } },
  { to: '/compare', icon: '⇌', title: 'Compare LLMs', desc: 'Claude vs local model — same question, side by side.', accent: '#6a8fc1' },
]

export const scenarios: Scenario[] = [
  { id: 'family', label: 'Family Conversation', icon: '🏠', opening_prompt: 'Practice a warm family dinner conversation in Kapampangan' },
  { id: 'market', label: 'At the Market', icon: '🛒', opening_prompt: 'Practice buying food at a Pampanga market' },
  { id: 'professional', label: 'Professional Context', icon: '💼', opening_prompt: 'Practice a formal workplace introduction in Kapampangan' },
  { id: 'greeting', label: 'Greetings & Small Talk', icon: '👋', opening_prompt: 'Practice common Kapampangan greetings and small talk' },
  { id: 'food', label: 'Food & Cooking', icon: '🍲', opening_prompt: 'Learn vocabulary around Kapampangan food and cooking' },
]

export const compareSamplePrompts: string[] = [
  'How do I say "I miss you" in Kapampangan?',
  'Explain the difference between sinulat and sumulat.',
  'Translate: "Good morning, have you eaten yet?"',
  'What does "Kaluguran da ka" mean?',
  'How do I conjugate the verb "mangan" in all three aspects?',
]

export const sidebarPanels: string[] = ['grammar_notes', 'vocabulary_cards']
