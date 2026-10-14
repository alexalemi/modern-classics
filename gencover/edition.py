"""What a cover says about its edition (Alex, 2026-10-13). The wording is
build_print.edition_label's, so the cover, the title page and the print
cover agree."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def env_of(book):
    return dict(re.findall(r"^(\w+)=(.*)$", (ROOT / "books" / book / "env").read_text(), re.M))


def label(book, original=False):
    if original:
        return "The original text"
    if env_of(book).get("EDITION", "").lower() == "restored":
        return "Restored edition"
    return "Retold in contemporary English"
