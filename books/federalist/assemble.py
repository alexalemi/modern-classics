#!/usr/bin/env python3
"""Assemble all 85 modernized Federalist Papers into a single HTML file."""

import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "modern_chapters")
OUTPUT_FILE = os.path.join(BASE_DIR, "federalist.html")

# Thematic sections for the table of contents
SECTIONS = [
    ("PART I: THE CASE FOR THE UNION", 1, 14),
    ("PART II: THE FAILURES OF THE CONFEDERATION", 15, 22),
    ("PART III: THE NEED FOR AN ENERGETIC GOVERNMENT", 23, 36),
    ("PART IV: THE STRUCTURE OF THE NEW GOVERNMENT", 37, 51),
    ("PART V: THE HOUSE OF REPRESENTATIVES", 52, 58),
    ("PART VI: THE SENATE", 59, 66),
    ("PART VII: THE EXECUTIVE", 67, 77),
    ("PART VIII: THE JUDICIARY", 78, 83),
    ("PART IX: GENERAL OBJECTIONS AND CONCLUSION", 84, 85),
]

HTML_HEAD = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>The Federalist Papers — In Modern English</title>
<style>
html {
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
p,ul,ol {
  margin-bottom: 2em;
  color: #1d1d1d;
  font-family: sans-serif;
}
p.footnote {
  font-size: 90%;
  margin-left: 10%;
  margin-right: 10%;
  margin-top: 1em;
  margin-bottom: 1em;
}
p.author {
  font-style: italic;
  color: #555;
  margin-bottom: 0.5em;
}
p.publius {
  text-align: right;
  font-style: italic;
  margin-top: 2em;
}
.toc a {
  text-decoration: none;
  color: #1d1d1d;
}
.toc a:hover {
  text-decoration: underline;
}
.toc li {
  margin-bottom: 0.5em;
}
</style>
</head>
<body>
"""

TITLE_SECTION = """\
<center>
<h1>The Federalist Papers</h1>
<h3>In Modern English</h3>
<h2>by Alexander Hamilton, James Madison, and John Jay</h2>
<p><s>1787-1788</s> 2025</p>
</center>
<hr>
<p><i>This is an AI modernization of The Federalist Papers into contemporary English. The original text is from <a href="https://www.gutenberg.org/ebooks/1404">Project Gutenberg</a>. The translation was done using Claude.</i></p>
<hr>
"""


def extract_modernized_text(filepath):
    """Extract content between <modernized_text> and </modernized_text> tags."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(
        r"<modernized_text>\s*\n(.*?)\n\s*</modernized_text>",
        content,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return ""


def parse_paper(text, paper_num):
    """Parse a paper's text into structured components and return HTML."""
    paragraphs = re.split(r"\n\n+", text)
    html_parts = []

    # The first paragraph should be "FEDERALIST No. X"
    # The second should be the title
    # The third should be the publication info
    # The fourth should be the author
    # The fifth should be the salutation
    # The rest is the body

    paper_title = ""
    author = ""
    anchor_id = f"paper-{paper_num}"

    i = 0
    # Parse FEDERALIST No. line
    if i < len(paragraphs) and paragraphs[i].startswith("FEDERALIST No."):
        heading_text = paragraphs[i].strip()
        i += 1
        # Next line is the title/subtitle
        if i < len(paragraphs):
            paper_title = paragraphs[i].strip()
            i += 1
        # Next line is publication info (date, journal)
        if i < len(paragraphs) and not paragraphs[i].strip().isupper():
            # Publication info line - skip it or include it lightly
            pub_info = paragraphs[i].strip()
            i += 1
        # Next line should be the author
        if i < len(paragraphs):
            candidate = paragraphs[i].strip()
            # Check if this looks like an author line
            if is_author_line(candidate):
                author = candidate
                i += 1

        # Build the heading
        html_parts.append(
            f'<h2 id="{anchor_id}">{heading_text}</h2>'
        )
        html_parts.append(f"<h3>{paper_title}</h3>")
        if author:
            html_parts.append(f'<p class="author">{author}</p>')
    else:
        # Fallback: just make a heading
        html_parts.append(
            f'<h2 id="{anchor_id}">FEDERALIST No. {paper_num}</h2>'
        )

    # Process remaining paragraphs
    for j in range(i, len(paragraphs)):
        para = paragraphs[j].strip()
        if not para:
            continue

        if para == "PUBLIUS":
            html_parts.append('<p class="publius">PUBLIUS</p>')
        elif para.startswith("To the People of the State of New York:"):
            html_parts.append(f"<p><i>{para}</i></p>")
        elif re.match(r"^\[\d+\]", para):
            # Footnote
            html_parts.append(f'<p class="footnote">{para}</p>')
        elif is_author_line(para):
            html_parts.append(f'<p class="author">{para}</p>')
        else:
            html_parts.append(f"<p>{para}</p>")

    return html_parts, paper_title, author


def is_author_line(text):
    """Check if a line looks like an author attribution."""
    text = text.strip()
    # Match lines that are just author names or combinations
    author_patterns = [
        r"^HAMILTON$",
        r"^MADISON$",
        r"^JAY$",
        r"^HAMILTON\s*(and|or|,?\s*with)\s*MADISON$",
        r"^MADISON\s*(and|or|,?\s*with)\s*HAMILTON$",
        r"^HAMILTON\s*(and|or|,?\s*with)\s*JAY$",
        r"^JAY\s*(and|or|,?\s*with)\s*HAMILTON$",
        r"^MADISON\s*(and|or|,?\s*with)\s*JAY$",
        r"^HAMILTON\s+or\s+MADISON$",
        r"^MADISON\s+or\s+HAMILTON$",
    ]
    for pattern in author_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False


def build_toc(papers_info):
    """Build a table of contents organized by thematic sections."""
    toc_parts = ['<div class="toc">', "<h2>Table of Contents</h2>"]

    for section_title, start, end in SECTIONS:
        toc_parts.append(f"<h3>{section_title}</h3>")
        toc_parts.append("<ol>")
        for num in range(start, end + 1):
            info = papers_info.get(num, {})
            title = info.get("title", "")
            author = info.get("author", "")
            anchor = f"paper-{num}"
            author_note = f" ({author})" if author else ""
            toc_parts.append(
                f'  <li value="{num}"><a href="#{anchor}">No. {num}: {title}</a>{author_note}</li>'
            )
        toc_parts.append("</ol>")

    toc_parts.append("</div>")
    toc_parts.append("<hr>")
    return "\n".join(toc_parts)


def main():
    papers_info = {}  # num -> {title, author}
    papers_html = {}  # num -> html string

    for num in range(1, 86):
        filename = f"{num:03d}.txt"
        filepath = os.path.join(CHAPTERS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping.")
            continue

        text = extract_modernized_text(filepath)
        if not text:
            print(f"WARNING: No modernized text found in {filepath}, skipping.")
            continue

        html_parts, title, author = parse_paper(text, num)
        papers_info[num] = {"title": title, "author": author}
        papers_html[num] = "\n".join(html_parts)

    # Build the full HTML
    parts = [HTML_HEAD, TITLE_SECTION]

    # Table of contents
    parts.append(build_toc(papers_info))

    # All papers
    for num in range(1, 86):
        if num in papers_html:
            parts.append(papers_html[num])
            parts.append("<hr>")

    parts.append("</body>\n</html>")

    html = "\n\n".join(parts)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"Written {OUTPUT_FILE}")
    print(f"File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"Papers assembled: {len(papers_html)}")


if __name__ == "__main__":
    main()
