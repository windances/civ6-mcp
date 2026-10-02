"""Audit every `.md` document in the corpus against the language rules, and say what it is.

    .venv\\Scripts\\python.exe .tools\\audit-md-language.py                  # every document
    .venv\\Scripts\\python.exe .tools\\audit-md-language.py --changed       # what changed vs HEAD
    .venv\\Scripts\\python.exe .tools\\audit-md-language.py --changed origin/main

The rules, from `AGENTS.md` and `civ_mcp/text_encoding.py`:

* a document DSH serves the model - `AGENTS.md`, `SKILL.md` (the skill), and each preset's
  `directive.md`, which `scripts/use-strategy.ps1` copies into that skill - is **pure ASCII with no
  BOM**, and has a Chinese backup `<name>.cn.md` beside it that holds Chinese and carries a BOM;
* every other document that holds a non-ASCII byte **carries a BOM** (a zh-CN editor would otherwise
  show mojibake - the damage is invisible until somebody opens the file);
* **documents written to be read side by side are the deliberate exception** to the English-only bar
  (human instruction 2026-09-30, 用于中英对照的文档除外): the per-decision playbooks under
  `prompts/tactics/` (bilingual H1 plus the human's instructions quoted verbatim in Chinese) and the
  `.zh.`/`.en.` prompt pairs. They are correct as they are - and they still carry a BOM.

This is the instrument for "are the documents compliant", so it reports the three roles separately
rather than a single pass/fail: a document that is bilingual on purpose and a document that leaked a
half-finished translation look identical to a byte counter, and only one of them is a defect. The
gates that run on every commit are `scripts/fix-text-encoding.py --check`,
`tests/test_text_encoding.py` and `tests/test_dsh_documents.py`; this is the human-facing read.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from civ_mcp import text_encoding  # noqa: E402

# Documents read side by side by design: a directory of playbooks, and the two-file prompt pairs.
BILINGUAL_DIRS = ("prompts/tactics/",)
BILINGUAL_SUFFIXES = (".zh.md", ".en.md", ".zh.txt", ".en.txt")


def cjk(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def prose_coverage(path: pathlib.Path) -> float:
    """The share of a backup's prose lines that carry Chinese.

    The structural checks - banner, BOM, sections, inline spans, a CJK floor - can all pass while a
    chunk of prose is still English, which is the failure a reader notices and no test does. This is
    the measurement for it: of the non-blank lines outside fenced blocks, the share that hold at
    least one CJK character. Table separator rows (`|---|---|`) and a YAML title are counted as
    English, so the honest reading of the number is "at least this much of it is translated".
    """
    inside = False
    prose = 0
    translated = 0
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if inside or not line.strip():
            continue
        prose += 1
        if cjk(line):
            translated += 1
    return translated / prose if prose else 1.0


def role(rel: str) -> str:
    name = pathlib.Path(rel).name
    if name in text_encoding.ASCII_ONLY:
        return "served (English only)"
    if name in text_encoding.ASCII_ONLY_DELIVERED:
        # English, but not a document anybody reads in translation: the rule file's `message:` lines
        # are printed to the orchestrator when a rule fails, and the advisor briefs are pasted into a
        # proposal prompt. Same bar, no backup.
        return "delivered (English only)"
    if name.endswith(".cn.md"):
        return "backup (Chinese)"
    if rel.startswith(BILINGUAL_DIRS) or name.endswith(BILINGUAL_SUFFIXES):
        return "bilingual by design"
    return "other"


def changed_documents(since: str) -> list[pathlib.Path]:
    listing = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", since],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return [
        ROOT / line.strip()
        for line in listing
        if line.strip().endswith(".md") and (ROOT / line.strip()).is_file()
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--changed", nargs="?", const="HEAD", metavar="REV",
        help="only .md files changed since REV (default HEAD)",
    )
    args = ap.parse_args()

    files = changed_documents(args.changed) if args.changed else text_encoding.documents(ROOT)
    if not files:
        print("no documents to check")
        return 0

    problems: list[str] = []
    width = max(len(str(p.relative_to(ROOT)).replace("\\", "/")) for p in files)
    for path in sorted(files):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig", errors="replace")
        has_bom = raw.startswith(text_encoding.BOM)
        non_ascii = [n for n, line in enumerate(text.splitlines(), 1) if not line.isascii()]
        print(
            f"{rel:<{width}}  {role(rel):<22}"
            f"{cjk(text):>6} CJK  {'BOM' if has_bom else '   '}  {len(non_ascii):>4} non-ASCII line(s)"
        )
        if role(rel) == "served (English only)":
            if has_bom:
                problems.append(f"{rel}: a served document must carry no BOM")
            if non_ascii:
                problems.append(
                    f"{rel}: a served document must be pure ASCII"
                    f" ({len(non_ascii)} line(s), first at {non_ascii[0]})"
                )
            backup = path.with_name(path.name[: -len(".md")] + ".cn.md")
            if not backup.is_file():
                problems.append(f"{rel}: no Chinese backup beside it")
            elif not backup.read_bytes().startswith(text_encoding.BOM):
                problems.append(f"{backup.relative_to(ROOT)}: the backup holds Chinese and has no BOM")
        elif role(rel) == "delivered (English only)":
            # The bar without the backup: these reach a model, so Chinese here is a defect, but
            # nobody reads them in translation and a `.cn.md` beside them would be a second file to
            # keep in step for no reader.
            if has_bom:
                problems.append(f"{rel}: a delivered document must carry no BOM")
            if non_ascii:
                problems.append(
                    f"{rel}: a delivered document must be pure ASCII"
                    f" ({len(non_ascii)} line(s), first at {non_ascii[0]})"
                )
        elif role(rel) == "backup (Chinese)":
            coverage = prose_coverage(path)
            print(f"{'':<{width}}  {'':<22}         prose in Chinese: {coverage:6.1%}")
            if not has_bom:
                problems.append(f"{rel}: the backup holds Chinese and has no BOM")
            if cjk(text) == 0:
                problems.append(f"{rel}: the backup holds no Chinese - a stub, not a translation")
            if coverage < 0.6:
                problems.append(
                    f"{rel}: only {coverage:.0%} of its prose lines carry Chinese - check for a "
                    "paragraph left in English"
                )
        elif non_ascii and not has_bom:
            problems.append(f"{rel}: holds non-ASCII and has no BOM")

    print()
    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"clean: {len(files)} document(s) checked, no problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
