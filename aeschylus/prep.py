"""Aeschylus: the seven surviving plays, from the Greek, with Smyth as crib.

sophocles/prep.py with the constants changed and ONE new mechanism. Read
that file's docstring first; everything there holds. Sources, from
Perseus' `canonical-greekLit` on GitHub:
    tlg0085.tlgNNN.perseus-grc2.xml    Smyth's Greek text (Loeb, 1926)
    tlg0085.tlgNNN.perseus-eng2/3.xml  Smyth's facing English PROSE

THE NEW MECHANISM IS KIND_FIXES, and it exists because THE GREEK MARKUP
OF AESCHYLUS LABELS SEVERAL LONG SPOKEN SCENES WITH THE KIND OF THE
CHORAL STANZA BEFORE THEM. Sophocles' files were clean; here a <div
subtype="anapests"> that opens on the Chorus' twenty-six chanted lines
greeting Agamemnon runs on for 190 lines and swallows the whole iambic
scene between Agamemnon and Clytemnestra; a <div subtype="lyric"> opened
for the Chorus' eight-line cry at Prometheus Bound 687 runs to 876 and
takes the entire Io scene with it. Six scenes and ~700 lines of dialogue
would have been set as VERSE, and check.py -- which asserts the modern
file against prep -- would have insisted on it. FOUND BY LISTING EVERY
DIVISION'S LINE SPAN AND READING THE LONG ONES, not by any check: a
division that runs 190 lines under a lyric label is wrong on its face.
The overrides are per SPEECH (line range, optional speaker), each with
its reason, and main() asserts that every one of them fired.

THE FORM is Alex's ruling from sophocles/: spoken scenes -> modern
prose, sung odes and chanted anapaests -> tab-indented verse. Smyth is
prose throughout, so the crib is never evidence for the setting.
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
       "master/data/tlg0085/tlg%03d/tlg0085.tlg%03d.perseus-%s.xml")

# Production order. The Oresteia IS a trilogy -- the only one that
# survives complete -- and is grouped under one divider; the other four
# stand alone. Prometheus Bound is last because its date is unknown and
# its authorship is disputed (many scholars think it is not by Aeschylus
# at all); it is included because it has always travelled with the seven.
PLAYS = [
    (2, "The Persians", "472 BC", "eng2"),
    (4, "Seven Against Thebes", "467 BC", "eng2"),
    (1, "The Suppliants", "c. 463 BC", "eng2"),
    (5, "Agamemnon", "458 BC", "eng3"),
    (6, "The Libation Bearers", "458 BC", "eng2"),
    (7, "The Eumenides", "458 BC", "eng2"),
    (3, "Prometheus Bound", "date unknown", "eng2"),
]
# The Oresteia's three plays nest under one divider (assemble.py nests a
# "chapter": true section under the nearest preceding part_before).
DIVIDERS = {
    "The Persians": "The Persians (472 BC)",
    "Seven Against Thebes": "Seven Against Thebes (467 BC)",
    "The Suppliants": "The Suppliants (c. 463 BC)",
    "Agamemnon": "The Oresteia (458 BC)",
    "Prometheus Bound": "Prometheus Bound (date unknown)",
}

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
          "iambics",
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
    # Agamemnon 810-974: the Chorus greets the king in anapaests (782-809)
    # and the <div> then runs on through Agamemnon's speech, Clytemnestra's
    # welcome, their stichomythia and her "there is the sea" speech.
    (5, 810, 974, None, False),
    # Agamemnon 1343-1406: the king's death-cries, the elders' twelve
    # couplets of deliberation, and Clytemnestra over the bodies -- all
    # iambic; the anapaests are only the Chorus' 1331-1342.
    (5, 1343, 1406, None, False),
    # Prometheus Bound 300-398: Oceanus arrives on anapaests (286-299) and
    # the whole iambic scene with Prometheus is marked with them.
    (3, 300, 398, None, False),
    # Prometheus Bound 696-876: the Chorus' eight-line cry at Io's entrance
    # is lyric; the 180 lines of Io and Prometheus after it are iambic.
    (3, 696, 876, None, False),
    # Libation Bearers 730-782: the Nurse scene, marked with the Chorus'
    # anapaests at 719-729.
    (6, 730, 782, None, False),
    # Libation Bearers 869-934: Aegisthus' cry, the Servant, Clytemnestra
    # and Orestes at the door, and Pylades' three lines -- iambic.
    (6, 869, 934, None, False),
    # Libation Bearers 1010-1062: Orestes' iambics alternate with the
    # Chorus' anapaests to the end; only his are spoken.
    (6, 1010, 1062, "Ὀρέστης", False),
    # Libation Bearers 152-163: the Chorus' short lyric inside the first
    # episode ("let the tear fall"), marked as episode.
    (6, 152, 163, "Χορός", True),
    # Seven Against Thebes 369-652: the shield scene. Seven pairs of
    # speeches -- the Scout describes a champion, Eteocles names the man
    # to face him -- framed by the Chorus' short lyric stanzas, and the
    # <div>s follow the stanzas, so the speeches inherit "strophe".
    (4, 369, 652, "Ἄγγελος", False),
    (4, 369, 652, "Ἐτεοκλής", False),
    # Eumenides 778-891: the Furies' lament in strophe and antistrophe,
    # answered each time by Athena in iambics.
    (7, 778, 891, "Ἀθηνᾶ", False),
    # Eumenides 299-306: the Furies' "Apollo will not save you" is iambic
    # trimeter, marked "choral" because the binding song follows it.
    (7, 299, 306, None, False),
    # EPIRRHEMATIC SCENES (added after batch one, when three agents flagged
    # the same thing independently): an actor answers the Chorus' sung
    # stanzas in iambic trimeter, and Perseus' strophe/antistrophe <div>s
    # wrap the reply with the stanza. Iambic trimeter is spoken; so the
    # actor's replies are prose and the Chorus' stanzas stay verse.
    (2, 260, 289, "Ἄγγελος", False),           # Persians, the first kommos
    (2, 681, 693, "Εἴδωλον Δαρείου", False),   # Darius' first speech
    (2, 697, 699, "Δαρεῖος", False),           # and his trochaic reply
    (4, 208, 244, "Ἐτεοκλής", False),          # Seven, Eteocles v. the women
    (4, 689, 711, "Ἐτεοκλής", False),          # Seven, before the seventh gate
    (1, 354, 417, "Βασιλεύς", False),          # Suppliants, the King's replies
    (5, 1074, 1113, "Χορός", False),           # Agamemnon, the elders answer
                                               # Cassandra's cries in trimeters
                                               # (their lyric begins at 1119)
    (5, 1412, 1425, "Κλυταιμήστρα", False),    # Agamemnon, her first reply in
                                               # the kommos is trimeter; her
                                               # anapaests begin at 1462
    # FOUND BY THE SYLLABLE-COUNT WITNESS (see check.py metre_report): a
    # speech whose every line runs 12-15 syllables inside a lyric division
    # is iambic trimeter, and a run of 6-11-syllable lines inside an
    # episode is lyric. Each was then read.
    (1, 739, 742, None, False),    # Suppliants: Danaus and the Chorus trade
    (1, 746, 749, None, False),    #   trimeter couplets between the lyric
    (1, 753, 756, None, False),    #   stanzas as the Egyptian fleet is seen
    (1, 882, 884, "Κῆρυξ", False), # the Herald's threats are trimeters
    (1, 893, 894, "Κῆρυξ", False),
    (3, 101, 113, None, False),    # Prometheus' first speech: trimeters
                                   #   between anapaests (93-100, 120-127)
    (3, 589, 592, None, False),    # Io's monody: four inset trimeters
    (7, 254, 275, "Χορός", True),  # Eumenides: the Furies' hunting song
                                   #   when they find Orestes, marked episode
    (6, 1044, 1064, None, False),  # Libation Bearers: the Chorus answers
                                   #   Orestes in trimeters here too; its
                                   #   anapaests are 1007-9, 1018-20, 1065-76
]
FIXES_HIT = collections.Counter()

# Greek/English speech-count differences, each with its reason. The two
# editions were marked up independently, so a small disagreement is a
# fact about the transcription and not about Sophocles. Never averaged.
EXPECT = {
    "The Persians": (211, 210,
        "the English folds the Chorus' opening anapaests into an "
        "unlabelled speech the parser reads differently"),
    "Prometheus Bound": (219, 214,
        "the Greek splits Prometheus' first lament (88-127) by metre into "
        "five speeches and his 846 speech in two; the English keeps each "
        "whole"),
    "Seven Against Thebes": (191, 193,
        "the English splits two speeches at line anchors (812, 848) the "
        "Greek keeps whole"),
    "Agamemnon": (235, 238,
        "the English gives the twelve elders' couplets at 475-501 to six "
        "named speakers where the Greek has three Chorus speeches, and "
        "the Greek splits Clytemnestra's welcome at 887"),
    "The Libation Bearers": (227, 226,
        "the Greek splits Electra's speech at 195 ('pheu.'); the English "
        "keeps 183-211 whole"),
}

# Greek words per play, DERIVED THEN PINNED as a regression guard (the
# purgatorio rule). The load-bearing witnesses are the ones from outside
# this file: the crib's independent parse, and the speech counts.
GREEK_WORDS = {
    "The Persians": 5221, "Seven Against Thebes": 5157,
    "The Suppliants": 4977, "Agamemnon": 8254,
    "The Libation Bearers": 5463, "The Eumenides": 5320,
    "Prometheus Bound": 5943,
}
TOTAL_GREEK = 40335

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
SPEAKER_FIXES = {("812", "Χορός"): "Ἄγγελος"}
FIXES_APPLIED = []
# The Suppliants writes the King's tag lower-case once (line 911).
SPEAKER_NORMALISE = {"βασιλεύς": "Βασιλεύς"}


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
CUTS = {
    "The Persians": [69], "Seven Against Thebes": [63],
    "The Suppliants": [139], "Agamemnon": [71, 139],
    "The Libation Bearers": [124], "The Eumenides": [95],
    "Prometheus Bound": [112],
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
    for n, title, date, eng in PLAYS:
        g = stream(fetch(n, "grc2"), play=n)
        e = stream(fetch(n, eng))
        gw = sum(len(t.split()) for _, _, ls, _ in g for _, t in ls)

        if title in EXPECT:
            want_g, want_e, why = EXPECT[title]
            if (len(g), len(e)) != (want_g, want_e):
                raise SystemExit(
                    f"{title}: speech counts {len(g)}/{len(e)}, expected "
                    f"{want_g}/{want_e} ({why}) -- the source changed")
        elif len(g) != len(e):
            raise SystemExit(
                f"{title}: Greek has {len(g)} speeches, English {len(e)}. "
                f"An undocumented disagreement between the two witnesses; "
                f"read it and add it to EXPECT with its reason.")
        if gw != GREEK_WORDS[title]:
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
                render(e[ea:eb], head + " -- Smyth's prose, crib only",
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
