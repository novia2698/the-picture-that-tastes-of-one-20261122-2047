#!/usr/bin/env python3
"""Entry for make.fun's "The picture that tastes of one ingredient".

The picture itself is entry.png, rendered at build time by
render_strawberry.py (Pillow) and committed next to this file. This program
is stdlib-only on purpose: the grading sandbox has no Pillow, so all it does
is copy the finished picture to the output directory.
"""
import os
import shutil
import sys


def output_dir():
    """Where the grader wants the picture: MAKEFUN_OUTPUT_DIR, else /output."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"


def source_path():
    """entry.png lives beside this file in the repository."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "entry.png")

def main():
    src = source_path()
    if not os.path.isfile(src):
        print("entry.png missing next to main.py", file=sys.stderr)
        return 1
    out = output_dir()
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, "entry.png")
    shutil.copyfile(src, dst)
    size = os.path.getsize(dst)
    print(f"wrote {dst} ({size} bytes)")
    if size > 1_048_576:
        print("entry.png is over the 1 MiB gate", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
