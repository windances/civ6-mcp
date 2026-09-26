"""Repair text that a PowerShell round trip damaged, without guessing.

    python scripts/repair-text.py            # report only; exit 1 when damage remains
    python scripts/repair-text.py --apply    # rewrite the punctuation and the lossless runs

The damage is one transform: a file's UTF-8 bytes were decoded as codepage 936 and written back as
UTF-8. `Get-Content | Set-Content` does it, and `scripts/fix-text-encoding.py --check` (run by the
pre-commit hook) blocks the result. This is the repair, in the two stages that need no judgement:

1. punctuation, by rule: `鈥?`/`鈥`/`閳?`/`閳` -> `—` (U+2014), `鈫?`/`鈫` -> `→` (U+2192);
2. every non-ASCII run whose reverse (`encode gbk -> decode utf-8`) loses no byte and yields only
   plausible characters -> the reversal verbatim. Box-drawing rules (`─`) and most Chinese recover
   exactly this way.

What is left after those two is reported, not invented: a run that lost a byte has to be resolved
from an authoritative source - the game's own `Vanilla_zh_Hans_CN.xml` for a game label, a clean copy
elsewhere in the repository for a quoted instruction. `--apply` never writes a guess.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import text_encoding  # noqa: E402

PUNCT = {
    "\u9225?": "\u2014", "\u9225": "\u2014", "\u95b3?": "\u2014", "\u95b3": "\u2014",
    "\u922b?": "\u2192", "\u922b": "\u2192",
}
EM_DASH = "\u2014"


def reverse(run: str) -> str:
    return run.encode("gbk", "replace").decode("utf-8", "replace")


def gbk_encodable(run: str) -> bool:
    """Can this run be GBK bytes at all? A character outside GBK (`‹`, an emoji, a check mark) is
    text somebody wrote, not damage - `encode(errors="replace")` would turn it into '?' and the
    reversal would look successful while destroying the character."""
    try:
        run.encode("gbk")
    except UnicodeEncodeError:
        return False
    return True


def plausible(text: str) -> bool:
    """A reversal we can trust: no dropped byte, and no character outside a text file's ranges."""
    if "\ufffd" in text:
        return False
    for ch in text:
        o = ord(ch)
        if 0x20 <= o <= 0x7E:
            continue
        if ch == EM_DASH or 0x2500 <= o <= 0x257F or 0x3000 <= o <= 0x303F:
            continue
        if 0x4E00 <= o <= 0x9FFF or 0xFF00 <= o <= 0xFFEF:
            continue
        return False
    return True


def repair_line(line: str) -> str:
    for bad, good in PUNCT.items():
        line = line.replace(bad, good)
    chars = list(line)
    i = 0
    while i < len(chars):
        if ord(chars[i]) <= 0x7F:
            i += 1
            continue
        j = i
        while j < len(chars) and ord(chars[j]) > 0x7F:
            j += 1
        run = "".join(chars[i:j])
        back = reverse(run)
        if gbk_encodable(run) and plausible(back):
            chars[i:j] = list(back)
            i += len(back)
        else:
            i = j
    return "".join(chars)


def esc(text: str) -> str:
    """ASCII-safe, because a zh-CN console cannot print every character that reaches here."""
    return "".join(ch if 32 <= ord(ch) < 127 else f"\\u{ord(ch):04x}" for ch in text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair GBK round-trip damage in this tree.")
    parser.add_argument("root", nargs="?", default=str(ROOT), help="tree to scan (default: the repo)")
    parser.add_argument("--apply", action="store_true", help="write the repairs (never a guess)")
    parser.add_argument("--verbose", action="store_true", help="name every line that would change")
    args = parser.parse_args()

    root = Path(args.root)
    changed = 0
    for path in text_encoding.source_files(root):
        raw = path.read_bytes()
        bom = raw.startswith(text_encoding.BOM)
        try:
            lines = raw.decode("utf-8-sig").splitlines(keepends=True)
        except UnicodeDecodeError:
            continue  # not UTF-8 at all: a different problem, and `--check` reports the BOM side
        new_lines = [repair_line(line) for line in lines]
        # Never touch a line that *documents* the damage: its examples are the point of the line.
        exempt = text_encoding.self_referential(lines)
        for i in exempt:
            new_lines[i] = lines[i]
        if new_lines != lines:
            changed += 1
            if args.verbose:
                for i, (old, new) in enumerate(zip(lines, new_lines), 1):
                    if old != new:
                        print(f"  would change {path.name}:{i}: {esc(old.strip()[:80])}")
                        print(f"                 -> {esc(new.strip()[:80])}")
            if args.apply:
                path.write_bytes((text_encoding.BOM if bom else b"") + "".join(new_lines).encode("utf-8"))
    # What is left is judged by the same rule the gate uses, so the two can never disagree.
    left = text_encoding.corrupt_lines(root)
    for path, number, line in left:
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        print(f"needs a source  {rel}:{number}: {esc(line[:110])}")
    print(f"{changed} file(s) {'repaired' if args.apply else 'repairable'}, {len(left)} line(s) needing a source")
    if left:
        print("resolve those from the game's own text or a clean copy in the repository, then re-run.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
