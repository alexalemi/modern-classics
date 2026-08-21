"""Dump every refused reference with exact text and position context,
so the hand table can be written against the real strings."""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refs as R
import structure as S
from refcheck import context, here
from shapes import CITE
from triage import REFUSE, RELATIVE

inv = R.inventory()
n = 0
for part, text in S.split_parts(S.body()):
    marks = context(text)
    for m in re.finditer(r"\((?:[^()]{0,200})\)", text, re.S):
        raw = re.sub(r"\s+", " ", m.group(0))
        if not CITE.fullmatch(raw):
            continue
        block, prop = here(marks, m.start())
        why = None
        for pat, reason in REFUSE:
            if re.search(pat, raw):
                why = reason
                break
        if why is None:
            inner = R.LEAD.sub("", raw[1:-1].strip())
            parsed, ok = R.parse(inner, part)
            if RELATIVE.search(raw) and not (
                    ok and all(r.valid(inv, part) for r in parsed)):
                if R.resolve_relative(raw, part, prop, block) is None:
                    why = "relative to a non-Proposition"
        if why:
            n += 1
            print(f"{n:>2}. P{part} {block} of {prop}")
            print(f"    {raw}")
            print(f"    -- {why[:70]}")
print(f"\n{n} refused")
