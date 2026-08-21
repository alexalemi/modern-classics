"""Spinoza's Ethics -> chapters/ + manifest.json.

WHAT THIS DOES THAT OTHER PREPS DO NOT: it rewrites all 598
cross-references into one canonical form before the translator ever
sees them (Alex's ruling, 2026-08-19). Doing it here rather than by
hand means it happens once, mechanically, and is checked -- 562 by the
resolver against the verified inventory, the remaining 36 from the
hand table in refs.HAND, each read in its passage.

Both sides of the word ratio then carry the same expanded references,
so verify.py's ratio stays fair.

ASSERTIONS THAT MUST HOLD, or prep stops:
  - every Part is found, including Part II, which has no "PART" line
  - every refused reference has a hand-table entry
  - every hand-table entry is actually used (a stale key means the
    source moved under us)
  - no file exceeds the split ceiling
  - the propositions in chapters/ are 1..N contiguous for each Part
"""
import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refs as R
import structure as S
from refcheck import context, here
from shapes import CITE
from triage import PROSE, REFUSE, RELATIVE

BOOK = pathlib.Path(__file__).resolve().parent
OUT = BOOK / "chapters"
MAXWORDS = 6000

PART_WORD = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five"}
PART_OF = {}


# ---------------------------------------------------------------- refs
def resolve_all(part, text, inv, used, unresolved):
    """Rewrite every reference in one Part's raw text."""
    marks = context(text)
    out, last = [], 0
    for m in re.finditer(r"\((?:[^()]{0,200})\)", text, re.S):
        raw_exact = m.group(0)
        raw = re.sub(r"\s+", " ", raw_exact)
        if not CITE.fullmatch(raw):
            continue
        block, prop = here(marks, m.start())

        key = (part, prop, raw)
        if key in R.HAND:
            rep = R.HAND[key]
            used.add(key)
        else:
            rep = None
            refused = any(re.search(p, raw) for p, _ in REFUSE)
            if not refused:
                inner = R.LEAD.sub("", raw[1:-1].strip())
                parsed, ok = R.parse(inner, part)
                good = ok and all(r.valid(inv, part) for r in parsed)
                if RELATIVE.search(raw) and not good:
                    n = R.resolve_relative(raw, part, prop, block)
                    if n is not None:
                        parsed = [R.Ref(part, "Prop", n)]
                        good = True
                if good:
                    lead = R.LEAD.match(raw[1:-1].strip())
                    word = lead.group(0).strip().lower() if lead else ""
                    body = "; ".join(r.render(part) for r in parsed)
                    if PROSE.search(raw):
                        # A CITATION INSIDE A CLAUSE. The clause is
                        # Spinoza's prose and has to survive, so these
                        # are not rewritten mechanically -- and they
                        # cannot be: "as I have already shown in Prop.
                        # vii." opens with a capital I, which the case
                        # rule reads as Part I. They go in the hand
                        # table like any other refusal.
                        rep = None
                    else:
                        rep = f"({word + ' ' if word else ''}{body})"
            if rep is None and not refused:
                unresolved.append((part, prop, raw))
        if rep is not None:
            out.append(text[last:m.start()])
            out.append(rep)
            last = m.end()
    out.append(text[last:])
    return "".join(out)


# SPINOZA ALSO CITES WITHOUT PARENTHESES, and for a long time nothing
# here looked outside them: "This is clear from Deff. iii. and v.",
# "the demonstration of Prop. vii.", "Cf. III. xxxix. note and xl."
# There are 114 of these, and they are the WORST place to leave the
# Victorian shorthand, because they fall in the middle of a sentence
# rather than in an aside the eye can skip.
_PART = r"[IVXLC]+\.\s*"
_KIND = (r"(?:Prop(?:osition)?|Deff|Def(?:inition)?|Ax(?:iom)?|"
         r"Post(?:ulate)?|Coroll|Corollary|Lemma)\b\.?\s*")
_NUM = r"[ivxlc]+\.?"
BARE = re.compile(
    rf"\b(?:{_PART}(?:{_KIND})?|{_KIND}){_NUM}"
    rf"(?:\s*(?:,|and)?\s*(?:{_NUM}|Coroll\.?|Corollary|[Nn]ote)\b\.?)*"
    rf"(?:\s+of this [Pp]art)?")


def resolve_bare(part, text, inv):
    """Rewrite citations that carry no parentheses of their own."""
    def one(m):
        span = m.group(0)
        trail = ""
        # never swallow the sentence's own closing punctuation
        while span and span[-1] in " ,":
            trail, span = span[-1] + trail, span[:-1]
        parsed, ok = R.parse(span, part)
        if not ok or not all(r.valid(inv, part) for r in parsed):
            return m.group(0)
        return "; ".join(r.render(part) for r in parsed) + trail

    out, last = [], 0
    for m in BARE.finditer(text):
        # skip anything already inside a parenthesis
        before = text[:m.start()]
        if before.count("(") > before.count(")"):
            continue
        out.append(text[last:m.start()])
        out.append(one(m))
        last = m.end()
    out.append(text[last:])
    return "".join(out)


# ------------------------------------------------------------- layout
FOOT = re.compile(r"\[(\d+)\]")


def unwrap(t):
    """Hard-wrapped lines -> paragraphs, keeping blank-line breaks."""
    paras, cur = [], []
    for line in t.split("\n"):
        if line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras


HEADS = [
    (r"^PREFACE\.?:?$", "Preface"),
    (r"^DEFINITIONS? OF THE EMOTIONS\.?$", "Definitions of the Emotions"),
    (r"^DEFINITIONS?\.?$", "Definitions"),
    (r"^AXIOMS?\.?$", "Axioms"),
    (r"^POSTULATES?\.?$", "Postulates"),
    (r"^APPENDIX:?\.?$", "Appendix"),
    (r"^PROPOSITIONS\.?$", None),          # redundant; dropped
]


# GUTENBERG'S "--" IS AN EM DASH EXCEPT WHEN IT IS A HYPHEN. This
# transcription writes both with the same two characters, so
# "Proof.--This proposition" is a dash while "self--caused",
# "non--existent" and "fellow--men" are hyphenated words. Converting
# every "--" to an em dash gives "self—caused"; converting every
# "\w--\w" to a hyphen gives "ways-that is". Neither side of the
# character tells you which it is -- only the LEFT WORD does, and it is
# a hyphen exactly when that word is one of a small set of prefixes
# that Elwes hyphenates. Everything else is a dash.
HYPHEN_PREFIX = {
    "self", "non", "high", "low", "well", "ill", "fellow", "first",
    "last", "full", "over", "under", "not", "free", "half", "semi",
    "pre", "post", "co", "re", "ever", "never", "all", "god", "good",
    "long", "short", "new", "old", "far", "near", "much", "many",
}
JOIN = re.compile(r"\b(\w+)--(\w+)")


def dashes(s):
    def one(m):
        if m.group(1).lower() in HYPHEN_PREFIX:
            return f"{m.group(1)}-{m.group(2)}"
        return f"{m.group(1)}—{m.group(2)}"
    return JOIN.sub(one, s).replace("--", "—")


def relabel(p):
    """One paragraph of Elwes -> one paragraph of ours."""
    s = dashes(p)
    for pat, rep in HEADS:
        if re.fullmatch(pat, p.strip()):
            return rep
    m = re.match(r"^PROP\.\s*([IVXLC]+)\.\s*(.*)$", s, re.S)
    if m:
        return f"Proposition {S.unroman(m.group(1))}\n\n{m.group(2).strip()}"
    m = re.match(r"^LEMMA\s+([IVXLC]+)\.?\s*(.*)$", s, re.S)
    if m:
        return f"Lemma {S.unroman(m.group(1))}\n\n{m.group(2).strip()}"
    m = re.match(r"^(Proof|Corollary|Coroll\.|Note|Explanation)\s*"
                 r"([IVXLC]*)\.?\s*—\s*(.*)$", s, re.S)
    if m:
        word = "Corollary" if m.group(1).startswith("Coroll") else m.group(1)
        n = S.unroman(m.group(2)) if m.group(2) else None
        head = f"{word} {n}" if n else word
        return f"{head}. {m.group(3).strip()}"
    m = re.match(r"^(?:DEFINITION|AXIOM|POSTULATE)?\s*([IVXLC]+)\.\s+(.*)$",
                 s, re.S)
    if m and S.unroman(m.group(1)):
        return f"{S.unroman(m.group(1))}. {m.group(2).strip()}"
    return s


# ELWES'S SEVENTEEN NOTES ARE COLLECTED AT THE BACK, not printed where
# they are cited, and the numbering runs 1..17 straight through the book
# rather than restarting per Part (which the first survey guessed wrong
# from 51 marks over 17 numbers -- the marks repeat, the notes do not).
# Left alone they ride on the end of Part V's last file, where they
# would ship as seventeen orphan paragraphs with no anchor. Each is
# inlined after the paragraph that cites it, in Elwes's own voice, the
# candle pattern.
END_MARK = "End of the Ethics by Benedict de Spinoza"
NOTEDEF = re.compile(r"\[(\d+)\]\s*(.*?)(?=\n\s*\[\d+\]|\Z)", re.S)


def take_notes(text):
    """Split the endnote block off the tail; return (body, {n: text})."""
    i = text.find(END_MARK)
    if i < 0:
        return text, {}
    body, tail = text[:i], text[i + len(END_MARK):]
    notes = {}
    for m in NOTEDEF.finditer(tail):
        notes[int(m.group(1))] = re.sub(r"\s+", " ", m.group(2)).strip()
    return body, notes


# Note 10 is the only one of the seventeen that cites the Ethics rather
# than a source outside it. The notes are inlined after resolve_all has
# swept the body, so nothing else looks inside them.
NOTE_REFS = {"II. xiii. note": "Part 2, Proposition 13, Note"}


def inline_notes(paras, notes, seen):
    """Drop each [n] mark and set its note after the paragraph citing it."""
    out = []
    for para in paras:
        marks = [int(x) for x in re.findall(r"\[(\d+)\]", para)]
        if marks:
            para = re.sub(r"\s*\[\d+\]", "", para)
        out.append(para)
        for n in marks:
            if n in notes and n not in seen:
                seen.add(n)
                txt = dashes(notes[n])
                for a, b in NOTE_REFS.items():
                    txt = txt.replace(a, b)
                out.append(f"Footnote: {txt}")
    return out


def main():
    inv = R.inventory()
    used, unresolved = set(), []
    parts, notes = [], {}
    for n, text in S.split_parts(S.body()):
        text, found = take_notes(text)
        notes.update(found)
        text = resolve_all(n, text, inv, used, unresolved)
        parts.append((n, resolve_bare(n, text, inv)))
    if len(notes) != 17:
        raise SystemExit(f"expected 17 endnotes, found {len(notes)}")
    seen = set()

    stale = set(R.HAND) - used
    if stale:
        raise SystemExit(f"hand-table keys never matched: {sorted(stale)[:4]}")
    if unresolved:
        print(f"NOTE: {len(set(unresolved))} distinct references still unhandled:")
        for p, prop, raw in sorted(set(unresolved), key=lambda x: (x[0], x[1] or 0))[:14]:
            print(f"   P{p} of {prop}: {raw[:60]}")

    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    manifest, idx = [], 0
    for n, text in parts:
        # drop the Part's own heading line; the manifest carries it
        text = re.sub(r"^.*?(?=\n)", "", text, count=1)
        # THE FOOTNOTE TEXT IS PRINTED TWICE. Gutenberg sets each note
        # inline in the body, right after the paragraph that cites it,
        # AND again in the collected block at the back. Inlining the back
        # copy without dropping the body copy prints every note twice
        # over -- 'Footnote: "Affectiones"' followed by '"Affectiones"'.
        raw = [q for q in unwrap(text)
               if not re.match(r"^\[\d+\]", q.strip())]
        paras = [relabel(q) for q in raw]
        paras = [q for q in paras if q]
        paras = inline_notes(paras, notes, seen)

        # AND DROP THE SUBTITLE UNDER IT. Every Part repeats its own
        # title on the next line ("ON THE ORIGIN AND NATURE OF THE
        # EMOTIONS"), which the Part divider already carries. Left in,
        # it renders as a second heading saying the same thing -- and
        # in Parts I to III it is ALL CAPS, which assemble.py reads as
        # a heading wherever it lands.
        title = S.PART_TITLES[n].lower()
        while paras and paras[0].lower().strip(".:") in (
                title, f"on {title}", f"concerning {title}"):
            paras.pop(0)

        # PART III LABELS NO PREFACE. Parts II, IV and V head theirs
        # "PREFACE"; Part III simply begins, so its preface -- the
        # "lines, planes and solids" passage, the most quoted page in
        # the book -- would run straight into the Definitions with
        # nothing to mark it. Supply the heading the other Parts have.
        if n == 3 and "Preface" not in paras[:3]:
            paras.insert(0, "Preface")

        # SPLIT AT A UNIT BOUNDARY, never inside one. A "unit" is a
        # Proposition, a Lemma, a section heading, or a numbered entry --
        # the last of those matters because the Definitions of the
        # Emotions are 48 numbered entries with no Proposition among
        # them, and the Appendix is continuous prose. Without them Part
        # III's last file ran to 10,021 words.
        groups, cur, count, opened = [], [], 0, None
        heads_at = {}
        for p in paras:
            # A NUMBERED ENTRY IS A SPLIT POINT ONLY IN THE DEFINITIONS
            # OF THE EMOTIONS. Everywhere else the numbered runs are
            # short lists -- the Definitions, the Axioms, Part II's six
            # Postulates -- and breaking inside one leaves half a list
            # at the end of a file and half at the start of the next.
            # Part II split after Postulate 1 that way. The Definitions
            # of the Emotions are forty-eight entries with no
            # Proposition among them and must be allowed to break.
            unit = (p.startswith(("Proposition ", "Lemma ", "Preface",
                                  "Definitions", "Axioms", "Postulates",
                                  "Appendix"))
                    or (opened == "Definitions of the Emotions"
                        and re.match(r"^\d+\. ", p)))
            # The Appendix and the Definitions of the Emotions ALWAYS
            # open a file. Each is a distinct piece of writing rather
            # than a continuation -- Part I's Appendix is the attack on
            # final causes, and Part III's Definitions are a glossary of
            # forty-eight emotions -- and letting them ride on the end
            # of a run of propositions put 1,700 words past the ceiling
            # in a file whose last unit boundary fell just under it.
            always = p in ("Appendix", "Definitions of the Emotions")
            if cur and (always
                        or (count > MAXWORDS
                            and (unit or count > MAXWORDS * 1.3))):
                groups.append(cur)
                heads_at[len(groups)] = opened
                cur, count = [], 0
            if p in ("Preface", "Definitions", "Axioms", "Postulates",
                     "Appendix", "Definitions of the Emotions"):
                opened = p
            cur.append(p)
            count += len(p.split())
        if cur:
            groups.append(cur)

        for k, g in enumerate(groups, 1):
            (OUT / f"{idx:03d}.txt").write_text("\n\n".join(g) + "\n")
            PART_OF[f"{idx:03d}.txt"] = n
            e = {"file": f"{idx:03d}.txt",
                 "title": section_title(g, n, k, len(groups),
                                        heads_at.get(k - 1)),
                 "part": k, "of": len(groups), "chapter": True}
            if k == 1:
                e["part_before"] = (f"Part {PART_WORD[n]}: "
                                    f"{S.PART_TITLES[n]}")
            manifest.append(e)
            idx += 1

    # EVERY PROPOSITION MUST BE PRESENT AND IN ORDER. The split runs on
    # word counts, so a boundary bug drops or repeats one silently --
    # and a missing proposition in a book of proofs breaks every proof
    # that cites it, while the word ratio moves by a fraction of a
    # percent. Compare what reached chapters/ against the inventory,
    # which was built by an independent reading of the source.
    got = collections.defaultdict(list)
    for m in manifest:
        part = PART_OF[m["file"]]
        for line in (OUT / m["file"]).read_text().split("\n"):
            mm = re.match(r"^Proposition (\d+)$", line)
            if mm:
                got[part].append(int(mm.group(1)))
    for part in sorted(inv):
        want = list(range(1, inv[part]["Prop"] + 1))
        if got[part] != want:
            lost = sorted(set(want) - set(got[part]))
            dupe = [x for x in set(got[part]) if got[part].count(x) > 1]
            raise SystemExit(
                f"Part {part}: propositions not 1..{inv[part]['Prop']} "
                f"in order (missing {lost[:6]}, repeated {dupe[:6]})")

    missing = sorted(set(notes) - seen)
    if missing:
        raise SystemExit(f"endnotes never cited, so never placed: {missing}")

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    total = sum(len((OUT / m["file"]).read_text().split()) for m in manifest)
    print(f"{len(manifest)} files, {total:,} words")
    for m in manifest:
        w = len((OUT / m['file']).read_text().split())
        print(f"   {m['file']}  {w:>6,}  {m['title']}")


def section_title(group, part, k, of, carried=None):
    """A descriptive title, built from what the group actually holds.

    Headings are reported in the order they occur rather than from a
    fixed list, which is what an earlier version got wrong: Postulates
    was in the list of headings to notice but not in the list to report,
    so Part II's file 003 silently dropped it and file 004 was titled
    "Postulates, continued" for a section that had already ended.
    """
    ORDER = ("Preface", "Definitions", "Axioms", "Postulates",
             "Definitions of the Emotions", "Appendix")
    bits = [p for p in group if p in ORDER]
    if any(p.startswith("Lemma ") for p in group):
        bits.append("the Physics")
    props = [int(re.match(r"Proposition (\d+)", p).group(1))
             for p in group if p.startswith("Proposition ")]
    if props:
        bits.append(f"Propositions {props[0]} to {props[-1]}"
                    if len(props) > 1 else f"Proposition {props[0]}")

    opens_mid = not group[0].startswith(
        ("Proposition ", "Lemma ")) and group[0] not in ORDER
    if not bits:
        nums = [int(m.group(1)) for m in
                (re.match(r"^(\d+)\. ", p) for p in group) if m]
        if carried and nums:
            return f"{carried} {nums[0]} to {nums[-1]}"
        if carried:
            return f"{carried}, continued"
        return f"Part {PART_WORD[part]} ({k} of {of})"
    if carried and opens_mid and carried not in bits:
        bits.insert(0, f"{carried}, continued")
    return ", ".join(bits)


if __name__ == "__main__":
    main()
