"""Euripides: the nineteen surviving plays, from the Greek, with Coleridge as crib.

aeschylus/prep.py with the constants changed and the SUNG/SPOKEN DECISION
MOVED FROM THE MARKUP TO THE METRE. Read that file and sophocles/prep.py
first; the parser, the crib alignment and the pinned boundaries are theirs.

WHY THE CLASSIFIER, AND NOT A LIST OF FIXES. For Sophocles the Perseus
division labels were right; for Aeschylus they were wrong in ~30 places
and each was corrected by hand in KIND_FIXES after reading. For Euripides
aeschylus/metre.py reports ~380 disagreements across 19 plays, and reading
the first hundred showed one shape every time: a <div> labelled for a
lyric passage runs on over the iambic scene after it (the whole Theseus-
Hippolytus scene, 856-1101, is "lyric"; Medea's 95-line messenger speech
is "anapests"; Alcestis' Apollo and Death argue in trimeters under
"anapests"). A hand list at that scale is a copy of the classifier's
output with typing errors added. So here the SYLLABLE COUNT IS THE
WITNESS OF RECORD and the division label is the tie-breaker:

  - a speech of two or more lines, at least 85% of them 12-15 syllables
    (iambic trimeter is 12, resolutions add; trochaic tetrameter 15-16 is
    also spoken) -> SPOKEN, whatever the div says;
  - a speech of four or more lines with a mean under 11 syllables -> SUNG,
    whatever the div says (short lyric cola);
  - a one-line speech, or a mixed one, takes the div's label, EXCEPT that
    a one-line speech of 12-16 syllables whose neighbours on both sides
    are spoken is spoken (stichomythia inside a mislabelled div).

Measured on Aeschylus, where the labels had been corrected by hand: the
rule reproduces the hand result on 812 of 839 multi-line speeches, and
every remaining disagreement was read -- trochaic tetrameter (now included
as spoken), and speeches that genuinely mix trimeter and lyric, which take
the label. KIND_FIXES survives for the residue that has to be read.
"""
import collections
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TEI = "{http://www.tei-c.org/ns/1.0}"
UA = {"User-Agent": "modern-classics/1.0 (alexalemi@gmail.com)"}
RAW = ("https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/"
       "master/data/tlg0006/tlg%03d/tlg0006.tlg%03d.perseus-%s.xml")

# Chronological order where a date is known. Cyclops (the one complete
# satyr play) and Rhesus (authorship disputed since antiquity) close the
# volume, as Prometheus Bound closes the Aeschylus.
PLAYS = [
    (2, "Alcestis", "438 BC", "eng2"),
    (3, "Medea", "431 BC", "eng2"),
    (4, "The Children of Heracles", "c. 430 BC", "eng2"),
    (5, "Hippolytus", "428 BC", "eng2"),
    (6, "Andromache", "c. 425 BC", "eng2"),
    (7, "Hecuba", "c. 424 BC", "eng2"),
    (8, "The Suppliants", "c. 423 BC", "eng2"),
    (12, "Electra", "c. 420 BC", "eng2"),
    (9, "Heracles", "c. 416 BC", "eng2"),
    (11, "The Trojan Women", "415 BC", "eng2"),
    (13, "Iphigenia Among the Taurians", "c. 414 BC", "eng2"),
    (10, "Ion", "c. 413 BC", "eng2"),
    (14, "Helen", "412 BC", "eng2"),
    (15, "The Phoenician Women", "c. 410 BC", "eng2"),
    (16, "Orestes", "408 BC", "eng2"),
    (17, "The Bacchae", "405 BC", "eng2"),
    (18, "Iphigenia at Aulis", "405 BC", "eng2"),
    (1, "Cyclops", "date unknown", "eng2"),
    (19, "Rhesus", "date unknown", "eng3"),
]
DIVIDERS = {t: f"{t} ({d})" for _, t, d, _ in PLAYS}

SUNG = {"choral", "strophe", "antistrophe", "epode", "mesode", "kommos",
        "lyric", "anapests", "astrophic", "proode",
        # the REFRAIN of a strophic pair, sung again after each stanza:
        # the Suppliants' hymn to Zeus, the binding song of the Furies,
        # the Agamemnon kommos. Perseus spells it three ways.
        "ephymnion", "ephymn.", "ephymn"}
SPOKEN = {"episode", "spoken", "dialogue", "prologue", "exodos", "textpart",
          # trochaic tetrameter is RECITATIVE (the sophocles ruling on
          # "close" and "trochaic"): the Queen's first exchange with the
          # elders in The Persians, Darius' with the Queen, and the
          # Agamemnon's last twenty-five lines, Clytemnestra facing the
          # elders down. Delivered, not sung.
          "trochees", "close",
          # "iambics" is what Perseus calls the Queen's iambic-trimeter
          # speeches in The Persians -- ordinary spoken dialogue.
          "iambics", "iambic", "dialogue",
          # Andromache 103-116: Andromache's lament in elegiac couplets, the
          # only elegiacs in tragedy. Sung (it is a lament, and it is not
          # trimeter); listed here only so is_sung knows the word, and
          # overridden to SUNG in KIND_FIXES.
          "elegiacs",
          # a hexameter oracle (Euripides' Suppliants, Helen): chanted, so
          # verse -- overridden in KIND_FIXES where it occurs
          "hexameter",
          # the Agamemnon crib (eng3) carries no division markup at all --
          # one <div type="translation"> -- so its speeches all arrive as
          # this. The crib's kinds are never used for anything but rendering
          # it, and it renders as prose, which is what Smyth is.
          "translation"}

# PER-SPEECH OVERRIDES OF THE DIVISION KIND -- see the docstring. Each is
# (play number, first line, last line, speaker or None, sung?), applied to
# any speech whose first line falls in the range (and whose speaker matches,
# if one is given). Ranges were confirmed by printing every speech in them
# and reading the Greek: iambic trimeter is spoken, and nothing else is.
KIND_FIXES = [
    # (play, first line, last line, speaker or None, sung?) -- the residue
    # the classifier cannot decide, each read. The classifier is right
    # about trimeter and tetrameter; what it cannot know is that a chanted
    # metre it has never seen is verse.
    (6, 103, 116, None, True),    # Andromache's lament in ELEGIAC couplets,
                                  #   the only elegiacs in tragedy: sung
    (8, 271, 285, None, True),    # Suppliants: the Chorus' plea to Theseus
                                  #   in dactylic HEXAMETERS, chanted
    (14, 164, 166, None, True),   # Helen: three hexameters opening her
                                  #   monody
    # ANTILABE FRAGMENTS at the edge of a trimeter speech (a half-line that
    # completes another speaker's line) pull it under the 85% test. A rule
    # that dropped edge fragments was TRIED AND REVERTED: it turned two
    # lyric stanzas spoken (Andromache 778-788, Electra 1182-84), because a
    # dactylo-epitrite stanza with one short colon looks the same. The two
    # real cases are fixed by hand instead.
    (2, 817, 820, None, False),   # Alcestis: Servant and Heracles, trimeters
    (12, 693, 698, None, False),  # Electra: "I know it all" and her reply
    (3, 835, 845, "Χορός", True), # Medea: the antistrophe of the Athens
                                  #   ode is dactylo-epitrite, 12-14 a line,
                                  #   and the strong rule read it as
                                  #   trimeter -- the ONE chorus stanza in
                                  #   nineteen plays it got wrong (the other
                                  #   hit, Alcestis 416-419, IS trimeter)
]
FIXES_HIT = collections.Counter()

# Greek/English speech-count differences, each with its reason. The two
# editions were marked up independently, so a small disagreement is a
# fact about the transcription and not about Sophocles. Never averaged.
EXPECT = {
    'Alcestis': (323, 331,
        'the English splits the parodos among First/Second Semichorus and single voices; the Greek keeps one Chorus'),
    'Medea': (250, 254,
        "the English splits Medea's speech at a line anchor (1005), gives the children two tags, and shifts one anchor by a line"),
    'Hippolytus': (299, 301,
        'the English adds a Second Half Chorus tag at 784 and splits a Chorus speech at 848'),
    'The Suppliants': (254, 270,
        'the English splits the 598-633 ode into half-chorus voices and two later Chorus speeches at anchors; the Greek keeps one Chorus each'),
    'Ion': (561, 569,
        'the English gives the parodos to nine numbered Chorus voices; the Greek has one Chorus'),
    'The Phoenician Women': (423, 422,
        'the Greek has a Chorus interjection at 293 the English merges'),
    'Iphigenia at Aulis': (425, 424,
        "the English merges Agamemnon's opening line into the following speech"),
    'Cyclops': (256, 262,
        'the English splits the chorus into halves at 487 and cuts two speeches at stage business the Greek keeps whole'),
}

# Greek words per play, DERIVED THEN PINNED as a regression guard (the
# purgatorio rule). The load-bearing witnesses are the ones from outside
# this file: the crib's independent parse, and the speech counts.
# DERIVED ON THE FIRST RUN (2026-09-09) AND PINNED as a regression guard
GREEK_WORDS = {
    'Alcestis': 6602,
    'Medea': 8026,
    'The Children of Heracles': 6272,
    'Hippolytus': 8257,
    'Andromache': 7397,
    'Hecuba': 7340,
    'The Suppliants': 7166,
    'Electra': 7781,
    'Heracles': 7977,
    'The Trojan Women': 7230,
    'Iphigenia Among the Taurians': 8497,
    'Ion': 9339,
    'Helen': 9982,
    'The Phoenician Women': 9951,
    'Orestes': 10115,
    'The Bacchae': 7662,
    'Iphigenia at Aulis': 9481,
    'Cyclops': 4142,
    'Rhesus': 5502,
}
TOTAL_GREEK = 148719

MAX_GREEK = 3300          # per file; Smyth runs 1.70x, so ~5.5k English out


def fetch(n, kind):
    p = os.path.join(HERE, f"_src_{n:03d}_{kind}.xml")
    if not os.path.exists(p):
        with urllib.request.urlopen(
                urllib.request.Request(RAW % (n, n, kind), headers=UA),
                timeout=180) as r:
            open(p, "wb").write(r.read())
    return ET.parse(p).getroot()


def text_of(el):
    """Flatten an element to its words.

    Parsed as XML, never regexed: epictetus/ records what a tag-stripping
    regex does to a deleted element's tail. <note> is apparatus and goes;
    <placeName>, <q>, <add> and <del> carry sentence text and stay.
    """
    if el.tag.replace(TEI, "") == "note":
        return ""
    out = [el.text or ""]
    for c in el:
        out.append(text_of(c))
        out.append(c.tail or "")
    return "".join(out)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


# A SPEAKER TAG PERSEUS GETS WRONG. Seven Against Thebes 812-821: the
# Chorus has just asked "so they killed each other with brothers' hands?"
# (811) and the answer -- "so alike was the fate that took them both; it
# has used up the whole unlucky family" -- is the Scout's, as the English
# XML and every edition have it. Perseus' Greek tags it as a second Chorus
# speech. Keyed on first line and wrong name so it can only fire on that
# speech; main() asserts it fired exactly once.
SPEAKER_FIXES = {}
FIXES_APPLIED = []
SPEAKER_NORMALISE = {"θεράπαινα": "Θεράπαινα", "Παιδαγωγός.": "Παιδαγωγός",
                     "Ημιχ. Χορός": "Ἡμιχόριον"}


def line_no(s):
    d = "".join(c for c in (s or "") if c.isdigit())
    return int(d) if d else None


def stream(root, play=None):
    """Every <sp>, in document order, as (kind, speaker, [(line, text)]).

    `play` is the tlg number, needed to apply KIND_FIXES; the English
    files are streamed without it (their kinds are never used).

    `kind` is the nearest enclosing div's subtype. Stage directions are
    attached to the speech they precede.
    """
    out = []
    pending = []

    def walk(e, kind):
        for c in e:
            t = c.tag.replace(TEI, "")
            if t == "div":
                walk(c, c.get("subtype") or c.get("type") or kind)
            elif t == "stage":
                pending.append(norm(text_of(c)))
            elif t == "sp":
                who = c.find(f"{TEI}speaker")
                name = norm(text_of(who)) if who is not None else ""
                lines = [(l.get("n"), norm(text_of(l)))
                         for l in c.findall(f"{TEI}l")]
                if not lines:
                    lines = [(None, norm(text_of(p)))
                             for p in c.findall(f"{TEI}p")]
                lines = [(n, t) for n, t in lines if t]
                name = SPEAKER_NORMALISE.get(name, name)
                key = (lines[0][0], name) if lines else None
                if key in SPEAKER_FIXES and play is not None:
                    name = SPEAKER_FIXES[key]
                    FIXES_APPLIED.append(key)
                # THE OVERRIDE IS PER SPEECH. An earlier draft assigned to
                # `kind` here, which is walk()'s variable for the ENCLOSING
                # DIV, so every later speech in that div inherited the fix:
                # the Chorus' twelve-line lyric at Libation Bearers 152-163
                # turned the whole recognition scene after it (164-305) into
                # verse. Found by the syllable-count witness, not by any
                # check -- check.py asserts the translation against prep and
                # would have insisted on the error.
                k = kind
                if play is not None and lines:
                    ln = line_no(lines[0][0])
                    for i, (p, lo, hi, who, sung) in enumerate(KIND_FIXES):
                        if (p == play and ln is not None and lo <= ln <= hi
                                and (who is None or who == name)):
                            k = "sung*" if sung else "spoken*"
                            FIXES_HIT[i] += 1
                out.append((k, name, lines, list(pending)))
                pending.clear()

    walk(root.find(f".//{TEI}body"), "spoken")
    return out


def is_sung(kind):
    if kind == "sung*":
        return True
    if kind == "spoken*":
        return False
    if kind in SUNG:
        return True
    if kind in SPOKEN:
        return False
    raise SystemExit(f"prep: unknown division kind {kind!r} -- classify it "
                     f"as sung or spoken before continuing")


def classify(speeches):
    """Decide sung/spoken per speech from the METRE, label as tie-breaker.

    Returns a new list with kind replaced by "sung*"/"spoken*" where the
    metre decides and left alone where the label stands. Two passes: the
    first decides multi-line speeches; the second gives a one-line 12-16
    syllable speech its neighbours' verdict when both agree it is spoken.
    """
    import metre
    out = []
    for kind, name, lines, stage in speeches:
        counts = [metre.syl(t) for _, t in lines if len(t.split()) >= 2]
        k = kind
        if kind in ("sung*", "spoken*"):
            pass                                  # a KIND_FIX; leave it
        elif len(counts) >= 2:
            tri = sum(1 for c in counts if 12 <= c <= 16) / len(counts)
            if tri >= 0.85:
                k = "spoken*"
            elif len(counts) >= 4 and \
                    sum(1 for c in counts if c < 11) / len(counts) >= 0.75:
                # a SHARE of short lines, not a mean: one antilabe fragment
                # before three trimeters (Alcestis 1119c-1122, 7/12/12/12)
                # pulled a mean under 11 and made a spoken speech lyric
                k = "sung*"
        out.append([k, name, lines, stage])
    # Second pass: STICHOMYTHIA INSIDE A MISLABELLED DIV. Single-line
    # speeches carry no metrical evidence on their own, and in a run of
    # one-liners every neighbour is another one-liner, so a neighbour test
    # never fires (Alcestis 38-63, Apollo and Death trading trimeters
    # under "lyric", stayed sung in the first draft). So: a maximal run of
    # consecutive speeches that are each already spoken or a one-liner of
    # 12-16 syllables is spoken throughout if it is three or more speeches
    # long or contains a speech the metre already decided. Lyric exchanges
    # are in short cola and never qualify.
    # ANTILABE: a trimeter split between two speakers (Alcestis 819,
    # "black robes and cut hair" / "Who is it that died?") leaves each
    # speaker a fragment of under twelve syllables, which the strong test
    # cannot see. A one-liner of any length is a WEAK candidate: it joins a
    # run but cannot make one, and a run with weak members must contain a
    # speech the metre decided outright. A lyric cry between two lyric
    # speeches never meets a spoken speech and is untouched.
    def cand(sp):
        kind, name, lines, stage = sp
        if kind == "spoken*":
            return "strong"
        if kind == "sung*":
            return None
        counts = [metre.syl(t) for _, t in lines if len(t.split()) >= 2]
        if len(counts) == 1 and 12 <= counts[0] <= 16:
            return "strong"
        if len(lines) == 1 and (not counts or counts[0] < 12):
            return "weak"
        return None
    i = 0
    while i < len(out):
        if not cand(out[i]):
            i += 1
            continue
        j = i
        while j < len(out) and cand(out[j]):
            j += 1
        run = out[i:j]
        strong = sum(1 for sp in run if cand(sp) == "strong")
        decided = any(sp[0] == "spoken*" for sp in run)
        weak = any(cand(sp) == "weak" for sp in run)
        if decided or (strong >= 3 and not weak):
            for sp in run:
                if sp[0] != "spoken*":
                    sp[0] = "spoken*"
        i = j
    return [tuple(s) for s in out]


def render(speeches, title, numbers=False):
    """One play as text. Sung speeches are tab-indented, spoken are not.

    LINE NUMBERS ONLY IN THE CRIB. chapters/ is the source text that
    verify.py measures the translation against, and a number on every
    line inflates its word count by about a quarter -- which would make
    the ratio, the one check that catches silent summarising, mean
    nothing. reference/ keeps the anchors; the speeches are in the same
    order in both files, so the crib aligns by speech regardless.
    """
    body = [title, ""]
    mode = None
    for kind, name, lines, stage in speeches:
        sung = is_sung(kind)
        if sung != mode:
            body.append(f"[{'Sung' if sung else 'Spoken'}]")
            body.append("")
            mode = sung
        for s in stage:
            body.append(f"({s})")
            body.append("")
        body.append(f"{name}.")
        for n, t in lines:
            tag = f"{n} " if (numbers and n) else ""
            body.append(("\t" if sung else "") + tag + t)
        body.append("")
    return "\n".join(body).rstrip() + "\n"


# FILE BOUNDARIES, PINNED. split_points() prefers a cut where the
# sung/spoken mode changes, so a later KIND_FIX near a boundary MOVED the
# boundary -- two finished Prometheus files each lost or gained two speeches
# when Io's four trimeters at 589-592 were reclassified. Boundaries are
# therefore derived once and pinned here as speech indices; a re-run that
# would compute different ones is not allowed to move a finished file.
# NOTE the index counts EVERY <sp>, including the Suppliants' four empty
# ones (all before its cut), which check.py drops: 139 here is 135 there.
# derived 2026-09-09 with MAX_GREEK 3300 and pinned; 45 files
CUTS = {
    'Alcestis': [92, 203],
    'Medea': [63, 168],
    'The Children of Heracles': [92],
    'Hippolytus': [117, 206],
    'Andromache': [65, 136],
    'Hecuba': [66, 157],
    'The Suppliants': [88, 148],
    'Electra': [116, 263],
    'Heracles': [40, 150],
    'The Trojan Women': [79, 160],
    'Iphigenia Among the Taurians': [88, 251],
    'Ion': [215, 398],
    'Helen': [95, 295, 389],
    'The Phoenician Women': [92, 211, 305],
    'Orestes': [140, 271, 375],
    'The Bacchae': [55, 178],
    'Iphigenia at Aulis': [109, 288],
    'Cyclops': [114],
    'Rhesus': [116],
}


def split_points(speeches, limit=MAX_GREEK, title=None):
    if title in CUTS:
        return list(CUTS[title])
    return _split_points(speeches, limit)


def _split_points(speeches, limit=MAX_GREEK):
    """Cut a play into parts at SPEECH boundaries, never inside a speech.

    Prefers a boundary where the sung/spoken mode changes, so a part
    never opens in the middle of an ode.
    """
    words = [sum(len(t.split()) for _, t in ls) for _, _, ls, _ in speeches]
    total = sum(words)
    n = max(1, -(-total // limit))
    target = total / n
    cuts, run, want = [], 0, target
    for i, w in enumerate(words):
        run += w
        if run >= want and i + 1 < len(speeches) and len(cuts) < n - 1:
            j = i
            for k in range(i, min(i + 12, len(speeches) - 1)):
                if is_sung(speeches[k][0]) != is_sung(speeches[k + 1][0]):
                    j = k
                    break
            cuts.append(j + 1)
            want += target
    return cuts


def main():
    chap = os.path.join(HERE, "chapters")
    ref = os.path.join(HERE, "reference")
    for d in (chap, ref):
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))

    manifest, idx, total = [], 0, 0
    derived = []
    for n, title, date, eng in PLAYS:
        g = classify(stream(fetch(n, "grc2"), play=n))
        e = stream(fetch(n, eng))
        gw = sum(len(t.split()) for _, _, ls, _ in g for _, t in ls)

        if not EXPECT:
            derived.append((title, len(g), len(e), gw, _split_points(g)))
        elif title in EXPECT:
            want_g, want_e, why = EXPECT[title]
            if (len(g), len(e)) != (want_g, want_e):
                raise SystemExit(
                    f"{title}: speech counts {len(g)}/{len(e)}, expected "
                    f"{want_g}/{want_e} ({why}) -- the source changed")
        elif GREEK_WORDS and len(g) != len(e):
            raise SystemExit(
                f"{title}: Greek has {len(g)} speeches, English {len(e)}. "
                f"An undocumented disagreement between the two witnesses; "
                f"read it and add it to EXPECT with its reason.")
        if GREEK_WORDS and gw != GREEK_WORDS[title]:
            raise SystemExit(f"{title}: {gw} Greek words, pinned "
                             f"{GREEK_WORDS[title]}")
        total += gw

        cuts = split_points(g, title=title)
        bounds = [0] + cuts + [len(g)]
        # the crib is cut at the SAME speech indices, which is only sound
        # where the counts agree; where they do not, scale the index
        scale = len(e) / len(g)
        for p in range(len(bounds) - 1):
            a, b = bounds[p], bounds[p + 1]
            ea, eb = round(a * scale), round(b * scale)
            head = title if len(bounds) == 2 else f"{title} (Part {p+1} of {len(bounds)-1})"
            open(os.path.join(chap, f"{idx:03d}.txt"), "w").write(
                render(g[a:b], head))
            open(os.path.join(ref, f"{idx:03d}.txt"), "w").write(
                render(e[ea:eb], head + " -- Coleridge's prose, crib only",
                       numbers=True))
            manifest.append({
                "file": f"{idx:03d}.txt",
                "title": title,
                "part": p + 1,
                "of": len(bounds) - 1,
                "chapter": True,
                **({"part_before": DIVIDERS[title]}
                   if p == 0 and title in DIVIDERS else {}),
            })
            idx += 1

    if derived:
        print("DERIVED -- pin these, then re-run:")
        for t, lg, le, w, cuts in derived:
            print(f"  {t!r}: greek {lg} eng {le} words {w} cuts {cuts}")
        raise SystemExit(1)
    if total != TOTAL_GREEK:
        raise SystemExit(f"total {total} Greek words, pinned {TOTAL_GREEK}")
    missed = [KIND_FIXES[i] for i in range(len(KIND_FIXES)) if not FIXES_HIT[i]]
    if missed:
        raise SystemExit(f"KIND_FIXES never applied: {missed} -- the source "
                         f"changed, or a range is wrong")
    if sorted(FIXES_APPLIED) != sorted(SPEAKER_FIXES):
        raise SystemExit(f"SPEAKER_FIXES applied {FIXES_APPLIED}, expected "
                         f"{list(SPEAKER_FIXES)} -- the source changed")
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w"),
              indent=1)
    print(f"{idx} files, {total:,} Greek words, {len(PLAYS)} plays; "
          f"kind fixes hit {dict(FIXES_HIT)}")
    for m in manifest:
        w = len(open(os.path.join(chap, m["file"])).read().split())
        print(f"  {m['file']}  {w:>6,}  {m['title']} "
              f"({m['part']}/{m['of']})")


if __name__ == "__main__":
    main()
