"""Sophocles: the seven surviving plays, from the Greek, with Jebb as crib.

Sources, both from Perseus' `canonical-greekLit` on GitHub -- the pattern
odyssey/prep.py established:
    tlg0011.tlgNNN.perseus-grc2.xml    Jebb's Greek text
    tlg0011.tlgNNN.perseus-eng2/3.xml  Jebb's facing English PROSE

THE FORM, AND WHY IT IS DERIVABLE RATHER THAN A JUDGEMENT CALL. Greek
tragedy alternates SPOKEN scenes (iambic trimeter) with SUNG choral odes
(lyric metres), and chanted anapaests between the two. Alex's ruling is
that the spoken scenes become modern PROSE and the sung parts stay
VERSE -- the one formal distinction that defines the genre, and the one
nearly every translation blurs. That distinction is IN THE MARKUP:

    episode / spoken / dialogue        SPOKEN  -> prose
    choral / strophe / antistrophe     SUNG    -> verse
    epode / mesode / kommos / lyric    SUNG    -> verse
    anapests                           CHANTED -> verse

so prep can derive it per speech and check.py can assert it, instead of
its being a convention applied by hand five hundred times.
NOTE JEBB IS PROSE THROUGHOUT, odes included. The verse setting is OURS;
the crib is never evidence for it.

TAKE SUNG/SPOKEN FROM THE GREEK ONLY. The two files were marked up
independently and their division LABELLING disagrees -- The Women of
Trachis counts 111 sung speeches in the Greek and 24 in the English,
which is a different markup generation (eng3). The metre is a fact about
the Greek, so the Greek decides; the English is used for MEANING alone.
Their SPEECH COUNTS, by contrast, agree well enough to be a witness
(4 plays exact, 3 off by <= 4) and the differences are pinned in EXPECT.

A <div> MAY CARRY BOTH DIRECT <sp> CHILDREN AND CHILD <div>s, and a
walk that recurses to the leaves and emits only those DROPS THE DIRECT
SPEECHES SILENTLY -- 176 of Ajax's 310 in the first draft of this file,
with no error and a plausible-looking count. The unit is therefore the
SPEECH, tagged with its nearest enclosing div, never the division.
"""
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
       "master/data/tlg0011/tlg%03d/tlg0011.tlg%03d.perseus-%s.xml")

# Production order, which is how the volume is arranged. The three Theban
# plays were NOT written as a trilogy and printing them as one misleads:
# Antigone is the EARLIEST of the three and Oedipus at Colonus the last
# thing Sophocles wrote, forty years later.
PLAYS = [
    (3, "Ajax", "c. 442 BC", "eng2"),
    (2, "Antigone", "c. 441 BC", "eng2"),
    (4, "Oedipus the King", "c. 429 BC", "eng2"),
    (1, "The Women of Trachis", "date unknown", "eng3"),
    (5, "Electra", "c. 410 BC", "eng2"),
    (6, "Philoctetes", "409 BC", "eng2"),
    (7, "Oedipus at Colonus", "401 BC", "eng2"),
]

SUNG = {"choral", "strophe", "antistrophe", "epode", "mesode", "kommos",
        "lyric", "anapests", "astrophic", "proode",
        # dactylic hexameter, once, at Philoctetes 839-842: Neoptolemus
        # speaks three epic lines inside the Chorus' lyric, and the
        # oracular metre is the whole point of them. Chanted, like the
        # anapaests, so it is set as verse. LOOKED AT, not inferred.
        "hexameter"}
SPOKEN = {"episode", "spoken", "dialogue", "prologue", "exodos", "textpart",
          # "close" is the stichomythia that ends Oedipus the King --
          # Oedipus and Creon trading single lines -- and "trochaic" is
          # the same shape in Philoctetes. Trochaic tetrameter is a
          # RECITATIVE metre in tragedy, faster than iambic to mark
          # excitement; it is delivered, not sung.
          "close", "trochaic"}

# Greek/English speech-count differences, each with its reason. The two
# editions were marked up independently, so a small disagreement is a
# fact about the transcription and not about Sophocles. Never averaged.
EXPECT = {
    "The Women of Trachis": (273, 269,
        "eng3 is a different markup generation and merges four "
        "single-line exchanges in the kommos"),
    "Philoctetes": (414, 415,
        "the English splits one of Neoptolemus' speeches at a line "
        "anchor the Greek keeps whole"),
    "Oedipus at Colonus": (546, 544,
        "two of the Chorus' short lyric interjections are merged in "
        "the English"),
}

# Greek words per play, DERIVED THEN PINNED as a regression guard (the
# purgatorio rule). The load-bearing witnesses are the ones from outside
# this file: the crib's independent parse, and the speech counts.
GREEK_WORDS = {
    "Ajax": 7915, "Antigone": 7360, "Oedipus the King": 9292,
    "The Women of Trachis": 7294, "Electra": 8704,
    "Philoctetes": 8830, "Oedipus at Colonus": 10400,
}
TOTAL_GREEK = 59795

MAX_GREEK = 3300          # per file; Jebb runs 1.54x, so ~5k English out


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


def stream(root):
    """Every <sp>, in document order, as (kind, speaker, [(line, text)]).

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
                out.append((kind, name, lines, list(pending)))
                pending.clear()

    walk(root.find(f".//{TEI}body"), "spoken")
    return out


def is_sung(kind):
    if kind in SUNG:
        return True
    if kind in SPOKEN:
        return False
    raise SystemExit(f"prep: unknown division kind {kind!r} -- classify it "
                     f"as sung or spoken before continuing")


def render(speeches, title, crib=None):
    """One play as text. Sung speeches are tab-indented, spoken are not."""
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
            tag = f"{n} " if n else ""
            body.append(("\t" if sung else "") + tag + t)
        body.append("")
    return "\n".join(body).rstrip() + "\n"


def split_points(speeches, limit=MAX_GREEK):
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
        g = stream(fetch(n, "grc2"))
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

        cuts = split_points(g)
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
                render(e[ea:eb], head + " -- Jebb's prose, crib only"))
            manifest.append({
                "file": f"{idx:03d}.txt",
                "title": title,
                "part": p + 1,
                "of": len(bounds) - 1,
                "chapter": True,
                **({"part_before": f"{title} ({date})"} if p == 0 else {}),
            })
            idx += 1

    if total != TOTAL_GREEK:
        raise SystemExit(f"total {total} Greek words, pinned {TOTAL_GREEK}")
    json.dump(manifest, open(os.path.join(HERE, "manifest.json"), "w"),
              indent=1)
    print(f"{idx} files, {total:,} Greek words, {len(PLAYS)} plays")
    for m in manifest:
        w = len(open(os.path.join(chap, m["file"])).read().split())
        print(f"  {m['file']}  {w:>6,}  {m['title']} "
              f"({m['part']}/{m['of']})")


if __name__ == "__main__":
    main()
