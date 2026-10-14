"""What a cover says about its edition (Alex, 2026-10-13): one word, top
right. The title page keeps build_print.edition_label's longer wording."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def env_of(book):
    return dict(re.findall(r"^(\w+)=(.*)$", (ROOT / "books" / book / "env").read_text(), re.M))


def label(book, original=False):
    """RETOLD or RESTORED, nothing more (Alex, 2026-10-13). The companion
    edition of the source text is one of the restored editions (RESTORED.md:
    the COMPANION shape), so it reads RESTORED."""
    if original or env_of(book).get("EDITION", "").lower() == "restored":
        return "Restored"
    return "Retold"
