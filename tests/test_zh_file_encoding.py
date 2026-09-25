"""Chinese prompt files carry a UTF-8 BOM, and the launcher strips it.

The `.zh.txt` task files are read by two different things with two different failure modes:

* a human, in whatever editor Windows hands them — and a BOM-less UTF-8 file on a zh-CN machine is
  decoded as codepage 936 (GBK), so `游戏应当已经在运行` renders as `娓告垙搴斿綋宸茬粡鍦ㄨ繍琛`. Nothing
  is corrupt: the bytes are valid UTF-8, the viewer guessed the encoding and guessed wrong. Measured
  on `prompts/tasks/continue-current.zh.txt` (2026-09-26), which lost its BOM to a rewrite that
  wrote plain UTF-8 while the committed version was `EF BB BF`.
* `scripts/run-dsh-headless.ps1`, which reads the file to build the prompt. It reads with
  `[IO.File]::ReadAllText` (BOM detection, UTF-8 fallback) and explicitly trims `U+FEFF`, so a BOM
  is safe there — but only because of that `TrimStart`. The two halves are asserted together so a
  BOM cannot be added for the human and then leak into the prompt as a zero-width character.
"""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
LAUNCHER = ROOT / "scripts" / "run-dsh-headless.ps1"
BOM = b"\xef\xbb\xbf"


def zh_files() -> list[pathlib.Path]:
    return sorted(p for p in PROMPTS.rglob("*") if p.is_file() and ".zh." in p.name)


class TestChinesePromptFiles:
    def test_there_are_chinese_prompt_files_to_check(self):
        assert zh_files(), "no .zh.* prompt file found — the glob, not the files, is wrong"

    def test_every_one_starts_with_a_utf8_bom(self):
        missing = [str(p.relative_to(ROOT)) for p in zh_files() if not p.read_bytes().startswith(BOM)]
        assert not missing, (
            "these files are valid UTF-8 but a zh-CN editor reads them as GBK and shows mojibake; "
            f"they must be written with a BOM: {missing}"
        )

    def test_every_one_decodes_as_utf8_and_holds_chinese(self):
        for path in zh_files():
            raw = path.read_bytes()
            text = raw.decode("utf-8")  # strict: raises if the bytes are not UTF-8
            assert any("\u4e00" <= ch <= "\u9fff" for ch in text), f"{path.name} carries no CJK character"
            assert len(text.strip()) > 100, f"{path.name} is too short to be an instruction file"


class TestTheLauncherToleratesTheBom:
    def test_the_reader_strips_a_leading_bom(self):
        text = LAUNCHER.read_text(encoding="utf-8")
        read = [ln for ln in text.splitlines() if "::ReadAllText($path)" in ln]
        assert read, "the launcher no longer reads the task file with [IO.File]::ReadAllText"
        assert "0xFEFF" in read[0], (
            "the task file is read but its BOM is not trimmed, so U+FEFF would enter the prompt"
        )
