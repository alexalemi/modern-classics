"""Per-book checks for the Ethics that verify.py structurally cannot do.

Two lessons from earlier books are built in:
  - IT EXITS NONZERO. epictetus/check.py printed findings and returned
    success for 48 files, so a real defect rode straight through a
    `check && commit` chain.
  - IT MIRRORS THE RENDERER RATHER THAN APPROXIMATING IT. Every
    disagreement between a check and assemble.py costs an edit to
    correct prose, so the heading test asks assemble.is_subheading and
    the emphasis test asks assemble.EMPH.

THE DECISIVE CHECK HERE IS CITATION PARITY. The Ethics is a machine of
1,075 cross-references and prep.py has already resolved every one of
them into the source files; the translator's job is to carry them
through untouched. A citation is the only thing in this book a reader
cannot repair for themselves, and a dropped or altered one moves the
word ratio by nothing at all.
"""
import collections
import pathlib
import re
import sys

BOOK = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BOOK.parent))
sys.path.insert(0, str(BOOK))
import assemble  # noqa: E402

SRC = BOOK / "chapters"
MOD = BOOK / "modern_chapters"

CITE = re.compile(r"\((?:by |see |compare |in |from )?"
                  r"(?:Part \d+|Proposition \d+|Definition \d+|Axiom \d+|"
                  r"Postulate \d+|Lemma \d+|the Axiom|the Definition)"
                  r"[^)]*\)")
PROP = re.compile(r"^Proposition (\d+)$", re.M)
NUM = re.compile(r"\d[\d,./]*(?<![.,/])")

# The thou-family, as in augustine/ and grimm/. Elwes has almost none,
# which is the point: what he has is a thin Victorian layer over an
# argument that is not old, and it all goes.
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|hath|hast|doth|dost|art|shalt|wilt|whilst|"
    r"whatsoever|whensoever|wheresoever|whereof|wherein|whereby|"
    r"wherefore|herein|thereof|therein|thereto|thereby|hereby|"
    r"appertain|appertains|appertaineth|nought|betwixt|amongst|"
    r"unto|ere|oft|sundry|divers)\b", re.I)
# Exemptions by EXACT PHRASE, never by loosening the sweep (grimm rule).
ARCHAIC_OK = [
    # Part 1, Proposition 15, pinned in must_contain. The line is famous
    # in this wording and the archaism is doing the work; everywhere
    # else "whatsoever" goes.
    "Whatsoever is, is in God",
]


def cites(text):
    return collections.Counter(re.sub(r"\s+", " ", c)
                               for c in CITE.findall(text))


# AN ENUMERATOR IS NOT A MEASURED VALUE, and Elwes sets them four
# ways: at the head of a paragraph, after a colon and one space,
# after a colon and two, after a colon and a dash, and simply after
# the previous sentence's full stop ('...Corollary).  2. That God
# cannot properly be styled...'). Each form missed left its digit
# counted as though a quantity had gone missing from the
# translation. The trailing capital is what distinguishes an
# enumerated clause from a figure that happens to end a sentence.
ENUM = re.compile("(?:^|\\n|:[\\s\u2014-]+|(?<=[.)])\\s+)"
                  "\\d+\\.(?=\\s+[A-Z])")


def numbers(text):
    """Counted, not a set: a set cannot see a dropped duplicate (hume).

    Enumerators are removed first. "Corollary 1. It follows: 1. That
    there can be no cause..." restates its own number, and writing that
    as "It follows, first, that" is a rendering decision, not a lost
    value. What this check is for is a measured quantity going missing.
    """
    text = ENUM.sub(" ", re.sub(CITE, " ", text))
    return collections.Counter(NUM.findall(text))


def main():
    out = []
    files = sorted(SRC.glob("*.txt"))
    done = 0
    for s in files:
        m = MOD / s.name
        if not m.exists():
            continue
        done += 1
        src, mod = s.read_text(), m.read_text()
        where = s.name

        # 1. CITATION PARITY -- the check this book exists for.
        cs, cm = cites(src), cites(mod)
        lost = cs - cm
        made = cm - cs
        if lost:
            out.append(f"{where}: citations dropped or altered: "
                       f"{list(lost)[:4]}")
        if made:
            out.append(f"{where}: citations invented: {list(made)[:4]}")

        # 2. PROPOSITION SEQUENCE, exact and in order.
        ps, pm = PROP.findall(src), PROP.findall(mod)
        if ps != pm:
            out.append(f"{where}: propositions differ — source {ps[:8]} "
                       f"vs modern {pm[:8]}")

        # 3. Q.E.D. and Footnote parity.
        for token in ("Q.E.D.", "Footnote:"):
            a, b = src.count(token), mod.count(token)
            if a != b:
                out.append(f"{where}: {token} appears {a}x in source, "
                           f"{b}x in translation")

        # 4. The fleming numeric diff, COUNTED (hume). Citations are
        #    excluded because they are checked exactly above and their
        #    numerals would swamp everything else.
        d = numbers(src) - numbers(mod)
        if d:
            out.append(f"{where}: numbers lost: {sorted(d)[:8]}")

        # 5. Archaism sweep.
        body = mod
        for ok in ARCHAIC_OK:
            body = body.replace(ok, "")
        hits = collections.Counter(w.lower() for w in ARCHAIC.findall(body))
        if hits:
            out.append(f"{where}: archaic forms survive: "
                       + ", ".join(f"{w}x{n}" if n > 1 else w
                                   for w, n in sorted(hits.items())))

        # 6. Emphasis parity, asked of the renderer itself, and no
        #    stray delimiter left behind (the boethius "can*not*" trap).
        es = len(assemble.EMPH.findall(src))
        em = len(assemble.EMPH.findall(mod))
        if es != em:
            out.append(f"{where}: {es} emphasis span(s) in source, "
                       f"{em} in translation")
        left = assemble.EMPH.sub("", mod)
        if "*" in left or "_" in left:
            out.append(f"{where}: stray emphasis delimiter that will "
                       f"ship as a literal asterisk")

        # 7. Every "Proposition N" line must render as a heading, and no
        #    line may be ALL CAPS (assemble reads one as a heading).
        for i, line in enumerate(mod.split("\n"), 1):
            t = line.strip()
            if not t or line.startswith(("\t", "    ")):
                continue
            if PROP.match(t) and not assemble.is_subheading(t):
                out.append(f"{where}:{i}: '{t}' will not render as a "
                           f"heading")
            if t.isupper() and len(t.split()) > 1:
                out.append(f"{where}:{i}: all-caps line will render as a "
                           f"heading: {t[:50]}")

    print(f"checked {done}/{len(files)} translated files")
    for line in out:
        print("  " + line)
    print(f"\n{len(out)} finding(s)" if out else "clean")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
