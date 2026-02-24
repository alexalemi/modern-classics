#!/usr/bin/env python3
"""Build the Plato's Dialogues HTML book from modernized chapter files."""

import re
import os

CHAPTERS_DIR = "/home/alemi/projects/modern-classics/dialogues/modern_chapters"
OUTPUT = "/home/alemi/projects/modern-classics/site/dialogues.html"

# Dialogue structure: groups of (file_nums, dialogue_name, subtitle)
# Multi-part dialogues get their parts combined into one section.
DIALOGUES = [
    # Trial & Death of Socrates
    ("trial", "The Trial and Death of Socrates", [
        ([0], "Euthyphro", "On Piety"),
        ([1], "Apology", "Socrates' Defense"),
        ([2], "Crito", "On Duty"),
        ([3, 4], "Phaedo", "On the Soul"),
    ]),
    # Virtue & Knowledge
    ("virtue", "Virtue and Knowledge", [
        ([5], "Meno", "On Virtue"),
        ([6, 7], "Protagoras", "On the Unity of Virtue"),
    ]),
    # Rhetoric, Love & Beauty
    ("rhetoric", "Rhetoric, Love, and Beauty", [
        ([8, 9], "Gorgias", "On Rhetoric"),
        ([10, 11], "Symposium", "On Love"),
        ([12, 13], "Phaedrus", "On Love and Rhetoric"),
    ]),
    # The Republic
    ("republic", "The Republic", [
        ([14], "Book I", "Justice and the Stronger"),
        ([15], "Book II", "The Ring of Gyges"),
        ([16], "Book III", "Education and the Noble Lie"),
        ([17], "Book IV", "The Tripartite Soul"),
        ([18], "Book V", "The Three Waves"),
        ([19], "Book VI", "The Sun and the Divided Line"),
        ([20], "Book VII", "The Allegory of the Cave"),
        ([21], "Book VIII", "The Decline of States"),
        ([22], "Book IX", "The Tyrant's Soul"),
        ([23], "Book X", "Poetry and the Allegory of Er"),
    ]),
    # Early Dialogues
    ("early", "Early Dialogues", [
        ([24], "Ion", "On Poetic Inspiration"),
        ([25], "Laches", "On Courage"),
        ([26], "Lysis", "On Friendship"),
        ([27], "Charmides", "On Temperance"),
    ]),
    # Euthydemus
    ("comic", "Euthydemus", [
        ([28, 29], "Euthydemus", "The Sophists' Comedy"),
    ]),
    # Language and Being
    ("language", "Language and Being", [
        ([30, 31], "Cratylus", "On the Correctness of Names"),
        ([32, 33], "Theaetetus", "On Knowledge"),
        ([34, 35], "Parmenides", "On the Forms"),
        ([36, 37], "Sophist", "On Being and Non-Being"),
        ([38, 39], "Statesman", "On the Art of Rule"),
    ]),
    # The Good Life
    ("good-life", "The Good Life", [
        ([40, 41], "Philebus", "On Pleasure and Wisdom"),
    ]),
    # Cosmology
    ("cosmology", "Cosmology", [
        ([42, 43], "Timaeus", "The Creation of the Universe"),
        ([44], "Critias", "The Legend of Atlantis"),
    ]),
    # The Laws
    ("laws", "The Laws", [
        ([45], "Book I", "The Origin of Law"),
        ([46], "Book II", "Education Through Music and Dance"),
        ([47], "Book III", "The Rise and Fall of States"),
        ([48], "Book IV", "The Founding of Magnesia"),
        ([49], "Book V", "The Ordering of the City"),
        ([50, 51], "Book VI", "Magistrates and Marriage"),
        ([52, 53], "Book VII", "Education from Infancy to Adulthood"),
        ([54], "Book VIII", "Festivals and Military Training"),
        ([55], "Book IX", "Criminal Law"),
        ([56], "Book X", "Theology and Impiety"),
        ([57], "Book XI", "Commercial and Civil Law"),
        ([58], "Book XII", "Final Provisions"),
    ]),
]


def read_chapter(n):
    path = os.path.join(CHAPTERS_DIR, f"{n:03d}.txt")
    with open(path, "r") as f:
        return f.read().strip()


def apply_inline_formatting(text):
    """Apply bold and italic markdown formatting."""
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    return text


def format_paragraph(text):
    """Convert a plain text paragraph to HTML."""
    if text.startswith("> "):
        inner = apply_inline_formatting(text[2:])
        return f'<blockquote><p>{inner}</p></blockquote>'
    text = apply_inline_formatting(text)
    return f'<p>{text}</p>'


def text_to_html(text):
    """Convert plain text with blank-line-separated paragraphs to HTML."""
    lines = text.split("\n")
    html_parts = []
    current_para = []

    def flush():
        if current_para:
            p = " ".join(current_para).strip()
            if p:
                html_parts.append(format_paragraph(p))
            current_para.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            flush()
        else:
            current_para.append(stripped)
    flush()
    return "\n\n".join(html_parts)


def get_chapter_body(file_nums):
    """Read one or more chapter files and combine them, stripping headers."""
    parts = []
    for n in file_nums:
        text = read_chapter(n)
        lines = text.split("\n")

        # Skip initial title/header lines until substantive content
        body_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "":
                continue
            # Skip lines that look like headers
            if re.match(r'^(PART\s+\d+|Part\s+\d+|BOOK\s+[IVXLCDM]+)', stripped, re.IGNORECASE):
                continue
            if re.match(r'^(Euthyphro|Apology|Crito|Phaedo|Meno|Protagoras|Gorgias|Symposium|Phaedrus|Republic|Ion|Laches|Lysis|Charmides|Euthydemus|Cratylus|Theaetetus|Parmenides|Sophist|Statesman|Philebus|Timaeus|Critias|Laws)', stripped):
                continue
            if re.match(r'^(Chapter|Section)\s+', stripped, re.IGNORECASE):
                continue
            if stripped.startswith("---") or stripped.startswith("==="):
                continue
            body_start = i
            break

        parts.append("\n".join(lines[body_start:]).strip())

    return "\n\n".join(parts)


def make_anchor(group_id, dialogue_name):
    """Create an HTML anchor from group and dialogue name."""
    s = re.sub(r'[^a-zA-Z0-9]+', '-', dialogue_name.lower()).strip('-')
    return f"{group_id}-{s}"


# Build HTML
html = []

html.append("""<!DOCTYPE html>
<html>
<head>
\t<meta charset="utf-8">
\t<title>Dialogues &mdash; Plato</title>
<style>
html {
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
}

body {
\tfont: large/1.556 "Libertine", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1,h2,h3,h4,h5,h6 {
  margin: 3em 0 1em;
\tfont-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1 {
  margin-top: 1em;
  text-align: center;
}

h2 {
  text-align: center;
}

p,ul,ol {
  margin-bottom: 2em;
  color: #1d1d1d;
  font-family: sans-serif;
}

blockquote {
  margin: 1.5em 2em;
  padding-left: 1em;
  border-left: 3px solid #ccc;
  font-style: italic;
}

blockquote p {
  margin-bottom: 1em;
}

.center {
  text-align: center;
}

.subtitle {
  text-align: center;
  font-style: italic;
  margin-top: -1em;
  margin-bottom: 3em;
}

.dialogue-subtitle {
  text-align: center;
  font-style: italic;
  font-size: 0.9em;
  color: #666;
  margin-top: -2em;
  margin-bottom: 2em;
  font-family: sans-serif;
}

.toc-group {
  font-weight: bold;
  margin-top: 1.5em;
  margin-bottom: 0.3em;
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

.toc-list {
  list-style: none;
  padding-left: 1.5em;
  margin-top: 0.3em;
}

.toc-list li {
  margin-bottom: 0.3em;
}

.toc-subtitle {
  font-style: italic;
  color: #888;
  font-size: 0.85em;
}

.speaker {
  font-weight: bold;
  font-variant: small-caps;
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}
</style>
</head>

<body>
""")

# Title page
html.append("""\t<center>
\t<h1>Dialogues</h1>
\t<h3>by Plato</h3>
\t<p class="center">
\tTranslated by Benjamin Jowett<br>
\t<s>399&ndash;347 BC</s> 2026
\t</p>
\t</center>

\t<hr>
""")

# Attribution
html.append("""\t<p><i>This is an AI modernization of Plato's Dialogues (from the Benjamin Jowett translation) into contemporary English. The original is available from <a href="https://standardebooks.org/ebooks/plato/dialogues/benjamin-jowett">Standard Ebooks</a>.</i></p>

\t<hr>
""")

# Table of Contents
html.append('<h2 id="contents">Contents</h2>\n')

for group_id, group_title, dialogues in DIALOGUES:
    html.append(f'<p class="toc-group">{group_title}</p>\n')
    html.append('<ul class="toc-list">\n')
    for file_nums, name, subtitle in dialogues:
        anchor = make_anchor(group_id, name)
        html.append(f'<li><a href="#{anchor}">{name}</a> <span class="toc-subtitle">&mdash; {subtitle}</span></li>\n')
    html.append('</ul>\n')

html.append('<hr>\n')

# Each group and its dialogues
for group_id, group_title, dialogues in DIALOGUES:
    html.append(f'\n<h2 id="{group_id}" class="center">{group_title}</h2>\n')

    for file_nums, name, subtitle in dialogues:
        anchor = make_anchor(group_id, name)
        html.append(f'\n<h3 id="{anchor}">{name}</h3>\n')
        html.append(f'<p class="dialogue-subtitle">{subtitle}</p>\n\n')

        body = get_chapter_body(file_nums)
        html.append(text_to_html(body))
        html.append('\n')

    html.append('<hr>\n')

# Footer
html.append("""
<p class="center"><em>F I N I S</em></p>

</body>
</html>
""")

with open(OUTPUT, "w") as f:
    f.write("".join(html))

print(f"Written to {OUTPUT}")
print(f"File size: {os.path.getsize(OUTPUT):,} bytes")
