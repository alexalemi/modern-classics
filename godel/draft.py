"""Draft proofs from the ABBYY layout: one file per leaf, godel/draft/NNN.txt,
in the markup the page proofreaders correct (see proof_prompt.txt).

    python3 godel/draft.py

Markup:
    # leaf NNN · page P              first line
    ⟨cont⟩ ...                       paragraph continuing from the last leaf
    ## Title                         chapter or section heading
    > line                           displayed matter (formula, list item,
                                     example sentence): one line per line
    [FN 8] text                      footnote 8; [FN cont] continues one
    [ART] what                       a figure or table (redrawn by hand)
A paragraph ending with ⟨cont⟩ continues on the next leaf. Running heads
and page numbers are dropped here. Footnotes are told from body text by
line spacing (about 80 px per line against 100: they are set smaller).
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import abbyy  # noqa: E402

FIRST, LAST = 13, 129          # Acknowledgments .. Bibliography
DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}


def is_word(k):
    k = k.lower()
    return k in DICT or k.rstrip("s") in DICT or k[:-2] in DICT or k[:-3] in DICT or k[:-1] in DICT


def soft(t):
    def one(m):
        x, y = m.group(1), m.group(2)
        if is_word(x + y) or not (is_word(x) and is_word(y)):
            return x + y
        return x + "-" + y
    t = re.sub(r"([A-Za-z]+)­([A-Za-z]+)", one, t)
    return t.replace("­", "-")


def clean(t):
    t = soft(t)
    t = re.sub(r"\bGodel", "Gödel", t)
    return t


def line_height(p):
    return (p["b"] - p["t"]) / max(1, len(p["lines"]))


def main():
    out_dir = HERE / "draft"
    out_dir.mkdir(exist_ok=True)
    open_fn = False
    for leaf, ps in abbyy.pages():
        if leaf < FIRST or leaf > LAST:
            continue
        ps = sorted(ps, key=lambda p: p["t"])
        page = leaf - 14 if leaf >= 17 else None      # leaf 17 is page 3
        body, notes = [], []
        in_notes = False
        for i, p in enumerate(ps):
            t = p["text"].strip()
            plain = re.sub(r"[*^{}]", "", t)
            if p["size"] >= 30:                       # chapter numeral
                body.append(("H", "## " + plain.strip()))
                continue
            # running head: the top line, a page number beside a title (the
            # old-style figures OCR as letters: "io" for 10)
            if i == 0 and p["t"] < 330 and len(plain.split()) <= 12:
                continue
            # page number alone (a chapter's first page prints it at the foot)
            if re.fullmatch(r"\W*[\dIVXLivxlo]{1,4}\W*", plain):
                continue
            lh = line_height(p)
            starts_fn = re.match(r"\^\{(\d+)\}\s*", t)
            if starts_fn and (lh <= 88 or len(p["lines"]) == 1):
                in_notes = True
                notes.append(f"[FN {starts_fn.group(1)}] " + clean(t[starts_fn.end():]))
                continue
            if in_notes:
                notes[-1] += " " + clean(t)
                continue
            # an open footnote from the last leaf finishes at this leaf's foot
            if open_fn and p is ps[-1] and lh <= 86 and len(p["lines"]) >= 1 and p["t"] > 2400:
                notes.append("[FN cont] " + clean(t))
                continue
            text = clean(t)
            short = len(p["lines"]) == 1 and len(plain.split()) <= 9 and not re.search(r"[.,;:]$", plain)
            if short and p["indent"] <= 10 and p["left"] < 60 and re.match(r"[A-Z]", plain):
                body.append(("H", "## " + text))
                continue
            if p["left"] >= 100 or (len(p["lines"]) <= 2 and p["indent"] <= 10 and p["left"] >= 40):
                for l in p["lines"]:
                    body.append(("D", "> " + clean(l.strip())))
                continue
            body.append(("P", text))
        open_fn = bool(notes) and not re.search(r"[.?!)”\"’']$", notes[-1])
        # a leaf that opens unindented, lower case, continues a paragraph
        lines = [f"# leaf {leaf:03d} · page {page or '?'}"]
        for k, (kind, text) in enumerate(body):
            if kind == "P" and k == 0:
                first = next(p for p in ps if clean(p["text"].strip()) == text)
                if first["indent"] < 30 and (text[:1].islower() or text[:1] in "(,;"):
                    text = "⟨cont⟩ " + text
            lines.append(text)
        if body and body[-1][0] == "P" and not re.search(r"[.?!:”\"’')]$", body[-1][1]):
            lines[-1] += " ⟨cont⟩"
        lines += notes
        (out_dir / f"{leaf:03d}.txt").write_text("\n\n".join(lines) + "\n")
    print("drafted", len(list(out_dir.glob("*.txt"))), "leaves")


if __name__ == "__main__":
    main()
