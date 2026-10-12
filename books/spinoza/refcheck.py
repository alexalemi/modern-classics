"""Run the resolver over all 430 references and report, without fixing
anything. This is the burke/ocr_sweep discipline: the tool's job is to
make a human look at every case it cannot vouch for.

Three outcomes are interesting and each means something different:
  UNPARSED  the grammar met a token it does not account for. A bug in
            refs.parse, or a shape genuinely outside the grammar.
  INVALID   parsed cleanly but points at an item that does not exist.
            Either the parser misread it or SPINOZA'S OWN TEXT IS
            WRONG -- and the second happens in this collection often
            enough (tyndall's six misprints, fleming's arithmetic) that
            it must never be assumed away.
  REFUSED   deliberately untouched, with a reason.
"""
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refs as R
import structure as S
from shapes import CITE
from triage import PROSE, REFUSE, RELATIVE

BLOCK = re.compile(
    r"^[ \t]*(PROP\.\s*([IVXLC]+)\.|Proof|Corollary|Coroll\.|Note|"
    r"Explanation)", re.M)


def context(text):
    """[(offset, block_name, prop_number_or_None)] through one Part."""
    out = []
    for m in BLOCK.finditer(text):
        out.append((m.start(), m.group(1).split()[0].rstrip("."),
                    S.unroman(m.group(2)) if m.group(2) else None))
    return out


def here(marks, pos):
    prior = [x for x in marks if x[0] < pos]
    if not prior:
        return "", None
    block = prior[-1][1]
    prop = next((n for _, _, n in reversed(prior) if n), None)
    if block.startswith("PROP"):
        block = "Proposition"
    return block, prop


def main():
    inv = R.inventory()
    tally = collections.Counter()
    bad = collections.defaultdict(list)

    for part, text in S.split_parts(S.body()):
        marks = context(text)
        for m in re.finditer(r"\((?:[^()]{0,200})\)", text, re.S):
            raw = re.sub(r"\s+", " ", m.group(0))
            if not CITE.fullmatch(raw):
                continue
            block, prop = here(marks, m.start())

            if any(re.search(p, raw) for p, _ in REFUSE):
                tally["refused"] += 1
                continue
            inner = R.LEAD.sub("", raw[1:-1].strip())

            parsed, ok = R.parse(inner, part)

            # STRUCTURE BEATS KEYWORD. RELATIVE is a keyword test ("the
            # same Coroll.") while parse is a structural one, and three
            # references match the keyword while carrying a perfectly
            # explicit target: "(by the same Coroll. II. xi.)",
            # "(by the same Def. vii. Part I.)", "(see its Def. in the
            # same note to III. xi.)". Ask the precise reader first and
            # fall back to the fuzzy one only when it finds nothing.
            if RELATIVE.search(raw) and not (
                    ok and all(r.valid(inv, part) for r in parsed)):
                n = R.resolve_relative(raw, part, prop, block)
                if n is None:
                    tally["relative-refused"] += 1
                    bad["relative refused (not a Proposition ref)"].append(
                        (part, prop, block, raw))
                else:
                    tally["relative-ok"] += 1
                continue

            if not ok:
                tally["unparsed"] += 1
                bad["UNPARSED"].append((part, prop, block, raw))
                continue
            invalid = [r for r in parsed if not r.valid(inv, part)]
            if invalid:
                tally["invalid"] += 1
                bad["INVALID target"].append(
                    (part, prop, block, f"{raw}  ->  {invalid}"))
            else:
                tally["ok"] += 1
                if PROSE.search(raw):
                    tally["ok-but-prose"] += 1

    print("outcome:")
    for k in ("ok", "ok-but-prose", "relative-ok", "refused",
              "relative-refused", "unparsed", "invalid"):
        print(f"   {k:<20}{tally[k]:>5}")
    for why, items in sorted(bad.items()):
        print(f"\n--- {why}  ({len(items)})")
        for part, prop, block, s in items[:14]:
            print(f"    P{part} {block[:11]:<12} of {str(prop):<5} {s[:78]}")
        if len(items) > 14:
            print(f"    ... and {len(items) - 14} more")


if __name__ == "__main__":
    main()
