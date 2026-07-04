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


story_adjectives = (
    "Ich heiße Laura, und ich habe eine neue Wohnung. Sie ist klein, aber sehr schön. "
    "Ich möchte euch die schöne Wohnung beschreiben. Im Wohnzimmer steht ein großes "
    "Sofa und ein kleiner Tisch. An der Wand hängt ein buntes Bild.\n\n"
    "Die neue Wohnung hat helle Zimmer und große Fenster. Ich mag das gemütliche "
    "Wohnzimmer am meisten. Dort habe ich einen bequemen Sessel und eine warme Decke. "
    "Am Abend lese ich dort ein gutes Buch und trinke einen heißen Tee.\n\n"
    "Die Küche ist modern. Ich habe einen neuen Herd und einen großen Kühlschrank. Auf "
    "dem Tisch steht eine kleine Vase mit frischen Blumen. Ich koche gern in dieser "
    "schönen Küche. Gestern habe ich eine leckere Suppe und einen frischen Salat "
    "gemacht.\n\n"
    "Das Schlafzimmer ist ruhig. Ich habe ein weiches Bett und einen kleinen Schrank. "
    "An der Wand hängt ein altes Foto von meiner Familie. Durch das große Fenster sehe "
    "ich einen grünen Garten. Am Morgen scheint die warme Sonne ins Zimmer.\n\n"
    "Das Badezimmer ist klein, aber praktisch. Es hat eine moderne Dusche und einen "
    "großen Spiegel. Auf dem weißen Regal stehen bunte Handtücher. Ich mag das saubere "
    "Badezimmer, denn dort beginnt mein neuer Tag.\n\n"
    "Ich habe auch einen kleinen Balkon. Dort steht ein runder Tisch und zwei grüne "
    "Stühle. Auf dem Balkon habe ich schöne Pflanzen und rote Blumen. An einem warmen "
    "Abend sitze ich dort und genieße die frische Luft. Der schöne Balkon ist mein "
    "Lieblingsplatz.\n\n"
    "Ich habe auch ein kleines Zimmer für meine Hobbys. Dort steht ein altes Klavier "
    "und ein großes Bücherregal. Ich habe viele interessante Bücher und ein paar alte "
    "Fotos. An der Wand hängt eine schöne Gitarre. In diesem gemütlichen Zimmer "
    "verbringe ich viele glückliche Stunden.\n\n"
    "Mein Büro ist auch schön. Ich habe einen neuen Laptop und eine schnelle "
    "Verbindung. Auf dem Schreibtisch liegt ein dickes Buch und ein roter Stift. Ich "
    "arbeite gern an diesem ruhigen Ort. Das kleine Büro hat einen guten Stuhl und eine "
    "helle Lampe.\n\n"
    "Meine Nachbarn sind sehr nett. Nebenan wohnt eine freundliche Familie mit zwei "
    "kleinen Kindern. Der nette Mann grüßt mich immer, und die junge Frau bringt mir "
    "manchmal einen frischen Kuchen. „Guten Morgen, liebe Nachbarin!“, sagen sie.\n\n"
    "Am Wochenende habe ich neue Möbel gekauft. Ich habe einen schönen Teppich und zwei "
    "bequeme Stühle. Der große Teppich liegt jetzt im Wohnzimmer. Die neuen Stühle "
    "stehen am Tisch. Alles sieht jetzt viel schöner aus.\n\n"
    "Im Flur habe ich einen praktischen Spiegel und einen kleinen Schrank. Dort hängen "
    "meine warme Jacke und mein blauer Mantel. Auf dem Boden liegt ein bunter Teppich. "
    "Der lange Flur ist jetzt sehr freundlich, und die ersten Gäste finden gleich einen "
    "guten Platz für ihre Schuhe.\n\n"
    "Letzte Woche hatte ich eine kleine Party. Ich habe gute Freunde eingeladen. Wir "
    "haben leckeres Essen gegessen und kalten Saft getrunken. Ein netter Freund hat "
    "eine schöne Pflanze mitgebracht, und eine liebe Freundin hat einen süßen Kuchen "
    "gebacken. Es war ein schöner Abend in meiner neuen Wohnung.\n\n"
    "Ich bin sehr glücklich in meiner neuen Wohnung. Sie ist ein schöner Ort zum Leben. "
    "Mit den richtigen Adjektiven kann ich alles gut beschreiben: das große Fenster, "
    "der bequeme Sessel und die frischen Blumen. Ein schönes Zuhause macht das Leben "
    "wirklich angenehm, und ich freue mich jeden Tag darüber."
)

story_local = (
    "Ich heiße Ben, und ich arbeite an der Rezeption in einem großen Bürogebäude. Den "
    "ganzen Tag fragen mich die Leute: „Wo ist das?“ oder „Wohin muss ich gehen?“ Ich "
    "helfe gern, denn ich kenne das Gebäude sehr gut.\n\n"
    "Am Morgen kommt eine Frau herein. Sie fragt: „Wo finde ich Herrn Müller?“ „Sein "
    "Büro ist oben“, sage ich. „Gehen Sie dort die Treppe hinauf. Oben gehen Sie nach "
    "links, und dann sind Sie da.“ Die Frau bedankt sich und geht hinauf.\n\n"
    "Später ruft ein Mann: „Woher kommt dieser Lärm?“ „Der kommt von draußen“, sage "
    "ich. „Die Arbeiter sind vor dem Gebäude.“ Der Mann nickt und geht wieder hinein. "
    "Drinnen ist es ruhiger als draußen.\n\n"
    "Ein Kollege sucht die neue Praktikantin. „Wo ist sie?“, fragt er. „Sie ist unten "
    "in der Kantine“, antworte ich. „Geh nach unten, dann geradeaus, und die Kantine "
    "ist rechts.“ Er sagt: „Danke!“ und geht dorthin. Nach ein paar Minuten kommen "
    "beide wieder herauf.\n\n"
    "Am Mittag will ich selbst nach draußen. Es ist ein schöner Tag, und ich möchte "
    "hier nicht die ganze Zeit drinnen sitzen. Ich gehe hinaus in den Park. Überall "
    "sitzen Menschen und essen. Ich finde keinen freien Platz, denn nirgendwo ist es "
    "leer. Also setze ich mich einfach ins Gras.\n\n"
    "Am Nachmittag kommt ein Kurier. „Wohin soll ich das Paket bringen?“, fragt er. "
    "„Bringen Sie es dorthin, in den dritten Stock“, sage ich. „Der Fahrstuhl ist da "
    "hinten. Fahren Sie hinauf, dann sehen Sie das Büro vorne rechts.“ Der Kurier fährt "
    "nach oben.\n\n"
    "Kurz danach sucht eine Kollegin ihre Brille. „Wo ist sie nur?“, fragt sie. "
    "„Vielleicht liegt sie da drüben“, sage ich und zeige nach vorne. Wir suchen "
    "überall — oben auf dem Regal, unten in der Schublade, hier und dort. Endlich finde "
    "ich sie. Sie liegt hinten auf dem Tisch. „Da ist sie ja!“, ruft die Kollegin "
    "froh.\n\n"
    "Eine ältere Dame ist verloren. „Ich weiß nicht, wohin ich muss“, sagt sie traurig. "
    "„Kein Problem“, sage ich freundlich. „Wohin möchten Sie denn?“ „Zum Ausgang“, sagt "
    "sie. „Kommen Sie mit mir“, sage ich. „Der Ausgang ist hier vorne. Gehen Sie "
    "einfach geradeaus, und dann sind Sie draußen.“\n\n"
    "Ein junger Mann fragt mich: „Wo kann ich hier parken?“ „Das Parkhaus ist gleich "
    "nebenan“, sage ich. „Fahren Sie hier raus, dann nach rechts. Die Einfahrt ist da "
    "vorne.“ Er dankt mir und fährt dorthin. Kurze Zeit später kommt er zurück und "
    "fragt, wo die Toilette ist. „Die ist da hinten links“, sage ich und zeige den "
    "Weg.\n\n"
    "Am späten Nachmittag ist wenig los. Die meisten Leute sind schon nach Hause "
    "gegangen. Hier an der Rezeption ist es jetzt still. Ich schaue nach draußen und "
    "sehe, wie die Menschen überallhin gehen — die einen nach links, die anderen nach "
    "rechts.\n\n"
    "Am Abend gehe ich auch nach Hause. „Wohin gehst du?“, fragt ein Kollege. „Nach "
    "Hause“, sage ich und lache. „Endlich!“ Mit kleinen Wörtern wie hier, dort, oben, "
    "unten, links und rechts kann ich jeden Weg gut erklären. Wo, wohin und woher — "
    "diese drei Fragen höre ich jeden Tag, und ich beantworte sie immer gern. Am Ende "
    "des Tages kenne ich wirklich jeden Weg im ganzen großen Gebäude."
)

story_verbsprep = (
    "Ich heiße Nina, und ich warte oft auf den Bus. Jeden Morgen stehe ich an der "
    "Haltestelle und denke an meinen Tag. Manchmal ärgere ich mich über den Verkehr, "
    "aber meistens bleibe ich ruhig und freue mich auf die Arbeit.\n\n"
    "Bei der Arbeit sprechen wir viel über neue Projekte. Ich interessiere mich für "
    "Technik, und deshalb gefällt mir mein Job. Mein Chef bittet mich oft um Hilfe, und "
    "ich kümmere mich gern um schwierige Aufgaben. Meine Kollegen danken mir für meine "
    "Arbeit, und das freut mich sehr.\n\n"
    "In der Mittagspause sprechen wir über unsere Pläne. Meine Kollegin freut sich auf "
    "ihren Urlaub. Sie träumt von einer Reise nach Italien. „Ich denke schon lange an "
    "dieses Land“, sagt sie. „Ich interessiere mich für die Kunst und die Kultur.“ Wir "
    "sprechen lange über ihre Pläne.\n\n"
    "Am Nachmittag nehme ich an einem Meeting teil. Wir diskutieren über ein neues "
    "Produkt. Alle glauben an den Erfolg. Ich ärgere mich ein bisschen über einen "
    "Kollegen, weil er nicht zuhört. Aber am Ende sind wir uns einig, und ich freue "
    "mich über das gute Ergebnis.\n\n"
    "Am Abend nehme ich an einem Deutschkurs teil. Ich freue mich immer auf den "
    "Unterricht. Wir sprechen über viele Themen und lachen zusammen. Die Lehrerin "
    "achtet auf unsere Aussprache und hilft uns bei den Fehlern. Ich denke oft an ihre "
    "Tipps, denn sie sind sehr nützlich.\n\n"
    "Nach dem Kurs warte ich auf meine Freundin. Wir wollen zusammen ins Kino gehen. "
    "Sie kommt ein bisschen zu spät, und ich denke schon: „Wo ist sie?“ Aber dann kommt "
    "sie, und ich freue mich über ihr Lächeln. Wir sprechen über den Film und über "
    "unseren Tag.\n\n"
    "Meine Freundin erzählt mir von ihrem Bruder. Er kümmert sich um seine kranke "
    "Mutter. „Ich bewundere ihn dafür“, sagt sie. „Er denkt immer an die Familie.“ Ich "
    "höre ihr zu und denke an meine eigene Familie. Ich sollte öfter an sie denken und "
    "mich mehr um sie kümmern.\n\n"
    "Am Abend rufe ich meine Mutter an. Sie freut sich über meinen Anruf. Wir sprechen "
    "über die alte Zeit, und sie erinnert sich an viele schöne Momente. „Ich denke oft "
    "an dich“, sagt sie. „Ich danke dir für deinen Anruf.“ Solche Gespräche bedeuten "
    "mir viel. Ich freue mich immer auf das nächste Telefonat mit ihr, denn sie erzählt "
    "mir gern von zu Hause.\n\n"
    "Manchmal ärgere ich mich über kleine Dinge, aber dann denke ich an die schönen "
    "Momente. Ich glaube an das Gute im Leben. Ich freue mich über jeden neuen Tag und "
    "kümmere mich um die Menschen, die ich liebe.\n\n"
    "Bevor ich schlafe, denke ich an den nächsten Tag. Ich freue mich schon auf das "
    "Wochenende. Ich träume von einem ruhigen Samstag mit einem guten Buch. Manchmal "
    "mache ich mir Sorgen um die Arbeit, aber ich glaube an mich und an meine "
    "Zukunft.\n\n"
    "Verben mit Präpositionen sind sehr wichtig. Ich warte auf etwas, ich denke an "
    "jemanden, und ich freue mich auf einen schönen Tag. Man muss die richtige "
    "Präposition lernen, denn sie gehört fest zum Verb. Mit ein bisschen Übung kann ich "
    "über alles sprechen, was mir wichtig ist."
)

story_ordinals = (
    "Ich heiße David, und ich erzähle euch von den wichtigen Tagen in meinem Jahr. "
    "Heute ist der erste September, und für mich beginnt eine neue Zeit. Am dritten "
    "September habe ich meinen ersten Tag in einer neuen Firma. Ich bin nervös, aber "
    "auch sehr glücklich.\n\n"
    "Mein neues Büro ist im vierten Stock. Am ersten Tag fahre ich mit dem Fahrstuhl "
    "nach oben. Meine Chefin begrüßt mich und zeigt mir alles. „Ihr Platz ist in der "
    "zweiten Reihe“, sagt sie. „Der erste Schreibtisch am Fenster gehört Ihnen.“ Ich "
    "freue mich über den schönen Platz.\n\n"
    "Die erste Woche ist nicht leicht. Am ersten Tag lerne ich die Kollegen kennen. Am "
    "zweiten Tag verstehe ich die Aufgaben besser. Am dritten Tag mache ich schon meine "
    "erste Präsentation. Am Ende der Woche bin ich müde, aber zufrieden.\n\n"
    "Ich habe viele wichtige Termine. Mein erstes Meeting ist am fünften September. Am "
    "zehnten habe ich einen Termin beim Arzt. Der Geburtstag meiner Mutter ist am "
    "fünfzehnten, und ich möchte ihn nicht vergessen. Am einunddreißigsten Dezember "
    "feiern wir Silvester.\n\n"
    "Auch im Kalender gibt es besondere Tage. Der erste Januar ist Neujahr. Der dritte "
    "Oktober ist ein Feiertag in Deutschland. Im Dezember warte ich auf den "
    "vierundzwanzigsten, denn das ist Heiligabend. Diese Tage sind für viele Menschen "
    "sehr wichtig. Am sechsten Januar feiern manche noch das Dreikönigsfest, und der "
    "erste Mai ist der Tag der Arbeit.\n\n"
    "Am Wochenende gehe ich ins Theater. Meine Karte ist für die dritte Reihe. „Wo ist "
    "mein Platz?“, frage ich. „In der dritten Reihe, der fünfte Sitz von links“, sagt "
    "die Frau. Das Theater ist alt und schön. Es ist schon das zweite Mal in diesem "
    "Jahr, dass ich hierher komme.\n\n"
    "Im Mai war ich auf einer Hochzeit. Es war die erste Hochzeit meines besten "
    "Freundes. Am zwölften Mai haben sie geheiratet. Ich saß in der ersten Reihe und "
    "war sehr gerührt. Es war einer der schönsten Tage in diesem Jahr.\n\n"
    "Ich wohne im dritten Stock eines alten Hauses. Meine Nachbarin wohnt im ersten "
    "Stock, und ein netter Student wohnt im zweiten. Der Aufzug ist oft kaputt, und "
    "dann muss ich die Treppe nehmen. Der Weg in den dritten Stock ist manchmal "
    "anstrengend, aber ich mag meine Wohnung.\n\n"
    "Am zweiten Samstag im Monat spiele ich Fußball. Letztes Mal war unser Team sehr "
    "gut. Wir haben das erste Spiel gewonnen und das zweite verloren. Am Ende waren wir "
    "auf dem dritten Platz. Beim nächsten Turnier möchten wir den ersten Platz. Nach "
    "dem Spiel gehen wir immer zusammen essen; das dritte Restaurant in unserer Straße "
    "ist unser Lieblingsort.\n\n"
    "Am einundzwanzigsten Juni ist der längste Tag des Jahres. Ich mag den Sommer am "
    "meisten. Mein Urlaub beginnt am ersten Juli. Zum ersten Mal fahre ich in diesem "
    "Jahr ans Meer. Ich zähle schon die Tage bis zu meinem zweiten Urlaub im Herbst.\n\n"
    "Ordinalzahlen brauche ich jeden Tag. Ich sage das Datum, ich finde meinen Platz, "
    "und ich wohne in einem bestimmten Stock. Der erste, der zweite, der dritte — mit "
    "diesen Wörtern kann ich Termine und Positionen gut angeben. Ohne sie wäre mein "
    "Kalender ein großes Chaos, und ich würde bestimmt jeden zweiten Termin verpassen."
)

BATCH = {
    "a2.adjective-endings-intro": {
        "intro": (
            "In this lesson you'll add endings to adjectives that stand before a noun "
            "(ein neuer Laptop, eine schnelle Verbindung, das kleine Büro), focusing on "
            "the nominative and accusative."
        ),
        "story": story_adjectives,
        "questions": [
            q(
                "Wie ist Lauras neue Wohnung?",
                "What is Laura's new flat like?",
                "Sie ist klein, aber sehr schön, mit hellen Zimmern und großen "
                "Fenstern.",
            ),
            q(
                "Was steht im Wohnzimmer?",
                "What is in the living room?",
                "Ein großes Sofa, ein kleiner Tisch und ein buntes Bild an der Wand.",
            ),
            q(
                "Was hat Laura gestern in der Küche gemacht?",
                "What did Laura make in the kitchen yesterday?",
                "Sie hat eine leckere Suppe und einen frischen Salat gemacht.",
            ),
            q(
                "Was sieht Laura durch das große Fenster im Schlafzimmer?",
                "What does Laura see through the big bedroom window?",
                "Sie sieht einen grünen Garten.",
            ),
            q(
                "Wer wohnt nebenan?",
                "Who lives next door?",
                "Eine freundliche Familie mit zwei kleinen Kindern.",
            ),
            q(
                "Was hat Laura am Wochenende gekauft?",
                "What did Laura buy on the weekend?",
                "Einen schönen Teppich und zwei bequeme Stühle.",
            ),
            q(
                "Was sagte ihre beste Freundin über die Wohnung?",
                "What did her best friend say about the flat?",
                "Sie sagte: „Was für eine schöne Wohnung! Du hast einen guten "
                "Geschmack.“",
            ),
            q(
                "Warum sind die richtigen Adjektive wichtig?",
                "Why are the right adjectives important?",
                "Weil Laura damit alles gut beschreiben kann: das große Fenster, der "
                "bequeme Sessel und die frischen Blumen.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze die Adjektivendung (Akkusativ, maskulin: einen ___ Laptop).",
                "Ich habe einen ___ Laptop. (neu)",
                "neuen",
            ),
            fib(
                "Ergänze die Adjektivendung (Nominativ, neutrum: das ___ Büro).",
                "Das ___ Büro hat große Fenster. (klein)",
                "kleine",
            ),
            mc(
                "Wähle die richtige Adjektivendung (Akkusativ, feminin: eine ___ "
                "Verbindung).",
                "Ich habe eine ___ Verbindung.",
                ["schnelle", "schneller", "schnellen"],
                "schnelle",
            ),
            fib(
                "Ergänze die Adjektivendung (Akkusativ, neutrum: ein ___ Buch).",
                "Ich lese ein ___ Buch. (gut)",
                "gutes",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Ich", "habe", "einen", "neuen", "Laptop"],
                "Ich habe einen neuen Laptop",
            ),
        ],
    },
    "a2.local-adverbs": {
        "intro": (
            "In this lesson you'll use local adverbs and the questions wo (where), "
            "wohin (where to) and woher (where from), plus words like hier, dort, oben, "
            "unten, links, rechts, hin and her."
        ),
        "story": story_local,
        "questions": [
            q(
                "Wo arbeitet Ben?",
                "Where does Ben work?",
                "Ben arbeitet an der Rezeption in einem großen Bürogebäude.",
            ),
            q(
                "Wo ist das Büro von Herrn Müller?",
                "Where is Mr Müller's office?",
                "Es ist oben; man geht die Treppe hinauf und dann nach links.",
            ),
            q(
                "Woher kommt der Lärm?",
                "Where does the noise come from?",
                "Der Lärm kommt von draußen, von den Arbeitern vor dem Gebäude.",
            ),
            q(
                "Wo ist die Kantine?",
                "Where is the canteen?",
                "Sie ist unten; man geht nach unten, dann geradeaus, und die Kantine "
                "ist rechts.",
            ),
            q(
                "Warum setzt sich Ben im Park ins Gras?",
                "Why does Ben sit in the grass in the park?",
                "Weil nirgendwo ein freier Platz ist; überall sitzen Menschen.",
            ),
            q(
                "Wohin soll der Kurier das Paket bringen?",
                "Where should the courier take the parcel?",
                "In den dritten Stock; der Fahrstuhl ist hinten, und das Büro ist vorne "
                "rechts.",
            ),
            q(
                "Wie hilft Ben der älteren Dame?",
                "How does Ben help the older lady?",
                "Er zeigt ihr den Ausgang: geradeaus nach vorne, und dann ist sie "
                "draußen.",
            ),
            q(
                "Welche drei Fragen hört Ben jeden Tag?",
                "Which three questions does Ben hear every day?",
                "Wo, wohin und woher.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze das Fragewort für den Ort (Position).",
                "___ bist du gerade? – Ich bin hier im Büro.",
                "Wo",
            ),
            fib(
                "Ergänze das Fragewort für die Richtung (Ziel).",
                "___ gehst du? – Ich gehe dorthin.",
                "Wohin",
            ),
            mc(
                "Wähle das Fragewort für die Herkunft.",
                "___ kommt der Lärm?",
                ["Woher", "Wohin", "Wo"],
                "Woher",
            ),
            fib(
                "Ergänze das Adverb (Richtung zum Sprecher).",
                "Komm mal ___!",
                "her",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Wohin", "gehst", "du"],
                "Wohin gehst du",
            ),
        ],
    },
    "a2.verbs-prepositions": {
        "intro": (
            "In this lesson you'll learn fixed verb + preposition combinations — warten "
            "auf, denken an, sprechen über, sich interessieren für, sich freuen auf — "
            "where the preposition belongs firmly to the verb."
        ),
        "story": story_verbsprep,
        "questions": [
            q(
                "Worauf wartet Nina jeden Morgen?",
                "What does Nina wait for every morning?",
                "Sie wartet auf den Bus.",
            ),
            q(
                "Wofür interessiert sich Nina?",
                "What is Nina interested in?",
                "Sie interessiert sich für Technik.",
            ),
            q(
                "Worüber sprechen Nina und ihre Kollegin in der Mittagspause?",
                "What do Nina and her colleague talk about at lunch?",
                "Sie sprechen über ihre Pläne und den Urlaub der Kollegin.",
            ),
            q(
                "Wovon träumt die Kollegin?",
                "What does the colleague dream of?",
                "Sie träumt von einer Reise nach Italien.",
            ),
            q(
                "Worüber ärgert sich Nina im Meeting?",
                "What does Nina get annoyed about in the meeting?",
                "Sie ärgert sich über einen Kollegen, weil er nicht zuhört.",
            ),
            q(
                "Worum kümmert sich der Bruder der Freundin?",
                "What does the friend's brother take care of?",
                "Er kümmert sich um seine kranke Mutter.",
            ),
            q(
                "Worüber freut sich Ninas Mutter?",
                "What is Nina's mother happy about?",
                "Sie freut sich über Ninas Anruf.",
            ),
            q(
                "Warum muss man die richtige Präposition lernen?",
                "Why must you learn the right preposition?",
                "Weil sie fest zum Verb gehört.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze die Präposition (warten ___).",
                "Ich warte ___ den Bus.",
                "auf",
            ),
            fib(
                "Ergänze die Präposition (denken ___).",
                "Ich denke ___ das Wochenende.",
                "an",
            ),
            mc(
                "Wähle die richtige Präposition (sprechen ___).",
                "Wir sprechen ___ das Projekt.",
                ["über", "auf", "an"],
                "über",
            ),
            fib(
                "Ergänze die Präposition (sich interessieren ___).",
                "Er interessiert sich ___ Technik.",
                "für",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Ich", "freue", "mich", "auf", "den", "Urlaub"],
                "Ich freue mich auf den Urlaub",
            ),
        ],
    },
    "a2.ordinal-numbers": {
        "intro": (
            "In this lesson you'll use ordinal numbers for dates and positions: der "
            "erste September, am dritten Oktober, im vierten Stock, in der zweiten "
            "Reihe."
        ),
        "story": story_ordinals,
        "questions": [
            q(
                "Welches Datum ist heute?",
                "What is today's date?",
                "Heute ist der erste September.",
            ),
            q(
                "Wann hat David seinen ersten Tag in der neuen Firma?",
                "When is David's first day at the new company?",
                "Am dritten September.",
            ),
            q(
                "In welchem Stock ist Davids neues Büro?",
                "On which floor is David's new office?",
                "Im vierten Stock.",
            ),
            q(
                "Wo ist Davids Platz im Büro?",
                "Where is David's spot in the office?",
                "In der zweiten Reihe, der erste Schreibtisch am Fenster.",
            ),
            q(
                "Wann ist der Geburtstag von Davids Mutter?",
                "When is David's mother's birthday?",
                "Am fünfzehnten September.",
            ),
            q(
                "Welcher Tag ist ein Feiertag in Deutschland?",
                "Which day is a public holiday in Germany?",
                "Der dritte Oktober.",
            ),
            q(
                "Wo ist Davids Platz im Theater?",
                "Where is David's seat at the theatre?",
                "In der dritten Reihe, der fünfte Sitz von links.",
            ),
            q(
                "Wann beginnt Davids Urlaub?",
                "When does David's holiday start?",
                "Am ersten Juli.",
            ),
        ],
        "exercises": [
            fib(
                "Ergänze die Ordinalzahl (1.).",
                "Heute ist der ___ September.",
                "erste",
            ),
            fib(
                "Ergänze die Ordinalzahl (3., Dativ: am ___).",
                "Mein Termin ist am ___ Oktober.",
                "dritten",
            ),
            mc(
                "Wähle die richtige Ordinalzahl (Dativ).",
                "Ich wohne im ___ Stock.",
                ["vierten", "vierte", "vier"],
                "vierten",
            ),
            fib(
                "Ergänze die Ordinalzahl (2., Dativ: in der ___).",
                "In der ___ Reihe sitzt mein Kollege.",
                "zweiten",
            ),
            reo(
                "Bringe die Wörter in die richtige Reihenfolge.",
                ["Heute", "ist", "der", "erste", "September"],
                "Heute ist der erste September",
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
