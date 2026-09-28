"""Kamo no Chōmei, Hōjōki (方丈記, 1212) -> chapters/000.txt.

    python3 hojoki/prep.py

Source: Japanese Wikisource, 方丈記 (國文大觀), from 丸岡桂・松下大三郎 編
『国文大観』9 日記草子部 (板倉屋書房, 明治36 = 1903), NDL pid 991361.
About 9,000 characters, from 行く川 to 方丈記終, including the closing waka.
One file; there are no chapter divisions in the original.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "source/wikisource.txt").read_text()
text = src[src.index("行く川"):src.index("方丈記終")].strip()
text = "\n\n".join(p.strip().replace("　", "") for p in text.split("\n") if p.strip())

(HERE / "chapters").mkdir(exist_ok=True)
(HERE / "chapters/000.txt").write_text(text + "\n")
(HERE / "manifest.json").write_text(json.dumps(
    [{"file": "000.txt", "title": "An Account of My Ten-Foot Hut", "part": 1, "of": 1,
      "chars": len(text)}], indent=2, ensure_ascii=False) + "\n")
print(len(text), "chars")
