"""Convert Standard Ebooks XHTML chapter files to plain text chapter files."""

import re
from pathlib import Path
from html.parser import HTMLParser


class XHTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        self.in_blockquote = False
        self.in_header = False
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag in ('head', 'title'):
            self.skip = True
        elif tag in ('h2', 'h3', 'h4'):
            self.in_header = True
        elif tag == 'blockquote':
            self.in_blockquote = True
        elif tag == 'p' and not self.skip:
            pass  # Will add newlines after
        elif tag == 'br':
            self.text.append('\n')
        elif tag == 'hr':
            self.text.append('\n* * *\n')

    def handle_endtag(self, tag):
        if tag in ('head', 'title'):
            self.skip = False
        elif tag in ('h2', 'h3', 'h4'):
            self.in_header = False
            self.text.append('\n\n')
        elif tag == 'blockquote':
            self.in_blockquote = False
        elif tag == 'p' and not self.skip:
            self.text.append('\n\n')

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)

    def get_text(self):
        text = ''.join(self.text)
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove the zero-width space character that Standard Ebooks uses
        text = text.replace('\u2060', '')
        return text.strip()


def convert_xhtml_to_text(xhtml_path):
    content = xhtml_path.read_text(encoding='utf-8')
    parser = XHTMLToText()
    parser.feed(content)
    return parser.get_text()


# Ordered list of (filename, book_label) tuples
CHAPTERS = [
    ("preface.xhtml", "Preface to the Fourth Edition"),
    ("the-problem.xhtml", "Introductory: The Problem"),
    # Book I: Wages and Capital
    ("chapter-1-1.xhtml", "Book I, Chapter 1: The Current Doctrine of Wages — Its Insufficiency"),
    ("chapter-1-2.xhtml", "Book I, Chapter 2: The Meaning of the Terms"),
    ("chapter-1-3.xhtml", "Book I, Chapter 3: Wages Not Drawn from Capital, but Produced by the Labor"),
    ("chapter-1-4.xhtml", "Book I, Chapter 4: The Maintenance of Laborers Not Drawn from Capital"),
    ("chapter-1-5.xhtml", "Book I, Chapter 5: The Real Functions of Capital"),
    # Book II: Population and Subsistence
    ("chapter-2-1.xhtml", "Book II, Chapter 1: The Malthusian Theory, Its Genesis and Support"),
    ("chapter-2-2.xhtml", "Book II, Chapter 2: Inferences from Facts"),
    ("chapter-2-3.xhtml", "Book II, Chapter 3: Inferences from Analogy"),
    ("chapter-2-4.xhtml", "Book II, Chapter 4: Disproof of the Malthusian Theory"),
    # Book III: The Laws of Distribution
    ("chapter-3-1.xhtml", "Book III, Chapter 1: The Inquiry Narrowed to the Laws of Distribution"),
    ("chapter-3-2.xhtml", "Book III, Chapter 2: Rent and the Law of Rent"),
    ("chapter-3-3.xhtml", "Book III, Chapter 3: Of Interest and the Cause of Interest"),
    ("chapter-3-4.xhtml", "Book III, Chapter 4: Of Spurious Capital and of Profits Often Mistaken for Interest"),
    ("chapter-3-5.xhtml", "Book III, Chapter 5: The Law of Interest"),
    ("chapter-3-6.xhtml", "Book III, Chapter 6: Wages and the Law of Wages"),
    ("chapter-3-7.xhtml", "Book III, Chapter 7: The Correlation and Coordination of These Laws"),
    ("chapter-3-8.xhtml", "Book III, Chapter 8: The Statics of the Problem Thus Explained"),
    # Book IV: Effect of Material Progress Upon the Distribution of Wealth
    ("chapter-4-1.xhtml", "Book IV, Chapter 1: The Dynamics of the Problem Yet to Seek"),
    ("chapter-4-2.xhtml", "Book IV, Chapter 2: The Effect of Increase of Population Upon the Distribution of Wealth"),
    ("chapter-4-3.xhtml", "Book IV, Chapter 3: The Effect of Improvements in the Arts Upon the Distribution of Wealth"),
    ("chapter-4-4.xhtml", "Book IV, Chapter 4: Effect of the Expectation Raised by Material Progress"),
    # Book V: The Problem Solved
    ("chapter-5-1.xhtml", "Book V, Chapter 1: The Primary Cause of Recurring Paroxysms of Industrial Depression"),
    ("chapter-5-2.xhtml", "Book V, Chapter 2: The Persistence of Poverty Amid Advancing Wealth"),
    # Book VI: The Remedy
    ("chapter-6-1.xhtml", "Book VI, Chapter 1: Insufficiency of Remedies Currently Advocated"),
    ("chapter-6-2.xhtml", "Book VI, Chapter 2: The True Remedy"),
    # Book VII: Justice of the Remedy
    ("chapter-7-1.xhtml", "Book VII, Chapter 1: The Injustice of Private Property in Land"),
    ("chapter-7-2.xhtml", "Book VII, Chapter 2: The Enslavement of Laborers the Ultimate Result of Private Property in Land"),
    ("chapter-7-3.xhtml", "Book VII, Chapter 3: Claim of Land Owners to Compensation"),
    ("chapter-7-4.xhtml", "Book VII, Chapter 4: Private Property in Land Historically Considered"),
    ("chapter-7-5.xhtml", "Book VII, Chapter 5: Of Property in Land in the United States"),
    # Book VIII: Application of the Remedy
    ("chapter-8-1.xhtml", "Book VIII, Chapter 1: Private Property in Land Inconsistent with the Best Use of Land"),
    ("chapter-8-2.xhtml", "Book VIII, Chapter 2: How Equal Rights to the Land May Be Asserted and Secured"),
    ("chapter-8-3.xhtml", "Book VIII, Chapter 3: The Proposition Tried by the Canons of Taxation"),
    ("chapter-8-4.xhtml", "Book VIII, Chapter 4: Endorsements and Objections"),
    # Book IX: Effects of the Remedy
    ("chapter-9-1.xhtml", "Book IX, Chapter 1: Of the Effect Upon the Production of Wealth"),
    ("chapter-9-2.xhtml", "Book IX, Chapter 2: Of the Effect Upon Distribution and Thence Upon Production"),
    ("chapter-9-3.xhtml", "Book IX, Chapter 3: Of the Effect Upon Individuals and Classes"),
    ("chapter-9-4.xhtml", "Book IX, Chapter 4: Of the Changes That Would Be Wrought in Social Organization and Social Life"),
    # Book X: The Law of Human Progress
    ("chapter-10-1.xhtml", "Book X, Chapter 1: The Current Theory of Human Progress — Its Insufficiency"),
    ("chapter-10-2.xhtml", "Book X, Chapter 2: Differences in Civilization — To What Due"),
    ("chapter-10-3.xhtml", "Book X, Chapter 3: The Law of Human Progress"),
    ("chapter-10-4.xhtml", "Book X, Chapter 4: How Modern Civilization May Decline"),
    ("chapter-10-5.xhtml", "Book X, Chapter 5: The Central Truth"),
    # Conclusion
    ("the-problem-of-individual-life.xhtml", "Conclusion: The Problem of Individual Life"),
]

def main():
    raw_dir = Path("raw_xhtml")
    chapters_dir = Path("chapters")
    chapters_dir.mkdir(exist_ok=True)

    manifest = []

    for i, (filename, label) in enumerate(CHAPTERS):
        xhtml_path = raw_dir / filename
        if not xhtml_path.exists():
            print(f"WARNING: {filename} not found, skipping")
            continue

        text = convert_xhtml_to_text(xhtml_path)
        out_name = f"{i:03d}.txt"
        out_path = chapters_dir / out_name

        # Prepend label as header
        full_text = f"{label}\n{'=' * len(label)}\n\n{text}"
        out_path.write_text(full_text, encoding='utf-8')

        lines = len(full_text.splitlines())
        words = len(full_text.split())
        manifest.append(f"{out_name}: {label} ({words} words, {lines} lines)")
        print(f"  {out_name}: {label} ({words:,} words)")

    # Write manifest
    Path("chapter_manifest.txt").write_text('\n'.join(manifest) + '\n', encoding='utf-8')
    print(f"\nTotal: {len(manifest)} chapters")


if __name__ == "__main__":
    main()
