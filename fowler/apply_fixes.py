"""Apply a proofreader's fixes to the OCR draft of a Fowler page.

    python3 fowler/apply_fixes.py 041 [042 ...]    # writes proof/NNN.txt

fixes/NNN.fix is a list of blocks, applied in order to preproof/NNN.txt:

    <<<
    exact text now in the draft (may span lines)
    ===
    what it should be
    >>>

Each OLD must occur EXACTLY ONCE in the text as it stands when the block is
reached, or the page is refused with the block's number: a fix that could
land in two places, or that no longer matches, is never guessed at. A whole
new page (a page the OCR destroyed) may be given as a single block
whose OLD is the entire draft body.

The result is the proof file, exactly as the page-reading pass wrote it, so
everything downstream (prep, checks) is unchanged.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SUF = ""                                   # "_kv" for the bwb_KV scan's leaves
BLOCK = re.compile(r"^<<<\n(.*?)\n===\n(.*?)\n?>>>$", re.S | re.M)


def ascii_quotes(t):
    return t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')


def apply(leaf):
    draft = (HERE / f"preproof{SUF}" / f"{leaf}.txt").read_text()
    fix = (HERE / f"fixes{SUF}" / f"{leaf}.fix").read_text()
    blocks = BLOCK.findall(fix)
    leftover = BLOCK.sub("", fix).strip()
    if leftover:
        return f"{leaf}: text outside any block: {leftover[:80]!r}"
    # the format is ASCII quotes throughout (Fowler's stress mark is a plain
    # '): the draft AND every block are normalised before matching, so a
    # block works whichever form its writer typed
    text = ascii_quotes(draft)
    blocks = [(ascii_quotes(o), ascii_quotes(n)) for o, n in blocks]
    for k, (old, new) in enumerate(blocks, 1):
        n = text.count(old)
        if n != 1:
            return f"{leaf}: block {k} matches {n} times: {old[:60]!r}"
        text = text.replace(old, new, 1)
    text = re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"

    if not re.match(r"page: \S+\n\n", text):
        return f"{leaf}: first line must be 'page: N' then a blank line"
    (HERE / f"proof{SUF}" / f"{leaf}.txt").write_text(text)
    return None


def main(argv):
    global SUF
    bad = 0
    args = argv[1:]
    if args and args[0] == "kv":          # python3 fowler/apply_fixes.py kv 077
        SUF, args = "_kv", args[1:]
    for leaf in args:
        err = apply(leaf.zfill(3))
        if err:
            print(err)
            bad += 1
        else:
            print(f"{leaf}: ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
