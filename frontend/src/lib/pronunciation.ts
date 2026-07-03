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

  get available(): boolean {
    return this.synth !== null
  }

  private pickVoice(lang: string): SpeechSynthesisVoice | undefined {
    const voices = this.synth?.getVoices() ?? []
    const target = lang.toLowerCase()
    const prefix = target.slice(0, 2)
    return (
      voices.find((v) => v.lang.toLowerCase() === target) ??
      voices.find((v) => v.lang.toLowerCase().startsWith(prefix))
    )
  }

  speak(text: string, lang = currentSpeechLang): void {
    if (!this.synth || !text.trim()) return
    this.synth.cancel()
    const utter = new SpeechSynthesisUtterance(text)
    utter.lang = lang
    const voice = this.pickVoice(lang)
    if (voice) utter.voice = voice
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
