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


story_konj1 = (
    "Pressebericht: Neue Pläne der Firma TechNova\n\n"
    "Gestern hat das Unternehmen TechNova auf einer Pressekonferenz seine Pläne für das "
    "nächste Jahr vorgestellt. Der Vorstand erklärte, man wolle das Unternehmen "
    "grundlegend verändern. In diesem Bericht wird zusammengefasst, was die "
    "Verantwortlichen gesagt haben. Dabei wird die indirekte Rede benutzt, um die "
    "Aussagen wiederzugeben.\n\n"
    "Der Geschäftsführer sagte, die Firma stehe vor einer wichtigen Phase. Man habe im "
    "letzten Jahr viel erreicht, aber es gebe noch viel zu tun. Die Umsätze seien "
    "gestiegen, und die Zahl der Kunden habe sich verdoppelt. Er betonte, das "
    "Unternehmen sei auf einem guten Weg.\n\n"
    "Weiter erklärte er, man werde in neue Technologien investieren. Besonders im "
    "Bereich der künstlichen Intelligenz sehe man großes Potenzial. Die Firma plane, "
    "hundert neue Mitarbeiter einzustellen. Er sagte, man suche vor allem gut "
    "ausgebildete Fachleute. Diese Fachleute könnten das Team entscheidend "
    "verstärken.\n\n"
    "Die Finanzchefin ergänzte, die Zahlen seien sehr positiv. Der Gewinn sei um zehn "
    "Prozent gestiegen, und man habe kaum Schulden. Sie sagte, das Unternehmen könne "
    "deshalb ohne Sorgen in die Zukunft blicken. Man wolle einen Teil des Gewinns in "
    "die Forschung stecken.\n\n"
    "Auch zu einem heiklen Thema äußerte sich der Vorstand. Es gab Gerüchte, die Firma "
    "wolle einen Konkurrenten kaufen. Der Geschäftsführer sagte, dazu könne er im "
    "Moment nichts sagen. Man prüfe verschiedene Möglichkeiten, aber es gebe noch keine "
    "Entscheidung. Er bat um Verständnis, dass er nicht mehr verraten dürfe.\n\n"
    "Ein Journalist fragte, ob die Preise steigen würden. Der Geschäftsführer "
    "antwortete, das sei zurzeit nicht geplant. Die Kunden müssten sich keine Sorgen "
    "machen. Man wolle fair bleiben und die Qualität weiter verbessern. Er versicherte, "
    "die Zufriedenheit der Kunden stehe an erster Stelle.\n\n"
    "Am Ende der Konferenz zeigte sich der Vorstand optimistisch. Man sei stolz auf das "
    "Erreichte und blicke voller Zuversicht nach vorn. Die nächsten Monate würden "
    "spannend, sagte der Geschäftsführer. Er dankte allen Mitarbeitern und meinte, ohne "
    "ihr Engagement wäre der Erfolg nicht möglich gewesen.\n\n"
    "Auch die Gewerkschaft nahm Stellung. Ihr Vertreter sagte, man begrüße die neuen "
    "Stellen, doch man erwarte faire Löhne. Die Mitarbeiter dürften nicht vergessen "
    "werden. Er betonte, die Belegschaft habe ein Recht auf Mitsprache. Das Unternehmen "
    "solle diese Versprechen ernst nehmen.\n\n"
    "Die Reaktionen auf die Pläne waren überwiegend positiv. Ein Experte sagte, die "
    "Strategie sei mutig, aber sinnvoll. Andere meinten, man müsse abwarten, ob die "
    "Firma ihre Versprechen halten könne. Insgesamt herrschte jedoch die Meinung, "
    "TechNova habe eine klare Vision.\n\n"
    "Der Konjunktiv I wird für die indirekte Rede benutzt. Man zeigt damit, dass man "
    "etwas nur wiedergibt und nicht selbst behauptet. Typische Formen sind: er habe, "
    "sie sei, man werde, es gebe, er könne. Wenn der Konjunktiv I wie der Indikativ "
    "aussieht, benutzt man den Konjunktiv II: sie hätten statt sie haben. So bleibt die "
    "Aussage klar als fremde Meinung erkennbar."
)

story_subjmodals = (
    "In jedem Büro gibt es Gerüchte und Vermutungen. Man hört etwas, ist sich aber "
    "nicht sicher, ob es stimmt. Für solche Fälle gibt es im Deutschen die subjektiven "
    "Modalverben. Mit ihnen kann man ausdrücken, was jemand behauptet, was man gehört "
    "hat oder was wahrscheinlich ist. Heute erzähle ich euch von den Gerüchten über "
    "meinen neuen Kollegen.\n\n"
    "Seit einer Woche haben wir einen neuen Kollegen, und alle reden über ihn. Er soll "
    "ein echtes Genie sein, sagt man. Angeblich hat er schon große Projekte geleitet. "
    "Er will sogar eine berühmte App selbst programmiert haben. Ob das wirklich stimmt, "
    "weiß niemand genau, aber die Geschichte klingt beeindruckend.\n\n"
    "„Er soll früher bei einer sehr bekannten Firma gearbeitet haben“, erzählt eine "
    "Kollegin. „Und er will dort das ganze System neu aufgebaut haben.“ Ich bin ein "
    "bisschen skeptisch. So ein junger Mensch dürfte kaum so viel Erfahrung haben. Aber "
    "vielleicht täusche ich mich ja auch.\n\n"
    "Am Montag habe ich ihn zum ersten Mal richtig getroffen. Er müsste eigentlich sehr "
    "stolz sein, dachte ich, aber er war ganz bescheiden. „Das kann nicht der große "
    "Experte sein“, dachte ich zuerst. Doch als er anfing zu reden, merkte ich schnell: "
    "Er versteht wirklich viel. Die Gerüchte könnten also doch wahr sein.\n\n"
    "Später fragte ich einen anderen Kollegen. „Stimmt es, dass er so erfahren ist?“ "
    "„Das mag sein“, antwortete er. „Aber man sollte nicht alles glauben. Er dürfte "
    "einfach ein guter Programmierer sein, mehr nicht.“ Da hatte er wohl recht. Man "
    "muss vorsichtig sein mit solchen Geschichten.\n\n"
    "Es gab noch mehr Gerüchte. Er soll ein sehr hohes Gehalt bekommen, hieß es. "
    "Angeblich will der Chef ihn unbedingt behalten. „Er muss dem Chef wirklich wichtig "
    "sein“, sagte jemand. Aber auch das konnte niemand beweisen. Vielleicht wollte "
    "einfach jemand die Geschichte interessanter machen.\n\n"
    "Nach ein paar Tagen legte sich die Aufregung. Der neue Kollege erwies sich als "
    "netter, normaler Mensch. Er ist gut in seinem Job, aber er ist kein Zauberer. Die "
    "meisten Gerüchte dürften stark übertrieben gewesen sein. „So ist es immer“, sagte "
    "meine Kollegin. „Am Anfang wird viel geredet.“\n\n"
    "Manchmal frage ich mich, wie solche Gerüchte überhaupt entstehen. Jemand hört "
    "etwas, erzählt es weiter, und am Ende klingt alles viel größer. „Die Hälfte davon "
    "kann gar nicht stimmen“, sagt mein Chef. „Man müsste immer nachfragen, bevor man "
    "etwas glaubt.“ Da hat er sicher recht.\n\n"
    "Am Ende habe ich etwas gelernt. Man sollte Gerüchte nicht zu ernst nehmen. Vieles, "
    "was erzählt wird, muss nicht stimmen. Der neue Kollege will vieles gemacht haben, "
    "und manches davon mag wahr sein. Aber am wichtigsten ist, dass er ein guter Mensch "
    "und ein guter Kollege ist.\n\n"
    "Subjektive Modalverben drücken eine Vermutung oder eine fremde Behauptung aus. "
    "„Sollen“ bedeutet, dass man es von anderen gehört hat: Er soll erfahren sein. "
    "„Wollen“ bedeutet, dass jemand etwas über sich selbst behauptet: Er will es "
    "programmiert haben. „Dürfte“, „müsste“ und „könnte“ zeigen, wie wahrscheinlich "
    "etwas ist. So kann ich vorsichtig über Dinge sprechen, die ich nicht genau weiß."
)

story_futur2 = (
    "Am Ende eines großen Projekts denke ich oft über die Zukunft nach. Was werde ich "
    "bis dann erreicht haben? Und was ist wohl gerade passiert, während ich hier sitze? "
    "Für solche Gedanken benutzt man im Deutschen das Futur II. Damit kann man "
    "ausdrücken, was in der Zukunft abgeschlossen sein wird, und Vermutungen über die "
    "Vergangenheit anstellen.\n\n"
    "Heute habe ich viel zu tun. Bis heute Abend werde ich den ganzen Bericht "
    "fertiggestellt haben. Bis morgen früh werde ich auch die letzten E-Mails "
    "beantwortet haben. Und bis zum Ende der Woche werden wir das komplette Projekt "
    "abgeschlossen haben. Ich freue mich schon auf diesen Moment.\n\n"
    "Mein Kollege ist heute nicht im Büro. „Wo ist er nur?“, frage ich mich. Er wird "
    "wohl den Zug verpasst haben. Oder er wird verschlafen haben. Vielleicht ist er "
    "auch krank geworden. „Er wird bestimmt einen guten Grund gehabt haben“, sagt meine "
    "Chefin. Wir machen uns aber keine großen Sorgen.\n\n"
    "Auch über andere Dinge stelle ich Vermutungen an. Die Kundin hat sich noch nicht "
    "gemeldet. Sie wird die Nachricht wohl noch nicht gelesen haben. Oder sie wird zu "
    "beschäftigt gewesen sein. „Sie wird sich schon melden“, denke ich. Manchmal muss "
    "man einfach Geduld haben.\n\n"
    "Ich plane auch weiter in die Zukunft. In fünf Jahren werde ich hoffentlich viel "
    "erreicht haben. Bis dahin werde ich vielleicht befördert worden sein. Ich werde "
    "neue Fähigkeiten gelernt und viele Projekte geleitet haben. Wenn ich zurückblicke, "
    "werde ich stolz auf meinen Weg sein.\n\n"
    "Meine Freundin und ich sprechen oft über solche Pläne. „Bis wir vierzig sind, "
    "werden wir sicher ein Haus gekauft haben“, sagt sie. „Und wir werden bestimmt viel "
    "gereist sein.“ Ich lächle. „Ja, und wir werden hoffentlich immer noch glücklich "
    "sein.“ Solche Gedanken geben uns Kraft.\n\n"
    "Am Abend denke ich an den vergangenen Tag. Ich habe fast alles geschafft. „Der "
    "Chef wird zufrieden sein“, denke ich. Er wird meinen Bericht inzwischen gelesen "
    "haben. Vielleicht wird er ihn sogar gelobt haben. Morgen werde ich es erfahren. "
    "Bis dahin bleibt es eine Vermutung.\n\n"
    "Auch meine Eltern rufe ich noch an. Sie sind nicht zu Hause. „Sie werden wohl "
    "spazieren gegangen sein“, denke ich. Oder sie werden schon geschlafen haben, denn "
    "es ist spät. Ich schreibe ihnen eine Nachricht. Bis morgen werden sie sie "
    "bestimmt gelesen haben.\n\n"
    "Bevor ich schlafe, mache ich noch eine kleine Liste. Bis zum nächsten Monat werde "
    "ich viele Dinge erledigt haben. Ich bin sicher: Wenn ich fleißig bleibe, werde ich "
    "meine Ziele erreicht haben. Das Gefühl, etwas geschafft zu haben, ist "
    "wunderbar.\n\n"
    "Das Futur II wird mit „werden“, dem Partizip II und „haben“ oder „sein“ gebildet: "
    "Ich werde den Bericht fertiggestellt haben. Es hat zwei Bedeutungen. Erstens "
    "beschreibt es eine Handlung, die in der Zukunft abgeschlossen sein wird. Zweitens "
    "drückt es eine Vermutung über die Vergangenheit aus: Sie wird den Zug verpasst "
    "haben. So kann man über abgeschlossene Zukunft und über wahrscheinliche "
    "Vergangenheit sprechen."
)

story_particles = (
    "Modalpartikeln sind kleine Wörter, die im Deutschen sehr wichtig sind. Sie ändern "
    "nicht die Bedeutung eines Satzes, aber sie geben ihm eine bestimmte Färbung. Mit "
    "ihnen klingt man natürlicher und drückt Gefühle wie Überraschung, Ungeduld oder "
    "Freundlichkeit aus. Heute erzähle ich euch von einem ganz normalen Tag, an dem ich "
    "viele solche Wörter benutzt habe.\n\n"
    "Am Morgen rief mich mein Freund an. „Komm doch mal vorbei!“, sagte er. „Wir haben "
    "uns ja schon lange nicht gesehen.“ „Das ist ja eine tolle Idee“, antwortete ich. "
    "„Aber ich muss halt zuerst arbeiten. Wie heißt du noch mal deine neue Adresse?“ "
    "Wir lachten, denn natürlich kannte ich seine Adresse.\n\n"
    "Im Büro war viel los. „Wo ist denn der Bericht?“, fragte mein Chef. „Der liegt "
    "doch auf Ihrem Tisch“, sagte ich. „Ach ja, stimmt“, sagte er. „Das habe ich wohl "
    "übersehen.“ Solche kleinen Wörter machten das Gespräch gleich viel freundlicher. "
    "Ohne sie hätte alles viel härter geklungen.\n\n"
    "Am Mittag beschwerte sich eine Kollegin. „Das dauert eben seine Zeit“, sagte sie. "
    "„Man kann halt nicht alles auf einmal machen.“ „Das ist schon richtig“, antwortete "
    "ich. „Aber wir sollten uns trotzdem beeilen.“ „Na gut“, sagte sie, „dann machen "
    "wir mal weiter.“ So kamen wir wieder gut voran.\n\n"
    "Am Nachmittag hatte ich ein Problem mit dem Computer. „Was ist denn jetzt los?“, "
    "dachte ich. „Das gibt es doch nicht!“ Ein Kollege half mir. „Probier es mal so“, "
    "sagte er. „Das klappt schon.“ Und tatsächlich, es funktionierte. „Na also“, sagte "
    "ich erleichtert. „Das war ja gar nicht so schwer.“\n\n"
    "Später kam ein neuer Kollege zu mir. „Könntest du mir mal helfen?“, fragte er "
    "höflich. „Klar, komm doch her“, sagte ich. „Das ist ja ganz einfach. Schau mal, du "
    "musst hier eben klicken.“ Er bedankte sich. „Das ist wirklich nett von dir.“ „Kein "
    "Problem“, sagte ich. „Das machen wir doch gern.“\n\n"
    "Am Abend traf ich Freunde in einem Café. „Wie war denn dein Tag?“, fragten sie. "
    "„Ach, ganz normal“, sagte ich. „Es war halt viel zu tun.“ „Trink doch erst mal "
    "einen Kaffee“, sagte einer. „Dann geht es dir gleich besser.“ Wir redeten und "
    "lachten, und der Stress war schnell vergessen.\n\n"
    "Zu Hause rief mich meine Mutter an. „Du klingst ja müde“, sagte sie. „Ruh dich "
    "doch ein bisschen aus.“ „Mach ich, Mama“, sagte ich. „Es war eben ein langer "
    "Tag.“ „Das kenne ich doch“, sagte sie und lachte. So ein kurzes Gespräch tut immer "
    "gut.\n\n"
    "So ein Tag zeigt, wie oft man Modalpartikeln benutzt. Sie sind fast in jedem Satz "
    "zu hören. „Komm doch mal“, „das ist ja toll“, „es dauert eben“ — ohne diese Wörter "
    "klingt Deutsch steif und unnatürlich. Für Lernende sind sie schwierig, aber sie "
    "sind der Schlüssel zu einer natürlichen Sprache.\n\n"
    "Modalpartikeln haben je nach Situation eine andere Wirkung. „Doch“ kann eine Bitte "
    "freundlicher machen oder Überraschung zeigen. „Ja“ drückt aus, dass etwas bekannt "
    "oder offensichtlich ist. „Halt“ und „eben“ bedeuten, dass man etwas akzeptiert. "
    "„Mal“ macht eine Aufforderung lockerer. Man lernt sie am besten, indem man viel "
    "zuhört und dann selbst ausprobiert."
)

BATCH = {
    "b2.konjunktiv1": {
        "intro": (
            "In this lesson you'll report what others said with Konjunktiv I (indirect "
            "speech): er habe, sie sei, man werde, es gebe. When Konjunktiv I looks like "
            "the indicative, Konjunktiv II is used instead (sie hätten)."
        ),
        "story": story_konj1,
        "questions": [
            q(
                "Was hat TechNova gestern vorgestellt?",
                "What did TechNova present yesterday?",
                "Seine Pläne für das nächste Jahr auf einer Pressekonferenz.",
            ),
            q(
                "Was sagte der Geschäftsführer über das letzte Jahr?",
                "What did the CEO say about last year?",
                "Man habe viel erreicht; die Umsätze seien gestiegen und die Zahl der "
                "Kunden habe sich verdoppelt.",
            ),
            q(
                "In welchen Bereich will die Firma investieren?",
                "In which area does the company want to invest?",
                "In neue Technologien, besonders in künstliche Intelligenz.",
            ),
            q(
                "Was sagte die Finanzchefin über die Zahlen?",
                "What did the CFO say about the figures?",
                "Sie seien sehr positiv; der Gewinn sei um zehn Prozent gestiegen und "
                "man habe kaum Schulden.",
            ),
            q(
                "Was sagte der Vorstand zu dem Gerücht über den Kauf eines "
                "Konkurrenten?",
                "What did the board say about the rumour of buying a competitor?",
                "Dazu könne er nichts sagen; man prüfe Möglichkeiten, aber es gebe noch "
                "keine Entscheidung.",
            ),
            q(
                "Was antwortete der Geschäftsführer auf die Frage nach steigenden "
                "Preisen?",
                "How did the CEO answer the question about rising prices?",
                "Das sei nicht geplant; die Kunden müssten sich keine Sorgen machen.",
            ),
            q(
                "Wie waren die Reaktionen auf die Pläne?",
                "How were the reactions to the plans?",
                "Überwiegend positiv; ein Experte nannte die Strategie mutig, aber "
                "sinnvoll.",
            ),
            q(
                "Wozu benutzt man den Konjunktiv I?",
                "What is Konjunktiv I used for?",
                "Für die indirekte Rede, um zu zeigen, dass man etwas nur wiedergibt und "
                "nicht selbst behauptet.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze den Konjunktiv I von haben (3. Person Singular).",
                "Der Kollege sagte, er ___ die Datei gesendet.",
                "habe",
            ),
            fib(
                "Ergänze den Konjunktiv I von sein (3. Person Singular).",
                "Sie meinte, das Projekt ___ fast fertig.",
                "sei",
            ),
            mc(
                "Wähle den Konjunktiv I von werden.",
                "Man berichtet, die Firma ___ bald wachsen.",
                ["werde", "wird", "würde"],
                "werde",
            ),
            fib(
                "Ergänze den Konjunktiv I von geben (es ___).",
                "Er sagte, es ___ noch viel zu tun.",
                "gebe",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Er", "sagte", "er", "habe", "die", "Datei", "gesendet"],
                "Er sagte, er habe die Datei gesendet",
            ),
        ],
    },
    "b2.subjective-modals": {
        "intro": (
            "In this lesson you'll express probability and hearsay with subjective "
            "modal verbs: sollen (I heard: er soll erfahren sein), wollen (he claims: "
            "er will es programmiert haben), and dürfte/müsste/könnte for likelihood."
        ),
        "story": story_subjmodals,
        "questions": [
            q(
                "Wofür benutzt man subjektive Modalverben?",
                "What are subjective modal verbs used for?",
                "Um auszudrücken, was jemand behauptet, was man gehört hat oder was "
                "wahrscheinlich ist.",
            ),
            q(
                "Was sagt man über den neuen Kollegen?",
                "What do people say about the new colleague?",
                "Er soll ein echtes Genie sein und angeblich große Projekte geleitet "
                "haben.",
            ),
            q(
                "Was behauptet der neue Kollege über sich selbst?",
                "What does the new colleague claim about himself?",
                "Er will eine berühmte App selbst programmiert haben.",
            ),
            q(
                "Warum war der Erzähler zuerst skeptisch?",
                "Why was the narrator skeptical at first?",
                "Weil so ein junger Mensch kaum so viel Erfahrung haben dürfte.",
            ),
            q(
                "Was rät der andere Kollege über die Gerüchte?",
                "What does the other colleague advise about the rumours?",
                "Man solle nicht alles glauben; der neue Kollege dürfte einfach ein "
                "guter Programmierer sein.",
            ),
            q(
                "Welches weitere Gerücht gab es über das Gehalt?",
                "What other rumour was there about the salary?",
                "Er solle ein sehr hohes Gehalt bekommen, und der Chef wolle ihn "
                "unbedingt behalten.",
            ),
            q(
                "Wie erwies sich der neue Kollege am Ende?",
                "How did the new colleague turn out in the end?",
                "Als netter, normaler Mensch, gut in seinem Job, aber kein Zauberer; die "
                "Gerüchte waren übertrieben.",
            ),
            q(
                "Was bedeuten „sollen“ und „wollen“ als subjektive Modalverben?",
                "What do sollen and wollen mean as subjective modal verbs?",
                "„sollen“ = man hat es von anderen gehört (er soll erfahren sein); "
                "„wollen“ = jemand behauptet es über sich selbst (er will es "
                "programmiert haben).",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze das subjektive Modalverb (er behauptet es selbst).",
                "Er ___ alles selbst programmiert haben.",
                "will",
            ),
            mc(
                "Wähle das subjektive Modalverb (Hörensagen).",
                "Sie ___ sehr erfahren sein.",
                ["soll", "will", "muss"],
                "soll",
            ),
            fib(
                "Ergänze das subjektive Modalverb (wahrscheinlich).",
                "Das Update ___ bald fertig sein.",
                "dürfte",
            ),
            mc(
                "Wähle das passende Modalverb (Möglichkeit).",
                "Das ___ sein, aber sicher ist es nicht.",
                ["mag", "will", "soll"],
                "mag",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Sie", "soll", "sehr", "erfahren", "sein"],
                "Sie soll sehr erfahren sein",
            ),
        ],
    },
    "b2.futur2": {
        "intro": (
            "In this lesson you'll use Futur II (werden + past participle + haben/sein) "
            "for actions that will be completed in the future (Ich werde es beendet "
            "haben) and for assumptions about the past (Sie wird den Zug verpasst "
            "haben)."
        ),
        "story": story_futur2,
        "questions": [
            q(
                "Wozu benutzt man das Futur II?",
                "What is Futur II used for?",
                "Um auszudrücken, was in der Zukunft abgeschlossen sein wird, und um "
                "Vermutungen über die Vergangenheit anzustellen.",
            ),
            q(
                "Was wird der Erzähler bis heute Abend erledigt haben?",
                "What will the narrator have done by this evening?",
                "Er wird den ganzen Bericht fertiggestellt haben.",
            ),
            q(
                "Warum ist der Kollege wohl nicht im Büro?",
                "Why is the colleague probably not at the office?",
                "Er wird wohl den Zug verpasst oder verschlafen haben, oder er ist krank "
                "geworden.",
            ),
            q(
                "Warum hat sich die Kundin noch nicht gemeldet?",
                "Why hasn't the customer been in touch yet?",
                "Sie wird die Nachricht wohl noch nicht gelesen haben oder zu "
                "beschäftigt gewesen sein.",
            ),
            q(
                "Was wird der Erzähler in fünf Jahren erreicht haben?",
                "What will the narrator have achieved in five years?",
                "Er wird vielleicht befördert worden sein, neue Fähigkeiten gelernt und "
                "viele Projekte geleitet haben.",
            ),
            q(
                "Was sagt die Freundin über die Zukunft mit vierzig?",
                "What does the girlfriend say about the future at forty?",
                "Sie werden sicher ein Haus gekauft haben und viel gereist sein.",
            ),
            q(
                "Was vermutet der Erzähler am Abend über den Chef?",
                "What does the narrator assume about the boss in the evening?",
                "Der Chef wird seinen Bericht inzwischen gelesen und ihn vielleicht "
                "gelobt haben.",
            ),
            q(
                "Wie bildet man das Futur II?",
                "How is Futur II formed?",
                "Mit „werden“ + Partizip II + „haben“/„sein“ (ich werde den Bericht "
                "fertiggestellt haben).",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze das Hilfsverb im Futur II (haben).",
                "Bis morgen werde ich den Bericht fertiggestellt ___.",
                "haben",
            ),
            fib(
                "Ergänze „werden“ (Futur II, 3. Person Singular).",
                "Sie ___ den Zug wohl verpasst haben.",
                "wird",
            ),
            mc(
                "Wähle das Hilfsverb.",
                "Bis Ende des Jahres werden wir das Projekt abgeschlossen ___.",
                ["haben", "sein", "werden"],
                "haben",
            ),
            fib(
                "Ergänze das Partizip II von verpassen.",
                "Er wird den Zug ___ haben.",
                "verpasst",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Sie", "wird", "den", "Zug", "verpasst", "haben"],
                "Sie wird den Zug verpasst haben",
            ),
        ],
    },
    "b2.modal-particles": {
        "intro": (
            "In this lesson you'll sound more natural with modal particles (doch, ja, "
            "halt, mal, eben, denn, wohl). They don't change the meaning but add nuance "
            "— friendliness, surprise, impatience or acceptance."
        ),
        "story": story_particles,
        "questions": [
            q(
                "Was machen Modalpartikeln mit einem Satz?",
                "What do modal particles do to a sentence?",
                "Sie ändern nicht die Bedeutung, aber geben ihm eine bestimmte Färbung "
                "(Überraschung, Ungeduld, Freundlichkeit).",
            ),
            q(
                "Was sagte der Freund am Morgen am Telefon?",
                "What did the friend say on the phone in the morning?",
                "„Komm doch mal vorbei! Wir haben uns ja schon lange nicht gesehen.“",
            ),
            q(
                "Wo lag der Bericht, den der Chef suchte?",
                "Where was the report the boss was looking for?",
                "Er lag auf dem Tisch des Chefs; er hatte ihn wohl übersehen.",
            ),
            q(
                "Was sagte die Kollegin über die Arbeit am Mittag?",
                "What did the colleague say about the work at midday?",
                "„Das dauert eben seine Zeit; man kann halt nicht alles auf einmal "
                "machen.“",
            ),
            q(
                "Wie half der Kollege beim Computerproblem?",
                "How did the colleague help with the computer problem?",
                "Er sagte „Probier es mal so“, und es funktionierte.",
            ),
            q(
                "Wie reagierte der Erzähler, als der neue Kollege um Hilfe bat?",
                "How did the narrator react when the new colleague asked for help?",
                "Freundlich: „Klar, komm doch her, das ist ja ganz einfach.“",
            ),
            q(
                "Warum sind Modalpartikeln für Lernende wichtig?",
                "Why are modal particles important for learners?",
                "Weil ohne sie Deutsch steif und unnatürlich klingt; sie sind der "
                "Schlüssel zu einer natürlichen Sprache.",
            ),
            q(
                "Welche Wirkung haben „doch“, „ja“ und „mal“?",
                "What effect do doch, ja and mal have?",
                "„doch“ macht eine Bitte freundlicher oder zeigt Überraschung; „ja“ "
                "zeigt, dass etwas bekannt/offensichtlich ist; „mal“ macht eine "
                "Aufforderung lockerer.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze die Modalpartikel (freundliche Aufforderung).",
                "Komm ___ mal vorbei!",
                "doch",
            ),
            mc(
                "Wähle die Modalpartikel (Überraschung / etwas Offensichtliches).",
                "Das ist ___ interessant!",
                ["ja", "mal", "denn"],
                "ja",
            ),
            fib(
                "Ergänze die Modalpartikel (man akzeptiert es).",
                "Es ist ___ kompliziert.",
                "halt",
            ),
            fib(
                "Ergänze das Wort (höfliche Nachfrage: noch ___).",
                "Wie heißt du ___ mal?",
                "noch",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Komm", "doch", "mal", "vorbei"],
                "Komm doch mal vorbei",
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
