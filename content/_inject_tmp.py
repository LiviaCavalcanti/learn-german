import json
import re
from pathlib import Path

PATH = Path("content/de/course.json")
text = PATH.read_text(encoding="utf-8")


def fib(instr, prompt, answer):
    return {
        "type": "fill-in-blank",
        "instructions": instr,
        "payload": {"items": [{"prompt": prompt}], "hints": []},
        "answer_key": {"items": [{"answer": answer}]},
    }


def conj(instr, prompt, answer):
    return {
        "type": "conjugation",
        "instructions": instr,
        "payload": {"items": [{"prompt": prompt}], "hints": []},
        "answer_key": {"items": [{"answer": answer}]},
    }


def mc(instr, prompt, options, answer):
    return {
        "type": "multiple-choice",
        "instructions": instr,
        "payload": {"items": [{"prompt": prompt, "options": options}], "hints": []},
        "answer_key": {"items": [{"answer": answer}]},
    }


def reo(instr, tokens, answer):
    return {
        "type": "reorder",
        "instructions": instr,
        "payload": {"items": [{"tokens": tokens}], "hints": []},
        "answer_key": {"items": [{"answer": answer}]},
    }


def q(prompt, translation, reference):
    return {"prompt": prompt, "translation": translation, "reference": reference}


story_adjprep = (
    "Am Ende eines Jahres denke ich gern über meine Gefühle und Einstellungen nach. "
    "Wofür bin ich dankbar? Worauf bin ich stolz? Womit bin ich zufrieden? Um solche "
    "Fragen zu beantworten, braucht man Adjektive mit festen Präpositionen. Jedes "
    "Adjektiv verlangt eine bestimmte Präposition, und die muss man einfach lernen.\n\n"
    "Zuerst zu meiner Arbeit. Ich bin sehr stolz auf mein Team. Wir haben in diesem "
    "Jahr viel erreicht, und ich bin zufrieden mit dem Ergebnis. Natürlich war nicht "
    "alles perfekt, aber ich bin überzeugt von unserem Weg. Für die gute Zusammenarbeit "
    "bin ich meinen Kollegen sehr dankbar.\n\n"
    "Ich bin auch sehr interessiert an neuen Technologien. Die Entwicklung geht schnell, "
    "und ich bin gespannt auf die Zukunft. Manchmal bin ich ein bisschen besorgt über "
    "die Risiken, aber insgesamt bin ich optimistisch. Ich bin fest davon überzeugt, "
    "dass wir viele Chancen haben, wenn wir offen bleiben.\n\n"
    "In meinem Beruf bin ich verantwortlich für ein kleines Team. Das bedeutet viel "
    "Verantwortung, aber ich bin stolz darauf. Meine Kollegen sind auf meine "
    "Unterstützung angewiesen, und ich bin froh über ihr Vertrauen. Gleichzeitig bin "
    "ich abhängig von ihrer Arbeit, denn allein könnte ich nichts erreichen.\n\n"
    "Auch privat gibt es viel, wofür ich dankbar bin. Ich bin froh über meine Familie "
    "und meine Freunde. Ich bin sehr zufrieden mit meinem Leben, auch wenn nicht immer "
    "alles leicht ist. Manchmal bin ich traurig über Dinge, die ich nicht ändern kann. "
    "Aber ich versuche, das Positive zu sehen.\n\n"
    "Meine Freundin ist bekannt für ihre gute Laune. Ich bin wirklich verliebt in ihren "
    "Optimismus. Wir sind beide begeistert von Reisen und neugierig auf fremde "
    "Kulturen. Natürlich ärgere ich mich manchmal über Kleinigkeiten, aber am Ende sind "
    "wir stolz auf das, was wir zusammen aufgebaut haben.\n\n"
    "Es gibt auch Dinge, mit denen ich unzufrieden bin. Ich bin manchmal enttäuscht von "
    "mir selbst, wenn ich meine Ziele nicht erreiche. Ich bin auch nicht immer "
    "zufrieden mit meiner Disziplin. Aber ich bin überzeugt davon, dass man aus Fehlern "
    "lernen kann. Deshalb bleibe ich hoffnungsvoll.\n\n"
    "Wenn ich in die Zukunft blicke, bin ich voller Erwartung. Ich bin gespannt auf "
    "neue Aufgaben und offen für Veränderungen. Ich bin bereit für neue "
    "Herausforderungen und interessiert an allem, was kommt. Und ich bin dankbar für "
    "jede Erfahrung, ob gut oder schlecht.\n\n"
    "Auch für meine Gesundheit bin ich dankbar. Ich achte auf meinen Körper und bin "
    "stolz auf meine Fortschritte beim Sport. Manchmal bin ich böse auf mich, wenn ich "
    "faul bin, aber meistens bin ich zufrieden mit meiner Routine. Ich bin überzeugt "
    "davon, dass ein gesundes Leben glücklich macht.\n\n"
    "Solche Adjektive mit Präpositionen brauche ich jeden Tag, um meine Einstellungen "
    "auszudrücken. Ich bin stolz auf etwas, zufrieden mit etwas, interessiert an etwas. "
    "Am Ende eines Jahres merke ich: Meine Gefühle sind vielfältig, aber vor allem bin "
    "ich dankbar für ein reiches und spannendes Leben.\n\n"
    "Viele Adjektive haben eine feste Präposition. „Stolz“ steht mit „auf“, „zufrieden“ "
    "mit „mit“, „interessiert“ mit „an“, „froh“ und „begeistert“ mit „über“. Man kann "
    "die Präposition nicht raten, sondern muss sie zusammen mit dem Adjektiv lernen. "
    "Für Sachen benutzt man oft ein da-Wort: Ich bin stolz darauf. So drückt man "
    "Meinungen und Gefühle präzise aus."
)

story_wordorder = (
    "Im Deutschen ist die Wortstellung flexibler, als viele denken. Das Verb steht zwar "
    "meistens an zweiter Stelle, aber am Anfang kann fast jedes Satzglied stehen. Was am "
    "Anfang steht, wird betont. Mit dieser Technik kann man genau das hervorheben, was "
    "einem wichtig ist. Heute erzähle ich von einem Tag, an dem die Betonung eine große "
    "Rolle spielte.\n\n"
    "Am Morgen entdeckte ich ein Problem im Programm. „Diesen Fehler habe ich noch nie "
    "gesehen“, sagte ich erstaunt. Normalerweise würde man sagen: „Ich habe diesen "
    "Fehler noch nie gesehen.“ Aber indem ich „diesen Fehler“ an den Anfang stellte, "
    "betonte ich genau das Problem. So merkten alle sofort, wie ungewöhnlich die "
    "Situation war.\n\n"
    "Mein Chef kam dazu und fragte, wann das passiert sei. „Gestern erst wurde das "
    "Update veröffentlicht“, erklärte ich. Das Wort „gestern“ stand am Anfang, weil die "
    "Zeit hier besonders wichtig war. Das Update war also ganz neu. Hätte ich gesagt "
    "„Das Update wurde gestern veröffentlicht“, wäre die Betonung schwächer gewesen.\n\n"
    "Dann suchten wir nach der Ursache. Einige Kollegen dachten, das Team hätte einen "
    "Fehler gemacht. Doch ich widersprach: „Nicht das Team ist schuld, sondern der "
    "Zeitplan.“ Mit dieser Struktur stellte ich klar, wer wirklich verantwortlich war. "
    "„Nicht … sondern“ hebt den Gegensatz besonders deutlich hervor. Alle verstanden "
    "sofort meinen Punkt.\n\n"
    "Die Stimmung war ein bisschen angespannt. „Gerade jetzt brauchen wir Ruhe“, sagte "
    "ich. Indem ich „gerade jetzt“ betonte, machte ich klar, dass der Moment "
    "entscheidend war. In stressigen Situationen ist die richtige Betonung sehr "
    "wichtig, denn sie lenkt die Aufmerksamkeit auf das Wesentliche.\n\n"
    "Am Mittag präsentierte ich meine Lösung. „Diese Methode habe ich schon oft "
    "benutzt“, sagte ich selbstbewusst. Das Objekt am Anfang zeigte, dass ich Erfahrung "
    "hatte. Meine Kollegen waren überzeugt. „Genau so machen wir das“, sagte mein Chef. "
    "Auch er betonte das Wichtigste, indem er „genau so“ an den Anfang stellte.\n\n"
    "Am Nachmittag ging alles besser. „Ohne eure Hilfe hätte ich das nie geschafft“, "
    "sagte ich dankbar zu meinem Team. Indem ich „ohne eure Hilfe“ betonte, zeigte ich, "
    "wie wichtig die Zusammenarbeit war. Solche kleinen Umstellungen im Satz können viel "
    "Wärme und Bedeutung ausdrücken.\n\n"
    "Auch in Besprechungen ist die Betonung nützlich. „Diesen Vorschlag finde ich gut“, "
    "sagte eine Kollegin und stellte damit ihre Zustimmung an den Anfang. Ein anderer "
    "meinte: „Genau darüber müssen wir reden.“ So lenkt jeder die Aufmerksamkeit auf "
    "das, was ihm am wichtigsten ist.\n\n"
    "Sogar in E-Mails achte ich auf die Betonung. „Bis Freitag brauche ich die Zahlen“, "
    "schreibe ich, wenn der Termin wichtig ist. So sieht der Leser sofort, worauf es "
    "ankommt.\n\n"
    "Am Abend dachte ich über den Tag nach. „Viel gelernt habe ich heute“, sagte ich "
    "mir. Die Betonung lag auf dem, was ich gewonnen hatte. Es war kein leichter Tag, "
    "aber gerade solche Tage machen einen besser. Am Ende war ich zufrieden mit mir und "
    "meinem Team.\n\n"
    "Die Wortstellung im Deutschen dient oft der Betonung. Das Verb bleibt an zweiter "
    "Stelle, aber davor kann man das wichtigste Satzglied stellen: das Objekt, eine "
    "Zeitangabe oder einen ganzen Nebensatz. „Diesen Fehler habe ich noch nie gesehen“ "
    "betont den Fehler. Mit „nicht … sondern“ hebt man einen Gegensatz hervor. So lenkt "
    "man die Aufmerksamkeit gezielt auf das, was zählt. Wer die Wortstellung bewusst "
    "einsetzt, wirkt sicher und überzeugend."
)

story_idioms = (
    "Die deutsche Sprache steckt voller fester Wendungen und Redewendungen. Manche kann "
    "man wörtlich verstehen, andere haben eine bildliche Bedeutung. Wer sie kennt, "
    "klingt viel natürlicher und drückt sich lebendiger aus. Heute erzähle ich von "
    "einer Woche im Büro, in der ich viele solcher Wendungen benutzt habe.\n\n"
    "Am Montag mussten wir eine wichtige Entscheidung treffen. Ein neues Projekt stand "
    "an, und wir wollten es sofort in Angriff nehmen. „Wir dürfen das nicht auf die "
    "lange Bank schieben“, sagte mein Chef. „Am Ende des Tages zählt nur das "
    "Ergebnis.“ Also machten wir uns gleich an die Arbeit.\n\n"
    "Am Dienstag gab es ein Problem. Ein Kollege verlor fast den Kopf, weil ein Termin "
    "näher rückte. „Bleib ruhig“, sagte ich. „Wir kriegen das hin.“ Gemeinsam behielten "
    "wir den Überblick. Zum Glück fiel unser Plan nicht ins Wasser, sondern wir fanden "
    "rechtzeitig eine Lösung.\n\n"
    "Am Mittwoch stellte jemand eine schlechte Idee vor. „Das kommt überhaupt nicht in "
    "Frage“, sagte mein Chef sofort. Er nahm kein Blatt vor den Mund. Trotzdem blieb "
    "die Stimmung gut, denn wir konnten offen miteinander reden. „Du hast den Nagel auf "
    "den Kopf getroffen“, sagte ich später zu einer Kollegin, die den Kern des Problems "
    "erkannt hatte.\n\n"
    "Am Donnerstag hatte eine Kollegin eine Prüfung. „Ich drücke dir die Daumen“, sagte "
    "ich ihr am Morgen. Sie war sehr nervös, aber am Ende lief alles gut. „Ich bin dir "
    "wirklich dankbar“, sagte sie später. „Deine Worte haben mir Mut gemacht.“ So "
    "halten wir im Team immer zusammen.\n\n"
    "Am Freitag zogen wir Bilanz. „Diese Woche haben wir viel geschafft“, sagte mein "
    "Chef. „Wir haben das Projekt gut in Gang gebracht.“ Ich hielt alle auf dem "
    "Laufenden, damit niemand den Überblick verlor. „Ende gut, alles gut“, sagte ein "
    "Kollege und lachte. Alle waren zufrieden.\n\n"
    "Natürlich sind solche Redewendungen für Lernende nicht leicht. Man kann sie nicht "
    "Wort für Wort übersetzen. „Jemandem die Daumen drücken“ bedeutet nicht wirklich, "
    "dass man die Daumen drückt, sondern dass man ihm Glück wünscht. Solche Bilder muss "
    "man einfach lernen und im richtigen Moment benutzen.\n\n"
    "Manche Redewendungen haben interessante Geschichten. „Tomaten auf den Augen haben“ "
    "bedeutet, dass man etwas Offensichtliches nicht sieht. „Die Katze im Sack kaufen“ "
    "heißt, etwas zu kaufen, ohne es geprüft zu haben. Solche Bilder machen die Sprache "
    "bunt und machen beim Lernen richtig Spaß.\n\n"
    "Ich sammle solche Ausdrücke in einem kleinen Heft. Wenn ich einen neuen höre, "
    "schreibe ich ihn sofort auf. „Übung macht den Meister“, sage ich mir immer. Und "
    "tatsächlich: Je mehr ich sie benutze, desto natürlicher klingen sie. Manchmal "
    "bringe ich sogar meine deutschen Kollegen zum Lachen, wenn ich eine passende "
    "Redewendung finde.\n\n"
    "Am Wochenende dachte ich über die Woche nach. Ich hatte viele Wendungen benutzt, "
    "ohne groß nachzudenken. Genau das ist das Ziel: dass die Redewendungen zur zweiten "
    "Natur werden. Wer sie sicher beherrscht, fühlt sich in der Sprache wirklich zu "
    "Hause. Und am Ende des Tages zählt genau das.\n\n"
    "Kollokationen sind feste Wortverbindungen, die man so und nicht anders benutzt: "
    "„eine Entscheidung treffen“, „ein Projekt in Angriff nehmen“. Redewendungen sind "
    "bildliche Ausdrücke: „die Daumen drücken“, „den Nagel auf den Kopf treffen“. Beide "
    "gehören zu einer natürlichen Sprache. Man lernt sie am besten, indem man viel "
    "liest, zuhört und sie dann selbst ausprobiert. Mit der Zeit gehen sie einem in "
    "Fleisch und Blut über."
)

story_cohesion = (
    "Sehr geehrte Damen und Herren,\n\n"
    "hiermit möchte ich Ihnen einen Überblick über das abgeschlossene Projekt geben. Im "
    "Folgenden fasse ich die wichtigsten Ergebnisse zusammen und gehe auf einige offene "
    "Punkte ein. Ich hoffe, dass dieser Bericht alle Ihre Fragen beantwortet.\n\n"
    "Zunächst freut es mich, Ihnen mitteilen zu können, dass das Projekt erfolgreich "
    "abgeschlossen wurde. Die Zusammenarbeit zwischen den Abteilungen verlief "
    "reibungslos. Einerseits konnten wir den Zeitplan einhalten, andererseits blieben "
    "wir sogar unter dem geplanten Budget. Insgesamt sind wir mit dem Ergebnis sehr "
    "zufrieden.\n\n"
    "Im Verlauf des Projekts gab es natürlich auch Herausforderungen. Zunächst mussten "
    "wir einige technische Probleme lösen. Zudem war die Abstimmung mit den externen "
    "Partnern anfangs schwierig. Dennoch fanden wir für jedes Problem eine Lösung. "
    "Folglich konnten wir alle Ziele erreichen.\n\n"
    "An dieser Stelle möchte ich betonen, dass wir stets transparent gearbeitet haben. "
    "Einerseits haben wir Sie regelmäßig informiert, andererseits standen wir für "
    "Rückfragen zur Verfügung. Auf diese Weise blieb das Vertrauen jederzeit "
    "erhalten.\n\n"
    "Besonders hervorheben möchte ich das Engagement des Teams. Alle Mitarbeiter haben "
    "sich hervorragend eingesetzt. Darüber hinaus haben sie viele eigene Ideen "
    "eingebracht. Aus diesem Grund verlief das Projekt so erfolgreich. Ich möchte mich "
    "an dieser Stelle herzlich bei allen Beteiligten bedanken.\n\n"
    "Was die nächsten Schritte betrifft, so schlage ich ein weiteres Treffen vor. Dabei "
    "könnten wir die Ergebnisse im Detail besprechen. Außerdem wäre es sinnvoll, über "
    "zukünftige Projekte zu sprechen. Ich würde mich freuen, wenn wir einen Termin in "
    "den nächsten Wochen finden könnten.\n\n"
    "Erlauben Sie mir außerdem einen Hinweis zur Dokumentation. Sämtliche Unterlagen "
    "wurden sorgfältig archiviert. Folglich können Sie jederzeit auf die Ergebnisse "
    "zugreifen. Bei Bedarf senden wir Ihnen gern eine vollständige Übersicht zu.\n\n"
    "Zusammenfassend lässt sich sagen, dass das Projekt ein großer Erfolg war. Sowohl "
    "die Qualität als auch die Effizienz haben unsere Erwartungen übertroffen. Ich bin "
    "überzeugt, dass wir auf dieser Grundlage weiter erfolgreich zusammenarbeiten "
    "werden. Für Ihr Vertrauen möchte ich mich ausdrücklich bedanken.\n\n"
    "Darüber hinaus möchte ich einige Zahlen nennen. Zum einen konnten wir die Kosten um "
    "zehn Prozent senken. Zum anderen stieg die Zufriedenheit der Kunden deutlich. Diese "
    "Ergebnisse sprechen für sich. Aus diesem Grund bin ich zuversichtlich, dass sich "
    "die Investition gelohnt hat.\n\n"
    "Sollten Sie noch Fragen haben, stehe ich Ihnen selbstverständlich jederzeit zur "
    "Verfügung. Sie erreichen mich unter der bekannten Telefonnummer oder per E-Mail. "
    "Ich würde mich über eine baldige Rückmeldung sehr freuen. Bis dahin wünsche ich "
    "Ihnen eine angenehme Zeit.\n\n"
    "Ich bedanke mich noch einmal für die gute Zusammenarbeit und das entgegengebrachte "
    "Vertrauen. Es war mir eine große Freude, dieses Projekt zu begleiten. Ich blicke "
    "mit Zuversicht auf unsere weitere Zusammenarbeit und hoffe auf viele weitere "
    "gemeinsame Erfolge.\n\n"
    "Abschließend möchte ich betonen, wie sehr ich die offene Kommunikation geschätzt "
    "habe. Ihre klaren Rückmeldungen haben uns stets geholfen. Dank Ihrer Unterstützung "
    "konnten wir schwierige Situationen gut meistern. Ich bin zuversichtlich, dass "
    "unsere künftigen Projekte ebenso erfolgreich verlaufen werden.\n\n"
    "Mit freundlichen Grüßen\n"
    "Ihr Projektleiter\n\n"
    "Ein formeller Brief hat feste Regeln. Man beginnt mit einer höflichen Anrede: "
    "„Sehr geehrte Damen und Herren“. Danach benutzt man einen sachlichen, höflichen "
    "Ton und die Höflichkeitsform „Sie“. Konnektoren wie „einerseits“, „andererseits“, "
    "„zudem“, „dennoch“ und „folglich“ verbinden die Gedanken zu einem klaren Text. Am "
    "Ende steht eine Grußformel: „Mit freundlichen Grüßen“. So entsteht ein "
    "zusammenhängender und professioneller Text."
)

BATCH = {
    "b2.adjective-prepositions": {
        "intro": (
            "In this lesson you'll express attitudes precisely with adjectives that "
            "take a fixed preposition: stolz auf, zufrieden mit, interessiert an, froh "
            "über, gespannt auf. The preposition must be learned with the adjective."
        ),
        "story": story_adjprep,
        "questions": [
            q(
                "Worauf ist der Erzähler bei der Arbeit stolz?",
                "What is the narrator proud of at work?",
                "Auf sein Team.",
            ),
            q(
                "Womit ist der Erzähler zufrieden?",
                "What is the narrator satisfied with?",
                "Mit dem Ergebnis der Arbeit.",
            ),
            q(
                "Wofür interessiert sich der Erzähler?",
                "What is the narrator interested in?",
                "Für neue Technologien.",
            ),
            q(
                "Wofür ist der Erzähler im Beruf verantwortlich?",
                "What is the narrator responsible for at work?",
                "Für ein kleines Team.",
            ),
            q(
                "Wofür ist die Freundin bekannt?",
                "What is the girlfriend known for?",
                "Für ihre gute Laune.",
            ),
            q(
                "Womit ist der Erzähler manchmal unzufrieden?",
                "What is the narrator sometimes dissatisfied with?",
                "Mit seiner Disziplin; er ist manchmal enttäuscht von sich selbst.",
            ),
            q(
                "Wie blickt der Erzähler in die Zukunft?",
                "How does the narrator look to the future?",
                "Voller Erwartung; er ist gespannt auf neue Aufgaben und offen für "
                "Veränderungen.",
            ),
            q(
                "Wie lernt man Adjektive mit Präpositionen?",
                "How do you learn adjectives with prepositions?",
                "Man kann die Präposition nicht raten, sondern muss sie zusammen mit dem "
                "Adjektiv lernen.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze die Präposition (stolz ___).",
                "Ich bin stolz ___ mein Team.",
                "auf",
            ),
            fib(
                "Ergänze die Präposition (zufrieden ___).",
                "Ich bin zufrieden ___ dem Ergebnis.",
                "mit",
            ),
            mc(
                "Wähle die Präposition (interessiert ___).",
                "Sie ist interessiert ___ neuen Technologien.",
                ["an", "auf", "für"],
                "an",
            ),
            fib(
                "Ergänze die Präposition (gespannt ___).",
                "Wir sind gespannt ___ die Zukunft.",
                "auf",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Ich", "bin", "stolz", "auf", "mein", "Team"],
                "Ich bin stolz auf mein Team",
            ),
        ],
    },
    "b2.word-order-emphasis": {
        "intro": (
            "In this lesson you'll structure sentences for emphasis. The verb stays in "
            "second position, but you can front the most important element — object, "
            "time or a whole clause. nicht … sondern highlights a contrast."
        ),
        "story": story_wordorder,
        "questions": [
            q(
                "Wo steht das Verb im deutschen Aussagesatz meistens?",
                "Where does the verb usually stand in a German statement?",
                "An zweiter Stelle.",
            ),
            q(
                "Was wird betont, wenn man ein Satzglied an den Anfang stellt?",
                "What is emphasized when you put an element at the beginning?",
                "Das, was am Anfang steht.",
            ),
            q(
                "Wie betonte der Erzähler den ungewöhnlichen Fehler?",
                "How did the narrator emphasize the unusual bug?",
                "Er stellte „diesen Fehler“ an den Anfang: „Diesen Fehler habe ich noch "
                "nie gesehen.“",
            ),
            q(
                "Warum stellte der Erzähler „gestern“ an den Satzanfang?",
                "Why did the narrator put gestern at the start of the sentence?",
                "Weil die Zeit wichtig war; das Update war ganz neu.",
            ),
            q(
                "Wer war laut dem Erzähler wirklich schuld?",
                "Who was really to blame according to the narrator?",
                "Nicht das Team, sondern der Zeitplan.",
            ),
            q(
                "Was drückt die Struktur „nicht … sondern“ aus?",
                "What does the structure nicht … sondern express?",
                "Sie hebt einen Gegensatz besonders deutlich hervor.",
            ),
            q(
                "Wie zeigte der Erzähler seinem Team seine Dankbarkeit?",
                "How did the narrator show his team his gratitude?",
                "Indem er sagte: „Ohne eure Hilfe hätte ich das nie geschafft.“",
            ),
            q(
                "Wozu dient die flexible Wortstellung im Deutschen?",
                "What is the flexible word order in German used for?",
                "Zur Betonung; man stellt das wichtigste Satzglied vor das Verb, um die "
                "Aufmerksamkeit darauf zu lenken.",
            ),
        ],
        "exercises": [
            reo(
                "Bringe die Wörter in die richtige Reihenfolge (Betonung auf das "
                "Objekt).",
                ["Diesen", "Fehler", "habe", "ich", "noch", "nie", "gesehen"],
                "Diesen Fehler habe ich noch nie gesehen",
            ),
            mc(
                "Wähle die richtige Form (Verb an zweiter Stelle).",
                "Gestern ___ das Update veröffentlicht.",
                ["wurde", "es wurde", "wurde es"],
                "wurde",
            ),
            fib(
                "Ergänze das Wort (nicht … ___).",
                "Nicht das Team ist schuld, ___ der Zeitplan.",
                "sondern",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Gerade", "jetzt", "brauchen", "wir", "Ruhe"],
                "Gerade jetzt brauchen wir Ruhe",
            ),
            fib(
                "Ergänze das Wort für die Betonung des Moments (___ jetzt).",
                "___ jetzt brauchen wir Ruhe.",
                "Gerade",
            ),
        ],
    },
    "b2.collocations-idioms": {
        "intro": (
            "In this lesson you'll use natural collocations (eine Entscheidung treffen, "
            "in Angriff nehmen) and idioms (jemandem die Daumen drücken, den Nagel auf "
            "den Kopf treffen), which cannot be translated word for word."
        ),
        "story": story_idioms,
        "questions": [
            q(
                "Was mussten die Kollegen am Montag machen?",
                "What did the colleagues have to do on Monday?",
                "Eine wichtige Entscheidung treffen und das neue Projekt in Angriff "
                "nehmen.",
            ),
            q(
                "Was sagte der Chef über das Aufschieben?",
                "What did the boss say about putting things off?",
                "Man dürfe das nicht auf die lange Bank schieben; am Ende des Tages "
                "zähle nur das Ergebnis.",
            ),
            q(
                "Was passierte am Dienstag mit dem Kollegen?",
                "What happened to the colleague on Tuesday?",
                "Er verlor fast den Kopf, weil ein Termin näher rückte.",
            ),
            q(
                "Wie reagierte der Chef auf die schlechte Idee am Mittwoch?",
                "How did the boss react to the bad idea on Wednesday?",
                "Er sagte: „Das kommt überhaupt nicht in Frage“ und nahm kein Blatt vor "
                "den Mund.",
            ),
            q(
                "Was sagte der Erzähler der Kollegin vor ihrer Prüfung?",
                "What did the narrator say to the colleague before her exam?",
                "„Ich drücke dir die Daumen.“",
            ),
            q(
                "Wie hielt der Erzähler am Freitag das Team informiert?",
                "How did the narrator keep the team informed on Friday?",
                "Er hielt alle auf dem Laufenden, damit niemand den Überblick verlor.",
            ),
            q(
                "Was bedeutet „jemandem die Daumen drücken“?",
                "What does 'to press one's thumbs for someone' mean?",
                "Dass man ihm Glück wünscht (nicht wörtlich).",
            ),
            q(
                "Was ist der Unterschied zwischen Kollokationen und Redewendungen?",
                "What is the difference between collocations and idioms?",
                "Kollokationen sind feste Wortverbindungen (eine Entscheidung treffen); "
                "Redewendungen sind bildliche Ausdrücke (die Daumen drücken).",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze das Verb (eine Entscheidung ___).",
                "Wir müssen eine Entscheidung ___.",
                "treffen",
            ),
            fib(
                "Ergänze das Nomen (in ___ nehmen).",
                "Wir nehmen das Projekt in ___.",
                "Angriff",
            ),
            mc(
                "Wähle das richtige Nomen (nicht in ___ kommen).",
                "Das kommt überhaupt nicht in ___.",
                ["Frage", "Angriff", "Gang"],
                "Frage",
            ),
            fib(
                "Ergänze das Wort (die ___ drücken = Glück wünschen).",
                "Ich drücke dir die ___.",
                "Daumen",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Wir", "müssen", "eine", "Entscheidung", "treffen"],
                "Wir müssen eine Entscheidung treffen",
            ),
        ],
    },
    "b2.cohesion-register": {
        "intro": (
            "In this lesson you'll write formal, well-structured texts. A formal letter "
            "uses a polite salutation (Sehr geehrte Damen und Herren), the Sie form, "
            "connectors (einerseits, dennoch, folglich) and a closing (Mit freundlichen "
            "Grüßen)."
        ),
        "story": story_cohesion,
        "questions": [
            q(
                "Wie beginnt der formelle Brief?",
                "How does the formal letter begin?",
                "Mit der Anrede „Sehr geehrte Damen und Herren“.",
            ),
            q(
                "Was teilt der Verfasser zu Beginn mit?",
                "What does the writer announce at the start?",
                "Dass das Projekt erfolgreich abgeschlossen wurde.",
            ),
            q(
                "Wie verlief die Zusammenarbeit zwischen den Abteilungen?",
                "How did the cooperation between departments go?",
                "Reibungslos; man hielt den Zeitplan ein und blieb unter dem Budget.",
            ),
            q(
                "Welche Herausforderungen gab es im Projekt?",
                "What challenges were there in the project?",
                "Einige technische Probleme und die anfangs schwierige Abstimmung mit "
                "externen Partnern.",
            ),
            q(
                "Warum verlief das Projekt laut dem Brief so erfolgreich?",
                "Why did the project go so well according to the letter?",
                "Wegen des großen Engagements des Teams und der vielen eigenen Ideen.",
            ),
            q(
                "Was schlägt der Verfasser für die nächsten Schritte vor?",
                "What does the writer suggest for the next steps?",
                "Ein weiteres Treffen, um die Ergebnisse zu besprechen und über "
                "zukünftige Projekte zu sprechen.",
            ),
            q(
                "Mit welcher Grußformel endet der Brief?",
                "With which closing does the letter end?",
                "Mit „Mit freundlichen Grüßen“.",
            ),
            q(
                "Welche Merkmale hat ein formeller Brief?",
                "What features does a formal letter have?",
                "Eine höfliche Anrede, ein sachlicher Ton mit der Sie-Form, verbindende "
                "Konnektoren und eine Grußformel am Ende.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze das Wort in der Anrede.",
                "Sehr ___ Damen und Herren,",
                "geehrte",
            ),
            fib(
                "Ergänze das Wort in der Grußformel.",
                "Mit freundlichen ___",
                "Grüßen",
            ),
            mc(
                "Wähle den passenden Konnektor.",
                "Einerseits war es teuer, ___ war es nützlich.",
                ["andererseits", "folglich", "hiermit"],
                "andererseits",
            ),
            fib(
                "Ergänze das Wort, das ein Fazit einleitet.",
                "___ lässt sich sagen, dass das Projekt ein Erfolg war.",
                "Zusammenfassend",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                [
                    "Hiermit", "teile", "ich", "Ihnen", "mit", "dass", "das",
                    "Projekt", "abgeschlossen", "ist",
                ],
                "Hiermit teile ich Ihnen mit, dass das Projekt abgeschlossen ist",
            ),
        ],
    },
}

for code, data in BATCH.items():
    pat = re.compile(r'\{[^{}\n]*"code":\s*"' + re.escape(code) + r'"[^{}\n]*\}')
    m = pat.search(text)
    if not m:
        raise SystemExit(f"not found: {code}")
    existing = json.loads(m.group(0))
    merged = {**existing, **data}
    w = len(data["story"].split())
    print(f"  {code:28s} words={w}")
    assert w >= 510, f"{code} story too short: {w}"
    pretty = json.dumps(merged, indent=2, ensure_ascii=False)
    lines = pretty.split("\n")
    reindented = lines[0] + "".join("\n            " + ln for ln in lines[1:])
    text = text[: m.start()] + reindented + text[m.end() :]

PATH.write_text(text, encoding="utf-8")
print("done")
