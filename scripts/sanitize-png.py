#!/usr/bin/env python3
"""Copy a reviewed screenshot into run evidence without embedded PNG metadata."""

import argparse
import hashlib
import os
from pathlib import Path

from validate import ROOT, Invalid, png_bytes, validate_png


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="original PNG, kept unchanged")
    parser.add_argument("destination", type=Path, help="new runs/.../evidence/*.png path")
    args = parser.parse_args()

    source = args.source.expanduser()
    if source.is_symlink() or not source.is_file():
        raise SystemExit("Source must be a regular PNG, not a symlink")
    root = (ROOT / "runs").resolve()
    destination = args.destination.expanduser().resolve()
    if destination.suffix.lower() != ".png" or not destination.is_relative_to(root) or destination.parent == root:
        raise SystemExit("Destination must be a new PNG below this repository's runs/ directory")

    try:
        cleaned = png_bytes(source, strip_metadata=True)
    except (Invalid, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        fd = os.open(destination, flags, 0o600)
    except FileExistsError as exc:
        raise SystemExit("Refusing to overwrite an existing screenshot") from exc
    with os.fdopen(fd, "wb") as output:
        output.write(cleaned)
    validate_png(destination)
    print("Sanitized screenshot written; inspect its pixels before publishing.")
    print("Original SHA256:", hashlib.sha256(source.read_bytes()).hexdigest())
    print("Sanitized SHA256:", hashlib.sha256(cleaned).hexdigest())


if __name__ == "__main__":
    main()
