/**
 * Bundled conjugation tables for the most common verbs, so they are available
 * offline in the conjugation "Seen verbs" list from the very first render — no
 * LLM call needed. Data is authored compactly (present + past forms; the
 * compound perfect and the future are derived from the auxiliary paradigms) and
 * expanded into full `ConjugationTable`s by the builders below.
 *
 * Covers the currently-available target languages (German, Spanish). Languages
 * without a bundle here fall back to on-demand LLM conjugation (see the store).
 */
import type { ConjugationTable, ConjugationTense } from '../../lib/types'

const DE_PERSONS = ['ich', 'du', 'er/sie/es', 'wir', 'ihr', 'sie/Sie']
const ES_PERSONS = ['yo', 'tú', 'él/ella/usted', 'nosotros', 'vosotros', 'ellos/ellas/ustedes']

const DE_HABEN = ['habe', 'hast', 'hat', 'haben', 'habt', 'haben']
const DE_SEIN = ['bin', 'bist', 'ist', 'sind', 'seid', 'sind']
const DE_WERDEN = ['werde', 'wirst', 'wird', 'werden', 'werdet', 'werden']
const ES_HABER = ['he', 'has', 'ha', 'hemos', 'habéis', 'han']

function mkTense(name: string, persons: string[], forms: string[]): ConjugationTense {
  return { name, note: '', cells: persons.map((label, i) => ({ label, form: forms[i] ?? '' })) }
}

interface DeVerb {
  inf: string
  en: string
  aux: 'haben' | 'sein'
  pii: string
  regular: boolean
  praesens: string[]
  praeteritum: string[]
}

function buildDe(v: DeVerb): ConjugationTable {
  const auxForms = v.aux === 'sein' ? DE_SEIN : DE_HABEN
  return {
    infinitive: v.inf,
    language: 'de',
    english: v.en,
    regular: v.regular,
    notes: '',
    auxiliary: v.aux,
    partizip_ii: v.pii,
    tenses: [
      mkTense('Präsens', DE_PERSONS, v.praesens),
      mkTense('Präteritum', DE_PERSONS, v.praeteritum),
      mkTense(
        'Perfekt',
        DE_PERSONS,
        auxForms.map((a) => `${a} ${v.pii}`),
      ),
      mkTense(
        'Futur I',
        DE_PERSONS,
        DE_WERDEN.map((w) => `${w} ${v.inf}`),
      ),
    ],
  }
}

interface EsVerb {
  inf: string
  en: string
  pii: string
  regular: boolean
  presente: string[]
  indefinido: string[]
  futuro: string[]
}

function buildEs(v: EsVerb): ConjugationTable {
  return {
    infinitive: v.inf,
    language: 'es',
    english: v.en,
    regular: v.regular,
    notes: '',
    auxiliary: 'haber',
    partizip_ii: v.pii,
    tenses: [
      mkTense('Presente', ES_PERSONS, v.presente),
      mkTense('Pretérito indefinido', ES_PERSONS, v.indefinido),
      mkTense(
        'Pretérito perfecto',
        ES_PERSONS,
        ES_HABER.map((h) => `${h} ${v.pii}`),
      ),
      mkTense('Futuro', ES_PERSONS, v.futuro),
    ],
  }
}

// prettier-ignore
const DE: DeVerb[] = [
  { inf: 'sein', en: 'to be', aux: 'sein', pii: 'gewesen', regular: false,
    praesens: ['bin', 'bist', 'ist', 'sind', 'seid', 'sind'],
    praeteritum: ['war', 'warst', 'war', 'waren', 'wart', 'waren'] },
  { inf: 'haben', en: 'to have', aux: 'haben', pii: 'gehabt', regular: false,
    praesens: ['habe', 'hast', 'hat', 'haben', 'habt', 'haben'],
    praeteritum: ['hatte', 'hattest', 'hatte', 'hatten', 'hattet', 'hatten'] },
  { inf: 'werden', en: 'to become', aux: 'sein', pii: 'geworden', regular: false,
    praesens: ['werde', 'wirst', 'wird', 'werden', 'werdet', 'werden'],
    praeteritum: ['wurde', 'wurdest', 'wurde', 'wurden', 'wurdet', 'wurden'] },
  { inf: 'können', en: 'can, to be able to', aux: 'haben', pii: 'gekonnt', regular: false,
    praesens: ['kann', 'kannst', 'kann', 'können', 'könnt', 'können'],
    praeteritum: ['konnte', 'konntest', 'konnte', 'konnten', 'konntet', 'konnten'] },
  { inf: 'müssen', en: 'must, to have to', aux: 'haben', pii: 'gemusst', regular: false,
    praesens: ['muss', 'musst', 'muss', 'müssen', 'müsst', 'müssen'],
    praeteritum: ['musste', 'musstest', 'musste', 'mussten', 'musstet', 'mussten'] },
  { inf: 'sagen', en: 'to say', aux: 'haben', pii: 'gesagt', regular: true,
    praesens: ['sage', 'sagst', 'sagt', 'sagen', 'sagt', 'sagen'],
    praeteritum: ['sagte', 'sagtest', 'sagte', 'sagten', 'sagtet', 'sagten'] },
  { inf: 'machen', en: 'to do, to make', aux: 'haben', pii: 'gemacht', regular: true,
    praesens: ['mache', 'machst', 'macht', 'machen', 'macht', 'machen'],
    praeteritum: ['machte', 'machtest', 'machte', 'machten', 'machtet', 'machten'] },
  { inf: 'geben', en: 'to give', aux: 'haben', pii: 'gegeben', regular: false,
    praesens: ['gebe', 'gibst', 'gibt', 'geben', 'gebt', 'geben'],
    praeteritum: ['gab', 'gabst', 'gab', 'gaben', 'gabt', 'gaben'] },
  { inf: 'kommen', en: 'to come', aux: 'sein', pii: 'gekommen', regular: false,
    praesens: ['komme', 'kommst', 'kommt', 'kommen', 'kommt', 'kommen'],
    praeteritum: ['kam', 'kamst', 'kam', 'kamen', 'kamt', 'kamen'] },
  { inf: 'sollen', en: 'should, to be supposed to', aux: 'haben', pii: 'gesollt', regular: false,
    praesens: ['soll', 'sollst', 'soll', 'sollen', 'sollt', 'sollen'],
    praeteritum: ['sollte', 'solltest', 'sollte', 'sollten', 'solltet', 'sollten'] },
  { inf: 'wollen', en: 'to want', aux: 'haben', pii: 'gewollt', regular: false,
    praesens: ['will', 'willst', 'will', 'wollen', 'wollt', 'wollen'],
    praeteritum: ['wollte', 'wolltest', 'wollte', 'wollten', 'wolltet', 'wollten'] },
  { inf: 'gehen', en: 'to go', aux: 'sein', pii: 'gegangen', regular: false,
    praesens: ['gehe', 'gehst', 'geht', 'gehen', 'geht', 'gehen'],
    praeteritum: ['ging', 'gingst', 'ging', 'gingen', 'gingt', 'gingen'] },
  { inf: 'wissen', en: 'to know', aux: 'haben', pii: 'gewusst', regular: false,
    praesens: ['weiß', 'weißt', 'weiß', 'wissen', 'wisst', 'wissen'],
    praeteritum: ['wusste', 'wusstest', 'wusste', 'wussten', 'wusstet', 'wussten'] },
  { inf: 'sehen', en: 'to see', aux: 'haben', pii: 'gesehen', regular: false,
    praesens: ['sehe', 'siehst', 'sieht', 'sehen', 'seht', 'sehen'],
    praeteritum: ['sah', 'sahst', 'sah', 'sahen', 'saht', 'sahen'] },
  { inf: 'lassen', en: 'to let, to leave', aux: 'haben', pii: 'gelassen', regular: false,
    praesens: ['lasse', 'lässt', 'lässt', 'lassen', 'lasst', 'lassen'],
    praeteritum: ['ließ', 'ließest', 'ließ', 'ließen', 'ließt', 'ließen'] },
  { inf: 'stehen', en: 'to stand', aux: 'haben', pii: 'gestanden', regular: false,
    praesens: ['stehe', 'stehst', 'steht', 'stehen', 'steht', 'stehen'],
    praeteritum: ['stand', 'standest', 'stand', 'standen', 'standet', 'standen'] },
  { inf: 'finden', en: 'to find', aux: 'haben', pii: 'gefunden', regular: false,
    praesens: ['finde', 'findest', 'findet', 'finden', 'findet', 'finden'],
    praeteritum: ['fand', 'fandest', 'fand', 'fanden', 'fandet', 'fanden'] },
  { inf: 'bleiben', en: 'to stay, to remain', aux: 'sein', pii: 'geblieben', regular: false,
    praesens: ['bleibe', 'bleibst', 'bleibt', 'bleiben', 'bleibt', 'bleiben'],
    praeteritum: ['blieb', 'bliebst', 'blieb', 'blieben', 'bliebt', 'blieben'] },
  { inf: 'nehmen', en: 'to take', aux: 'haben', pii: 'genommen', regular: false,
    praesens: ['nehme', 'nimmst', 'nimmt', 'nehmen', 'nehmt', 'nehmen'],
    praeteritum: ['nahm', 'nahmst', 'nahm', 'nahmen', 'nahmt', 'nahmen'] },
  { inf: 'heißen', en: 'to be called', aux: 'haben', pii: 'geheißen', regular: false,
    praesens: ['heiße', 'heißt', 'heißt', 'heißen', 'heißt', 'heißen'],
    praeteritum: ['hieß', 'hießest', 'hieß', 'hießen', 'hießt', 'hießen'] },
]

// prettier-ignore
const ES: EsVerb[] = [
  { inf: 'ser', en: 'to be', pii: 'sido', regular: false,
    presente: ['soy', 'eres', 'es', 'somos', 'sois', 'son'],
    indefinido: ['fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron'],
    futuro: ['seré', 'serás', 'será', 'seremos', 'seréis', 'serán'] },
  { inf: 'haber', en: 'to have (auxiliary)', pii: 'habido', regular: false,
    presente: ['he', 'has', 'ha', 'hemos', 'habéis', 'han'],
    indefinido: ['hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron'],
    futuro: ['habré', 'habrás', 'habrá', 'habremos', 'habréis', 'habrán'] },
  { inf: 'estar', en: 'to be', pii: 'estado', regular: false,
    presente: ['estoy', 'estás', 'está', 'estamos', 'estáis', 'están'],
    indefinido: ['estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron'],
    futuro: ['estaré', 'estarás', 'estará', 'estaremos', 'estaréis', 'estarán'] },
  { inf: 'tener', en: 'to have', pii: 'tenido', regular: false,
    presente: ['tengo', 'tienes', 'tiene', 'tenemos', 'tenéis', 'tienen'],
    indefinido: ['tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvisteis', 'tuvieron'],
    futuro: ['tendré', 'tendrás', 'tendrá', 'tendremos', 'tendréis', 'tendrán'] },
  { inf: 'hacer', en: 'to do, to make', pii: 'hecho', regular: false,
    presente: ['hago', 'haces', 'hace', 'hacemos', 'hacéis', 'hacen'],
    indefinido: ['hice', 'hiciste', 'hizo', 'hicimos', 'hicisteis', 'hicieron'],
    futuro: ['haré', 'harás', 'hará', 'haremos', 'haréis', 'harán'] },
  { inf: 'poder', en: 'can, to be able to', pii: 'podido', regular: false,
    presente: ['puedo', 'puedes', 'puede', 'podemos', 'podéis', 'pueden'],
    indefinido: ['pude', 'pudiste', 'pudo', 'pudimos', 'pudisteis', 'pudieron'],
    futuro: ['podré', 'podrás', 'podrá', 'podremos', 'podréis', 'podrán'] },
  { inf: 'decir', en: 'to say, to tell', pii: 'dicho', regular: false,
    presente: ['digo', 'dices', 'dice', 'decimos', 'decís', 'dicen'],
    indefinido: ['dije', 'dijiste', 'dijo', 'dijimos', 'dijisteis', 'dijeron'],
    futuro: ['diré', 'dirás', 'dirá', 'diremos', 'diréis', 'dirán'] },
  { inf: 'ir', en: 'to go', pii: 'ido', regular: false,
    presente: ['voy', 'vas', 'va', 'vamos', 'vais', 'van'],
    indefinido: ['fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron'],
    futuro: ['iré', 'irás', 'irá', 'iremos', 'iréis', 'irán'] },
  { inf: 'ver', en: 'to see', pii: 'visto', regular: false,
    presente: ['veo', 'ves', 've', 'vemos', 'veis', 'ven'],
    indefinido: ['vi', 'viste', 'vio', 'vimos', 'visteis', 'vieron'],
    futuro: ['veré', 'verás', 'verá', 'veremos', 'veréis', 'verán'] },
  { inf: 'dar', en: 'to give', pii: 'dado', regular: false,
    presente: ['doy', 'das', 'da', 'damos', 'dais', 'dan'],
    indefinido: ['di', 'diste', 'dio', 'dimos', 'disteis', 'dieron'],
    futuro: ['daré', 'darás', 'dará', 'daremos', 'daréis', 'darán'] },
  { inf: 'saber', en: 'to know', pii: 'sabido', regular: false,
    presente: ['sé', 'sabes', 'sabe', 'sabemos', 'sabéis', 'saben'],
    indefinido: ['supe', 'supiste', 'supo', 'supimos', 'supisteis', 'supieron'],
    futuro: ['sabré', 'sabrás', 'sabrá', 'sabremos', 'sabréis', 'sabrán'] },
  { inf: 'querer', en: 'to want, to love', pii: 'querido', regular: false,
    presente: ['quiero', 'quieres', 'quiere', 'queremos', 'queréis', 'quieren'],
    indefinido: ['quise', 'quisiste', 'quiso', 'quisimos', 'quisisteis', 'quisieron'],
    futuro: ['querré', 'querrás', 'querrá', 'querremos', 'querréis', 'querrán'] },
  { inf: 'llegar', en: 'to arrive', pii: 'llegado', regular: true,
    presente: ['llego', 'llegas', 'llega', 'llegamos', 'llegáis', 'llegan'],
    indefinido: ['llegué', 'llegaste', 'llegó', 'llegamos', 'llegasteis', 'llegaron'],
    futuro: ['llegaré', 'llegarás', 'llegará', 'llegaremos', 'llegaréis', 'llegarán'] },
  { inf: 'pasar', en: 'to pass, to happen', pii: 'pasado', regular: true,
    presente: ['paso', 'pasas', 'pasa', 'pasamos', 'pasáis', 'pasan'],
    indefinido: ['pasé', 'pasaste', 'pasó', 'pasamos', 'pasasteis', 'pasaron'],
    futuro: ['pasaré', 'pasarás', 'pasará', 'pasaremos', 'pasaréis', 'pasarán'] },
  { inf: 'deber', en: 'must, to owe', pii: 'debido', regular: true,
    presente: ['debo', 'debes', 'debe', 'debemos', 'debéis', 'deben'],
    indefinido: ['debí', 'debiste', 'debió', 'debimos', 'debisteis', 'debieron'],
    futuro: ['deberé', 'deberás', 'deberá', 'deberemos', 'deberéis', 'deberán'] },
  { inf: 'poner', en: 'to put', pii: 'puesto', regular: false,
    presente: ['pongo', 'pones', 'pone', 'ponemos', 'ponéis', 'ponen'],
    indefinido: ['puse', 'pusiste', 'puso', 'pusimos', 'pusisteis', 'pusieron'],
    futuro: ['pondré', 'pondrás', 'pondrá', 'pondremos', 'pondréis', 'pondrán'] },
  { inf: 'parecer', en: 'to seem', pii: 'parecido', regular: false,
    presente: ['parezco', 'pareces', 'parece', 'parecemos', 'parecéis', 'parecen'],
    indefinido: ['parecí', 'pareciste', 'pareció', 'parecimos', 'parecisteis', 'parecieron'],
    futuro: ['pareceré', 'parecerás', 'parecerá', 'pareceremos', 'pareceréis', 'parecerán'] },
  { inf: 'quedar', en: 'to stay, to remain', pii: 'quedado', regular: true,
    presente: ['quedo', 'quedas', 'queda', 'quedamos', 'quedáis', 'quedan'],
    indefinido: ['quedé', 'quedaste', 'quedó', 'quedamos', 'quedasteis', 'quedaron'],
    futuro: ['quedaré', 'quedarás', 'quedará', 'quedaremos', 'quedaréis', 'quedarán'] },
  { inf: 'creer', en: 'to believe', pii: 'creído', regular: false,
    presente: ['creo', 'crees', 'cree', 'creemos', 'creéis', 'creen'],
    indefinido: ['creí', 'creíste', 'creyó', 'creímos', 'creísteis', 'creyeron'],
    futuro: ['creeré', 'creerás', 'creerá', 'creeremos', 'creeréis', 'creerán'] },
  { inf: 'hablar', en: 'to speak, to talk', pii: 'hablado', regular: true,
    presente: ['hablo', 'hablas', 'habla', 'hablamos', 'habláis', 'hablan'],
    indefinido: ['hablé', 'hablaste', 'habló', 'hablamos', 'hablasteis', 'hablaron'],
    futuro: ['hablaré', 'hablarás', 'hablará', 'hablaremos', 'hablaréis', 'hablarán'] },
]

export const COMMON_CONJUGATIONS: Record<string, ConjugationTable[]> = {
  de: DE.map(buildDe),
  es: ES.map(buildEs),
}
