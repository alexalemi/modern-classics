"""Check every book's editor's introduction. See INTRODUCTIONS.md.

    python3 check_introductions.py [book ...]

EXITS NONZERO ON ANY FAILURE (the epictetus rule: a checker that cannot
fail a build will eventually be ignored).

The checks divide into three kinds:

  MECHANICAL   word band, markup conventions, and agreement with the
               renderer -- is_subheading and EMPH are asked THEMSELVES
               rather than approximated, because every disagreement
               between a check and the renderer costs an edit to correct
               prose (the epictetus/boethius lesson).

  MANNER       the banned-phrase list. Alex asked for no mannered prose;
               this is the mechanical half of that. It cannot see bad
               writing, only the specific tics that recur, so it is a
               floor and not a verdict -- read the file too.

  IDENTITY     the author is named and a date is given. This is the one
               check here that can see an introduction written about the
               WRONG BOOK, which is otherwise invisible: it reads
               perfectly, renders perfectly, and is about Herodotus.
"""
import re
import sys
from pathlib import Path

import assemble

ROOT = Path(__file__).parent
MIN_WORDS, MAX_WORDS = 200, 650

# Each entry is (regex, why). Case-insensitive. Keep every addition
# justified by something that actually appeared -- a list nobody can
# explain gets loosened the first time it fires on good prose.
BANNED = [
    (r"\btimeless\b", "blurb vocabulary"),
    (r"\bimmortal\b", "blurb vocabulary"),
    (r"\bseminal\b", "blurb vocabulary"),
    (r"\bmasterpiece\b", "blurb vocabulary"),
    (r"\bmagisterial\b", "blurb vocabulary"),
    (r"\btowering\b", "blurb vocabulary"),
    (r"\bluminous\b", "blurb vocabulary"),
    (r"\bunflinching(ly)?\b", "blurb vocabulary"),
    (r"\bhaunting(ly)?\b", "blurb vocabulary"),
    (r"\bsearing\b", "blurb vocabulary"),
    (r"\btour de force\b", "blurb vocabulary"),
    (r"\ba testament to\b", "blurb vocabulary"),
    (r"\bprofound (meditation|reflection|insight)", "blurb vocabulary"),
    (r"\ba meditation on\b", "blurb vocabulary"),
    (r"\bdeceptively simple\b", "blurb vocabulary"),
    (r"\bahead of (its|his|her) time\b", "blurb vocabulary"),
    (r"\bneeds no introduction\b", "blurb vocabulary"),
    (r"\bone of the (most|greatest)\b", "importance in place of information"),
    (r"\bremains one of\b", "importance in place of information"),
    (r"\b(still |just )?as relevant (today|now)\b", "relevance-mongering"),
    (r"\bspeaks? (to us|across)\b", "relevance-mongering"),
    (r"\bresonate", "relevance-mongering"),
    (r"\bwhat it means to be human\b", "relevance-mongering"),
    (r"\bthe human condition\b", "relevance-mongering"),
    (r"\bto this day\b", "relevance-mongering"),
    (r"\bnot (just|merely|only) a .{1,40}\bbut\b", "the 'not just X but Y' tic"),
    (r"\bisn't (just|merely) \w+, it'?s\b", "the 'not just X but Y' tic"),
    (r"\bat (its|their) core\b", "filler"),
    (r"\bat the heart of\b", "filler"),
    (r"\bin many ways\b", "filler"),
    (r"\bnothing short of\b", "filler"),
    (r"\bit is no exaggeration\b", "filler"),
    (r"\binvites? (us|the reader|you) to\b", "telling the reader what to do"),
    (r"\breminds? us that\b", "telling the reader what to think"),
    (r"\bsheds? light on\b", "filler"),
    (r"\bserves? as a\b", "filler"),
    (r"\bstands? as (a|the)\b", "filler"),
    (r"\bgrapple[sd]? with\b", "filler"),
    (r"\bdelves? into\b", "filler"),
    (r"\brich tapestry\b", "filler"),
    (r"\blittle did (he|she|they)\b", "novelistic throat-clearing"),
    (r"\bdear reader\b", "address to the reader"),
    (r"\blet us (now )?(turn|begin|consider)\b", "address to the reader"),
    (r"\bwe shall see\b", "address to the reader"),
    (r"\bherein\b", "archaism"),
    (r"\bAI modernization\b", "the page header already says this"),
]

CENTURY = re.compile(r"\bcenturies?\b|\bcentury\b", re.I)
YEAR = re.compile(r"\b\d{3,4}\b")
STOP = {"the", "of", "and", "de", "von", "van", "la", "le", "saint", "sir",
        "lord", "jr", "st"}


def name_tokens(author):
    """Distinctive name words to look for, or () if there is no author."""
    if not author or author.lower() in ("anonymous", "unknown", "various"):
        return ()
    words = re.findall(r"[A-Za-zÀ-ÿŌōū'’-]+", author)
    return tuple(w for w in words
                 if len(w) >= 4 and w.lower() not in STOP)


def check(book):
    """Return a list of problem strings for one book directory."""
    bad = []
    env = assemble.read_env(book / "env")
    path = book / "introduction.txt"
    if not path.exists():
        return ["no introduction.txt"]
    raw = path.read_text()
    text = raw.strip("\n").rstrip()
    if not text:
        return ["introduction.txt is empty"]

    # --- mechanical -------------------------------------------------
    n = len(text.split())
    if not MIN_WORDS <= n <= MAX_WORDS:
        bad.append(f"{n} words, want {MIN_WORDS}-{MAX_WORDS}")
    if "--" in text:
        bad.append("contains '--'; assemble.py ships it literally while "
                   "`se typogrify` converts it, so page and epub diverge")
    for i, line in enumerate(text.split("\n"), 1):
        if line[:1] in (" ", "\t"):
            bad.append(f"line {i} is indented; it would render as <pre>")
        s = line.strip()
        if s and s == s.upper() and re.search(r"[A-Z]{2}", s):
            bad.append(f"line {i} is all caps; the renderer reads it as a heading")
        if re.match(r"#{1,6}\s|\* |\d+\. ", s):
            bad.append(f"line {i} looks like Markdown; the pipeline is markup-free")
    # emphasis must actually render, and nothing may be left over
    if "*" in assemble.EMPH.sub("", text) or re.search(
            r"(?<![A-Za-z0-9_])_", assemble.EMPH.sub("", text)):
        bad.append("an emphasis marker does not match assemble.EMPH; it "
                   "would ship as a literal asterisk or underscore")
    pars = [" ".join(p.split()) for p in text.split("\n\n") if p.strip()]
    if len(pars) < 2:
        bad.append(f"{len(pars)} paragraph(s); want three to five")
    for p in pars:
        if assemble.is_subheading(p):
            bad.append(f"renders as an <h4> heading, not a paragraph: {p[:60]!r}")

    # --- manner -----------------------------------------------------
    for pat, why in BANNED:
        m = re.search(pat, text, re.I)
        if m:
            bad.append(f"mannered: {m.group(0)!r} ({why})")

    # --- identity ---------------------------------------------------
    toks = name_tokens(env.get("AUTHOR", ""))
    if toks and not any(re.search(rf"\b{re.escape(t)}", text, re.I) for t in toks):
        bad.append(f"never names the author ({env.get('AUTHOR')})")
    if not (YEAR.search(text) or CENTURY.search(text)):
        bad.append("gives no date: no year and no century named")
    return bad


def main():
    books = sys.argv[1:]
    if not books:
        books = sorted(d.name for d in ROOT.iterdir()
                       if (d / "env").exists() and (d / "modern_chapters").exists())
    fails = 0
    missing = []
    for name in books:
        problems = check(ROOT / name)
        if problems == ["no introduction.txt"]:
            missing.append(name)
            continue
        if problems:
            fails += 1
            print(f"{name}:")
            for p in problems:
                print(f"    {p}")
    if missing:
        print(f"\n{len(missing)} without an introduction: {' '.join(missing)}")
    done = len(books) - len(missing)
    print(f"\n{done}/{len(books)} have one; {fails} with problems")
    return 1 if (fails or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
