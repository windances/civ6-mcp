"""Put the UTF-8 BOM back on the documents that lost it.

    python scripts/fix-text-encoding.py            # fix, and report what changed
    python scripts/fix-text-encoding.py --check    # report only; exit 1 when something is missing

Run it after editing `AGENTS.md`, a tactics file or a temporary task file with a tool that writes
plain UTF-8: the BOM is what keeps a zh-CN editor from decoding the file as codepage 936 and showing
mojibake. `tests/test_text_encoding.py` is the same check, so a run of the suite says the same thing.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import text_encoding  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore UTF-8 BOMs on non-ASCII documents.")
    parser.add_argument("root", nargs="?", default=str(ROOT), help="tree to scan (default: the repo)")
    parser.add_argument("--check", action="store_true", help="report only; exit 1 if any is missing")
    args = parser.parse_args()

    root = pathlib.Path(args.root)
    if args.check:
        missing = text_encoding.offenders(root)
        for path in missing:
            print(f"missing BOM  {path.relative_to(root) if path.is_relative_to(root) else path}")
        print(f"{len(missing)} document(s) would show as mojibake in a GBK viewer")
        return 1 if missing else 0

    fixed = text_encoding.fix(root)
    for path in fixed:
        print(f"BOM restored {path.relative_to(root) if path.is_relative_to(root) else path}")
    print(f"{len(fixed)} document(s) fixed, {len(text_encoding.documents(root))} scanned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
