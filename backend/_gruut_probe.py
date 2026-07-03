import inspect
import time

import gruut

print("dir:", [n for n in dir(gruut) if not n.startswith("_")])
print("sentences sig:", inspect.signature(gruut.sentences))

# Try reusing a TextProcessor and disabling verbalization.
from gruut import sentences

def ipa(word, **kw):
    out = []
    for sent in sentences(word, lang="de", **kw):
        for tok in sent:
            if tok.phonemes:
                out.append("".join(tok.phonemes))
    return " ".join(out)

kw = dict(
    verbalize_numbers=False,
    verbalize_dates=False,
    verbalize_currency=False,
    verbalize_times=False,
)
# warm
t0 = time.perf_counter()
print("warm:", ipa("Haus", **kw), f"{time.perf_counter()-t0:.2f}s")

words = ["Hund", "Katze", "laufen", "springen", "Wasser", "Feuer", "arbeiten", "lesen"]
t1 = time.perf_counter()
for w in words:
    ipa(w, **kw)
t2 = time.perf_counter()
print(f"{len(words)} words no-verbalize: {t2-t1:.2f}s ({(t2-t1)/len(words)*1000:.0f} ms/word)")
