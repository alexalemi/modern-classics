"""Build chapters/ + manifest.json for Cato's Letters (selected) from
the Wikisource HTML in raw/NNN.html.

Trenchard & Gordon's Cato's Letters (1720–23) run to 138 letters plus
extras; no complete Gutenberg/SE source exists. This volume selects 18
letters — the ones revolutionary-era Americans actually reprinted and
quoted (the free-speech and power letters, the natural-rights core
59–63, property, the colonies letter, the farewell); the selection is
documented in text_analysis.txt.

Per letter: parse the mw-parser HTML; drop the wiki navigation header
(everything before the salutation "SIR," or the first body paragraph),
footnotes, and the signature block; title from titles the orchestrator
embeds below (Wikisource titles, shortened). One letter per file —
they average ~2,400 words, ideal single-agent size.
"""

import html as H
import json
import re
from pathlib import Path

BOOK = Path(__file__).parent

# (number, short title, author-signature G=Gordon T=Trenchard as attributed)
SELECT = [
    (15, "Of Freedom of Speech"),
    (25, "The Destructive Spirit of Arbitrary Power"),
    (31, "The Weakness and Inconsistencies of Human Nature"),
    (33, "Cautions Against the Encroachments of Power"),
    (35, "Of Public Spirit"),
    (38, "The Right of the People to Judge of Government"),
    (42, "Considerations on the Nature of Laws"),
    (45, "Of the Equality and Inequality of Men"),
    (59, "Liberty Proved to Be the Unalienable Right of All Mankind"),
    (60, "All Government Instituted by Men, for the Good of Men"),
    (61, "How Free Governments Are to Be Framed So As to Last"),
    (62, "The Nature and Extent of Liberty"),
    (63, "Civil Liberty Produces All Civil Blessings"),
    (68, "Property and Commerce Secure in a Free Government Only"),
    (84, "Property the First Principle of Power"),
    (106, "Of Plantations and Colonies"),
    (115, "The Encroaching Nature of Power"),
    (138, "Cato's Farewell"),
]

manifest = []
for i, (n, short) in enumerate(SELECT):
    t = BOOK.joinpath("raw", f"{n:03d}.html").read_text()
    t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.S)
    t = re.sub(r'<sup[^>]*class="reference"[^>]*>.*?</sup>', "", t, flags=re.S)
    t = re.sub(r'<ol class="references">.*?</ol>', "", t, flags=re.S)
    paras = re.findall(r"<p[^>]*>(.*?)</p>", t, flags=re.S)
    out, started = [], False
    for p in paras:
        text = " ".join(H.unescape(re.sub(r"<[^>]+>", " ", p)).replace("​", "").split())
        if not text:
            continue
        if not started:
            if re.match(r"^SIR[,.]?$", text) or text.startswith("SIR,"):
                started = True
                out.append("Sir,")
                rest = text[4:].strip() if text.startswith("SIR,") and len(text) > 5 else ""
                if rest:
                    out.append(rest)
            continue
        if re.match(r"^[GT]\.?$|^I am, &c\.|^T and G|^G$|^T$", text):
            out.append(text.rstrip("."))
            break
        text = re.sub(r"\s*\[\d+\]\s*", " ", text)
        out.append(text)
    assert started and len(out) > 3, f"letter {n}: parse failed ({len(out)} paras)"
    title = f"Letter {n}: {short}"
    content = title + "\n\n" + "\n\n".join(out) + "\n"
    fn = f"{i:03d}.txt"
    BOOK.joinpath("chapters", fn).write_text(content)
    manifest.append({"file": fn, "title": title, "part": 1, "of": 1,
                     "words": len(content.split()), "letter": n})

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{len(manifest)} letters")
for m in manifest:
    print(f"  {m['file']} {m['words']:>6}  {m['title'][:64]}")
