"""Put the UTF-8 BOM back on the documents that lost it, and keep `AGENTS.md` pure ASCII.

    python scripts/fix-text-encoding.py            # fix, and report what changed
    python scripts/fix-text-encoding.py --check    # report only; exit 1 when something is missing

Run it after editing a document with a tool that writes plain UTF-8: the BOM is what keeps a zh-CN
editor from decoding the file as codepage 936 and showing mojibake. `AGENTS.md` is the exception in the
other direction - human instruction 2026-09-27 made it English only, so it is pure ASCII with no BOM,
and the typographic marks in it (`—`, `→`, `…`) are normalised here while CJK prose is reported for a
rewrite. `tests/test_text_encoding.py` is the same check, so a run of the suite says the same thing.
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

    def shown(path: pathlib.Path) -> str:
        return str(path.relative_to(root) if path.is_relative_to(root) else path)

    if args.check:
        missing = text_encoding.offenders(root)
        for path in missing:
            print(f"missing BOM  {shown(path)}")
        print(f"{len(missing)} document(s) would show as mojibake in a GBK viewer")
        # The BOM is only a display hint: a file can carry one and still hold a decoded-as-GBK round
        # trip's leavings (measured 2026-09-26 in five files, source included). Check that too.
        corrupt = text_encoding.corrupt_lines(root)
        for path, number, line in corrupt:
            print(f"corrupt text  {shown(path)}:{number}: {line[:120]}")
        print(f"{len(corrupt)} line(s) carry GBK round-trip damage")
        # And the English-only bar for the agent reference: a BOM it should not have, then any
        # non-ASCII line that survives the mark table - which is prose somebody has to translate.
        boms = text_encoding.stray_boms(root)
        for path in boms:
            print(f"stray BOM  {shown(path)} (pure ASCII carries none - run without --check)")
        lines = text_encoding.ascii_lines(root)
        for path, number, line in lines:
            print(f"not ASCII  {shown(path)}:{number}: {line.strip()[:110]}")
        print(
            f"{len(boms)} stray BOM(s), {len(lines)} non-ASCII line(s) in "
            + ", ".join(text_encoding.ASCII_ONLY)
        )
        return 1 if (missing or corrupt or boms or lines) else 0

    fixed = text_encoding.fix(root)
    for path in fixed:
        print(f"BOM restored {shown(path)}")
    normalised = text_encoding.ascii_fix(root)
    for path in normalised:
        print(f"ASCII-normalised {shown(path)}")
    print(
        f"{len(fixed)} BOM(s) restored, {len(normalised)} document(s) normalised, "
        f"{len(text_encoding.documents(root))} scanned"
    )
    remaining = text_encoding.ascii_lines(root)
    for path, number, line in remaining[:10]:
        print(f"still not ASCII  {shown(path)}:{number}: {line.strip()[:110]}")
    if remaining:
        print(f"{len(remaining)} line(s) need an English rewrite (the mark table cannot do it)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
