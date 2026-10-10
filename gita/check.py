"""Per-book checks for gita/ -- the euclid-rivals / lucretius pattern.

THE DRAFT IS THE FILE OF RECORD. An agent writes gita/drafts/NNN.txt, which
is the English with a verse marker -- {47}, or {42-44} where one English
sentence must carry several verses -- at the point where each verse begins.
This script checks the draft and, ONLY WHEN IT IS CLEAN, writes
modern_chapters/NNN.txt with the markers removed. Never edit
modern_chapters/ by hand: a hand edit there is a fact held in two places
(duplicated-fact-bugs), and this script fails any file whose modern text is
not exactly its stripped draft.

What verify.py cannot see, and this checks:
  1. A DROPPED VERSE. Seven hundred short verses, many of them catalogue
     lines (the warriors of chapter 1, the glories of chapter 10): a lost
     verse moves the word ratio by under one percent. Every verse 1..n must
     be marked exactly once, in order, against the counts prep.py asserts
     from the critical edition.
  2. A MISATTRIBUTED SPEECH (euclid-speaker-tags). The speaker tags are the
     critical edition's 55 "X uvaca" lines, no more and no fewer, each its
     own paragraph, in order, and each immediately before the verse the
     Sanskrit puts it on. Where the vulgate (and Besant) add a tag the
     critical edition lacks, the speech stays inside Sanjaya's narration.
  3. THE ARCHAISM AND CALQUE SWEEP. Besant writes "thee", "thou", "hath",
     "the Blessed Lord", "the Unmanifested", "Reason" for buddhi; with her
     open all day the drift is into her English. And the Sanskrit
     vocative epithets (Partha, Kaunteya, Parantapa, Madhusudana ...) are
     resolved, never carried bare. No exemption list: if a correct
     sentence ever fires, add an EXACT PHRASE to ALLOW with the reason.
  4. NAMES (the fleming rule for a text with no digits): every proper name
     in a chapter's Sanskrit must appear in its English, in the form the
     ledger locks.
  5. Heading exact; prose only (no tab); no markup; no "--"; no line
     ending in a hyphen; no paragraph the renderer would set as a heading.
Exit status nonzero on any finding.

    python3 gita/check.py NNN [NNN ...]     check drafts, write modern files
    python3 gita/check.py                   check every draft that exists
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import assemble                                       # noqa: E402

# PROVISIONAL (the dogen rule: derive the band from finished files, never
# from a guess). English words per Sanskrit word, verse lines only. Besant's
# literal 1922 English runs 1.75-2.32 per chapter (1.97 overall); a
# readable retelling that resolves epithets and folds in the allusions runs
# above a crib. Re-derive from file 000 and record the band in running_notes.
MIN_RATIO, MAX_RATIO = 1.9, 3.1  # set 2026-10-09 from the voice batch: ch1 2.15, ch2 2.32 (1.21x Besant); projects to 2.1-2.8

MARK = re.compile(r"\{(\d+)(?:-(\d+))?\}")
ARCHAIC = re.compile(
    r"\b(thou|thee|thy|thine|hast|hath|doth|dost|shalt|wilt|art thou|ye|"
    r"unto|ere|whilst|amongst|betwixt|methinks|forsooth|yonder|nay|"
    r"verily|behold|wherefore|whence|whither|hither|perchance|o'er|"
    r"ne'er|'tis|'twas|aught|naught|hark|lo|spake|fain|cometh|goeth|"
    r"doeth|knoweth|seeth|liveth)\b", re.I)
# Besant's calques and the Theosophical capitals, and the bare Sanskrit
# vocatives. Case-sensitive on purpose: "reason" is a word, "the Reason"
# meaning buddhi is her costume.
BANNED = [
    (re.compile(r"\bBlessed Lord\b"), "Besant's 'the Blessed Lord' (tag is 'Krishna said:')"),
    (re.compile(r"\bUnmanifest(ed)?\b"), "capitalised 'Unmanifest': write 'the unmanifest'"),
    (re.compile(r"\bthe SELF\b|\bthe Self\b"), "capital 'Self': the ledger locks lowercase 'self'"),
    (re.compile(r"(?<![.!?] )(?<!^)\bReason\b"), "Besant's 'Reason' for buddhi: 'understanding'"),
    (re.compile(r"\bthe Eternal\b"), "Besant's 'the Eternal' for brahman: 'Brahman'"),
    (re.compile(r"\bO [A-Z]"), "vocative 'O ...': modern English drops the O"),
    (re.compile(r"(?<=[a-z,;:—] )(Me|My|Mine|Myself|Thee|Thou|Thy|You|Your|Yourself|He|Him|His)\b"),
     "reverential capital on a pronoun mid-sentence: the ledger locks lowercase"),
    # Not "Bharata" (the ancestor, and the Bharata clan) and not "Pandava"
    # (the Pandavas are an army in chapter 1): the vocative ban above
    # catches "O Bharata"; these never name anyone but Krishna or Arjuna.
    (re.compile(r"\b(Partha|Kaunteya|Parantapa|Dhananjaya|Gudakesha|"
                r"Madhusudana|Janardana|Keshava|Hrishikesha|Govinda|Varshneya|"
                r"Achyuta|Madhava|Kurunandana|Purusharshabha|Mahabaho|Savyasachin|"
                r"Kurusattama|Bharatarshabha)\b"),
     "bare Sanskrit epithet: resolve it (running_notes NAMES AND EPITHETS)"),
    (re.compile(r"\bkarma\b", re.I), "'karma' is a false friend: 'action' / 'work'"),
    (re.compile(r"\bavatars?\b", re.I), "the word avatar is not in the Gita: 4.6-8 say 'I come into being'"),
    (re.compile(r"\b(sattvic|rajasic|tamasic)\b", re.I), "the gunas' adjectives are 'of goodness / passion / darkness'"),
]
# Exact phrases a banned pattern may legitimately sit inside, each with its
# reason. Empty until a correct sentence fires (fix the check, not the text).
ALLOW = []

# Sanskrit stem (IAST, as it appears in chapters/) -> accepted English forms.
# A key is a regex matched at the START of a Sanskrit word in the verse lines
# only, never inside one: "manu" alone fires on every manusya (human being),
# "krpa" on krpaya (pity), "makar" on bhimakarma. Each key was run over all
# eighteen source files before it was kept. Only names; the epithets for
# Krishna and Arjuna are resolved, never carried, so they are not here.
NAMES = {
    "duryodhan": ["Duryodhana"], "bhīṣm": ["Bhishma"], "droṇ": ["Drona"],
    "karṇ": ["Karna"], "kṛpaś": ["Kripa"], "aśvatthām": ["Ashvatthaman"],
    "vikarṇ": ["Vikarna"], "saumadatti": ["Somadatta"], "yuyudhān": ["Yuyudhana"],
    "virāṭ": ["Virata"], "drupad": ["Drupada"], "dhṛṣṭaket": ["Dhrishtaketu"],
    "cekitān": ["Chekitana"], "kāśi": ["Kashi"], "kāśy": ["Kashi"],
    "purujit": ["Purujit"], "kuntibhoj": ["Kuntibhoja"], "śaibya": ["Shaibya"],
    "yudhāmany": ["Yudhamanyu"], "uttamauj": ["Uttamaujas"],
    "saubhadr": ["Subhadra"], "draupadey": ["Draupadi"],
    "pāñcajany": ["Panchajanya"], "devadatt": ["Devadatta"], "pauṇḍr": ["Paundra"],
    "anantavijay": ["Anantavijaya"], "sughoṣ": ["Sughosha"], "sughoṣamaṇipuṣpak": ["Manipushpaka"],
    "yudhiṣṭhir": ["Yudhishthira"], "nakula": ["Nakula"], "sahadev": ["Sahadeva"],
    "śikhaṇḍ": ["Shikhandi"], "dhṛṣṭadyumn": ["Dhrishtadyumna"], "sātyak": ["Satyaki"],
    "jayadrath": ["Jayadratha"], "janak": ["Janaka"], "vivasvat": ["Vivasvat"],
    "ikṣvāk": ["Ikshvaku"], "bṛhaspat": ["Brihaspati"], "nārad": ["Narada"],
    "asito": ["Asita"], "devalo": ["Devala"], "vyās": ["Vyasa"], "marīc": ["Marichi"],
    "vāsava": ["Indra"], "śaṃkar": ["Shiva", "Shankara"], "vitteś": ["Kubera"],
    "pāvak": ["Agni", "fire"], "meru": ["Meru"], "skand": ["Skanda"], "bhṛgu": ["Bhrigu"],
    "himālay": ["Himalaya"], "aśvattha[ṃmḥ]": ["fig"], "citrarath": ["Chitraratha"],
    "kapil": ["Kapila"], "uccaiḥśravas": ["Ucchaihshravas"], "airāvat": ["Airavata"],
    "kāmadhuk": ["Kamadhuk", "wishing cow", "cow of plenty"], "kandarp": ["Kandarpa", "Kama"],
    "vāsuk": ["Vasuki"], "anantaś": ["Ananta"], "varuṇ": ["Varuna"],
    "aryam": ["Aryaman"], "yamaḥ": ["Yama"], "prahlād": ["Prahlada"],
    "vainatey": ["Garuda"], "rāmaḥ": ["Rama"], "makaraś": ["makara"],
    "jāhnav": ["Ganges"], "uśan": ["Ushanas"], "vṛṣṇ": ["Vrishni"],
    "gāyatr": ["Gayatri"], "mārgaśīrṣ": ["Margashirsha"], "kusumākar": ["spring"],
    "rudr": ["Rudra"], "ādityānām": ["Aditya"], "rudrādity": ["Aditya"], "vasav": ["Vasu"], "sādhy": ["Sadhya"],
    "aśvin": ["Ashvin"], "marut": ["Marut"], "gandharv": ["Gandharva"],
    "yakṣarakṣ": ["Yaksha", "yaksha"], "brahmāṇam": ["Brahma"],
    "gāṇḍīv": ["Gandiva"], "kurukṣetr": ["Kurukshetra"], "dhṛtarāṣṭr": ["Dhritarashtra"],
    "saṃjay": ["Sanjaya"], "vedeṣu": ["Veda"], "vedair": ["Veda"],
    "sāmaved": ["Sama"], "ṛk sāma": ["Rig"], "bṛhatsām": ["Brihat"],
    "praṇav": ["Om"], "oṃ": ["Om"], "oṃkār": ["Om"], "tat sad": ["Tat"],
    "manur": ["Manu"], "manava": ["Manu"], "viṣṇ": ["Vishnu"],
}


def strip_markers(text):
    text = re.sub(r"\{\d+(?:-\d+)?\} ?", "", text)
    return "\n".join(l.rstrip() for l in text.split("\n"))


def sanskrit_words(src):
    return sum(len(l.split()) for l in src.split("\n") if l.startswith("\t"))


def check(f, entry, chap, drafts, mod, write):
    say = []
    src = open(os.path.join(chap, f), encoding="utf-8").read()
    draft = open(os.path.join(drafts, f), encoding="utf-8").read()
    lines = draft.split("\n")
    n = entry["verses"]

    # 5. heading and form
    if lines[0] != entry["title"]:
        say.append(f"line 1 is {lines[0]!r}; the manifest says {entry['title']!r}")
    if len(lines) < 3 or lines[1].strip():
        say.append("line 2 must be blank (one file per chapter: no part marker)")
    body = "\n".join(lines[2:])
    for i, ln in enumerate(lines, 1):
        if ln.startswith("\t") or ln.startswith("    "):
            say.append(f"indented line {i}: the edition is prose")
            break
    for i, ln in enumerate(lines, 1):
        if ln.rstrip().endswith("-") and not ln.rstrip().endswith("--"):
            say.append(f"line {i} ends in a hyphen: both renderers join it as 'x- y'")
    if "--" in draft:
        say.append("double hyphen: use a real em dash with spaces ( — )")
    if re.search(r"[\[\]*_<>#]", draft):
        say.append("markup character ([ ] * _ < > #): the edition is plain prose")

    # 1. verse markers
    seq = []
    for m in MARK.finditer(body):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if b < a or b - a > 4:
            say.append(f"odd range marker {m.group(0)}")
        seq.extend(range(a, b + 1))
    if seq != list(range(1, n + 1)):
        missing = sorted(set(range(1, n + 1)) - set(seq))
        dup = sorted({x for x in seq if seq.count(x) > 1})
        order = [f"{x}>{y}" for x, y in zip(seq, seq[1:]) if y != x + 1][:5]
        say.append(f"verse markers: missing {missing[:12]}, repeated {dup[:12]}, "
                   f"out of order at {order}")
    # strip_markers removes "{N} "; a marker not set off by whitespace on
    # both sides would weld two words ("word.{5} Next" -> "word.Next")
    for m in MARK.finditer(body):
        before = body[m.start() - 1] if m.start() else "\n"
        after = body[m.end()] if m.end() < len(body) else ""
        if not before.isspace() or after != " ":
            say.append(f"marker {m.group(0)} must have whitespace before it and one space after it")
    if re.search(r"[{}]", MARK.sub("", body)):
        say.append("a brace that is not a well-formed verse marker {N} or {N-M}")

    # 2. speakers
    tags = set(t for _, t in entry["speakers"]) | {
        "Dhritarashtra said:", "Sanjaya said:", "Arjuna said:", "Krishna said:"}
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    got = []
    for k, p in enumerate(paras):
        flat = " ".join(p.split())
        if flat in tags:
            nxt = MARK.match(paras[k + 1]) if k + 1 < len(paras) else None
            got.append([int(nxt.group(1)) if nxt else None, flat])
        elif re.match(r"^(Dhritarashtra|Sanjaya|Arjuna|Krishna) said:", flat):
            say.append(f"speaker tag not alone in its paragraph: {flat[:50]}")
    if got != entry["speakers"]:
        say.append(f"speaker tags {got} != critical edition {entry['speakers']} "
                   "(tag own paragraph; next paragraph opens on that verse's marker)")

    clean = strip_markers(draft)
    text = "\n".join(clean.split("\n")[2:])

    # ratio
    sw = sanskrit_words(src)
    ew = len(" ".join(p for p in text.split("\n\n")
                      if " ".join(p.split()) not in tags).split())
    r = ew / max(1, sw)
    if not MIN_RATIO <= r <= MAX_RATIO:
        say.append(f"ratio {r:.2f} outside {MIN_RATIO}-{MAX_RATIO} "
                   f"({ew} English / {sw} Sanskrit words)")

    # 3. sweeps
    def allowed(m, t):
        ctx = t[max(0, m.start() - 60):m.end() + 60]
        return any(ok in ctx for ok in ALLOW)
    for m in ARCHAIC.finditer(text):
        if not allowed(m, text):
            say.append(f"archaism {m.group(0)!r}: ...{text[max(0, m.start()-30):m.end()+30]!r}")
    # Flatten per paragraph, joined by a pilcrow, so a tag paragraph
    # ("Krishna said:") does not read as mid-sentence punctuation before
    # a verse that opens on "You" or "My".
    flat_text = " ¶ ".join(" ".join(p.split()) for p in text.split("\n\n"))
    for pat, why in BANNED:
        for m in pat.finditer(flat_text):
            if not allowed(m, flat_text):
                say.append(f"{why}: ...{flat_text[max(0, m.start()-30):m.end()+30]!r}")

    # 4. names
    verse = " ".join(l for l in src.lower().split("\n") if l.startswith("\t"))
    for stem, engs in NAMES.items():
        if (re.search(r"(?<![a-zāīūṛṝḷṃḥṅñṭḍṇśṣ])" + stem, verse)
                and not any(e.lower() in text.lower() for e in engs)):
            say.append(f"name {stem!r} in the Sanskrit, none of {engs} in the English")

    # 5. renderer
    stripped = assemble.EMPH.sub("", text)
    if "*" in stripped or "_" in stripped:
        say.append("asterisk or underscore that EMPH will not render")
    for par in paras:
        par = " ".join(MARK.sub("", par).split())
        if not par:
            continue
        if len(par) > 3 and par == par.upper() and any(c.isalpha() for c in par):
            say.append(f"all-caps paragraph renders as a heading: {par[:50]}")
        elif assemble.is_subheading(par):
            say.append(f"paragraph renders as a subheading: {par[:60]}")

    # the generated file
    mp = os.path.join(mod, f)
    if not say and write:
        os.makedirs(mod, exist_ok=True)
        open(mp, "w", encoding="utf-8").write(clean)
    if os.path.exists(mp) and open(mp, encoding="utf-8").read() != clean:
        say.append("modern_chapters file differs from the stripped draft: edit the "
                   "DRAFT and rerun, never modern_chapters/")
    return say, r


def main(argv):
    chap = os.path.join(HERE, "chapters")
    drafts = os.path.join(HERE, "drafts")
    mod = os.path.join(HERE, "modern_chapters")
    want = argv[1:]
    manifest = {e["file"]: e for e in json.load(open(os.path.join(HERE, "manifest.json")))}
    bad = seen = 0
    for f in sorted(manifest):
        if want and f[:3] not in want:
            continue
        if not os.path.exists(os.path.join(drafts, f)):
            if want:
                print(f"{f}: no draft at gita/drafts/{f}")
                bad += 1
            elif os.path.exists(os.path.join(mod, f)):
                print(f"{f}: modern_chapters file with no draft behind it")
                bad += 1
            continue
        seen += 1
        say, r = check(f, manifest[f], chap, drafts, mod, write=True)
        if say:
            bad += 1
            print(f"{f}:")
            for s in say:
                print(f"  {s}")
        else:
            print(f"{f}: ok  (ratio {r:.2f}); modern_chapters/{f} written")
    print(f"\nchecked {seen}/{len(manifest)} drafts")
    if bad:
        print(f"{bad} file(s) with findings")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
