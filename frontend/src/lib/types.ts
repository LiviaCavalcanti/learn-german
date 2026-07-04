export type Level = 'A1' | 'A2' | 'B1' | 'B2' | 'C1'

export interface LanguageOption {
  code: string
  name: string
  endonym: string
  level_framework: string
  levels: string[]
  voice: string
  has_conjugation: boolean
}

export interface NativeOption {
  code: string
  name: string
}

export interface LanguagesResponse {
  targets: LanguageOption[]
  natives: NativeOption[]
}

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
  native_lang: string
  level: string
  transcript: string
  translation: string | null
  notes: string | null
  created_at: string
}

export interface VocabItem {
  id: number
  material_id: number | null
  target_lang: string
  word: string
  lemma: string
  pos: string | null
  meaning_en: string
  cefr: string | null
  example_de: string | null
  example_en: string | null
  grammar_tags: string[]
  created_at: string
  ipa?: string | null
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
  // Variant grouping: exercises sharing a group_id are alternates of one slot.
  group_id?: number | null
  variant_position?: number
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

export interface ReviewCard {
  srstate_id: number
  item_type: 'vocab' | 'exercise'
  item_id: number
  due: string
  reps: number
  lapses: number
  state: string
  last_review: string | null
  is_due: boolean
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  item: any
}

export type Rating = 'again' | 'hard' | 'good' | 'easy'

export interface AnswerAttempt {
  id: number
  exercise_id: number
  kind: 'check' | 'feedback' | string
  responses: string[]
  answer_text: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: any
  correct: number
  total: number
  created_at: string
}

export interface FeedbackError {
  original: string
  correction: string
  explanation: string
}

export interface AnswerFeedback {
  has_errors: boolean
  corrected: string
  errors: FeedbackError[]
  summary: string
  verdict: 'correct' | 'partial' | 'incorrect' | 'unanswered'
  score: number
  reference: string
}

export interface CourseIndex {
  title: string
  levels: { level: string; title: string; units: number; lessons: number }[]
}

export interface LessonQuestion {
  prompt: string
  translation?: string
}

export interface Lesson {
  code: string
  title: string
  grammar_topics: string[]
  can_do: string
  seed_text: string
  intro?: string
  story?: string
  questions?: LessonQuestion[]
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

export interface LevelProgress {
  level: string
  title: string
  lessons_total: number
  lessons_completed: number
  percent: number
}

export interface NextLesson {
  code: string
  title: string
  level: string
  can_do: string
}

export interface CourseProgress {
  levels: LevelProgress[]
  total_lessons: number
  completed_lessons: number
  percent: number
  completed_codes: string[]
  next_lesson: NextLesson | null
}

export interface ConjugationCell {
  label: string
  form: string
}

export interface ConjugationTense {
  name: string
  note: string
  cells: ConjugationCell[]
}

export interface ConjugationTable {
  infinitive: string
  language: string
  english: string
  regular: boolean
  notes: string
  auxiliary: string
  partizip_ii: string
  tenses: ConjugationTense[]
}

export interface VerbVocabResult {
  created: boolean
  item: VocabItem
}

// --- Tutor / teacher chat ---
export type ChatContextKind = 'none' | 'material' | 'vocab' | 'exercise' | 'text'

export interface ChatContext {
  kind: ChatContextKind
  id?: number | null
  label?: string | null
  text?: string | null
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'teacher' | string
  content: string
  created_at: string
}

export interface ChatSession {
  id: number
  title: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  context: any
  created_at: string
  updated_at: string
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[]
}

export interface ChatTurn {
  user_message: ChatMessage
  teacher_message: ChatMessage
}

export interface LearnerProfile {
  summary: string
  focus: string
  strengths: string[]
  difficulties: string[]
  updated_at: string
}

export interface TeacherCardSuggestion {
  front: string
  back: string
  cefr: string
  tags: string[]
}
