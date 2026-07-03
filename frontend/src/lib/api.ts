import type {
  AnswerAttempt,
  AnswerFeedback,
  ChatContext,
  ChatSession,
  ChatSessionDetail,
  ChatTurn,
  ConjugationTable,
  CourseIndex,
  CourseLevelDetail,
  CourseProgress,
  DictLookup,
  Exercise,
  LearnerProfile,
  LanguagesResponse,
  Material,
  MaterialSummary,
  Rating,
  ReviewCard,
  ReviewQueueItem,
  ReviewStats,
  TeacherCardSuggestion,
  VerbVocabResult,
  VocabItem,
} from './types'

// When VITE_API_BASE isn't set, talk to the backend on the same host the page was
// loaded from (port 8000). This works locally *and* from a phone that opened the app
// via a LAN / Tailscale IP, without hard-coding any address.
const BASE =
  (import.meta.env.VITE_API_BASE as string) ||
  (typeof window !== 'undefined'
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : 'http://127.0.0.1:8000')

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const resp = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!resp.ok) {
    throw new Error(`${resp.status} ${await resp.text()}`)
  }
  if (resp.status === 204) {
    return undefined as T
  }
  return (await resp.json()) as T
}

// --- Current language (set by the LanguageProvider) --------------------------
let apiTarget = 'de'
let apiNative = 'en'

/** Update the target/native language threaded into language-scoped requests. */
export function setApiLanguage(target: string, native: string): void {
  apiTarget = target || 'de'
  apiNative = native || 'en'
}

export function getApiLanguage(): { target: string; native: string } {
  return { target: apiTarget, native: apiNative }
}

/** Append the current target language (plus any extra params) to a path. */
function withLang(path: string, extra?: Record<string, string>): string {
  const sep = path.includes('?') ? '&' : '?'
  const params = new URLSearchParams({ lang: apiTarget, ...(extra ?? {}) })
  return `${path}${sep}${params.toString()}`
}

export interface NewMaterial {
  title: string
  media_type: string
  level: string
  source_url: string | null
  transcript: string
  translation: string | null
}

export const api = {
  health: () => req<{ status: string }>('/health'),
  languages: () => req<LanguagesResponse>('/languages'),

  materials: () => req<MaterialSummary[]>(withLang('/materials')),
  material: (id: number) => req<Material>(`/materials/${id}`),
  createMaterial: (data: NewMaterial) =>
    req<Material>('/materials', {
      method: 'POST',
      body: JSON.stringify({ ...data, source_lang: apiTarget, native_lang: apiNative }),
    }),
  deleteMaterial: (id: number) => req<void>(`/materials/${id}`, { method: 'DELETE' }),
  generate: (id: number, stage: number) =>
    req<{ themes: string[]; vocab_added: number; exercises_added: number }>(
      `/materials/${id}/generate?stage=${stage}`,
      { method: 'POST' },
    ),
  generateSection: (
    id: number,
    stage: number,
    section: 'vocab' | 'exercises',
    batch = 0,
  ) =>
    req<{
      vocab_added?: number
      exercises_added?: number
      exercise_batches?: number
      batch?: number
    }>(`/materials/${id}/generate?section=${section}&batch=${batch}&stage=${stage}`, {
      method: 'POST',
    }),

  rewriteMaterial: (id: number, body: { instructions?: string; target_lines?: number }) =>
    req<Material>(`/materials/${id}/rewrite`, { method: 'POST', body: JSON.stringify(body) }),

  exercises: (materialId: number) =>
    req<Exercise[]>(withLang(`/exercises?material_id=${materialId}`)),
  generateVariant: (exerciseId: number, stage: number) =>
    req<Exercise>(`/exercises/${exerciseId}/variant?stage=${stage}`, { method: 'POST' }),
  replaceExercise: (exerciseId: number, direction: 'easier' | 'harder') =>
    req<Exercise>(`/exercises/${exerciseId}/replace?direction=${direction}`, {
      method: 'POST',
    }),
  attempts: (exerciseId: number) =>
    req<AnswerAttempt[]>(`/exercises/${exerciseId}/attempts`),
  vocab: (materialId: number) => req<VocabItem[]>(withLang(`/vocab?material_id=${materialId}`)),
  allVocab: (limit = 1000) => req<VocabItem[]>(withLang(`/vocab?limit=${limit}`)),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  createVocab: (data: Record<string, any>) =>
    req<VocabItem>('/vocab', {
      method: 'POST',
      body: JSON.stringify({ ...data, target_lang: apiTarget }),
    }),
  deleteVocab: (ids: number[]) =>
    req<{ deleted: number }>('/vocab/delete', {
      method: 'POST',
      body: JSON.stringify({ ids }),
    }),
  replaceVocab: (id: number, direction: 'easier' | 'harder') =>
    req<VocabItem>(`/vocab/${id}/replace?direction=${direction}`, { method: 'POST' }),
  composeFromVocab: (body: {
    vocab_ids: number[]
    level?: string
    title?: string
    instructions?: string
  }) =>
    req<{ material_id: number; title: string; vocab_added: number; exercises_added: number }>(
      '/vocab/compose',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  vocabTopics: () =>
    req<{ topics: { topic: string; count: number; samples: { word: string; meaning_en: string }[] }[] }>(
      '/vocab/topics',
    ),

  dictLookup: (word: string) =>
    req<DictLookup>(
      withLang(`/dictionary/lookup?word=${encodeURIComponent(word)}`, { native: apiNative }),
    ),
  dictStatus: () => req<{ available: boolean; entry_count: number }>('/dictionary/status'),

  conjugate: (verb: string) =>
    req<ConjugationTable>(withLang(`/conjugation?verb=${encodeURIComponent(verb)}`)),

  addVerb: (body: {
    infinitive: string
    english?: string
    partizip_ii?: string
    auxiliary?: string
    cefr?: string | null
  }) =>
    req<VerbVocabResult>('/vocab/verb', {
      method: 'POST',
      body: JSON.stringify({ ...body, target_lang: apiTarget }),
    }),

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  practiceAnswer: (body: { exercise_id: number; responses: string[]; rating?: Rating }) =>
    req<any>('/practice/answer', { method: 'POST', body: JSON.stringify(body) }),

  practiceFeedback: (body: { exercise_id: number; answer: string }) =>
    req<AnswerFeedback>('/practice/feedback', {
      method: 'POST',
      body: JSON.stringify({ ...body, native_lang: apiNative }),
    }),

  reviewStats: () => req<ReviewStats>('/review/stats'),
  reviewQueue: (limit = 20) => req<ReviewQueueItem[]>(withLang(`/review/queue?limit=${limit}`)),
  reviewGrade: (body: { item_type: string; item_id: number; rating: Rating }) =>
    req<{ due: string; reps: number }>('/review/grade', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  reviewCards: (params: { item_type?: string; limit?: number } = {}) => {
    const q = new URLSearchParams()
    if (params.item_type) q.set('item_type', params.item_type)
    q.set('limit', String(params.limit ?? 500))
    return req<ReviewCard[]>(`/review/cards?${q.toString()}`)
  },
  reviewRemoveCards: (srstate_ids: number[]) =>
    req<{ removed: number }>('/review/cards/remove', {
      method: 'POST',
      body: JSON.stringify({ srstate_ids }),
    }),
  reviewDeleteCards: (srstate_ids: number[]) =>
    req<{ deleted: number }>('/review/cards/delete', {
      method: 'POST',
      body: JSON.stringify({ srstate_ids }),
    }),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  updateVocab: (id: number, data: Record<string, any>) =>
    req<VocabItem>(`/vocab/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  updateExercise: (
    id: number,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data: { instructions?: string; answer_key?: any },
  ) => req<Exercise>(`/exercises/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  importJson: (data: any) =>
    req<{ material_id: number; vocab_added: number; exercises_added: number }>('/imports/json', {
      method: 'POST',
      body: JSON.stringify({ ...data, source_lang: apiTarget, native_lang: apiNative }),
    }),
  importText: (data: { raw_text: string; level?: string; title?: string }) =>
    req<{ material_id: number; vocab_added: number; exercises_added: number }>('/imports/text', {
      method: 'POST',
      body: JSON.stringify({ ...data, source_lang: apiTarget, native_lang: apiNative }),
    }),

  course: () => req<CourseIndex>(withLang('/course')),
  courseProgress: () => req<CourseProgress>(withLang('/course/progress')),
  courseLevel: (level: string) => req<CourseLevelDetail>(withLang(`/course/${level}`)),
  startLesson: (code: string) =>
    req<Material>(
      withLang(`/course/lessons/${encodeURIComponent(code)}/start`, { native: apiNative }),
      { method: 'POST' },
    ),

  vocabSearch: (q: string, semantic = false) =>
    req<VocabItem[]>(
      withLang(`/vocab/search?q=${encodeURIComponent(q)}${semantic ? '&semantic=true' : ''}`),
    ),
  vocabReindex: (rebuild = false) =>
    req<{ indexed: number }>(`/vocab/reindex${rebuild ? '?rebuild=true' : ''}`, {
      method: 'POST',
    }),

  ingestStatus: () =>
    req<{ transcription_available: boolean; enabled: boolean; model: string }>('/ingest/status'),
  transcribe: (source_url: string) =>
    req<{ transcript: string }>('/ingest/transcribe', {
      method: 'POST',
      body: JSON.stringify({ source_url, source_lang: apiTarget }),
    }),

  // --- Tutor / teacher chat ---
  tutorSessions: () => req<ChatSession[]>('/tutor/sessions'),
  tutorCreateSession: (body: { title?: string; context?: ChatContext }) =>
    req<ChatSession>('/tutor/sessions', { method: 'POST', body: JSON.stringify(body) }),
  tutorSession: (id: number) => req<ChatSessionDetail>(`/tutor/sessions/${id}`),
  tutorDeleteSession: (id: number) =>
    req<void>(`/tutor/sessions/${id}`, { method: 'DELETE' }),
  tutorSend: (id: number, body: { message: string; context?: ChatContext }) =>
    req<ChatTurn>(`/tutor/sessions/${id}/messages`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  tutorProfile: () => req<LearnerProfile>('/tutor/profile'),
  tutorSuggestCard: (body: { text?: string; message_id?: number; context?: ChatContext }) =>
    req<TeacherCardSuggestion>('/tutor/cards/suggest', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  tutorCreateCard: (body: { front: string; back: string; cefr?: string; tags?: string[] }) =>
    req<{ exercise_id: number; srstate_id: number }>('/tutor/cards', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
