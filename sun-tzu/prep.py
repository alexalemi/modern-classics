"""Gutenberg #132 (Giles's Art of War) -> chapters/ + manifest.json.

THIS BOOK IS A CRIB MODERNISATION, NOT A TRANSLATION FROM THE ORIGINAL,
and that has to be said in the front matter. Sun Tzu wrote about 6,000
Chinese characters around the fifth century BC; what is modernised here
is Lionel Giles's 1910 English, which is itself a scholarly translation
with an apparatus. Every other from-the-original book in this collection
(ovid/, de-officiis/, galileo/, the Vernes) works from the source
language with an English crib alongside. This one cannot: nobody here
reads classical Chinese.

WHAT IS IN THE BOOK AND WHAT IS NOT
  - THE THIRTEEN CHAPTERS ENTIRE, verses AND commentary. The commentary
    is 53% of the text (416 bracketed blocks, 21,700 words) and 214 of
    those blocks quote the ancient Chinese commentators -- Ts'ao Kung,
    Tu Mu, Li Ch'uan, Mei Yao-ch'en, Chang Yu. That is the classical
    reception of the Art of War and it is what makes Giles's edition
    worth having; most modern editions drop it and print the verses
    alone. Rendered as "Commentary: ..." paragraphs, the candle pattern.
  - GILES'S 14,600-WORD INTRODUCTION IS NOT TRANSLATED. It is his own
    scholarly essay -- Sun Tzu's life, the text's authenticity, a
    bibliography, appreciations by Chinese critics -- by a man who is
    not Sun Tzu, and it goes to reference/ as a crib on the bunyan
    (Offor) and mill (editor's introduction) precedent.
  - GILES'S OWN SIXTEEN FOOTNOTES ARE KEPT, inlined after the paragraph
    that cites them. They are his, first person, and several are the
    best thing on the page ("Unless you enter the tiger's lair, you
    cannot get hold of the tiger's cubs").

THE SOURCE DEFECT THIS PREP EXISTS TO FIX. Gutenberg sets the footnote
TEXT wherever the print page happened to break, not next to its marker,
so "[1] 'Words on Wellington,' by Sir. W. Fraser." arrives as a
standalone paragraph a screen away from the "[1]" that calls it -- and
the numbering RESTARTS IN EVERY CHAPTER, so there are three separate
"[1]"s. Pair them per chapter and move the text to the citing block (the
candle rule), and ASSERT the pairing is total: a note attached to the
wrong sentence reads perfectly and no mechanical check downstream can
see it.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
SRC = BOOK / "_pg132.txt"
OUT = BOOK / "chapters"
REF = BOOK / "reference"

MAXW = 7000

WORD = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
        "Thirteen").split()

CHAP = re.compile(r"^Chapter ([IVX]+)\.\s+(.+?)\s*$", re.M)
FOOTNOTE_TEXT = re.compile(r"^\[(\d+)\]\s+(?=\S)")
MARKER = re.compile(r"\s*\[(\d+)\]")

# Giles's chapter titles are set in capitals. Title-case them, but keep
# his spelling: "Manoeuvering" is his, and the oe ligature is dropped
# because the pipeline is plain text.
FIXED_TITLE = {
    "MANŒUVERING": "Manoeuvring",
    "WEAK POINTS AND STRONG": "Weak Points and Strong",
    "THE NINE SITUATIONS": "The Nine Situations",
    "THE ATTACK BY FIRE": "The Attack by Fire",
    "THE USE OF SPIES": "The Use of Spies",
    "THE ARMY ON THE MARCH": "The Army on the March",
    "VARIATION OF TACTICS": "Variation of Tactics",
    "TACTICAL DISPOSITIONS": "Tactical Dispositions",
    "ATTACK BY STRATAGEM": "Attack by Stratagem",
    "LAYING PLANS": "Laying Plans",
    "WAGING WAR": "Waging War",
    "ENERGY": "Energy",
    "TERRAIN": "Terrain",
}


VERSE = re.compile(r"^\d+[,.\d\s]*\.")


def split_parts(pars, maxw):
    """Cut into <= maxw-word parts, ONLY at the start of a numbered verse."""
    total = sum(len(p.split()) for p in pars)
    k = max(1, -(-total // maxw))
    if k == 1:
        return [pars]
    target = total / k
    parts, cur, run = [], [], 0
    for p in pars:
        w = len(p.split())
        if cur and VERSE.match(p) and run + w / 2 > target and len(parts) < k - 1:
            parts.append(cur)
            cur, run = [], 0
        cur.append(p)
        run += w
    parts.append(cur)
    return parts


# SOURCE DEFECTS, corrected here and ASSERTED so that they cannot vanish
# silently if Gutenberg ever re-transcribes the file (the candle rule).
#
# 1. CHAPTER EIGHT LOST AN OPENING BRACKET. Sun Tzu lists the five
#    besetting sins of a general, and each item is followed by a
#    bracketed note; item (4), "a delicacy of honour which is sensitive
#    to shame", has a note that begins "This need not be taken to mean
#    that a sense of honour is really a defect in a general" and ends
#    with a closing bracket that has no opener. Without the fix the note
#    reads as SUN TZU'S OWN TEXT rather than as the commentator's gloss
#    on it -- and it reads perfectly that way, which is why nothing
#    downstream could catch it. Found by tracking bracket depth.
# 2. SIX COMMENTARY BLOCKS HAVE NO CLOSING BRACKET AT ALL. Each one
#    therefore runs on into whatever follows it, and what follows is Sun
#    Tzu -- so his own words ship labelled as somebody's commentary on
#    them, which reads perfectly and is invisible to every downstream
#    check. WHERE EACH NOTE ENDS HAD TO BE READ, not guessed, and the six
#    are not alike:
#      - chapter Four's note ends on a COUPLET it is quoting, so the
#        bracket goes after the verse, not before it;
#      - chapter Nine's note is followed by an UNNUMBERED continuation of
#        Sun Tzu's verse 2 ("Do not climb heights in order to fight"),
#        which is why a rule keyed on verse numbers alone is not enough;
#      - chapter Thirteen's note interrupts a sentence of Sun Tzu's,
#        which resumes afterwards with "was due to I Chih".
SOURCE_FIXES = [
    ("\n\nThis need not be taken to mean that a sense of honour",
     "\n\n[This need not be taken to mean that a sense of honour"),
    ('And finger fail to plumb."',
     'And finger fail to plumb."]'),
    ("Peiwar Kotal in the second Afghan war.\n[1]",
     "Peiwar Kotal in the second Afghan war.\n[1]]"),
    ('plans conducive to our success and to the enemy\u2019s failure."',
     'plans conducive to our success and to the enemy\u2019s failure."]'),
    ("Cf. infra, \u00a7\u00a7 11, 13.",
     "Cf. infra, \u00a7\u00a7 11, 13.]"),
    ('entail the ruin or surrender of his whole army." [2]',
     'entail the ruin or surrender of his whole army." [2]]'),
    ("changed to Yin by P\u2019an Keng in 1401.",
     "changed to Yin by P\u2019an Keng in 1401.]"),
]


def apply_source_fixes(body):
    for bad, good in SOURCE_FIXES:
        if bad not in body:
            raise SystemExit(
                f"SOURCE_FIXES no longer applies -- the defect is gone from "
                f"the source, so this correction must be re-checked:\n  {bad!r}")
        body = body.replace(bad, good, 1)
    # STRAY DUPLICATED CLOSING BRACKETS, 16 of them, are transcription
    # noise ("...ff. 1, 2.] ]"). Collapse them first, so that a block's
    # end can be recognised by its last character.
    # A FOOTNOTE MARKER'S BRACKET IS NOT A STRAY, and this is the trap:
    # a note ends "...what mine are?" [1] ]", and collapsing that run
    # eats the BLOCK'S OWN closing bracket rather than the noise. The
    # block then never closes, and Sun Tzu's next verse -- "All warfare
    # is based on deception", the most quoted line in the book -- ships
    # labelled as somebody's commentary on itself. Ride the markers
    # through on a sentinel (the pillow-problems rule) so the collapse
    # cannot see them.
    body = re.sub(r"\[(\d+)\]", r"@@FN\1@@", body)
    n = len(re.findall(r"\]\s*\]", body))
    assert n >= 5, f"expected the '] ]' noise, found {n} runs"
    while re.search(r"\]\s*\]", body):
        body = re.sub(r"\]\s*\]", "]", body)
    # A VERSE THAT FOLLOWS A CLOSING BRACKET WITHOUT A BLANK LINE IS
    # WELDED TO THE NOTE. Chapter twelve's verse 10 sits directly under
    # the six stray brackets collapsed above, so once they are gone it is
    # still inside Tu Mu's note -- and would ship labelled "Commentary:",
    # handing Sun Tzu's own words to a commentator. Give it its own
    # paragraph. Asserted at exactly one, so a second occurrence has to
    # be looked at rather than silently absorbed.
    welded = re.findall(r"\]\r?\n(?=\d+[.,])", body)
    assert len(welded) == 1, f"{len(welded)} welded verses, expected 1"
    body = re.sub(r"\]\r?\n(?=\d+[.,])", "]\n\n", body)
    body = re.sub(r"@@FN(\d+)@@", r"[\1]", body)
    return body


def paragraphs(block):
    return [re.sub(r"[ \t]*\n[ \t]*", " ", p).strip()
            for p in re.split(r"\n\s*\n", block) if p.strip()]


def main():
    raw = SRC.read_text()
    start = raw.index("*** START OF THE PROJECT GUTENBERG EBOOK")
    end = raw.index("*** END OF THE PROJECT GUTENBERG EBOOK")
    body = raw[raw.index("\n", start) + 1:end]

    body = apply_source_fixes(body)
    cuts = list(CHAP.finditer(body))
    assert len(cuts) == 13, f"{len(cuts)} chapters found, expected 13"

    # Giles's own front matter -> reference/, not translated
    REF.mkdir(exist_ok=True)
    (REF / "giles_introduction.txt").write_text(body[:cuts[0].start()].strip()
                                                + "\n")

    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()

    manifest, idx, notes_placed = [], 0, 0
    unclosed = []
    for n, m in enumerate(cuts, 1):
        stop = cuts[n].start() if n < len(cuts) else len(body)
        title = f"Chapter {WORD[n - 1]}: {FIXED_TITLE[m.group(2)]}"
        pars = paragraphs(body[m.end():stop])

        # --- pair Giles's footnotes with their markers, PER CHAPTER
        notes, kept = {}, []
        for p in pars:
            fm = FOOTNOTE_TEXT.match(p)
            if fm:
                assert fm.group(1) not in notes, (n, fm.group(1))
                notes[fm.group(1)] = FOOTNOTE_TEXT.sub("", p).strip()
            else:
                kept.append(p)

        # A COMMENTARY BLOCK MAY SPAN A PARAGRAPH BREAK -- six of them do,
        # leaving thirteen paragraphs with unbalanced brackets. Treating
        # each paragraph independently strands a "[" in the body text,
        # which ships as a literal bracket. Track the depth instead, and
        # label EVERY paragraph of a block, so that a reader who meets a
        # continuation knows whose voice it is.
        # A BLOCK IS RECOGNISED BY ITS FIRST AND LAST CHARACTERS, not by
        # counting brackets. Gutenberg's brackets do not balance -- notes
        # carry stray closers inside them and the counts drift by five in
        # chapter twelve -- so arithmetic gives the wrong answer. A
        # paragraph beginning "[" opens a block; the first paragraph
        # ending "]" closes it; everything between is the same voice.
        out, in_block = [], False
        for p in kept:
            cited = MARKER.findall(p)
            body_text = MARKER.sub("", p).strip()
            opening = body_text.startswith("[")
            # A NUMBERED VERSE IS NEVER INSIDE A NOTE. Three commentary
            # blocks in this source have NO CLOSING BRACKET at all -- one
            # ends on a couplet, one on a footnote marker, one on a
            # quotation -- and without this rule each swallows the verse
            # after it, which then ships as somebody's commentary on
            # itself. Same defect as the "All warfare is based on
            # deception" case, and it reads perfectly every time.
            # Counted below, so that a fourth has to be looked at.
            if in_block and VERSE.match(body_text):
                in_block = opening = False
                unclosed.append((n, body_text[:55]))
            if in_block or opening:
                if body_text.endswith("]"):
                    in_block = False
                elif opening:
                    in_block = True
                body_text = "Commentary: " + body_text.strip("[] ").strip()
            out.append(body_text)
            for c in cited:
                assert c in notes, f"chapter {n}: marker [{c}] has no text"
                out.append("Footnote: " + notes.pop(c))
                notes_placed += 1
        assert not notes, f"chapter {n}: unplaced footnotes {sorted(notes)}"
        assert not in_block, f"chapter {n}: a commentary block never closed"

        # A CUT MUST NOT SEPARATE A VERSE FROM ITS COMMENTARY. Chapter
        # Eleven runs 9,682 words, so it splits -- and the boundary is
        # forced onto the start of a numbered verse, because a part that
        # opened on "Commentary: Tu Mu says..." would leave the reader
        # with a gloss on a sentence they have not read.
        for k, part in enumerate(split_parts(out, MAXW), 1):
            name = f"{idx:03d}.txt"
            (OUT / name).write_text(title + "\n\n" + "\n\n".join(part) + "\n")
            words = len(" ".join(part).split())
            manifest.append({"file": name, "title": title, "part": k,
                             "of": len(split_parts(out, MAXW)),
                             "words": words})
            assert words <= MAXW + 500, f"{name} is {words} words"
            idx += 1

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    assert notes_placed == 16, f"{notes_placed} footnotes placed, expected 16"
    assert not unclosed, (
        f"a commentary block still runs on into a verse -- the source is "
        f"missing a closing bracket that SOURCE_FIXES does not cover: "
        f"{unclosed}")

    # --- SECOND READING: every word of the chapter region must survive,
    # in order, once the brackets and markers this prep removes are
    # accounted for. Compares CHARACTERS, not tokens (the mill rule).
    # THE FOOTNOTES ARE COMPARED SEPARATELY (the mill rule): the raw
    # reading has them where the print page broke, and this prep has
    # moved them to their markers, so an in-order comparison would
    # diverge at the first one by design.
    want = body[cuts[0].start():]
    want = re.sub(r"(?m)^\[\d+\][ \t]+(?=\S).*(?:\n(?![ \t]*\n).*)*", " ", want)
    want = re.sub(r"\[\d+\]", " ", want)
    want = re.sub(r"^Chapter [IVX]+\..*$", " ", want, flags=re.M)
    want = re.sub(r"[\[\]]", " ", want)
    got_all = "\n\n".join((OUT / m["file"]).read_text().split("\n", 1)[1]
                          for m in manifest)
    inlined = re.findall(r"(?m)^Footnote: (.*)$", got_all)
    assert len(inlined) == 16, f"{len(inlined)} inlined footnotes"
    for note in inlined:
        assert got_all.count("Footnote: " + note) == 1, f"duplicated: {note}"
    got = "\n\n".join(p for p in re.split(r"\n\s*\n", got_all)
                      if not p.startswith("Footnote: "))
    # INLINE CITATION BRACKETS survive inside a note ("[Ch'ien Han Shu,
    # ch. 3.]"), so strip brackets from BOTH sides or the comparison
    # diverges on a difference that is only in the comparison.
    got = re.sub(r"[\[\]]", " ", got.replace("Commentary:", " "))
    squash = lambda s: re.sub(r"\s+", "", s)
    a, b = squash(want), squash(got)
    if a != b:
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]),
                 min(len(a), len(b)))
        raise SystemExit(f"diverges at char {i} (source {len(a)}, out {len(b)}):\n"
                         f"  source ...{a[max(0, i-70):i+70]}\n"
                         f"  output ...{b[max(0, i-70):i+70]}")
    print(f"cross-check: {len(a):,} characters match, in order")

    total = sum(m["words"] for m in manifest)
    print(f"{len(manifest)} chapters, {total:,} words; "
          f"largest {max(m['words'] for m in manifest):,}")
    print(f"{notes_placed} of Giles's footnotes paired and inlined")
    print(f"reference/giles_introduction.txt: "
          f"{len((REF / 'giles_introduction.txt').read_text().split()):,} words")


if __name__ == "__main__":
    main()
