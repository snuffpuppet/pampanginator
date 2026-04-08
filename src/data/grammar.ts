export interface GrammarSection {
  id: string
  title: string
  subtitle: string
  summary: string
  examplePrompt: string // sent to Ading when user taps "Show me an example"
  table?: { headers: string[]; rows: string[][] }
  rules?: string[]
}

export const GRAMMAR_SECTIONS: GrammarSection[] = [
  // ── START HERE ──────────────────────────────────────────────────────────────
  {
    id: 'syllabary',
    title: 'Start Here: The Syllabary',
    subtitle: 'AA, BA, KA, DA — the key to all verb forms',
    summary: 'Before learning verb aspects, focus, or pronouns, learn the syllabary — the Abakada (AA, BA, KA, DA…). In Kapampangan, every syllable is either a lone vowel (V) or a consonant paired with a vowel (CV). This is not just the alphabet — it is the engine of the entire verb system. Every tense/aspect change is a syllable-level operation on the root word.',
    examplePrompt: 'Teach me the Kapampangan syllabary (AA, BA, KA, DA…) as a beginner would first learn it. Then show me, using syllable-by-syllable breakdown, how the progressive, completed, and contemplated aspects are formed from the roots sulat (write), basa (read), and datang (arrive). Make the syllable operations very visual.',
    rules: [
      'Every syllable is V (vowel alone) or CV (consonant + vowel)',
      'The 16 base syllables: AA · BA · KA · DA · GA · LA · MA · NA · NGA · PA · RA · SA · TA · WA · YA — each consonant always paired with its inherent /a/ vowel',
      'D and R are the same sound in many dialects — da/ra are interchangeable',
      'No native /h/ — H only appears in borrowed words',
      '─────────────────────────────────────────',
      'PROGRESSIVE aspect = reduplicate (copy) the first CV syllable and place it before the root',
      'COMPLETED aspect = insert -in- between the first consonant and the rest of the word',
      'CONTEMPLATED aspect = insert -um- between the first consonant and the rest of the word',
      '─────────────────────────────────────────',
      'Vowel-initial roots: -in- and -um- prefix the whole word → ininom (completed of inum), uminom (contemplated)',
    ],
    table: {
      headers: ['Root', 'Syllables', 'Progressive (copy first CV)', 'Completed (insert -in-)', 'Contemplated (insert -um-)'],
      rows: [
        ['sulat — write', '[su]·[lat]', '[su]·sulat', 's·[in]·ulat', 's·[um]·ulat'],
        ['basa — read', '[ba]·[sa]', '[ba]·basa(n)', 'b·[in]·asa', 'b·[um]·asa'],
        ['datang — arrive', '[da]·[tang]', '[da]·datang', 'd·[in]·atang', 'd·[um]·atang'],
        ['lakad — walk', '[la]·[kad]', '[la]·lakad', 'l·[in]·akad', 'l·[um]·akad'],
        ['inum — drink (V-initial)', '[i]·[num]', '[i]·inum', '[in]·inum', '[um]·inum'],
      ],
    },
  },
  // ── GRAMMAR SECTIONS ────────────────────────────────────────────────────────
  {
    id: 'sentence-structure',
    title: 'Sentence Structure',
    subtitle: 'VSO Word Order',
    summary: 'Default order is Verb – Subject – Object (VSO), though topic prominence allows flexibility. Kapampangan is topic-prominent, meaning the verb changes to show which noun is the "focus" of the sentence.',
    examplePrompt: 'Give me two examples of basic Kapampangan VSO sentences with a word-by-word English breakdown.',
    rules: [
      'Default: Verb – Subject – Object',
      'Topic prominence overrides strict word order',
      'Verb comes first in most basic sentences',
    ],
  },
  {
    id: 'verb-focus',
    title: 'Verb Focus System',
    subtitle: 'The Heart of Kapampangan Grammar',
    summary: 'Kapampangan has Austronesian alignment — the verb changes with affixes to show which noun is the "topic" (focus) of the sentence. This is the most important feature of Kapampangan grammar.',
    examplePrompt: 'Give me one clear example sentence for each of the five voices in the Kapampangan verb focus system (Actor, Object, Goal, Locative, Circumstantial), with English translations.',
    table: {
      headers: ['Voice', 'Focus on', 'Key Affix', 'Example'],
      rows: [
        ['Actor Focus (AF)', 'The one doing the action', 'mag-, mang-, -um-', 'Sinulat ku. (I wrote.)'],
        ['Object/Patient Focus (OF)', 'The thing acted on', '-en, -an, i-', 'Silatanan na ku. (He wrote to me.)'],
        ['Goal/Benefactive Focus (BF)', 'The person receiving benefit', '-an', 'Dinan kong pera. (I gave them money.)'],
        ['Locative Focus (LF)', 'The place of the action', '-an', 'Direction / location as topic'],
        ['Circumstantial Focus (CF)', 'Instrument or benefactee', 'i-', 'Tool or means as subject'],
      ],
    },
  },
  {
    id: 'verb-aspects',
    title: 'Verb Aspects',
    subtitle: 'Aspect-Based, Not Tense-Based',
    summary: 'Kapampangan is aspect-based — verbs show whether an action is completed, ongoing, or not yet done. This differs significantly from English tenses and from Tagalog (where aspect forms look similar but mean the opposite).',
    examplePrompt: 'Show me all three aspects (Contemplated, Progressive, Completed) for the verbs mangan (to eat) and sulat (to write), with English meanings and a note about the Tagalog false friends.',
    table: {
      headers: ['Aspect', 'Meaning', 'Formation', 'Example (sulat = write)'],
      rows: [
        ['Contemplated', 'Not yet done (future)', 'mag-/-um- prefix', 'Sumulat (will write)'],
        ['Progressive', 'Currently happening', 'Reduplication of first syllable', 'Susulat (is writing)'],
        ['Completed', 'Already done (past)', '-in- infix', 'Sinulat (wrote)'],
      ],
    },
    rules: [
      '⚠️ Tagalog false friend: Susulat = "is writing" in Kapampangan, but "will write" in Tagalog',
      '⚠️ Tagalog false friend: Sumulat = "will write" in Kapampangan, but "wrote" in Tagalog',
    ],
  },
  {
    id: 'noun-markers',
    title: 'Noun Markers',
    subtitle: 'Case Markers',
    summary: 'Nouns are marked by case. There are two noun classes: personal (names of people) and common (everything else). Case markers show the grammatical role of each noun in the sentence.',
    examplePrompt: 'Give me three example sentences showing the absolutive, ergative, and oblique case markers in Kapampangan, for both common nouns and personal names.',
    table: {
      headers: ['Case', 'Common nouns', 'Personal names'],
      rows: [
        ['Absolutive (topic/subject)', 'ing (sg) / deng/reng (pl)', 'i (sg) / di/ri (pl)'],
        ['Ergative (actor / possessor)', 'ning (sg) / dening (pl)', 'ni (sg) / di/ri (pl)'],
        ['Oblique (location, direction)', 'king (sg) / karing (pl)', 'kay (sg) / kari/kadi (pl)'],
      ],
    },
  },
  {
    id: 'pronouns',
    title: 'Pronouns',
    subtitle: 'The Always-Present Rule',
    summary: 'Kapampangan pronouns come in absolutive (topic) and ergative (actor/possessor) forms. Critically, the pronoun must always be present even when the noun it represents is also stated in the sentence.',
    examplePrompt: 'Explain the Kapampangan pronoun always-present rule with three example sentences — one correct, one wrong, and one using a portmanteau pronoun like ke.',
    rules: [
      '✅ Dinatang ya i Erning. (pronoun ya required even with i Erning)',
      '❌ Dinatang i Erning. (INCORRECT — pronoun missing)',
      'Enclitic pronoun always comes before another pronoun or discourse marker',
      'Portmanteau: Ikit ke = Ikit ku ya (I saw him/her)',
    ],
    table: {
      headers: ['Person', 'Absolutive', 'Ergative'],
      rows: [
        ['1st sg', 'yaku / aku', 'ku'],
        ['2nd sg', 'ika', 'mu'],
        ['3rd sg', 'ya', 'na / ne'],
        ['1st pl excl', 'ikami', 'mi'],
        ['1st pl incl', 'ikata / ikatamu', 'ta / tamu'],
        ['2nd pl', 'ikayu', 'yu'],
        ['3rd pl', 'ila', 'da / ra'],
      ],
    },
  },
  {
    id: 'negation',
    title: 'Negation',
    subtitle: 'Ali vs. Ala',
    summary: 'Kapampangan uses two main negation words: ali/e for negating verbs and statements, and ala for negating existence or possession (opposite of ati).',
    examplePrompt: 'Give me three example sentences using ali/e to negate verbs, and three using ala to negate existence/possession. Include English translations.',
    rules: [
      'ali / e — negates verbs and statements',
      'ala — negates existence/possession (there is no / does not have)',
      'ati — affirmative existence/possession (there is / has)',
      'E ku pa mengan. — I haven\'t eaten yet.',
      'Ala na mung lugud. — There is no more love.',
    ],
  },
  {
    id: 'particles',
    title: 'Common Particles',
    subtitle: 'Discourse Markers',
    summary: 'Particles add nuance of time, hearsay, emphasis, and conditionality to sentences. They are small but powerful words that significantly change meaning.',
    examplePrompt: 'Show me example sentences for na, pa, lang, daw, and ba, with English translations and explanations of the nuance each particle adds.',
    table: {
      headers: ['Particle', 'Use'],
      rows: [
        ['ba', 'Optional question marker for yes/no questions'],
        ['na', 'Now, already, yet, anymore'],
        ['pa', 'Still, yet, more'],
        ['din / rin', 'Also, too (inclusive)'],
        ['lang', 'Only, just'],
        ['daw / raw', 'Hearsay — "they say that…"'],
        ['ita', 'Perhaps, probably'],
        ['naman', 'Also, in turn (contrastive/additive)'],
        ['kung', 'If (conditional)'],
      ],
    },
  },
  {
    id: 'demonstratives',
    title: 'Demonstratives',
    subtitle: 'Singular & Plural Forms',
    summary: 'Kapampangan demonstratives are unique in having singular and plural forms. They also distinguish between abstract (iti) and concrete (ini) references for "this".',
    examplePrompt: 'Explain the difference between iti and ini in Kapampangan with example sentences, and show me the full demonstrative table in use.',
    table: {
      headers: ['Meaning', 'Near speaker', 'Near listener', 'Far from both'],
      rows: [
        ['This/That (abstract)', 'iti', 'iyan', 'ita'],
        ['This/That (concrete)', 'ini', 'iyan', 'ita'],
        ['Plural', 'reni / deni', 'den / ren', 'reta / deta'],
        ['Locative (here/there)', 'keni', 'keti', 'karin'],
      ],
    },
  },
]
