"""Temporary: time each staged generation call against the real model."""

from __future__ import annotations

import time

from sprachheft.agents.generator import generate_exercises, generate_vocabulary
from sprachheft.models import Material
from sprachheft.services.generation import EXERCISE_BATCHES

material = Material(
    id=1,
    title="Mein Arbeitstag",
    level="A2",
    transcript=(
        "Heute arbeite ich im Büro. Ich trinke Kaffee und schreibe eine E-Mail "
        "an meine Kollegin. Am Nachmittag habe ich ein Meeting mit dem Team."
    ),
)

t = time.time()
vocab = generate_vocabulary(material, 2)
print(f"vocab      : {len(vocab):2d} items in {time.time() - t:5.0f}s")

for i, types in enumerate(EXERCISE_BATCHES):
    t = time.time()
    exs = generate_exercises(material, 2, types)
    print(f"batch {i} {types}: {len(exs)} in {time.time() - t:5.0f}s -> {[e.type for e in exs]}")
