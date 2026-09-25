"""Every document a human opens is unambiguous in a zh-CN viewer.

A BOM-less UTF-8 file on a Chinese Windows machine is decoded as codepage 936 (GBK) by any editor
that cannot detect the encoding, so `游戏应当已经在运行` renders as `娓告垙搴斿綋宸茬粡鍦ㄨ繍琛` — the
bytes are valid UTF-8 and nothing is corrupt, the viewer guessed and guessed wrong. Measured on this
repo on 2026-09-26: a Chinese task file, an English one (twelve em dashes), `AGENTS.md`, and the
tactics/strategy documents.

The policy is one line per family, and it is cheap to keep:

* a `.zh.` file carries a UTF-8 BOM;
* a `.en.` file is **pure ASCII** (the one encoding no viewer can guess wrong) and carries none;
* any other document containing a non-ASCII byte carries a BOM;
* the launcher strips the BOM before building the prompt, and must keep doing so.

`civ_mcp.text_encoding` is the single source of truth for the document walk, and
`scripts/fix-text-encoding.py` is the one command that repairs an offender — the agent's own
`write`/`edit` tools emit plain UTF-8 and strip the BOM on every edit, which is what made all of
this visible in the first place.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import text_encoding  # noqa: E402

PROMPTS = ROOT / "prompts"
LAUNCHER = ROOT / "scripts" / "run-dsh-headless.ps1"
BOM = text_encoding.BOM


def variants(infix: str) -> list[pathlib.Path]:
    return sorted(p for p in PROMPTS.rglob("*") if p.is_file() and infix in p.name)


class TestLanguageVariants:
    def test_there_is_one_of_each_to_check(self):
        assert variants(".zh."), "no .zh.* prompt file found - the glob, not the files, is wrong"
        assert variants(".en."), "no .en.* prompt file found - the glob, not the files, is wrong"

    def test_chinese_files_start_with_a_utf8_bom(self):
        missing = [str(p.relative_to(ROOT)) for p in variants(".zh.") if not p.read_bytes().startswith(BOM)]
        assert not missing, (
            "valid UTF-8, but a zh-CN editor reads these as GBK and shows mojibake; they must be "
            f"written with a BOM: {missing} - run `python scripts/fix-text-encoding.py`"
        )

    def test_chinese_files_decode_as_utf8_and_hold_chinese(self):
        for path in variants(".zh."):
            text = path.read_bytes().decode("utf-8")  # strict: raises if the bytes are not UTF-8
            assert any("\u4e00" <= ch <= "\u9fff" for ch in text), f"{path.name} carries no CJK character"
            assert len(text.strip()) > 100, f"{path.name} is too short to be an instruction file"

    def test_english_files_are_pure_ascii(self):
        # ASCII needs no encoding hint, and the sibling .en.* files are ASCII: a `.en.` file that
        # needs a BOM is a file that should not have one.
        for path in variants(".en."):
            text = path.read_bytes().decode("ascii", errors="replace")
            offenders = sorted({ch for ch in text if ord(ch) > 127})
            assert not offenders, (
                f"{path.relative_to(ROOT)} is not ASCII: a BOM-less non-ASCII byte is shown as GBK "
                f"mojibake on a zh-CN machine - found {offenders} "
                f"(U+{', U+'.join(f'{ord(c):04X}' for c in offenders)})"
            )


class TestEveryDocumentIsUnambiguous:
    def test_there_are_documents_to_check(self):
        found = text_encoding.documents(ROOT)
        assert len(found) > 50, "the document walk found almost nothing - the glob is wrong"

    def test_a_document_with_non_ascii_carries_a_bom(self):
        missing = [str(path.relative_to(ROOT)) for path in text_encoding.offenders(ROOT)]
        assert not missing, (
            "these documents hold non-ASCII bytes and no BOM, so a zh-CN editor shows them as GBK "
            f"mojibake; run `python scripts/fix-text-encoding.py` to restore it: {missing}"
        )

    def test_every_document_decodes_as_utf8(self):
        for path in text_encoding.documents(ROOT):
            path.read_bytes().decode("utf-8")  # strict: raises if the bytes are not UTF-8

    def test_the_fixer_and_the_check_agree(self):
        # `offenders` is what the test fails on and what the script repairs; if they ever diverge the
        # failure message would name a file the documented command does not fix.
        assert text_encoding.offenders(ROOT) == [p for p in text_encoding.documents(ROOT) if text_encoding.needs_bom(p)]


class TestTheLauncherToleratesTheBom:
    def test_the_reader_strips_a_leading_bom(self):
        text = LAUNCHER.read_text(encoding="utf-8-sig")
        read = [ln for ln in text.splitlines() if "::ReadAllText($path)" in ln]
        assert read, "the launcher no longer reads the task file with [IO.File]::ReadAllText"
        assert "0xFEFF" in read[0], (
            "the task file is read but its BOM is not trimmed, so U+FEFF would enter the prompt"
        )
