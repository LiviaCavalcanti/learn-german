/**
 * Conjugation background-job store (per target language).
 *
 * Lives at module scope (outside React) so an in-flight conjugation keeps
 * running when the learner navigates to another tab. Completed tables are cached
 * in localStorage per language, so any verb is conjugated by the LLM only once —
 * reloads and revisits read the cached table instead of asking again. The ~20
 * most common verbs of each language ship as bundled tables (see
 * commonConjugations.ts): they are seeded as ready-to-show jobs and appear in
 * the "seen verbs" list, fully available, from the very first render — offline,
 * with no LLM call. Languages without a bundle fall back to background
 * preloading. Freshly looked-up verbs appear immediately too, with a loading
 * indicator while their request is still in flight.
 */
import { api } from '../../lib/api'
import type { ConjugationTable } from '../../lib/types'
import { COMMON_VERBS } from './commonVerbs'
import { COMMON_CONJUGATIONS } from './commonConjugations'

const CACHE_PREFIX = 'sprachheft.conjugation.cache.'
/** Cap on *non-common* verbs kept in the persistent cache (common verbs are always kept). */
const MAX_CACHED = 60
const ERROR_MSG = 'Could not conjugate that verb. Check the spelling and try again.'

export type JobStatus = 'idle' | 'loading' | 'done' | 'error'

export interface ConjugationJob {
  /** Stable key (lowercased label). */
  id: string
  /** Text shown in the seen list: the typed form while loading, the resolved infinitive once done. */
  label: string
  status: JobStatus
  table: ConjugationTable | null
  error: string | null
  vocabStatus: 'added' | 'exists' | null
  /** One of the language's preloaded common verbs. */
  common: boolean
}

export interface ConjugationState {
  lang: string
  /** Job ids, most-recent first. */
  order: string[]
  jobs: Record<string, ConjugationJob>
  /** Which job's result is currently shown. */
  activeId: string | null
}

interface StoredEntry {
  label: string
  table: ConjugationTable
  vocabStatus: 'added' | 'exists' | null
}
interface StoredCache {
  order: string[]
  entries: Record<string, StoredEntry>
}

function keyFor(label: string): string {
  return label.trim().toLowerCase()
}

const commonSets: Record<string, Set<string>> = {}
function commonSetFor(lang: string): Set<string> {
  if (!commonSets[lang]) commonSets[lang] = new Set((COMMON_VERBS[lang] ?? []).map(keyFor))
  return commonSets[lang]
}

function cacheKey(lang: string): string {
  return CACHE_PREFIX + lang
}

function loadCache(lang: string): StoredCache {
  try {
    const raw = localStorage.getItem(cacheKey(lang))
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed && Array.isArray(parsed.order) && parsed.entries) {
        return parsed as StoredCache
      }
    }
  } catch {
    /* ignore */
  }
  return { order: [], entries: {} }
}

/** Persist the fully-loaded tables so we never ask the LLM for them again. */
function saveCache(lang: string, next: ConjugationState) {
  try {
    const common = commonSetFor(lang)
    const order: string[] = []
    const entries: Record<string, StoredEntry> = {}
    let others = 0
    for (const id of next.order) {
      const job = next.jobs[id]
      if (!job || job.status !== 'done' || !job.table) continue
      if (!common.has(id)) {
        if (others >= MAX_CACHED) continue
        others++
      }
      entries[id] = { label: job.label, table: job.table, vocabStatus: job.vocabStatus }
      order.push(id)
    }
    const payload: StoredCache = { order, entries }
    localStorage.setItem(cacheKey(lang), JSON.stringify(payload))
  } catch {
    /* ignore storage errors */
  }
}

function buildInitial(lang: string): ConjugationState {
  const common = commonSetFor(lang)
  const cache = loadCache(lang)
  const jobs: Record<string, ConjugationJob> = {}
  const order: string[] = []
  // Restore cached tables as ready-to-show jobs (no LLM call needed).
  for (const id of cache.order) {
    const entry = cache.entries[id]
    if (!entry || jobs[id]) continue
    jobs[id] = {
      id,
      label: entry.label,
      status: 'done',
      table: entry.table,
      error: null,
      vocabStatus: entry.vocabStatus ?? null,
      common: common.has(id),
    }
    order.push(id)
  }
  // Seed the bundled common-verb tables as ready-to-show jobs — available
  // offline from the very first render, no LLM call ever.
  for (const table of COMMON_CONJUGATIONS[lang] ?? []) {
    const id = keyFor(table.infinitive)
    if (jobs[id]) continue
    jobs[id] = {
      id,
      label: table.infinitive,
      status: 'done',
      table,
      error: null,
      vocabStatus: null,
      common: true,
    }
    order.push(id)
  }
  // Seed any remaining common verbs (languages without a bundle) as idle
  // placeholders; they are fetched on first visit by preloadCommon().
  for (const label of COMMON_VERBS[lang] ?? []) {
    const id = keyFor(label)
    if (jobs[id]) continue
    jobs[id] = { id, label, status: 'idle', table: null, error: null, vocabStatus: null, common: true }
    order.push(id)
  }
  return { lang, order, jobs, activeId: null }
}

const states: Record<string, ConjugationState> = {}
const listeners = new Set<() => void>()

function ensure(lang: string): ConjugationState {
  if (!states[lang]) states[lang] = buildInitial(lang)
  return states[lang]
}

function emit() {
  listeners.forEach((l) => l())
}

function commit(lang: string, next: ConjugationState, persist = false) {
  states[lang] = next
  if (persist) saveCache(lang, next)
  emit()
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function getSnapshot(lang: string): ConjugationState {
  return ensure(lang)
}

function setActive(lang: string, id: string) {
  const state = ensure(lang)
  if (state.activeId === id) return
  commit(lang, { ...state, activeId: id })
}

interface StartOpts {
  /** Show this job's result (used for user lookups, not background preloads). */
  activate: boolean
  /** Move the verb to the front of the list (recent-first); off for preloads. */
  reorder: boolean
  common?: boolean
}

function startJob(lang: string, id: string, query: string, opts: StartOpts) {
  const state = ensure(lang)
  const existing = state.jobs[id]
  // Cached or already in flight — just focus it, never ask the LLM again.
  if (existing && existing.status === 'done' && existing.table) {
    if (opts.activate) setActive(lang, id)
    return
  }
  if (existing && existing.status === 'loading') {
    if (opts.activate) setActive(lang, id)
    return
  }
  const job: ConjugationJob = {
    id,
    label: existing?.label ?? query,
    status: 'loading',
    table: existing?.table ?? null,
    error: null,
    vocabStatus: existing?.vocabStatus ?? null,
    common: opts.common ?? existing?.common ?? commonSetFor(lang).has(id),
  }
  const order = opts.reorder
    ? [id, ...state.order.filter((x) => x !== id)]
    : state.order.includes(id)
      ? state.order
      : [...state.order, id]
  commit(lang, {
    ...state,
    order,
    jobs: { ...state.jobs, [id]: job },
    activeId: opts.activate ? id : state.activeId,
  })
  // Only verbs the learner actively looked up are added to their vocabulary;
  // background preloads just warm the conjugation cache.
  void runJob(lang, id, query, opts.activate)
}

/** Start (or focus) a conjugation. The verb shows in the seen list while loading. */
export function conjugate(lang: string, input: string) {
  const q = input.trim()
  if (!q) return
  startJob(lang, keyFor(q), q, { activate: true, reorder: true })
}

/** Focus a seen verb; (re)fetch it only if we don't have a cached table yet. */
export function select(lang: string, id: string) {
  const state = ensure(lang)
  const job = state.jobs[id]
  if (!job) return
  if (job.status === 'done' || job.status === 'loading') {
    setActive(lang, id)
    return
  }
  startJob(lang, id, job.label, { activate: true, reorder: true })
}

/** Fetch any common verbs not yet cached, in the background (no LLM call if cached). */
export function preloadCommon(lang: string) {
  for (const label of COMMON_VERBS[lang] ?? []) {
    const id = keyFor(label)
    const job = ensure(lang).jobs[id]
    if (!job || job.status === 'idle' || job.status === 'error') {
      startJob(lang, id, label, { activate: false, reorder: false, common: true })
    }
  }
}

/** Clear the learner's looked-up verbs, keeping the always-loaded common ones. */
export function clearSeen(lang: string) {
  const prev = ensure(lang)
  const jobs: Record<string, ConjugationJob> = {}
  const order: string[] = []
  for (const label of COMMON_VERBS[lang] ?? []) {
    const id = keyFor(label)
    const existing = prev.jobs[id]
    jobs[id] =
      existing && existing.status === 'done' && existing.table
        ? { ...existing, common: true }
        : { id, label, status: 'idle', table: null, error: null, vocabStatus: null, common: true }
    order.push(id)
  }
  commit(lang, { lang, order, jobs, activeId: null }, true)
  preloadCommon(lang)
}

async function runJob(lang: string, provisionalId: string, query: string, addToVocab: boolean) {
  let result: ConjugationTable
  try {
    result = await api.conjugate(query)
  } catch {
    failJob(lang, provisionalId)
    return
  }
  finishJob(lang, provisionalId, result)
  if (!addToVocab) return
  // Best-effort: add the resolved verb to vocabulary (secondary to showing the table).
  const infId = keyFor(result.infinitive)
  try {
    const saved = await api.addVerb({
      infinitive: result.infinitive,
      english: result.english,
      partizip_ii: result.partizip_ii,
      auxiliary: result.auxiliary,
    })
    setVocabStatus(lang, infId, saved.created ? 'added' : 'exists')
  } catch {
    /* ignore vocab errors */
  }
}

function finishJob(lang: string, provisionalId: string, result: ConjugationTable) {
  const state = ensure(lang)
  const inf = result.infinitive
  const infId = keyFor(inf)
  const provisional = state.jobs[provisionalId]
  const existingInf = state.jobs[infId]
  // The learner cleared the list while this was loading — don't resurrect it.
  if (!provisional && !existingInf) return

  const jobs = { ...state.jobs }
  let order = [...state.order]
  let activeId = state.activeId

  // The typed form may resolve to a different infinitive (e.g. "ging" → "gehen");
  // drop the provisional entry and merge into the resolved one.
  if (provisionalId !== infId && jobs[provisionalId]) {
    delete jobs[provisionalId]
    order = order.filter((x) => x !== provisionalId)
    if (activeId === provisionalId) activeId = infId
  }

  const wasCommon = existingInf?.common ?? provisional?.common ?? commonSetFor(lang).has(infId)
  jobs[infId] = {
    id: infId,
    label: inf,
    status: 'done',
    table: result,
    error: null,
    vocabStatus: existingInf?.vocabStatus ?? provisional?.vocabStatus ?? null,
    common: wasCommon,
  }
  if (!order.includes(infId)) order.push(infId)
  // Preloaded common verbs keep their seeded position; user lookups jump to front.
  if (!wasCommon) order = [infId, ...order.filter((x) => x !== infId)]
  commit(lang, { ...state, order, jobs, activeId }, true)
}

function failJob(lang: string, id: string) {
  const state = ensure(lang)
  const job = state.jobs[id]
  if (!job) return
  // Surface the error only for the verb the learner is looking at; a failed
  // background preload quietly reverts to idle so it can be retried later.
  const next: ConjugationJob =
    state.activeId === id
      ? { ...job, status: 'error', error: ERROR_MSG, table: null }
      : { ...job, status: 'idle', error: null }
  commit(lang, { ...state, jobs: { ...state.jobs, [id]: next } })
}

function setVocabStatus(lang: string, id: string, status: 'added' | 'exists') {
  const state = ensure(lang)
  const job = state.jobs[id]
  if (!job) return
  commit(lang, { ...state, jobs: { ...state.jobs, [id]: { ...job, vocabStatus: status } } }, true)
}
