#!/usr/bin/env python3
"""Build site/index.html, the front page: every modern retelling, by shelf.

    python3 build_index.py

THE LIST IS DERIVED FROM env, NEVER KEPT HERE (the build_restored.py
rule). A book is on the front page because its env names a SHELF=, one
of SHELVES below; title, author, date, epub and original-text link come
from env and the build tree, and the reading time is computed from the
retelling's own word count. The only per-book text stored in this file
is the blurb, which exists nowhere else, and one display title.

SHELF=, NOT TOPIC=. TOPIC= is the Restored Editions page's key, and the
Royal Institution volumes carry both (Ball is "Science" here and
"Physical sciences" there), so one key cannot serve both pages.

Within a shelf, books run in order of composition, so the year tabs read
as a timeline down each section. Stylesheet: site/site.css, shared with
restored.html and about.html through render_card() and page_shell(). Covers:
site/covers/thumb/, made by build_feeds.make_thumbs().
"""
import html
import re
import sys
from pathlib import Path

import assemble

ROOT = Path(__file__).parent
SITE = ROOT / "site"

SHELVES = ["Epic, Myth & Tragedy", "Tales & Novels", "The Art of Living",
           "Philosophy", "Politics, War & Law", "Economics",
           "Histories & Lives", "Science", "Mathematics & Logic"]

WORDS_PER_MINUTE = 235   # the median the hand-written read times implied

# Where the front page names a book differently from its env: democracy2's
# ORIGINAL_WORK is the French title, which is what its own page shows.
TITLES = {
    "democracy2": "Democracy in America (From the French)",
}

# One line per book, and a blurb has no other home. Keyed by book directory.
BLURBS = {
    'aeschylus':
        'The Oresteia complete, with the Persians, the Seven, the Suppliants and Prometheus Bound — from the Greek: the scenes as fast modern prose, the odes as verse, and the net, the yoke and the lion cub kept in the same words every time.',
    'augustine':
        'The first autobiography — the stolen pears, the garden at Milan, the night at Ostia — every sentence addressed to God, so that reading it is overhearing.',
    'autobiography':
        'The original American life story — runaway apprentice to statesman, told with a wink.',
    'ball':
        'The funniest of the Christmas lecturers takes you from the sun to the nebulae, measuring the sky with two children and a pair of scissors.',
    'boethius':
        'Waiting to be executed, the last Roman philosopher is visited by Philosophy, who tells him that nothing he has lost was ever his. With all thirty-nine poems.',
    'bunyan':
        'The most famous journey in English — the Slough of Despond, Vanity Fair, and the key called Promise that was in his pocket all along. Both parts complete.',
    'burke':
        'The book that invented conservatism — a warning, written in 1790, that a society is not a machine you can take apart and rebuild to a drawing.',
    'candide':
        "Voltaire's whirlwind satire of optimism in a broken world.",
    'candle':
        'The most famous science lectures ever given: the whole of chemistry drawn out of one burning candle, ending with the news that you are a slow candle yourself.',
    'catos-letters':
        'Eighteen selected letters on liberty, power, and free speech — the columns that taught America to argue for revolution.',
    'cellini':
        'A Florentine goldsmith dictates his own life while he works: two popes, the sack of Rome, several killings, a prison escape, and the Perseus cast with the roof on fire. From the Italian.',
    'common-law':
        'The life of the law has not been logic: it has been experience — crime, tort, contract and inheritance traced back to rules whose reasons died centuries ago.',
    'common-sense':
        'The pamphlet that talked America into independence.',
    'de-officiis':
        "Cicero's last book, a letter to his son — translated from the Latin: nothing dishonorable is ever truly useful.",
    'decameron':
        'Ten friends flee the plague and tell a hundred stories — bawdy, sly, and humane.',
    'democracy':
        'A young Frenchman tours the United States and sees the democratic future — flaws and all.',
    'democracy2':
        "A second pass, translated directly from Tocqueville's French.",
    'descartes':
        'Descartes doubts everything and rebuilds from “I think, therefore I am.”',
    'dialogues':
        'The complete dialogues — Socrates on trial, in the agora, and at the limits of knowledge.',
    'dogen':
        'Three short manuals from the founder of Sōtō Zen: how to sit, how to study, and how to cook. From the Chinese.',
    'eighty-days':
        'Phileas Fogg bets £20,000 that he can circle the globe in eighty days — complete from the French, with a final trick of the calendar.',
    'enchiridion':
        'The Stoic pocket manual — fifty-one drills for keeping your head, from a philosopher born enslaved.',
    'epictetus':
        "The lectures the Enchiridion was cut down from — a former slave telling Rome's young gentlemen that they are the ones in chains.",
    'ethics':
        'The original inquiry into the good life — happiness, virtue as habit, the mean, and friendship.',
    'euclid-rivals':
        'The author of Alice puts every geometry textbook of his day on trial, as a farce: the ghost of Euclid against Herr Niemand, Mr. Nobody, who loses every case.',
    'euripides':
        'Every surviving play, complete — Medea, the Bacchae, the Trojan Women, and the satyr play about blinding a giant — from the Greek: the arguments as fast modern prose, the songs as verse.',
    'federalist':
        "The Constitution's authors explain — and sell — their design.",
    'flatland':
        'Geometry as social satire: a square discovers the third dimension.',
    'fleming':
        "Six Christmas lectures arguing that a ripple, a ship's wake, a sung note, a petal's colour and Marconi's new wireless signal are all one thing in different media.",
    'forces':
        'Six Christmas lectures for children on gravity, heat, magnetism and electricity, arriving at the discovery that they are one force in different forms. With the original figures.',
    'galileo':
        "Four days of brilliant argument about whether the Earth moves — the vernacular bestseller that got its author hauled before the Inquisition, translated from Galileo's own Italian.",
    'gallic-war':
        "Caesar's own dispatches from the conquest of Gaul.",
    'grimm':
        'All two hundred tales and ten legends, complete — the famous ones and the hundred and sixty that nobody prints.',
    'herodotus':
        'The first history book — Persia, Egypt, and the Greek wars, with magnificent detours.',
    'hume':
        'Why experience can never prove the sun will rise tomorrow, and why Hume thinks that need not worry you.',
    'inferno':
        'Led down through Hell by a dead poet, Dante meets people he knew — popes, neighbours, a former teacher — still arguing Florentine politics. From the Italian, tercet for tercet.',
    'journey-center-earth':
        'A coded parchment, a dead Icelandic volcano, and a plunge into a lost world underground — complete from the French, not the mangled Victorian version.',
    'kenzeiki':
        "The oldest life of the founder of Sōtō Zen, written so that ordinary people could read it — with his letters, his kitchen rules, and the farmers' sworn statement about a coloured cloud.",
    'leviathan':
        'Why we need government at all — the founding argument of the modern state, written amid civil war.',
    'lucretius':
        'Everything is atoms and empty space, the soul dies with the body, and the gods never lift a finger. From the Latin, the whole poem, as prose — ending, without consolation, on the plague at Athens.',
    'malthus':
        "Malthus' unsettling arithmetic of people and food.",
    'meditations':
        "A Roman emperor's private notes to himself on how to live.",
    'memorabilia':
        'Socrates remembered by his other student — practical, sociable, and useful, with the Choice of Heracles.',
    'mill':
        "One principle pushed as far as it will go: the only ground for interfering with anyone's freedom is preventing harm to somebody else.",
    'montaigne':
        'The man who invented the essay, talking to you across four centuries about death, friendship, cannibals, and himself.',
    'nights':
        "Shahrazad's frame and eighteen of the great tales — the Fisherman and the Jinni, the Hunchback, Sindbad, Aladdin, Ali Baba — with Burton's fake-antique costume taken off.",
    'odyssey':
        'A soldier ten years trying to get home, a wife holding off a houseful of suitors, and a son who was a baby when he left. From the Greek, all twenty-four books, as prose.',
    'origin-of-species':
        "Darwin's patient, overwhelming case for evolution by natural selection.",
    'ovid':
        'The great storybook of classical myth — Daphne, Phaethon, Narcissus, Icarus, Orpheus, Pygmalion, Midas and hundreds more. All fifteen books, from the Latin.',
    'paradiso':
        'The third book of the Comedy: heaven as a bird waiting for dawn and a baby reaching for milk, and Saint Peter calling the papacy a sewer. From the Italian, tercet for tercet.',
    'peloponnesian-war':
        'Power, plague, and the ruin of Athens, by the first analytical historian.',
    'pillow-problems':
        'Seventy-two problems the author of Alice worked out in his head, in bed, in the dark — and an introduction saying exactly which thoughts he was keeping out.',
    'progress-and-poverty':
        "Why progress and poverty rise together — and George's famous remedy, the land tax.",
    'purgatorio':
        'The second book of the Comedy, where everyone is going to be saved and knows it — the dead embrace, tease, and ask after old friends. From the Italian, tercet for tercet.',
    'quixote':
        'A gentleman reads too many books of chivalry and rides out to fix the world with a labourer who talks in proverbs. Both volumes, all 126 chapters, from the Spanish.',
    'rhetoric':
        'The art of persuasion, from the Greek: argument, character and emotion — anger, fear, envy, the young and the old — then style, ending on “I have spoken; you have heard; judge.”',
    'roman-lives':
        'The fall of the Republic in five lives — Caesar, Cato, Cicero, Brutus, Antony — five angles on one catastrophe.',
    'seneca':
        'All 124 letters from a Stoic — a daily course in living, from saving time to facing the end.',
    'soap-bubbles':
        'Three Christmas lectures for children on why a bubble is round, why a jet of water breaks into beads, and how to make a fountain sing.',
    'social-contract':
        'The general will, the social contract, and the most famous opening line in political philosophy.',
    'sophocles':
        'All seven surviving plays — Oedipus, Antigone, Ajax, Electra and the rest — from the Greek: the arguments as fast modern prose, the odes as verse, because the chorus was singing.',
    'spinoza':
        'God and Nature are one thing, free will is a name for our ignorance, and forty-eight emotions are defined in order — all set out like a geometry textbook.',
    'subjection':
        'The companion to On Liberty — marriage as the law then stood was bondage, and the real obstacle is that most men cannot yet imagine living with an equal.',
    'sun-tzu':
        'The oldest book on war, with the commentary most editions cut: two thousand years of Chinese generals arguing with Sun Tzu and with each other.',
    'symbolic-logic':
        'The author of Alice teaching logic to children as a board game with red and grey counters — cats that understand French, and a club with no members.',
    'tangled-tale':
        "Ten comic stories with a puzzle hidden in each — then Carroll's gleeful review of the wrong answers his readers sent in.",
    'the-prince':
        'The infamous handbook of power politics.',
    'theophrastus':
        'Thirty ruthless comic sketches of annoying Athenians — every one of them still alive and probably in your contacts.',
    'thompson':
        'Six Christmas lectures on light, given thirteen months after the X-ray was announced. Asked what it is, its discoverer says: I do not know.',
    'true-history':
        'The first science fiction story: a voyage to the moon, war between planets, and a narrator who swears that he lies.',
    'tusculan':
        'Five days on death, pain, grief, and the passions — from the Latin, with the Sword of Damocles.',
    'twenty-thousand-leagues':
        "Captain Nemo's Nautilus carries three captives beneath every sea — the complete novel from Verne's French, not the abridged Victorian version.",
    'two-treatises':
        'The demolition of the divine right of kings, and the case for government by consent.',
    'tyndall':
        'Sound taught with a row of five boys, a shivering glass tube and a flame that ducks at the letter S — then Tyndall discovers the invisible clouds that swallow fog signals on clear days.',
    'utopia':
        "The island where everything works — and the deadpan joke is that you can't tell how much More means it.",
    'way-to-wealth':
        "Poor Richard's proverbs rolled into one sly speech — delivered to a crowd that applauds, then ignores it.",
    'wealth-of-nations':
        'The book that invented economics: pins, markets, and the invisible hand.',
    'wollstonecraft':
        'Not that women are equal, but that nobody knows what women are like, because their character is manufactured by their upbringing. Written in six weeks, and angrier than its reputation.',
}


def esc(s):
    return html.escape(s, quote=True)


def dashes(date):
    """env writes ranges with a hyphen; the page sets an en dash."""
    return re.sub(r"(?<=\d)-(?=\d|c\.)", "–", date)


def first_year(date):
    """(sort key, tab label) from a DATE: first year of a range, with
    "c." and the era kept, and AD shown only below 1000."""
    raw = date.split("; ")[0]
    circa = "c. " if raw.startswith("c. ") else ""
    bc = "BC" in raw
    cent = re.search(r"(\d+)(st|nd|rd|th) century", raw)
    if cent:
        n = int(cent.group(1))
        key = -(n * 100 - 50) if bc else n * 100 - 50
        return key, f"{cent.group(1)}{cent.group(2)} c.{' BC' if bc else ''}"
    year = int(re.search(r"\d+", raw).group())
    era = "BC" if bc else ("AD" if year < 1000 else "")
    return (-year if bc else year), f"{circa}{year} {era}".strip()


def added(page):
    """Tie-break for books with the same first year (the three Dante
    cantiche all begin c. 1308): the order they joined the collection,
    which for a series is the order it is read in."""
    import build_feeds
    return build_feeds.added_date(page) or "9999"


def read_time(bdir):
    words = sum(len(f.read_text().split())
                for f in (bdir / "modern_chapters").glob("*.txt"))
    minutes = words / WORDS_PER_MINUTE
    if minutes < 100:
        m = max(10, round(minutes / 10) * 10)
        return "~1-hour read" if m == 60 else f"~{m}-minute read"
    return f"~{round(minutes / 60)}-hour read"


def collect():
    books, errors = [], []
    for envf in sorted(ROOT.glob("*/env")):
        env = assemble.read_env(envf)
        shelf = env.get("SHELF")
        if not shelf:
            continue
        bdir = envf.parent
        d = bdir.name
        page = env.get("PAGE", d) + ".html"
        thumb = f"covers/thumb/{d}.jpg"
        if shelf not in SHELVES:
            errors.append(f"{d}: SHELF={shelf!r} is not one of SHELVES")
        if d not in BLURBS:
            errors.append(f"{d}: no blurb in build_index.BLURBS")
        if not (SITE / page).exists():
            errors.append(f"{d}: no site/{page}")
        if not (SITE / thumb).exists():
            errors.append(f"{d}: no {thumb} (run build_feeds.py)")
        key, tab = first_year(env["DATE"])
        epub = assemble.find_epub(bdir, ROOT)
        books.append({
            "dir": d, "shelf": shelf, "page": page, "thumb": thumb,
            "title": TITLES.get(d, env["ORIGINAL_WORK"]),
            "author": env["AUTHOR"], "date": dashes(env["DATE"]),
            "key": key, "tab": tab, "read": read_time(bdir),
            "epub": f"ebooks/{epub}" if epub else None,
            "original": (env.get("PAGE", d) + "-original.html")
                        if env.get("ORIGINAL_TEXT") == "yes" else None,
            "original_epub": assemble.find_epub(bdir, ROOT, original=True)
                             if env.get("ORIGINAL_TEXT") == "yes" else None,
            "blurb": BLURBS.get(d, ""),
        })
    shelved = {b["dir"] for b in books}
    errors += [f"{d}: has a blurb but no SHELF= in its env"
               for d in BLURBS if d not in shelved]
    if errors:
        sys.exit("build_index: " + "\n  ".join(["refusing to build"] + errors))
    return books


def card(b):
    meta = [f"{esc(b['author'])} ({esc(b['date'])})", b["read"]]
    if b["epub"]:
        meta.append(f'<a href="{esc(b["epub"])}">epub</a>')
    if b["original"]:
        link = f'<a href="{esc(b["original"])}">original text</a>'
        if b["original_epub"]:
            link += f' (<a href="ebooks/{esc(b["original_epub"])}">epub</a>)'
        meta.append(link)
    return render_card(b["page"], b["thumb"], b["tab"], b["title"],
                       " &middot; ".join(meta), b["blurb"])


# ---- shared by build_restored.py and build_about.py, so the three pages
# ---- are one design and cannot drift apart

def render_card(page, thumb, tab, title, meta_html, blurb):
    """One book: cover plate, year tab, title, meta line (already HTML),
    blurb (plain text)."""
    plate = (f'<a class="plate" href="{page}" tabindex="-1" aria-hidden="true">'
             f'<img src="{thumb}" alt="" width="150" height="225" loading="lazy"></a>')
    return f'''  <li class="card">
    {plate}
    <div class="copy">
      <div class="tab">{esc(tab)}</div>
      <h3><a href="{page}">{esc(title)}</a></h3>
      <p class="author">{meta_html}</p>
      <p class="blurb">{esc(blurb)}</p>
    </div>
  </li>'''


NAV = {
    "index.html": "Retellings",
    "restored.html": "Restored editions",
    "about.html": "About",
}


def nav(current):
    links = [f'<a href="{href}">{label}</a>' for href, label in NAV.items()
             if href != current]
    return (" &middot; ".join(links) + ' &middot; Follow along: <a href="feed.xml">RSS</a>'
            ' &middot; <a href="opds.atom">OPDS catalog</a> for e-readers')


PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>{doc_title}</title>
	<link rel="alternate" type="application/rss+xml" title="Modern Classics" href="feed.xml">
	<link rel="alternate" type="application/atom+xml;profile=opds-catalog;kind=acquisition" title="Modern Classics OPDS catalog" href="opds.atom">
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&family=Yellowtail&family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
	<link rel="stylesheet" href="site.css">
</head>

<body>
<!-- one-ink printing: every cover is set in the page's navy on its paper -->
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <filter id="ink" color-interpolation-filters="sRGB">
    <feColorMatrix type="matrix" values=".33 .5 .17 0 0  .33 .5 .17 0 0  .33 .5 .17 0 0  0 0 0 1 0"/>
    <feComponentTransfer>
      <feFuncR type="table" tableValues="0.106 0.957"/>
      <feFuncG type="table" tableValues="0.192 0.937"/>
      <feFuncB type="table" tableValues="0.302 0.886"/>
    </feComponentTransfer>
  </filter>
</svg>

<header class="masthead">
  <h1>{h1}</h1>
  <p class="motto">{motto}</p>
  <nav>{nav}</nav>
</header>

<main>
{body}
</main>
</body>
</html>
'''


def page_shell(current, doc_title, h1, motto, body):
    return PAGE.format(doc_title=doc_title, h1=h1, motto=motto,
                       nav=nav(current), body=body)


def main():
    books = collect()
    parts = []
    for shelf in SHELVES:
        row = sorted((b for b in books if b["shelf"] == shelf),
                     key=lambda b: (b["key"], added(b["page"])))
        if not row:
            continue
        parts.append(f'<h2>{esc(shelf)}</h2>\n<ul class="deck">')
        parts += [card(b) for b in row]
        parts.append("</ul>\n")
    (SITE / "index.html").write_text(page_shell(
        "index.html", "Modern Classics", "Modern Classics",
        "Classic texts, retold in contemporary English", "\n".join(parts)))
    print(f"wrote site/index.html ({len(books)} books on "
          f"{sum(1 for s in SHELVES if any(b['shelf'] == s for b in books))} shelves)")


if __name__ == "__main__":
    main()
