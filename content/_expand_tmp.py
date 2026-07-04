"""One-off: expand the A1 Unit 1 stories to ~650-700 words with paragraphs + dialogue."""

import json
import pathlib
import re

PATH = pathlib.Path("content/de/course.json")

STORIES = {
    "a1.alphabet-pronunciation": """Guten Tag! Mein Name ist Björn Häberle. Björn schreibt man B-J-Ö-R-N, und Häberle schreibt man H-Ä-B-E-R-L-E. Ich komme aus Österreich, aus einer kleinen Stadt in den Bergen, und ich wohne jetzt in Hamburg, in der Grünstraße. Heute ist mein erster Tag im Sprachkurs. Ich bin ein bisschen nervös, aber ich bin auch sehr froh. Ich möchte viele Menschen kennenlernen und endlich gut Deutsch sprechen.

Um neun Uhr kommt die Lehrerin in den Raum. Sie lächelt und begrüßt uns:
„Guten Morgen, herzlich willkommen!"
Sie heißt Frau Yılmaz. Ihren Namen schreibt man Y-I-L-M-A-Z. Sie schreibt ihren Namen groß an die Tafel und sagt:
„Namen sind wichtig. Bitte hört gut zu und buchstabiert langsam."
Dann fragt sie jeden Menschen im Kurs:
„Wie heißen Sie, und wie schreibt man Ihren Namen?"

Eine Frau antwortet langsam:
„Ich heiße Chiara. Man schreibt das C-H-I-A-R-A. Ich komme aus Italien."
Ein Mann sagt freundlich:
„Guten Tag, ich bin Paul aus Polen. Mein Name hat ein besonderes Zeichen."
Die Lehrerin nickt und sagt:
„Kein Problem, wir üben das zusammen."
So hören wir viele Namen: Chiara, Paul, Aiko, Omar und Maria. Jeder Name ist anders, und jeder Name ist interessant.

Danach erklärt Frau Yılmaz das Alphabet. Das deutsche Alphabet hat sechsundzwanzig Buchstaben. Dazu kommen die Umlaute ä, ö und ü und das scharfe s, also das ß. Wir sprechen die Vokale a, e, i, o und u ganz klar. Das w klingt fast wie ein englisches v, und das v klingt oft wie f. Das z spricht man wie ts, zum Beispiel in dem Wort Zebra. Das j klingt wie ein englisches y. Die Lehrerin sagt jeden Buchstaben vor, und wir sprechen laut nach: a, be, ce, de, e, ef, ge, ha, i, jot, ka, el, em, en.

Dann buchstabieren wir zusammen die Namen von Städten.
„Wie schreibt man München?", fragt die Lehrerin.
„M-Ü-N-C-H-E-N", antworte ich.
„Sehr gut. Und wie schreibt man Köln?"
„K-Ö-L-N."
Zürich schreibt man Z-Ü-R-I-C-H, und Wien schreibt man W-I-E-N. Ich frage meine Nachbarin:
„Woher kommst du?"
Sie antwortet:
„Ich komme aus Spanien, aus Malaga."
„Und wie schreibt man das?"
„M-A-L-A-G-A", sagt sie und lacht.

Nach den Städten üben wir die Zahlen von null bis zwölf. Die Zahlen sind wichtig für die Adresse und für die Telefonnummer. Frau Yılmaz fragt:
„Wie ist Ihre Telefonnummer?"
Ich sage meine Nummer langsam, Ziffer für Ziffer. Dann buchstabiere ich meine E-Mail-Adresse. Das ist am Anfang schwer, aber die Lehrerin hilft mir. Sie sagt:
„Sprache ist wie Musik. Man muss sie hören und oft üben."

Am Ende macht die Lehrerin ein kleines Spiel. Sie sagt nur die Buchstaben, und wir raten das Wort. Sie sagt:
„E-M-I-L."
Alle rufen zusammen:
„Emil!"
„Sehr gut", sagt Frau Yılmaz. Dann buchstabiert sie B-E-R-L-I-N.
„Das ist keine Person, das ist eine Stadt!", ruft Paul, und alle lachen. Das Spiel macht großen Spaß, und wir lernen dabei sehr schnell.

In der Pause trinke ich einen Kaffee. Ich schreibe meine Adresse auf ein Blatt Papier. Meine Adresse ist Grünstraße drei in Hamburg. Chiara kommt zu mir und fragt:
„Wie schreibt man deinen Familiennamen noch einmal?"
Ich sage langsam:
„H-Ä-B-E-R-L-E."
Sie wiederholt den Namen, und ich sage:
„Genau, das ist richtig!"
Wir sind beide froh, denn das Buchstabieren ist gar nicht so schwer.

Am Abend bin ich müde, aber sehr zufrieden. Ich habe viele Namen gehört und viele Städte buchstabiert. Ich kann jetzt Guten Tag und Auf Wiedersehen sagen. Ich kann meinen Namen buchstabieren, und ich kann fragen: Wie heißt du, und woher kommst du? Das ist ein guter Anfang. Morgen komme ich wieder, denn Deutsch macht mir Freude.""",
    "a1.sein-haben": """Hallo, ich bin Anna. Ich bin dreißig Jahre alt, und ich bin Programmiererin. Ich arbeite bei einer kleinen Firma in der Stadt. Heute bin ich ein bisschen müde, aber ich bin bereit, denn ich habe viel Zeit. Am Morgen bin ich zu Hause. Mein Mann ist auch da. Er heißt Tom, und er ist Lehrer. Wir sind eine kleine Familie, und wir haben zwei Kinder.

Die Kinder sind noch klein. Lena ist fünf, und Max ist sieben. Heute sind sie sehr fröhlich, denn sie haben keine Schule. Beim Frühstück fragt Tom:
„Bist du müde?"
Ich antworte:
„Ja, ich bin ein bisschen müde, aber ich bin glücklich."
Wir haben Kaffee und frische Brötchen. Max hat großen Hunger und ruft:
„Ich habe Hunger, und ich habe Durst!"
„Hier ist dein Saft", sagt Tom.
Lena hat auch Hunger. Sie ist noch klein, aber sie ist sehr klug.

Um neun Uhr sind wir alle wach. Die Sonne scheint, und der Himmel ist blau. Es ist ein schöner Tag. Ich habe heute frei, und Tom hat auch frei. Wir haben Zeit für die Kinder. Lena fragt:
„Gehen wir in den Park?"
„Ja, sehr gern", sage ich. Die Kinder sind begeistert und sofort bereit.

Am Vormittag sind wir im Park. Der Park ist groß und schön. Die Kinder haben ein Fahrrad und einen Ball. Sie sind sehr aktiv. Max ist schnell, und Lena ist mutig. Ich bin stolz auf sie. Wir spielen zusammen Ball, und Tom läuft mit Max um die Wette. Lena ruft:
„Papa ist schnell, aber Max ist schneller!"

Im Park ist auch ein Freund. Er heißt David, er ist Musiker, und er hat eine Gitarre dabei. David fragt:
„Wie geht es euch? Seid ihr müde?"
Wir lachen und sagen:
„Nein, wir sind fit, und wir haben gute Laune!"
David hat Zeit und Lust auf Musik. Er spielt ein Lied, und die Kinder singen mit. Wir sind alle glücklich.

Am Mittag haben wir Hunger. Wir machen ein Picknick. Wir haben Äpfel, Käse und Wasser. Das Essen ist einfach, aber lecker. Die Kinder sind zufrieden. Max fragt:
„Haben wir noch Äpfel?"
„Ja, natürlich", sagt Tom und gibt ihm einen roten Apfel.
„Danke, Papa!", sagt Max mit vollem Mund, und wir müssen lachen.

Am Nachmittag sind wir wieder zu Hause. Am späten Nachmittag haben wir Besuch. Meine Mutter ist da, und sie ist sehr herzlich. Sie fragt:
„Seid ihr müde? Habt ihr Hunger?"
Die Kinder rufen:
„Ja, wir haben Hunger, Oma!"
Meine Mutter hat immer etwas Süßes dabei. Sie hat Kekse und Schokolade, und die Kinder sind begeistert. Sie spielt mit den Kindern und hat immer eine gute Geschichte.

Ich bin dankbar. Ich habe eine Familie, ich habe Freunde, und ich habe einen freien Tag. Tom sagt:
„Du bist eine gute Mutter."
Ich sage:
„Und du bist ein guter Vater. Wir sind ein gutes Team."
Am Abend sind die Kinder müde. Um acht Uhr sind sie im Bett. Tom und ich haben Tee und Ruhe. Ich denke: Heute ist ein guter Tag. Wir sind gesund, wir haben genug, und wir sind zusammen. Das ist das Wichtigste. Morgen habe ich wieder Arbeit, aber heute bin ich einfach nur glücklich.""",
    "a1.personal-pronouns": """Wir sind eine Lerngruppe, und wir lernen zusammen Deutsch. Ich heiße Sofia, und ich komme aus Brasilien, aus São Paulo. Du kennst mich noch nicht, aber ich erzähle dir gern von uns. In der Gruppe sind wir fünf Personen. Ich bin Studentin, und ich lerne Deutsch für mein Studium. Du bist vielleicht auch Studentin oder Student, wer weiß.

Neben mir sitzt Ahmed. Er kommt aus Ägypten, aus Kairo, und er ist sehr fleißig. Er lernt jeden Tag, und er spricht schon gut Deutsch. Vor mir sitzt Yuki. Sie kommt aus Japan. Sie ist ruhig, aber sie ist klug. Sie schreibt alles genau auf. Hinter mir sitzen Omar und Elena. Sie sind nett und immer freundlich. Ahmed und Yuki sind ein gutes Beispiel: Sie arbeiten hart, und sie helfen uns oft.

Unsere Lehrerin heißt Frau Weber. Sie ist freundlich, und sie erklärt alles langsam. Wenn wir eine Frage haben, sagt sie:
„Fragt mich einfach! Ihr seid hier, um zu lernen."
Am Anfang der Stunde fragt sie:
„Guten Morgen! Wie geht es euch?"
Wir antworten:
„Uns geht es gut, danke."

Dann arbeiten wir. Ich lese einen Text, und du liest vielleicht denselben Text zu Hause. Ahmed hört gut zu. Er wiederholt die Wörter, und er spricht laut. Yuki macht die Übungen im Buch. Sie ist schnell, und sie macht selten einen Fehler. Im Raum gibt es auch einen Computer. Er ist neu, und er funktioniert gut. Wir benutzen ihn für die Aussprache, denn er zeigt uns die richtige Betonung.

Nach einer Stunde machen wir eine Pause. Ahmed fragt mich:
„Woher kommst du genau?"
Ich sage:
„Ich komme aus São Paulo. Und du, woher kommst du?"
Er lacht und sagt:
„Das weißt du doch, ich komme aus Kairo!"
Yuki sagt:
„Ihr sprecht schon viel besser als am Anfang."
Wir freuen uns über das Lob und trinken zusammen einen Tee.

Frau Weber kommt zurück und fragt:
„Seid ihr bereit?"
Wir sagen:
„Ja, wir sind bereit."
Sie gibt uns eine Aufgabe. Ich schreibe einen kurzen Text über meine Familie. Du schreibst vielleicht über deine Stadt. Ahmed schreibt über seine Arbeit, und Yuki schreibt über ihr Hobby. Jeder von uns ist anders, aber wir haben ein Ziel: Wir wollen Deutsch lernen.

Am Ende lesen wir unsere Texte vor. Ich lese zuerst, dann liest Ahmed, und danach liest Yuki. Frau Weber sagt:
„Ihr macht das sehr gut!"
Manchmal machen wir Fehler, aber das ist kein Problem. Wenn ich einen Fehler mache, hilft mir Yuki. Wenn Ahmed einen Fehler macht, korrigiere ich ihn freundlich. So helfen wir uns gegenseitig, und wir lernen jeden Tag ein bisschen mehr.

Am Ende der Stunde sage ich:
„Auf Wiedersehen, bis morgen!"
Ahmed und Yuki winken und rufen:
„Tschüss, Sofia!"
Wir gehen nach Hause, aber morgen kommen wir wieder. Ich lerne von euch, und ihr lernt von mir. Denn zusammen sind wir stark, und zusammen lernen wir gern.""",
    "a1.questions": """Es ist Montagmorgen, und ich bin neu in der Stadt. Ich heiße Leo, und ich habe viele Fragen. Wo ist der Bahnhof? Wann fährt der Bus? Wie finde ich die Sprachschule? Wo kann ich einen Kaffee trinken? Ich weiß es noch nicht, aber ich frage einfach, denn fragen ist der beste Weg.

Zuerst gehe ich zur Information am Bahnhof. Dort arbeitet eine Frau. Ich frage:
„Guten Morgen, haben Sie einen Moment Zeit?"
„Ja, natürlich. Wie kann ich Ihnen helfen?", antwortet sie.
„Wo ist die Grünstraße?"
„Die Grünstraße ist nicht weit. Gehen Sie geradeaus und dann links."
„Wie lange dauert das zu Fuß?", frage ich weiter.
„Ungefähr zehn Minuten."

Dann frage ich:
„Fährt auch ein Bus dorthin?"
„Ja, der Bus Nummer fünf fährt direkt."
„Und wann kommt der nächste Bus?"
Sie schaut auf den Plan und sagt:
„In fünf Minuten."
„Was kostet die Fahrt?"
„Zwei Euro fünfzig."
„Vielen Dank!"
„Gern geschehen."

Ich nehme den Bus. Neben mir sitzt ein junger Mann. Er fragt mich:
„Bist du auch neu hier?"
„Ja, ich bin ganz neu. Woher kommst du?"
„Ich komme aus Griechenland. Und du?"
„Ich komme aus Mexiko."
„Was machst du hier in der Stadt?"
„Ich lerne Deutsch. Und du, warum bist du hier?"
„Ich arbeite hier, und ich lerne auch Deutsch."
Wir lachen, denn wir haben das gleiche Ziel. Er heißt Niko, und er ist sehr sympathisch.

An der Haltestelle frage ich:
„Wo muss ich aussteigen?"
„An der nächsten Haltestelle", sagt Niko.
Vor der Schule stehen viele Leute. Ich frage eine Frau:
„Ist das die Sprachschule?"
„Ja, genau."
„Wann beginnt der Kurs?"
„Um neun Uhr. Wie spät ist es jetzt?"
Ich schaue auf die Uhr und sage:
„Es ist Viertel vor neun. Wir haben noch Zeit."

Im Kurs stellt die Lehrerin auch viele Fragen. Sie fragt:
„Wie heißen Sie? Woher kommen Sie? Warum lernen Sie Deutsch?"
Ich antworte ehrlich und ruhig. Dann fragt sie:
„Haben Sie noch Fragen?"
„Ja, eine Frage habe ich. Wie sagt man auf Deutsch danke?"
Alle lachen freundlich, denn danke sage ich schon die ganze Zeit.

In der Pause frage ich Niko:
„Trinkst du einen Kaffee?"
„Ja, gern. Wo gibt es hier Kaffee?"
Eine Frau zeigt uns die Küche. Ich frage sie:
„Ist der Kaffee gratis?"
„Ja, der Kaffee ist für alle."
Wir trinken zusammen einen Kaffee und sprechen über den ersten Tag.

Am Ende des Tages habe ich viele Antworten. Ich weiß jetzt: Der Bahnhof ist dort, der Bus Nummer fünf fährt oft, und der Kurs beginnt um neun. Ich habe auch einen neuen Freund, Niko. Fragen ist wirklich wichtig, denn wer fragt, der lernt. Und ich frage gern, jeden Tag ein bisschen mehr.""",
}

text = PATH.read_text(encoding="utf-8")
for code, story in STORIES.items():
    body = json.dumps(story, ensure_ascii=False)[1:-1]
    pattern = re.compile(r'("code":\s*"' + re.escape(code) + r'"[\s\S]*?"story":\s*")[^"]*(")')
    text, n = pattern.subn(lambda m: m.group(1) + body + m.group(2), text, count=1)
    assert n == 1, f"expected one match for {code}, got {n}"
    print("  %-28s words=%d" % (code, len(story.split())))

PATH.write_text(text, encoding="utf-8")
print("done")
