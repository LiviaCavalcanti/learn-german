export type Level = 'A1' | 'A2' | 'B1' | 'B2'

export interface MaterialSummary {
  id: number
  title: string
  media_type: string
  level: string
  created_at: string
  vocab_count: number
  exercise_count: number
}

export interface Material {
  id: number
  title: string
  media_type: string
  source_url: string | null
  source_lang: string
  level: string
  transcript: string
  translation: string | null
  notes: string | null
  created_at: string
}

export interface VocabItem {
  id: number
  material_id: number | null
  word: string
  lemma: string
  pos: string | null
  meaning_en: string
  cefr: string | null
  example_de: string | null
  example_en: string | null
  grammar_tags: string[]
  created_at: string
}

export interface Exercise {
  id: number
  material_id: number | null
  source: string
  type: string
  cefr: string | null
  grammar_tags: string[]
  instructions: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload: any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  answer_key: any
  created_at: string
}

export interface DictEntry {
  headword: string
  pos: string | null
  ipa: string | null
  translations: string[]
  senses: string[]
}

export interface DictLookup {
  query: string
  lemma: string
  available: boolean
  entries: DictEntry[]
  google_translate_url: string
}

export interface ReviewStats {
  due_now: number
  total_vocab: number
  total_exercises: number
  reviews_today: number
  streak: number
  next_due: string | null
}

export interface ReviewQueueItem {
  srstate_id: number
  item_type: 'vocab' | 'exercise'
  item_id: number
  due: string
  reps: number
  lapses: number
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  item: any
}

export type Rating = 'again' | 'hard' | 'good' | 'easy'

export interface CourseIndex {
  title: string
  levels: { level: string; title: string; units: number; lessons: number }[]
}

export interface Lesson {
  code: string
  title: string
  grammar_topics: string[]
  can_do: string
  seed_text: string
  level?: string
  unit_title?: string
}

export interface CourseUnit {
  unit: number
  title: string
  lessons: Lesson[]
}

export interface CourseLevelDetail {
  level: string
  title: string
  units: CourseUnit[]
}
