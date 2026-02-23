"""Try to split the original text into sections based on the splits file."""

import os
import sys
from pathlib import Path

def split_original(original_text, splits, out_dir):
    text = original_text

    for i, split in enumerate(splits):
        part, *rest = text.split(split)
        text = split + split.join(rest)

        with open(out_dir / f"{i:03d}.txt", 'w') as f:
            f.write(part)

        print(f"Chapter {i} is {len(part)} characters")

    with open(out_dir / f"{len(splits):03d}.txt", 'w') as f:
        f.write(text)
    print(f"Chapter {len(splits)} is {len(text)} characters")



if __name__ == "__main__":
    if len(sys.argv) < 3: 
        print("ERROR: You need to feed in the source text and the splits file.")

    source_text = sys.argv[1]
    splits_file = sys.argv[2]

    out_dir = Path(source_text).parent / "chapters"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(source_text, 'r') as f:
        original_text = f.read()

    with open(splits_file, 'r') as f:
        splits = f.readlines()


    print(f"Splitting {source_text} using the splits file: {splits_file}, output_dir = {out_dir}")
    print(f"Splits = {splits}")

    split_original(original_text, splits, out_dir)

