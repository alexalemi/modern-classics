#!/usr/bin/env python3
"""Give every Wealth of Nations file a title line, and write manifest.json.

The book had no manifest.json, so assemble.load_manifest fell back to
"one file, one section, heading = the file's first line". Three things
followed from that, and only the first was visible:

 1. The five Books were translated in separate batches that each chose
    their own heading convention -- "Chapter 1:", "CHAPTER V:", "Chapter
    One:", "Book IV, Chapter VIII --", and a running head reading "The
    Wealth of Nations - Chapter X, Part I: ..." -- so the contents list
    read as five different books.
 2. NINE FILES ARE MECHANICAL MID-ARGUMENT CUTS whose first line is a
    SENTENCE. strip_front drops the first line of every file it is
    given, so those nine opening sentences were being set as contents
    entries instead of as text. They are now the second part of the
    chapter they continue.
 3. TWO SUBHEADINGS WERE DELETED OUTRIGHT. strip_front also skips any
    line matching PART_LINE (^Part [IVXLC0-9]+: \\S) while reading a
    file's front matter, so Smith's "Part I:" and "Part II:" in Book IV
    chapter III were read as part dividers and dropped -- the words "Why
    These Restrictions Are Unreasonable Even on the Mercantile System"
    appeared nowhere on the page. Word form ("Part One:") does not match
    the pattern, and every part number in the book now uses it.

Chapter numbers go to Arabic throughout, which is also what makes
assemble.CHAP_LINE recognise them and set them as chapters within their
Book rather than as top-level sections.
"""
import json
import pathlib
import re

BOOK = pathlib.Path(__file__).resolve().parent
MOD = BOOK / "modern_chapters"

DIVIDERS = {
    "000.txt": "Book One: The Causes of Improvement in the Productive "
               "Powers of Labor",
    "024.txt": "Book Two: On the Nature, Accumulation, and Employment of "
               "Capital",
    "031.txt": "Book Three: How Wealth Grows in Different Societies",
    "035.txt": "Book Four: Systems of Political Economy",
    "054.txt": "Book Five: The Revenue of the Sovereign or Commonwealth",
}

# file -> (title, how many leading non-blank lines the title replaces).
# A count of 2 or 3 is the running head, the stray Roman numeral and the
# descriptive line that three of the five batches printed separately.
TITLES = {
    "000": ("Introduction and Plan of the Work", 2),
    "001": ("Chapter 1: On the Division of Labor", 1),
    "002": ("Chapter 2: On the Principle That Gives Rise to the Division "
            "of Labor", 1),
    "003": ("Chapter 3: The Division of Labor Is Limited by the Size of "
            "the Market", 1),
    "004": ("Chapter 4: On the Origin and Use of Money", 1),
    "005": ("Chapter 5: Of the Real and Nominal Price of Commodities", 2),
    "006": ("Chapter 6: Of the Component Parts of the Price of "
            "Commodities", 2),
    "007": ("Chapter 7: Of the Natural and Market Price of Commodities", 2),
    "008": ("Chapter 8: Of the Wages of Labor", 2),
    "009": ("Chapter 9: Of the Profits of Capital", 2),
    "010": ("Chapter 10, Part One: Wages and Profit in the Different "
            "Employments of Labor and Capital", 3),
    "011": ("Chapter 10, Part Two: Inequalities Caused by the Policy of "
            "Europe", 3),
    "012": ("Chapter 11: Of the Rent of Land", 3),
    "013": ("Chapter 11, Part Two: Products That Sometimes Do and "
            "Sometimes Don't Yield Rent", 3),
    "014": ("Chapter 11, Part Three: Variations in the Relative Value of "
            "the Two Sorts of Produce", 3),
    "015": ("Digression on the Changing Value of Silver Over the Last "
            "Four Centuries", 1),
    "016": ("Second Period", 1),
    "017": ("Third Period", 1),
    "018": ("Variations in the Proportion Between the Values of Gold and "
            "Silver", 1),
    "019": ("Grounds of the Suspicion That Silver's Value Is Still "
            "Declining", 1),
    "021": ("Conclusion of the Digression on Changes in the Value of "
            "Silver", 1),
    "022": ("Effects of Economic Progress on the Real Price of "
            "Manufactured Goods", 1),
    "023": ("Conclusion of the Chapter", 1),
    "024": ("Introduction", 2),
    "025": ("Chapter 1: The Division of Capital", 1),
    "026": ("Chapter 2: Money as a Branch of Society's General Capital, "
            "or the Cost of Maintaining the National Capital", 1),
    "028": ("Chapter 3: The Accumulation of Capital, or Productive and "
            "Unproductive Labor", 1),
    "029": ("Chapter 4: Capital Lent at Interest", 1),
    "030": ("Chapter 5: The Different Uses of Capital", 1),
    "031": ("Chapter 1: The Natural Progress of Wealth", 2),
    "032": ("Chapter 2: How Agriculture Was Held Back in Europe After the "
            "Fall of Rome", 1),
    "033": ("Chapter 3: The Rise of Cities and Towns After the Fall of "
            "Rome", 1),
    "034": ("Chapter 4: How the Commerce of Cities Improved the "
            "Countryside", 1),
    "035": ("Introduction", 2),
    "036": ("Chapter 1: The Principle of the Commercial, or Mercantile, "
            "System", 1),
    "037": ("Chapter 2: Restrictions on Importing Foreign Goods That "
            "Could Be Produced at Home", 1),
    "038": ("Chapter 3: The Extraordinary Restrictions on Imports from "
            "Countries with Which the Balance of Trade Is Unfavorable", 1),
    "039": ("Chapter 3, Part Two: Why These Extraordinary Restrictions "
            "Are Unreasonable on Any Principles", 1),
    "040": ("Chapter 4: Of Drawbacks", 1),
    "041": ("Chapter 5: Of Export Subsidies", 1),
    "042": ("A Digression on the Grain Trade and Grain Laws", 1),
    "043": ("Chapter 6: Of Treaties of Commerce", 1),
    "044": ("Chapter 7: Of Colonies", 1),
    "045": ("Chapter 7, Part Two: Causes of the Prosperity of New "
            "Colonies", 1),
    "047": ("Chapter 7, Part Three: The Advantages Europe Has Derived "
            "from the Discovery of America and of a Passage to the East "
            "Indies", 1),
    "051": ("Chapter 8: Conclusion of the Mercantile System", 3),
    "052": ("Chapter 9: The Agricultural Systems of Political Economy", 3),
    "054": ("Chapter 1, Part One: The Expense of Defense", 3),
    "055": ("Chapter 1, Part Two: The Expense of Justice", 3),
    "056": ("Chapter 1, Part Three: The Expense of Public Works and "
            "Public Institutions", 3),
    "057": ("Chapter 1, Part Three, continued: Public Works and "
            "Institutions for Facilitating Particular Branches of "
            "Commerce", 3),
    "059": ("Article Two: The Cost of Educating Young People", 1),
    "061": ("Article Three: The Cost of Institutions for the Instruction "
            "of People of All Ages", 1),
    "063": ("Chapter 1, Part Four: The Cost of Supporting the Dignity of "
            "the Head of State", 1),
    "064": ("Chapter 2: The Sources of the General or Public Revenue of "
            "Society", 1),
    "066": ("Article Two: Taxes on Profit, or on the Income from "
            "Capital", 1),
    "067": ("Appendix to Articles One and Two: Taxes on the Capital Value "
            "of Land, Houses, and Capital", 1),
    "068": ("Article Three: Taxes on the Wages of Labor", 1),
    "069": ("Article Four: Taxes Intended to Fall on Every Kind of "
            "Income", 1),
    "071": ("Chapter 3: Of Public Debts", 1),
}

# continuation file -> the file it continues. Every one of these opens on
# a sentence in the SOURCE as well, which is what identifies them: the
# splitter cut a long chapter and there is no heading to be had.
CONTINUES = {"020": "019", "027": "026", "046": "045", "048": "047",
             "049": "047", "050": "047", "053": "052", "058": "057",
             "060": "059", "062": "061", "065": "064", "070": "069",
             "072": "071"}

# A "Part <Roman>:" line anywhere in a file's front matter is eaten by
# strip_front. Rewritten in word form wherever it appears as a
# subheading, which is also how the titles above are written.
WORD = {"I": "One", "II": "Two", "III": "Three", "IV": "Four"}
SUBPART = re.compile(r"^(?:PART|Part) ([IV]+)(:|\b)")


def main():
    names = sorted(p.stem for p in MOD.glob("*.txt")
                   if re.fullmatch(r"\d{3}\.txt", p.name))
    assert set(names) == set(TITLES) | set(CONTINUES), "file set changed"

    # part numbers, from the continuation map
    parts = {}
    for child, parent in sorted(CONTINUES.items()):
        kids = sorted(c for c, p in CONTINUES.items() if p == parent)
        parts[parent] = (1, len(kids) + 1)
        parts[child] = (kids.index(child) + 2, len(kids) + 1)

    manifest = []
    for n in names:
        path = MOD / f"{n}.txt"
        lines = path.read_text().split("\n")
        if n in CONTINUES:
            title = TITLES[CONTINUES[n]][0]
            eat = 0
        else:
            title, eat = TITLES[n]
        idx = [i for i, l in enumerate(lines) if l.strip()][:eat]
        keep = [l for i, l in enumerate(lines) if i not in idx]
        keep = [SUBPART.sub(lambda m: f"Part {WORD[m.group(1)]}{m.group(2)}",
                            l) if l.strip().lower().startswith("part ")
                else l for l in keep]
        head = [title]
        part, of = parts.get(n, (1, 1))
        if of > 1:
            head.append(f"(Part {part} of {of})")
        path.write_text("\n".join(head + [""] + keep).lstrip("\n"))

        entry = {"file": f"{n}.txt", "title": title, "part": part, "of": of,
                 "words": len(path.read_text().split())}
        if f"{n}.txt" in DIVIDERS:
            entry["part_before"] = DIVIDERS[f"{n}.txt"]
        manifest.append(entry)

    (BOOK / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    chapters = sum(1 for m in manifest if m["part"] == 1)
    print(f"{len(manifest)} files, {chapters} sections, "
          f"{sum(m['words'] for m in manifest):,} words")


if __name__ == "__main__":
    main()
