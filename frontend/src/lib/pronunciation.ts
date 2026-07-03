/**
 * Pronunciation (text-to-speech) provider seam.
 *
 * Today this uses the browser's built-in Web Speech API — offline, free, and
 * backed by the German voices installed on the user's OS. The `SpeechProvider`
 * interface plus the `getSpeech()` factory keep call sites decoupled from the
 * implementation, so a higher-quality backend voice (e.g. a local Piper TTS
 * endpoint) can be swapped in later by setting `VITE_TTS_MODE=backend` and
 * implementing `BackendSpeechProvider` — with no changes at the call sites.
 */

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
 * Placeholder for a future backend voice (e.g. Piper TTS served from FastAPI).
 * Prepared but intentionally not wired: selecting it means implementing `speak()`
 * to fetch `${VITE_API_BASE}/pronunciation/audio?word=…` and play the returned
 * audio, then enabling the `'backend'` branch in `getSpeech()` below.
 */
// class BackendSpeechProvider implements SpeechProvider { /* … */ }

let instance: SpeechProvider | null = null

export function getSpeech(): SpeechProvider {
  if (instance) return instance
  const mode = (import.meta.env.VITE_TTS_MODE as string) || 'webspeech'
  switch (mode) {
    // case 'backend':
    //   instance = new BackendSpeechProvider()
    //   break
    default:
      instance = new WebSpeechProvider()
  }
  return instance
}
