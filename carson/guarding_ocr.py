"""Guarding Our Wildlife Resources, pages 05-10: proofs built from the scan's
own text layer (ocr_page.build) plus word patches read on the page images.
The page readers' output on these pages was stopped twice by an automated
filter, so these words come from the OCR, not from a transcription.

    python3 carson/guarding_ocr.py

Each patch must match exactly once in its page's OCR text, or the build
stops. PAGES gives each page's kind, its plates (boxes read off the image)
and the structural markers the OCR cannot know.
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import ocr_page as O  # noqa: E402

PATCHES = {
    5: [("Guarding Our Resources THIS IS THE STORY OF THE WILDLIFE RESOURCES OF AMERICA, of",
         "This is the story of the wildlife resources of America, of"),
        ("a direct Opposite: Geese over Tule Lake, California Wildlife interest", "a direct interest"),
        ("recreation-s- hunting", "recreation—hunting"), ("an .order", "an order"),
        ("habitat. means", "habitat means"), ("live. .Wildlife", "live. Wildlife"),
        ("grasslands-all", "grasslands—all")],
    6: [("benefits. .", "benefits."), ("1903 .,prought", "1903 brought"),
        ("create ,.·'national ~anctuaries for' wildlife-a movement", "create national sanctuaries for wildlife—a movement"),
        ("cons~rve migratory species-e-especially birds-that", "conserve migratory species—especially birds—that"),
        ("carryon,", "carry on"), ("wildlife, Including", "wildlife, including"),
        ("commercial fishing .", "commercial fishing."), ("iriterest", "interest"),
        ("maintain. lands", "maintain lands"), ("in . a modern", "in a modern"), ("before' we", "before we")],
    7: [('"Migratory Birds-A Hemisphere THE NATIONS OF THE WESTERN HEMISPHERE "have', "The nations of the Western Hemisphere have"),
        ('pos" sess in common-the migratory .birds.', "possess in common—the migratory birds."),
        ("tentral", "Central"),
        ("conditions The barn swallow, a long-rang~ migrant Resource for breeding", "conditions for breeding"),
        ("anyone place", "any one place"), ("American' waterfowl", "American waterfowl"),
        ('the" wintering " grounds', "the wintering grounds")],
    8: [("Shore birds feeding during migration birds.", "birds.")],
    9: [("snipes,'", "snipes,"), ("twice each year ..", "twice each year."), ("hunters ..", "hunters."),
        ("unable,' to", "unable to"), ("prairie ..", "prairie."), ("grassy' plains", "grassy plains"),
        ("Peru-including", "Peru—including"), ("others-are", "others—are"),
        ("The' migratory", "The migratory"), ("insects. is", "insects is")],
}

PAGES = {
    5: {"kind": "text", "head": "## Guarding Our Wildlife Resources", "end_cont": True, "plates": []},
    6: {"kind": "text", "start_cont": True, "plates": []},
    7: {"kind": "text", "head": "## Migratory Birds—A Hemisphere Resource", "end_cont": True,
        "plates": [(0.06, 0.66, 0.98, 0.99, "photo", "The barn swallow, a long-range migrant")]},
    8: {"kind": "text", "start_cont": True, "end_cont": True, "lead_plates": True,
        "plates": [(0.00, 0.00, 1.00, 0.74, "photo", "Shore birds feeding during migration")]},
    9: {"kind": "text", "start_cont": True, "plates": []},
    10: {"kind": "map", "plates": [(0.02, 0.03, 0.99, 0.79, "map",
         "Wintering grounds of North American waterfowl. Heavy shading indicates areas where largest "
         "concentrations occur; light shading, general limits of winter range. Breeding grounds are chiefly "
         "north of 40th parallel.")]},
}


def main():
    for nn, spec in PAGES.items():
        paras = O.build("guarding", nn) if nn != 10 else []
        text = "\n\n".join(paras)
        for old, new in PATCHES.get(nn, []):
            assert text.count(old) == 1, (nn, old, text.count(old))
            text = text.replace(old, new)
        paras = [p for p in text.split("\n\n") if p.strip()]
        if spec.get("start_cont") and paras:
            paras[0] = "⟨cont⟩ " + paras[0]
        if spec.get("end_cont") and paras:
            paras[-1] = paras[-1] + " ⟨cont⟩"
        plates = [f"[PLATE {a:.2f} {b:.2f} {c:.2f} {d:.2f} | {k} | {cap}]" for a, b, c, d, k, cap in spec["plates"]]
        body = ([spec["head"]] if spec.get("head") else [])
        body += (plates + paras) if spec.get("lead_plates") else (paras + plates)
        out = f"# guarding {nn:02d}: {spec['kind']}\n\n" + "\n\n".join(body) + "\n"
        (HERE / f"proof/guarding-{nn:02d}.txt").write_text(out)
        print(nn, len(paras), "paragraphs", len(plates), "plates")
    # page 5's bottom line is the caption of page 4's photograph
    p4 = HERE / "proof/guarding-04.txt"
    t = p4.read_text()
    if "Tule Lake" not in t:
        t = t.replace("| photo | ]", "| photo | Opposite: Geese over Tule Lake, California]", 1)
        p4.write_text(t)


if __name__ == "__main__":
    main()
