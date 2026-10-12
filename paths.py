"""Where things live in the repo. Every script finds book directories here.

The books moved from the repo root into books/ on 2026-10-12. A book is
still NAMED by its directory name everywhere -- ebook_meta.json "dir", the
epub uid ({REPO}/tree/main/{name}, kept as-is so readers' libraries do not
see 292 new books), build/covers/{name}.jpg, site/covers/{name}.jpg -- and
book_dir() turns that name into the path. It also accepts a path, so
`python3 assemble.py flatland` and `python3 assemble.py books/flatland`
both work, and every `{book}/...` instruction written before the move
still does.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOOKS = ROOT / "books"
SITE = ROOT / "site"


def book_dir(arg):
    """books/<name> for a bare book name; an existing path is returned as is."""
    p = Path(arg)
    if p.exists() and (p / "env").exists():
        return p
    name = p.name if p.name else str(arg).rstrip("/")
    if (BOOKS / name).exists():
        return BOOKS / name
    return p                      # let the caller report the missing book


def all_books():
    """Every book directory (one with an env file), sorted by name."""
    return sorted(p.parent for p in BOOKS.glob("*/env"))
