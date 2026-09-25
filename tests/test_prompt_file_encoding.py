"""Language-variant prompt files are unambiguous in a zh-CN viewer.

`prompts/**/*.zh.*` and `prompts/**/*.en.*` are read by two things with two different failure modes:
a human in whatever editor Windows hands them, and `scripts/run-dsh-headless.ps1`, which builds the
prompt out of the file. On a zh-CN machine an editor that cannot see a BOM falls back to codepage 936
(GBK), so valid UTF-8 renders as mojibake. Both halves of the problem have been measured here
(2026-09-26):

* `prompts/tasks/continue-current.zh.txt` lost its BOM to a rewrite and rendered as
  `娓告垙搴斿綋宸茬粡鍦ㄨ繍琛` — the bytes were never wrong.
* `prompts/tasks/continue-current.en.txt` gained twelve em dashes (`U+2014`) and rendered them as
  GBK garbage; the three sibling `.en.txt` files are pure ASCII and were never affected.

So the rule per family is the cheap one: a Chinese file carries a BOM (and is otherwise UTF-8), and
an English file is **pure ASCII** and needs no encoding hint at all. The launcher half is asserted
too: it reads with `[IO.File]::ReadAllText` (BOM detection, UTF-8 fallback) and trims `U+FEFF`, so a
BOM is safe there — but only because of that `TrimStart`, and it must not be dropped.
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
LAUNCHER = ROOT / "scripts" / "run-dsh-headless.ps1"
BOM = b"\xef\xbb\xbf"


def variants(infix: str) -> list[pathlib.Path]:
    return sorted(p for p in PROMPTS.rglob("*") if p.is_file() and infix in p.name)


class TestChinesePromptFiles:
    def test_there_are_chinese_files_to_check(self):
        assert variants(".zh."), "no .zh.* prompt file found - the glob, not the files, is wrong"

    def test_every_one_starts_with_a_utf8_bom(self):
        missing = [str(p.relative_to(ROOT)) for p in variants(".zh.") if not p.read_bytes().startswith(BOM)]
        assert not missing, (
            "valid UTF-8, but a zh-CN editor reads these as GBK and shows mojibake; they must be "
            f"written with a BOM: {missing}"
        )

    def test_every_one_decodes_as_utf8_and_holds_chinese(self):
        for path in variants(".zh."):
            text = path.read_bytes().decode("utf-8")  # strict: raises if the bytes are not UTF-8
            assert any("\u4e00" <= ch <= "\u9fff" for ch in text), f"{path.name} carries no CJK character"
            assert len(text.strip()) > 100, f"{path.name} is too short to be an instruction file"


class TestEnglishPromptFiles:
    def test_there_are_english_files_to_check(self):
        assert variants(".en."), "no .en.* prompt file found - the glob, not the files, is wrong"

    def test_every_one_is_pure_ascii(self):
        # ASCII is the only encoding a viewer cannot guess wrong, and it is what the other English
        # task files already are: a `.en.` file that needs a BOM is a file that should not have one.
        for path in variants(".en."):
            text = path.read_bytes().decode("ascii", errors="replace")
            offenders = sorted({ch for ch in text if ord(ch) > 127})
            assert not offenders, (
                f"{path.relative_to(ROOT)} is not ASCII: a BOM-less non-ASCII byte is shown as GBK "
                f"mojibake on a zh-CN machine - found {offenders} "
                f"(U+{', U+'.join(f'{ord(c):04X}' for c in offenders)})"
            )


class TestTheLauncherToleratesTheBom:
    def test_the_reader_strips_a_leading_bom(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        read = [ln for ln in text.splitlines() if "::ReadAllText($path)" in ln]
        assert read, "the launcher no longer reads the task file with [IO.File]::ReadAllText"
        assert "0xFEFF" in read[0], (
            "the task file is read but its BOM is not trimmed, so U+FEFF would enter the prompt"
        )
