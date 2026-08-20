"""Structural survey of Elwes's Ethics, run BEFORE any prep is written.

The Ethics is not prose with headings; it is a machine of numbered parts
that cite each other. Every proof is a chain of references, and a
reference that does not resolve is a defect no word-ratio can see. So
find out exactly what the source does before deciding anything:
how the Parts are headed, how many of each numbered item each Part has,
every spelling of a reference, and where the translator's own footnotes
are.
"""
import collections
import pathlib
import re

SRC = (pathlib.Path(__file__).resolve().parent / "source" / "ethics.txt")
t = SRC.read_text()

# Gutenberg wrapper off
m = re.search(r"\*\*\* ?START OF TH[EI]S? PROJECT GUTENBERG[^\n]*\n", t)
if m:
    t = t[m.end():]
m = re.search(r"\*\*\* ?END OF TH[EI]S? PROJECT GUTENBERG", t)
if m:
    t = t[:m.start()]

print(f"body: {len(t.split()):,} words\n")

print("=== every line containing PART <roman>")
for m in re.finditer(r"^.*\bPART\s+[IVX]+\b.*$", t, re.M):
    print(f"   {m.start():>7}  {m.group(0).strip()[:74]!r}")

print("\n=== headings of numbered items, by form")
forms = collections.Counter()
for m in re.finditer(r"^\s*(PROP\.|Prop\.|DEFINITIONS?|AXIOMS?|POSTULATES?|"
                     r"APPENDIX|Proof|Corollary|Note|Lemma|Explanation|"
                     r"Definition of the Affects|PREFACE)\.?", t, re.M):
    forms[m.group(1)] += 1
for k, n in forms.most_common():
    print(f"   {k:<28} {n:>5}")

print("\n=== reference spellings (whitespace-normalised)")
flat = re.sub(r"\s+", " ", t)
refs = re.findall(r"\((?:[^()]{0,80})\)", flat)
cited = [r for r in refs
         if re.search(r"\b(Prop|Deff?|Ax|Post|Coroll|Lemma|Note)\b", r)]
shapes = collections.Counter(
    re.sub(r"\b[ivxlc]+\b", "<n>", re.sub(r"\b[IVXLC]+\b", "<N>", r))
    for r in cited)
for k, n in shapes.most_common(22):
    print(f"   {n:>5}  {k[:70]}")
print(f"   ... {len(cited):,} parenthetical references in all, "
      f"{len(shapes)} distinct shapes")

print("\n=== references broken across a line in the RAW text")
broken = re.findall(r"\((?:[^()\n]{0,40})\n[^()]{0,40}\)", t)
print(f"   {len(broken)} of them, e.g.")
for b in broken[:5]:
    print("      ", repr(b))

print("\n=== translator's footnotes")
marks = re.findall(r"\[(\d+)\]", t)
print(f"   {len(marks)} bracketed marks, "
      f"{len(set(marks))} distinct numbers, max {max(map(int, marks))}")
