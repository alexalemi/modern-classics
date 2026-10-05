"""Ernest Nagel and James R. Newman, Gödel's Proof (New York University Press,
1958) -> chapters/ and modern_chapters/ (a RESTORED EDITION).

    python3 godel/draft.py && python3 godel/apply_fixes.py && python3 godel/prep.py

The 1958 text was never renewed (A359592; no renewal 1985-86), so it is in
the US public domain. Its acknowledgments say several diagrams came from
the June 1956 Scientific American, which WAS renewed (RE195135, 1984). So
nothing of the printed art is reproduced: the three figures are drawn
afresh from their mathematics (figures.py), the four tables are set anew
from their contents (TABLES below), and the explanatory captions printed
under them -- which may be the magazine's words -- are replaced by this
edition's own. The authors' text is otherwise as printed.

Words: one scan (University of Florida, gdelsproof00nage), its ABBYY OCR
drafted per leaf (draft.py), corrected against the page image by readers
working from proof_prompt.txt as patches (fixes/, apply_fixes.py -> proof/).

Composition: the proofs' paragraphs joined across page breaks (⟨cont⟩);
displayed formulas as tab-indented lines, two-column displays as tables;
footnotes as "Footnote: ⁿ ..." after the paragraph that cites them; an
exponent Unicode cannot write (2^{m}, 3^{11²}) set as LaTeX.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
DICT = {w.strip().lower() for w in open("/usr/share/dict/words")}
SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
UNSUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
SUB_UN = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

# chapter numeral -> file title; the proofs give numeral and title as two
# headings, the manifest one
CHAPTERS = {"I": "Introduction", "II": "The Problem of Consistency",
            "III": "Absolute Proofs of Consistency",
            "IV": "The Systematic Codification of Formal Logic",
            "V": "An Example of a Successful Absolute Proof of Consistency",
            "VI": "The Idea of Mapping and Its Use in Mathematics",
            "VII": "Gödel's Proofs", "VIII": "Concluding Reflections"}

ED = "set anew for this edition"
TABLES = {
    # Boole's syllogism (printed p. 41)
    "ART Table 1: a syllogism": [
        f"*Table 1* ({ED}): a syllogism, first in words, then in Boole's notation, where ‘*g* ⊂ *p*’ says that the class of gentlemen is contained in the class of polite persons and a line over a letter means ‘not’, and last as equations, where two letters together mean the class of things having both characteristics and ‘= 0’ that the class has no members.",
        "\tAll gentlemen are polite. | *g* ⊂ *p* | *g p̄* = 0\n"
        "\tNo bankers are polite. | *b* ⊂ *p̄* | *bp* = 0\n"
        "\tNo gentlemen are bankers. | ∴ *g* ⊂ *b̄* | *gb* = 0"],
    # the constant signs (p. 70)
    "ART Table 2: the ten constant signs": [
        f"*Table 2* ({ED}): the ten constant signs, their Gödel numbers, and their usual meanings.",
        "\tConstant sign | Gödel number | Usual meaning\n"
        "\t∼ | 1 | not\n\t∨ | 2 | or\n\t⊃ | 3 | If . . . then\n\t∃ | 4 | There is an . . .\n"
        "\t= | 5 | equals\n\t0 | 6 | zero\n\ts | 7 | The immediate successor of\n"
        "\t( | 8 | punctuation mark\n\t) | 9 | punctuation mark\n\t, | 10 | punctuation mark"],
    # the three kinds of variables (pp. 71-72)
    "ART Table 1: numerical variables": [
        f"*Table 3* ({ED}): the variables and their Gödel numbers. Numerical variables take the primes greater than 10:",
        "\tNumerical variable | Gödel number | A possible substitution instance\n"
        "\t*x* | 11 | 0\n\t*y* | 13 | s0\n\t*z* | 17 | *y*"],
    "ART Table 2: sentential variables": [
        "Sentential variables take the squares of the primes greater than 10:",
        "\tSentential variable | Gödel number | A possible substitution instance\n"
        "\t*p* | 11² | 0 = 0\n\t*q* | 13² | (∃*x*)(*x* = sy)\n\t*r* | 17² | *p* ⊃ *q*"],
    "ART Table 3: predicate variables": [
        "Predicate variables take the cubes of the primes greater than 10:",
        "\tPredicate variable | Gödel number | A possible substitution instance\n"
        "\t*P* | 11³ | Prime\n\t*Q* | 13³ | Composite\n\t*R* | 17³ | Greater than"],
    # 243,000,000 and '0 = 0' (p. 76)
    "ART Table 4": [
        f"*Table 4* ({ED}): the Gödel number 243,000,000 taken apart. Read down, the number is factored into prime powers, and the exponents 6, 5, 6 are read as the signs they number, giving the formula ‘0 = 0’; read up, the number is built from the formula.",
        "\tA | 243,000,000\n\tB | 64 × 243 × 15,625\n\tC | 2⁶ × 3⁵ × 5⁶\n"
        "\tD | 6, 5, 6 → 0, =, 0\n\tE | 0 = 0"],
    # the two truth tables of the Appendix (p. 112): the authors' own text
    "ART Table: truth table for the first axiom": [
        "\t*p* | (*p* ∨ *p*) | (*p* ∨ *p*) ⊃ *p*\n\tK₁ | K₁ | K₁\n\tK₂ | K₂ | K₁"],
    "ART Table: truth table for the second axiom": [
        "\t*p* | *q* | (*p* ∨ *q*) | *p* ⊃ (*p* ∨ *q*)\n"
        "\tK₁ | K₁ | K₁ | K₁\n\tK₁ | K₂ | K₁ | K₁\n\tK₂ | K₁ | K₁ | K₁\n\tK₂ | K₂ | K₂ | K₁"],
}
FIGURES = {
    "ART Fig. 1": "[Figure aa: Fig. 1, drawn for this edition — A triangle. Its three vertices, each marked K, are the members of the class K; its three sides, each marked L, are the members of the class L. Every pair of vertices lies on just one side, and every side contains just two vertices.]",
    "ART Fig. 2": "[Figure ab: Fig. 2, drawn for this edition — On the left, figures in a plane: a straight segment, a square, and two parallel segments. On the right, the same figures on the surface of a sphere, where straight lines become arcs of great circles: a single arc, a four-sided region bounded by arcs, and two arcs which, extended (dotted), meet at the poles.]",
    "ART Figure 3": "[Figure ac: Fig. 3, drawn for this edition — (a) The theorem of Pappus. A, B, C lie on line I and A′, B′, C′ on line II; the points R, S, T where AB′ crosses A′B, AC′ crosses A′C, and BC′ crosses B′C lie on one line, III. (b) Its dual. Lines A, B, C pass through point I and lines A′, B′, C′ through point II; the lines R, S, T, each drawn through a pair of the crossing points, pass through one point, III.]",
}
# printed caption lines a reader kept (they go with the redrawn art)
DROP = ["Predicate Variables are associated with the cubes of prime numbers greater than 10."]


def is_word(k):
    k = k.lower()
    return k in DICT or k.rstrip("s") in DICT or k[:-2] in DICT or k[:-3] in DICT or k[:-1] in DICT


def join_break(a, b):
    """Join text broken at a page: a line-end hyphen closes up if the halves
    make a word (simultane- ously), and stays if they are two words."""
    m = re.search(r"([A-Za-z]+)-$", a)
    if m:
        w = re.match(r"[A-Za-z]+", b)
        if w and (is_word(m.group(1) + w.group(0)) or not (is_word(m.group(1)) and is_word(w.group(0)))):
            return a[:-1] + b
        return a + b
    return a + " " + b


def latex(token):
    """'2^{*m*}', '3^{11²}', '*p*⁹_{*m*+10}' -> \\(...\\)."""
    t = token.replace("*", "")
    t = re.sub(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "^{" + m.group(1).translate(UNSUP) + "}", t)
    t = t.replace("×", r"\times ")
    return r"\(" + t + r"\)"


def midword(text):
    """An italic letter set against a roman one ('s*y*': the successor of y)
    cannot be marked: assemble's emphasis needs no letter before the
    asterisk. Those few are set roman."""
    return re.sub(r"(?<=[A-Za-z])\*([A-Za-z]{1,2})\*", r"\1", text)


def exponents(text):
    text = midword(text)
    return re.sub(r"[^\s(),;:]*[\^_]\{[^\s]*", lambda m: latex(m.group(0).rstrip(".,;")) + m.group(0)[len(m.group(0).rstrip(".,;")):], text)


def blocks():
    """The proofs as one stream: (leaf, kind, text). kinds: H, P, D (display
    line), FN (number, text), ART."""
    out = []
    for f in sorted((HERE / "proof").glob("*.txt")):
        leaf = int(f.stem)
        paras = [p.strip() for p in re.split(r"\n\s*\n", f.read_text()) if p.strip()]
        for p in paras:
            if p.startswith("# leaf"):
                continue
            if p in DROP:
                continue
            if p.startswith("## "):
                out.append((leaf, "H", p[3:].replace("*", "").strip()))
            elif p.startswith("[FN "):
                m = re.match(r"\[FN (\w+)\]\s*(.*)", p, re.S)
                out.append((leaf, "FN", (m.group(1), " ".join(m.group(2).split()))))
            elif p.startswith("[ART"):
                out.append((leaf, "ART", p.strip("[]")))
            elif p.startswith("> "):
                for line in p.split("\n"):
                    out.append((leaf, "D", line[2:].strip() if line.startswith("> ") else line.strip()))
            else:
                out.append((leaf, "P", " ".join(p.split())))
    return out


def compose():
    secs, cur = [], None
    pending_num = None
    notes = {}                  # number -> text
    last_fn = None
    for leaf, kind, text in blocks():
        if kind == "H":
            if text in CHAPTERS:
                pending_num = text
                continue
            if pending_num:
                assert text == CHAPTERS[pending_num], (pending_num, text)
                cur = (f"{pending_num}. {text}", [])
                secs.append(cur)
                pending_num = None
                continue
            if text in ("Gödel's Proof",):           # the half-title
                continue
            if text == "Acknowledgments":
                cur = ("Acknowledgments", [("P", "*To Bertrand Russell*")])
                secs.append(cur)
                continue
            if text == "Appendix":
                cur = ("Appendix: Notes", [])
                secs.append(cur)
                continue
            if text == "Notes":
                continue
            if text == "Brief Bibliography":
                cur = ("Brief Bibliography", [])
                secs.append(cur)
                continue
            cur[1].append(("H", text))
            continue
        items = cur[1]
        if kind == "FN":
            num, body = text
            if num == "cont":
                notes[last_fn] = join_break(notes[last_fn].rstrip(" ⟨cont⟩").rstrip(), body)
            else:
                last_fn = num
                notes[num] = body
                items.append(("FNREF", num, leaf))
            continue
        if kind == "ART":
            key = next((k for k in list(TABLES) + list(FIGURES) if text.startswith(k)), None)
            assert key, text
            if key in FIGURES:
                items.append(("P", FIGURES[key]))
            else:
                for t in TABLES[key]:
                    items.append(("T", t) if t.startswith("\t") else ("P", t))
            continue
        if kind == "D" and text.startswith("⟨cont⟩"):
            k = max(i for i, x in enumerate(items) if x[0] == "D")
            items[k] = ("D", join_break(items[k][1].replace("⟨cont⟩", "").rstrip(), text[len("⟨cont⟩"):].strip()))
            continue
        if kind == "P" and text.startswith("⟨cont⟩"):
            open_ = [i for i, x in enumerate(items) if x[0] in ("P", "D") and "⟨cont⟩" in x[1]]
            if not open_:
                # the last page did not mark its paragraph open: join to the
                # last paragraph, and say so
                open_ = [i for i, x in enumerate(items) if x[0] == "P"]
                print(f"  leaf {leaf}: ⟨cont⟩ with no open paragraph; joined to the last", file=sys.stderr)
            k = max(open_)
            items[k] = (items[k][0], join_break(items[k][1].replace("⟨cont⟩", "").rstrip(), text[len("⟨cont⟩"):].strip()))
            continue
        items.append((kind, text))
    return secs, notes


def place_notes(items, notes):
    """Each footnote after the paragraph that carries its mark; a footnote
    whose mark is not found goes after the last paragraph of its leaf."""
    out = []
    refs = [x for x in items if x[0] == "FNREF"]
    body = [x for x in items if x[0] != "FNREF"]
    placed = set()
    for x in body:
        out.append(x)
        if x[0] in ("P", "D"):
            for _, num, _ in refs:
                mark = num.translate(SUP)
                if num not in placed and re.search(r"(?<![⁰-⁹\d×])" + mark + r"(?![⁰-⁹])", x[1]):
                    out.append(("FN", num))
                    placed.add(num)
    missing = [num for _, num, _ in refs if num not in placed]
    for num in missing:
        out.append(("FN", num))
    return out, missing


def render(title, items, notes):
    lines = [title, ""]
    k = 0
    while k < len(items):
        kind, text = items[k][0], items[k][1]
        if kind == "D":
            group = []
            while k < len(items) and items[k][0] == "D":
                group.append(items[k][1])
                k += 1
            # two-column displays are tables; single lines are lined matter
            for is_tab in (True, False):
                pass
            runs, run = [], []
            for g in group:
                t = " | " in g
                if run and (" | " in run[-1]) != t:
                    runs.append(run)
                    run = []
                run.append(g)
            runs.append(run)
            for r in runs:
                lines.append("\n".join("\t" + exponents(g) for g in r))
                lines.append("")
            continue
        if kind == "H":
            lines.append(text)
        elif kind == "FN":
            lines.append(f"Footnote: {text.translate(SUP)} " + exponents(notes[text]))
        elif kind == "T":
            lines.append(text)
        else:
            lines.append(exponents(text))
        lines.append("")
        k += 1
    return "\n".join(lines).rstrip() + "\n"


def main():
    secs, notes = compose()
    for d in ("chapters", "modern_chapters"):
        (HERE / d).mkdir(exist_ok=True)
        for f in (HERE / d).glob("*.txt"):
            f.unlink()
    manifest = []
    all_missing = []
    for i, (title, items) in enumerate(secs):
        if title == "Brief Bibliography":
            items = [(k, t.replace(" | ", ". ", 1)) if k == "P" else (k, t) for k, t in items]
        items, missing = place_notes(items, notes)
        all_missing += [(title, m) for m in missing]
        text = render(title, items, notes)
        assert "⟨cont⟩" not in text and "[ART" not in text, (title, re.findall(r".{40}(?:⟨cont⟩|\[ART).{20}", text))
        bare = re.sub(r"\[Figure (\w+): [^\]]*\]", r"[Figure \1]", text)
        (HERE / f"chapters/{i:03d}.txt").write_text(bare)
        (HERE / f"modern_chapters/{i:03d}.txt").write_text(text)
        manifest.append({"file": f"{i:03d}.txt", "title": title, "part": 1, "of": 1})
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(len(secs), "sections;", len(notes), "footnotes;", sum(len(t.split()) for t, _ in secs), "title words")
    for t, m in all_missing:
        print(f"  footnote {m} ({t}): mark not found, placed at the end", file=sys.stderr)


if __name__ == "__main__":
    main()
