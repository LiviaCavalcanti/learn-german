import type {
  CourseIndex,
  CourseLevelDetail,
  DictLookup,
  Exercise,
  Material,
  MaterialSummary,
  Rating,
  ReviewQueueItem,
  ReviewStats,
  VocabItem,
} from './types'

const BASE = (import.meta.env.VITE_API_BASE as string) || 'http://127.0.0.1:8000'

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

  materials: () => req<MaterialSummary[]>('/materials'),
  material: (id: number) => req<Material>(`/materials/${id}`),
  createMaterial: (data: NewMaterial) =>
    req<Material>('/materials', { method: 'POST', body: JSON.stringify(data) }),
  deleteMaterial: (id: number) => req<void>(`/materials/${id}`, { method: 'DELETE' }),
  generate: (id: number, stage: number) =>
    req<{ themes: string[]; vocab_added: number; exercises_added: number }>(
      `/materials/${id}/generate?stage=${stage}`,
      { method: 'POST' },
    ),

  exercises: (materialId: number) =>
    req<Exercise[]>(`/exercises?material_id=${materialId}`),
  vocab: (materialId: number) => req<VocabItem[]>(`/vocab?material_id=${materialId}`),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  createVocab: (data: Record<string, any>) =>
    req<VocabItem>('/vocab', { method: 'POST', body: JSON.stringify(data) }),
  vocabTopics: () =>
    req<{ topics: { topic: string; count: number; samples: { word: string; meaning_en: string }[] }[] }>(
      '/vocab/topics',
    ),

  dictLookup: (word: string) =>
    req<DictLookup>(`/dictionary/lookup?word=${encodeURIComponent(word)}`),
  dictStatus: () => req<{ available: boolean; entry_count: number }>('/dictionary/status'),

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  practiceAnswer: (body: { exercise_id: number; responses: string[]; rating?: Rating }) =>
    req<any>('/practice/answer', { method: 'POST', body: JSON.stringify(body) }),

  reviewStats: () => req<ReviewStats>('/review/stats'),
  reviewQueue: (limit = 20) => req<ReviewQueueItem[]>(`/review/queue?limit=${limit}`),
  reviewGrade: (body: { item_type: string; item_id: number; rating: Rating }) =>
    req<{ due: string; reps: number }>('/review/grade', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  importJson: (data: any) =>
    req<{ material_id: number; vocab_added: number; exercises_added: number }>('/imports/json', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  importText: (data: { raw_text: string; level?: string; title?: string }) =>
    req<{ material_id: number; vocab_added: number; exercises_added: number }>('/imports/text', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  course: () => req<CourseIndex>('/course'),
  courseLevel: (level: string) => req<CourseLevelDetail>(`/course/${level}`),
  startLesson: (code: string) =>
    req<Material>(`/course/lessons/${encodeURIComponent(code)}/start`, { method: 'POST' }),

  vocabSearch: (q: string, semantic = false) =>
    req<VocabItem[]>(
      `/vocab/search?q=${encodeURIComponent(q)}${semantic ? '&semantic=true' : ''}`,
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
      body: JSON.stringify({ source_url }),
    }),
}
