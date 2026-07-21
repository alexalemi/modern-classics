"""Build chapters/ + manifest.json for Galileo's Dialogue from the
it.wikisource HTML in raw/ (Dedica, Al discreto lettore, and the four
Giornate — Days — of the Dialogo, 1632).

Structure: front matter (dedication to the Grand Duke + the famous
"To the Discerning Reader" foreword) as file 000 with split headings;
each Day is one *section* stitched from ~3200-Italian-word part files
split at speaker-turn boundaries. Speaker turns are marked in the
source as bold small-caps "Salv."/"Sagr."/"Simp." at paragraph heads;
the prep expands them to full names on their own line (SALVIATI /
SAGREDO / SIMPLICIO) followed by the speech — the Plato-dialogues
convention that assemble.py renders as bold speaker tags.

Ratio note for verify: Italian → modern English runs ≈ 0.95–1.25;
run verify.py with default bounds (0.6–1.6 is safe) or 0.85–1.35.

WARNING: do NOT re-run this script once translation has started —
part boundaries are packed from turn word counts, so any upstream
change reflows file boundaries and orphans already-translated parts.
The 2026-07-21 artifact fixes (footnote residue, lacunae, mid-
paragraph speaker markers, and bare SALV/SAGR/SIMP tokens that carry
no small-caps span) were hand-applied to chapters/ and folded in
here only so a from-scratch re-run converges to the same text.
"""

import html as H
import json
import re
from pathlib import Path

BOOK = Path(__file__).parent
TARGET = 3200

SPEAKERS = {"Salv": "SALVIATI", "Sagr": "SAGREDO", "Simp": "SIMPLICIO"}
DAYS = [("giornata1", "The First Day"), ("giornata2", "The Second Day"),
        ("giornata3", "The Third Day"), ("giornata4", "The Fourth Day")]


def strip_margin_notes(t):
    """Remove the printed margin summaries (postille), rendered by
    wikisource as position:absolute spans interleaved mid-sentence.
    They contain nested spans, so count depth to find the close."""
    out, i = [], 0
    while True:
        j = t.find('<span style="position: absolute', i)
        if j < 0:
            out.append(t[i:])
            break
        out.append(t[i:j])
        depth, k = 0, len(t)
        for m in re.finditer(r"<span|</span>", t[j:]):
            depth += 1 if m.group(0) == "<span" else -1
            if depth == 0:
                k = j + m.end()
                break
        i = k
    return "".join(out)


def clean_html(name):
    t = BOOK.joinpath("raw", f"{name}.html").read_text()
    t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.S)
    t = re.sub(r'<sup[^>]*class="reference"[^>]*>.*?</sup>', "", t, flags=re.S)
    t = re.sub(r'<ol class="references">.*?</ol>', "", t, flags=re.S)
    t = re.sub(r'<div class="ws-noexport"[^>]*>.*?</div>', "", t, flags=re.S)
    t = strip_margin_notes(t)
    # a third postille form: a full-sentence summary wrapped in a
    # small-caps span (>=4 words) interleaved mid-paragraph. Speaker
    # tags (Salv/Sagr/Simp) and inline proper names (Galileo, Ticone,
    # ...) are 1-2 words, so a word-count gate spares them.
    def _drop_smallcaps_postille(m):
        inner = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        return "" if len(inner.split()) >= 4 else m.group(0)
    t = re.sub(r'<span style="font-variant:small-caps">(.*?)</span>',
               _drop_smallcaps_postille, t, flags=re.S)
    # mark speaker tags before stripping markup (<b> appears outside
    # or inside the small-caps span depending on the transcriber)
    t = re.sub(r"(?:<b>)?<span[^>]*small-caps[^>]*>\s*(?:<b>)?\s*(Salv|Sagr|Simp)\.?\s*(?:</b>)?\s*</span>(?:</b>)?\.?",
               lambda m: f"\n@@{m.group(1)}@@ ", t)
    # a handful of tags in the source are bare uppercase tokens with no
    # small-caps span at all (SALV/SAGR/SIMP), sometimes mid-sentence
    t = re.sub(r"(?:(?<=^)|(?<=[.!?…»]) )\s*(SALV|SAGR|SIMP)\b\.?\s+",
               lambda m: f"\n@@{m.group(1).title()}@@ ", t)
    paras = re.findall(r"<p[^>]*>(.*?)</p>", t, flags=re.S)
    out = []
    for p in paras:
        text = H.unescape(re.sub(r"<[^>]+>", " ", p))
        text = re.sub(r"\[\s*p\.\s*\d+\s*modifica\s*\]", " ", text)  # wiki page markers
        text = re.sub(r"\(\d{1,3}\)", "", text)             # footnote-number residue
        text = re.sub(r"\[\[Immagine:[^\]]*\]\]", " ", text)  # empty wiki image stubs
        text = re.sub(r"\[\s*\.+\s*\]\s*", "", text)          # editorial lacunae [...]
        text = re.sub(r"\[(si)\]", r"\1", text)               # editorial supplements
        text = re.sub(r"\[\s*(?=@@)", "", text)  # stray bracket before a speaker marker
        # a speaker change mid-paragraph: split so turns_from_paras sees it
        text = " ".join(text.split())
        pieces = [s.strip() for s in
                  re.split(r"(?=@@(?:Salv|Sagr|Simp)@@)", text) if s.strip()]
        for text in pieces[:-1]:
            out.append(text)
        text = pieces[-1] if pieces else ""
        if (not text
                or text in ("SALVIATI, SAGREDO e SIMPLICIO.", "INTERLOCUTORI")
                or "<dc:" in p
                or re.fullmatch(r"GIORNATA [A-Z]+\.?", text)):
            continue
        out.append(text)
    return out


def turns_from_paras(paras):
    """Group paragraphs into (speaker, [paras]) turns."""
    turns = []
    cur_speaker, cur = None, []
    for p in paras:
        m = re.match(r"@@(Salv|Sagr|Simp)@@\s*(.*)", p)
        if m:
            if cur:
                turns.append((cur_speaker, cur))
            cur_speaker = SPEAKERS[m.group(1)]
            cur = [m.group(2)] if m.group(2) else []
        else:
            cur.append(p)
    if cur:
        turns.append((cur_speaker, cur))
    return turns


# ---- front matter --------------------------------------------------------
front = ["Front Matter", "", "To the Grand Duke"]
front += [""] + clean_html("dedica") + ["", "To the Discerning Reader", ""]
front += clean_html("lettore")
content = "\n".join(front).replace("\n\n\n", "\n\n") + "\n"
BOOK.joinpath("chapters", "000.txt").write_text(content)
manifest = [{"file": "000.txt", "title": "Front Matter", "part": 1, "of": 1,
             "words": len(content.split()),
             "split_headings": ["To the Grand Duke", "To the Discerning Reader"]}]

# ---- the four days -------------------------------------------------------
file_no = 1
for name, title in DAYS:
    turns = turns_from_paras(clean_html(name))
    total = sum(len(" ".join(ps).split()) for _, ps in turns)
    nparts = max(1, round(total / TARGET))
    per = total / nparts
    groups, cur, curw = [], [], 0
    for sp, ps in turns:
        w = len(" ".join(ps).split())
        if cur and curw + w > per * 1.2:
            groups.append(cur); cur, curw = [], 0
        cur.append((sp, ps)); curw += w
        if curw >= per:
            groups.append(cur); cur, curw = [], 0
    if cur:
        groups.append(cur)
    for part, group in enumerate(groups, 1):
        out = [title]
        if len(groups) > 1:
            out.append(f"\n(Part {part} of {len(groups)})")
        for sp, ps in group:
            if sp:
                out.append(f"\n{sp}\n" + "\n\n".join(ps))
            else:
                out.append("\n" + "\n\n".join(ps))
        content = "\n".join(out) + "\n"
        fn = f"{file_no:03d}.txt"
        BOOK.joinpath("chapters", fn).write_text(content)
        manifest.append({"file": fn, "title": title, "part": part,
                         "of": len(groups),
                         "words": len(content.split())})
        file_no += 1

BOOK.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"-> {file_no} files")
tot = sum(m["words"] for m in manifest)
print("total Italian words:", tot)
for m in manifest[:6]:
    print(f"  {m['file']}  {m['title']:<16} part {m['part']}/{m['of']} {m['words']:>6}")
print("  ...")
