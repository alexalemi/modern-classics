"""Assemble modern_chapters/*.txt into site/leviathan.html."""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent / "site" / "leviathan.html"

PART_HEADINGS = {
    1: "Part I: Of Man",
    17: "Part II: Of Commonwealth",
    32: "Part III: Of a Christian Commonwealth",
    44: "Part IV: Of the Kingdom of Darkness",
}
PART_LINE = re.compile(r"^Part (I|II|III|IV): ", re.I)
PART_MARK = re.compile(r"^\(Part \d+ of \d+\)$")
CHAP_LINE = re.compile(r"^Chapter (\d+): (.*)$")


def is_subheading(par: str) -> bool:
    if "\n" in par or len(par) > 90:
        return False
    if par[-1] in ".;:,—":
        return False
    words = par.split()
    # title-case-ish: most significant words capitalized
    caps = sum(1 for w in words if w[0].isupper())
    return caps >= max(1, len(words) // 2)


def render_body(text: str) -> str:
    out = []
    for par in re.split(r"\n\s*\n", text):
        par = par.rstrip()
        if not par.strip():
            continue
        if re.search(r"^[ \t]", par, re.M):  # indented outline (ch. 9)
            out.append(f'<pre class="outline">{html.escape(par)}</pre>')
        elif is_subheading(par.strip()):
            out.append(f"<h4>{html.escape(par.strip())}</h4>")
        else:
            out.append(f"<p>{html.escape(par.strip())}</p>")
    return "\n".join(out)


manifest = json.loads((HERE / "manifest.json").read_text())

# Group consecutive files belonging to the same chapter
groups = []
for m in manifest:
    if m["part"] == 1:
        groups.append({"files": [], "src_title": m["title"]})
    groups[-1]["files"].append(m["file"])

sections = []  # {id, toc_label, heading, body, part_before}
for g in groups:
    raw_parts = []
    for i, fn in enumerate(g["files"]):
        lines = (HERE / "modern_chapters" / fn).read_text().split("\n")
        # strip leading part dividers, chapter heading, and part markers
        j = 0
        while j < len(lines):
            s = lines[j].strip()
            if not s or PART_LINE.match(s) or PART_MARK.match(s):
                j += 1
            elif (CHAP_LINE.match(s) or s in ("The Epistle Dedicatory",
                                              "A Review and Conclusion")):
                heading = s
                j += 1
            else:
                break
        raw_parts.append("\n".join(lines[j:]).strip())
        if i == 0:
            first_heading = heading if 'heading' in dir() else lines[0].strip()
    body = "\n\n".join(raw_parts)

    if g["src_title"] == "THE INTRODUCTION":
        # file 000 holds the Epistle Dedicatory and the Introduction
        ded, intro = re.split(r"\n\s*Introduction\s*\n", body, maxsplit=1)
        sections.append({"id": "epistle", "toc": "The Epistle Dedicatory",
                         "heading": "The Epistle Dedicatory",
                         "body": ded, "part_before": None})
        sections.append({"id": "introduction", "toc": "Introduction",
                         "heading": "Introduction",
                         "body": intro, "part_before": None})
        continue

    first_line = next(l.strip() for l in
                      (HERE / "modern_chapters" / g["files"][0])
                      .read_text().split("\n")
                      if l.strip() and not PART_LINE.match(l.strip()))
    m = CHAP_LINE.match(first_line)
    if m:
        num = int(m.group(1))
        sections.append({"id": f"ch-{num}", "toc": first_line,
                         "heading": first_line, "body": body,
                         "part_before": PART_HEADINGS.get(num)})
    else:
        sections.append({"id": "review", "toc": "A Review and Conclusion",
                         "heading": "A Review and Conclusion",
                         "body": body, "part_before": None})

# Build TOC
toc = []
toc.append('<p><a href="#epistle">The Epistle Dedicatory</a></p>')
toc.append('<p><a href="#introduction">Introduction</a></p>')
open_list = False
for s in sections:
    if s["id"] in ("epistle", "introduction"):
        continue
    if s["part_before"]:
        if open_list:
            toc.append("</ul>")
        toc.append(f'<p class="toc-book">{s["part_before"]}</p>')
        toc.append('<ul class="toc-list">')
        open_list = True
    if s["id"] == "review":
        if open_list:
            toc.append("</ul>")
            open_list = False
        toc.append('<p><a href="#review">A Review and Conclusion</a></p>')
    else:
        toc.append(f'<li><a href="#{s["id"]}">{html.escape(s["heading"])}</a></li>')
if open_list:
    toc.append("</ul>")

# Build body
chapters_html = []
for s in sections:
    if s["part_before"]:
        pid = "part-" + s["part_before"].split(":")[0].split()[-1].lower()
        chapters_html.append(f'<h2 id="{pid}" class="center">{s["part_before"]}</h2>')
    tag = "h2" if s["id"] in ("epistle", "introduction", "review") else "h3"
    chapters_html.append(f'<{tag} id="{s["id"]}">{html.escape(s["heading"])}</{tag}>')
    chapters_html.append(render_body(s["body"]))

STYLE = """html {
  max-width: 70ch;
  padding: 3em 1em;
  margin: auto;
  line-height: 1.75;
  font-size: 1.25em;
}

body {
	font: large/1.556 "Libertine", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1,h2,h3,h4,h5,h6 {
  margin: 3em 0 1em;
	font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

h1 {
  margin-top: 1em;
  text-align: center;
}

h4 {
  margin: 2em 0 1em;
  font-style: italic;
  font-weight: 600;
}

p,ul,ol {
  margin-bottom: 2em;
  color: #1d1d1d;
  font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif;
}

pre.outline {
  font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif;
  white-space: pre-wrap;
  line-height: 1.6;
  margin-bottom: 2em;
  color: #1d1d1d;
}

.center {
  text-align: center;
}

.toc-book {
  font-weight: bold;
  margin-top: 1em;
  font-family: "Essays 1743", Palatino, "Palatino Linotype", "Book Antiqua", Georgia, "Times New Roman", serif;
}

.toc-list {
  list-style: none;
  padding-left: 1.5em;
}

.toc-list li {
  margin-bottom: 0.3em;
}"""

page = f"""<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<title>Leviathan &mdash; Thomas Hobbes</title>
<style>
{STYLE}
</style>
</head>

<body>
	<center>
	<h1>Leviathan</h1>
	<h3>or, The Matter, Form, and Power of a Commonwealth, Ecclesiastical and Civil</h3>
	<h3>by Thomas Hobbes</h3>
	<p class="center">
	<s>1651</s> 2026
	</p>
	</center>

	<hr>
	<p><i>This is an AI modernization of Leviathan into contemporary English. The original is available from <a href="https://www.gutenberg.org/ebooks/3207">Project Gutenberg</a>.</i></p>

	<hr>
<h2 id="contents">Contents</h2>
{chr(10).join(toc)}

<hr>
{chr(10).join(chapters_html)}

</body>
</html>
"""

OUT.write_text(page)
print(f"wrote {OUT} ({len(page)} bytes, {len(sections)} sections)")
