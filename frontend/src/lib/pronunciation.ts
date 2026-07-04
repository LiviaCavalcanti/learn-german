/**
 * Pronunciation (text-to-speech) provider seam.
 *
 * By default the app now speaks via the backend (`BackendSpeechProvider`): the
 * FastAPI service synthesizes each word with espeak-ng in the *target* language
 * and returns WAV audio. This is OS-independent — it does not depend on which
 * voices are installed on the learner's device — so a Spanish word is always
 * pronounced in Spanish, never in whatever default voice the browser falls back
 * to. When the backend audio is unavailable (the optional `phonetics` extra is
 * not installed, or the request fails), it transparently falls back to the
 * browser's Web Speech API.
 *
 * Set `VITE_TTS_MODE=webspeech` to force the browser-only Web Speech provider.
 * The `SpeechProvider` interface plus the `getSpeech()` factory keep call sites
 * decoupled from the implementation.
 */
import { API_BASE } from './api'

export interface SpeechProvider {
  /** Whether speech output is usable in the current environment. */
  readonly available: boolean
  /** Speak the given text (in the current target language by default). */
  speak(text: string, lang?: string): void
  /** Stop any in-progress speech. */
  cancel(): void
}

// Current TTS language (BCP-47), updated by the LanguageProvider when the learner
// switches target language. Defaults to German for backwards compatibility.
let currentSpeechLang = 'de-DE'

/** Set the voice/language used by speech output (e.g. 'de-DE', 'es-ES'). */
export function setSpeechLang(voice: string): void {
  currentSpeechLang = voice || 'de-DE'
}

/** The current speech language (BCP-47). */
export function getSpeechLang(): string {
  return currentSpeechLang
}

class WebSpeechProvider implements SpeechProvider {
  private synth: SpeechSynthesis | null =
    typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null

  // Browsers populate the voice list asynchronously: the first getVoices() call
  // often returns []. If we speak before voices load, no voice matches the target
  // language and the engine falls back to the OS default voice — which is exactly
  // the "wrong language" bug. So we cache voices and refresh on `voiceschanged`.
  private voices: SpeechSynthesisVoice[] = []

  constructor() {
    if (!this.synth) return
    this.refreshVoices()
    if (typeof this.synth.addEventListener === 'function') {
      this.synth.addEventListener('voiceschanged', () => this.refreshVoices())
    } else {
      this.synth.onvoiceschanged = () => this.refreshVoices()
    }
  }

  private refreshVoices(): void {
    const list = this.synth?.getVoices() ?? []
    if (list.length) this.voices = list
  }

  get available(): boolean {
    return this.synth !== null
  }

  /** Best voice for a BCP-47 tag: exact match, then region variant, then base language. */
  private pickVoice(lang: string): SpeechSynthesisVoice | undefined {
    if (!this.voices.length) this.refreshVoices()
    const target = lang.toLowerCase().replace('_', '-')
    const base = target.slice(0, 2)
    const norm = (v: SpeechSynthesisVoice) => v.lang.toLowerCase().replace('_', '-')
    return (
      this.voices.find((v) => norm(v) === target) ??
      this.voices.find((v) => norm(v).startsWith(`${base}-`)) ??
      this.voices.find((v) => norm(v) === base)
    )
  }

  speak(text: string, lang = currentSpeechLang): void {
    if (!this.synth || !text.trim()) return
    this.synth.cancel()
    const utter = new SpeechSynthesisUtterance(text)
    utter.lang = lang

    const voice = this.pickVoice(lang)
    if (voice) {
      utter.voice = voice
      this.synth.speak(utter)
      return
    }

    // No matching voice yet. If the list simply hasn't loaded, wait once for it so
    // we can attach the right-language voice instead of using the OS default.
    if (!this.voices.length && typeof this.synth.addEventListener === 'function') {
      const synth = this.synth
      let done = false
      const finish = () => {
        if (done) return
        done = true
        synth.removeEventListener('voiceschanged', finish)
        this.refreshVoices()
        const v = this.pickVoice(lang)
        if (v) utter.voice = v
        synth.speak(utter)
      }
      synth.addEventListener('voiceschanged', finish)
      // Safety net if the event never fires (some browsers preload voices).
      window.setTimeout(finish, 300)
      return
    }

    // Voices are loaded but none matches this language (not installed on the OS):
    // still set utter.lang so the engine picks the closest available match.
    this.synth.speak(utter)
  }

  cancel(): void {
    this.synth?.cancel()
  }
}

/**
 * Speaks by fetching WAV audio from the backend (espeak-ng in the target
 * language) and playing it. Falls back to the browser's Web Speech API when the
 * backend audio endpoint is unavailable (e.g. the `phonetics` extra isn't
 * installed) or a request fails — and remembers that so it stops retrying.
 */
class BackendSpeechProvider implements SpeechProvider {
  private fallback = new WebSpeechProvider()
  // Cache object URLs by `${lang}|${text}` so repeated plays are instant.
  private cache = new Map<string, string>()
  private audio: HTMLAudioElement | null = null
  // null = untried, true = backend works, false = backend down (use fallback).
  private backendOk: boolean | null = null

  get available(): boolean {
    // Backend audio may work; the Web Speech fallback covers the rest.
    return this.backendOk === true || this.fallback.available
  }

  speak(text: string, lang = currentSpeechLang): void {
    const clean = text.trim()
    if (!clean) return
    if (this.backendOk === false) {
      this.fallback.speak(clean, lang)
      return
    }
    void this.playBackend(clean, lang)
  }

  private async playBackend(text: string, lang: string): Promise<void> {
    const key = `${lang}|${text}`
    try {
      let url = this.cache.get(key)
      if (!url) {
        const params = new URLSearchParams({ word: text, lang: lang.slice(0, 2) })
        const resp = await fetch(`${API_BASE}/pronunciation/audio?${params.toString()}`)
        if (!resp.ok) throw new Error(`tts ${resp.status}`)
        url = URL.createObjectURL(await resp.blob())
        this.cache.set(key, url)
      }
      this.backendOk = true
      this.cancel()
      this.audio = new Audio(url)
      await this.audio.play()
    } catch {
      // Backend TTS isn't usable here — switch to the browser voice from now on.
      if (this.backendOk !== true) this.backendOk = false
      this.fallback.speak(text, lang)
    }
  }

  cancel(): void {
    if (this.audio) {
      this.audio.pause()
      this.audio = null
    }
    this.fallback.cancel()
  }
}

let instance: SpeechProvider | null = null

export function getSpeech(): SpeechProvider {
  if (instance) return instance
  const mode = (import.meta.env.VITE_TTS_MODE as string) || 'backend'
  switch (mode) {
    case 'webspeech':
      instance = new WebSpeechProvider()
      break
    default:
      instance = new BackendSpeechProvider()
  }
  return instance
}
