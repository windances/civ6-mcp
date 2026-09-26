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

import importlib.util
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from civ_mcp import text_encoding  # noqa: E402

PROMPTS = ROOT / "prompts"
LAUNCHER = ROOT / "scripts" / "run-dsh-headless.ps1"
BOM = text_encoding.BOM


def repair_module():
    """`scripts/repair-text.py` has a hyphen in its name, so it is loaded by path."""
    spec = importlib.util.spec_from_file_location("repair_text", ROOT / "scripts" / "repair-text.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["repair_text"] = module
    spec.loader.exec_module(module)
    return module


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


class TestTheTextItselfIsStillText:
    """A BOM is a display hint; it says nothing about whether the characters are still the ones
    somebody wrote. Measured 2026-09-26: a `Get-Content | Set-Content` round trip decoded five files
    as GBK and re-encoded them as UTF-8, so `在集结前` became `鍦ㄩ泦缁撳墠` and every em dash became
    `鈥?` - in source files, docstrings, and the game's own menu labels. Every BOM was in place and
    843 tests passed, which is why this check exists."""

    # The shapes a GBK round trip leaves behind; `looks_corrupt` has to recognise every one.
    CORRUPT_SAMPLES = [
        "\u9366\u3129\u6ce6\u7f01\u64b3\u58a0\u951b\u5c83",       # 在集结前, decoded as GBK
        "\u4e00\u4e2a em dash \u9225? left behind",                # a dash that lost a byte
        "a private-use byte \ue585 in the middle",
        "a lost byte \u5728\ufffd\u96c6",
    ]

    def test_the_damaged_shapes_are_recognised(self):
        for sample in self.CORRUPT_SAMPLES:
            assert text_encoding.looks_corrupt(sample), f"not recognised as damage: {sample!r}"

    def test_clean_chinese_and_english_are_not_flagged(self):
        clean = [
            "在集结前，规划集结方案，不能被堵住，不同部队移动力不一样",
            "the pre-war analysis, the staging and the assault apply to every camp",
            "中文里正常的问号是全角的，而不是半角字符。",
            "\u6e29\u99a8\u7684\u5efa\u8bae\uff1a\u4fdd\u6301\u6b63\u5e38",   # 温馨的建议：保持正常
        ]
        for line in clean:
            assert not text_encoding.looks_corrupt(line), f"false positive: {line!r}"

    def test_no_file_in_the_repository_still_carries_the_damage(self):
        found = text_encoding.corrupt_lines(ROOT)
        shown = [f"{p.relative_to(ROOT)}:{n}" for p, n, _ in found]
        assert not found, (
            "valid UTF-8, BOM in place, and still not the text somebody wrote (a GBK round trip - "
            "`Get-Content | Set-Content` is the usual cause). Repair with "
            f"`python scripts/repair-text.py --apply`, then `python scripts/fix-text-encoding.py`: {shown}"
        )


class TestTheGateIsMandatory:
    """The check is not advice: it runs before every commit, and the repair never guesses."""

    HOOK = ROOT / ".githooks" / "pre-commit"
    INSTALLER = ROOT / "scripts" / "install-hooks.py"

    def test_the_hook_runs_the_check(self):
        text = self.HOOK.read_text(encoding="utf-8")
        assert "fix-text-encoding.py" in text and "--check" in text, (
            ".githooks/pre-commit no longer runs the text-integrity check"
        )
        assert "repair-text.py" in text, "the hook names the failure but not the repair"

    def test_the_installer_points_git_at_the_hook(self):
        assert self.INSTALLER.is_file(), "scripts/install-hooks.py is the documented way in"
        text = self.INSTALLER.read_text(encoding="utf-8")
        assert "core.hooksPath" in text and ".githooks" in text

    def test_this_clone_has_the_hook_installed(self):
        result = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode not in (0, 1):
            return  # no git here: the hook cannot be enforced, and that is not this test's business
        assert result.stdout.strip() == ".githooks", (
            "the commit gate is not installed in this clone - run `python scripts/install-hooks.py`"
        )


class TestTheRepairDoesNotGuess:
    """A repair that mangles a clean file is worse than no repair, and the failure is silent."""

    def test_a_clean_line_is_left_alone(self):
        module = repair_module()
        # `‹`/`›` and a check mark are outside GBK: encoding them with errors="replace" would turn
        # them into '?' and the reversal would look successful while eating the characters.
        for line in ("Agent \u2039Claude\u203a", "DONE \u2713", "在集结前，规划集结方案"):
            assert module.repair_line(line) == line, f"a clean line was rewritten: {line!r}"

    def test_a_damaged_line_is_repaired(self):
        module = repair_module()
        # A two-character word corrupts to a whole number of GBK pairs, so the reversal is exact.
        sample = "\u5317\u4eac".encode("utf-8").decode("gbk")     # 北京 -> 鍖椾含
        assert module.repair_line(sample) == "\u5317\u4eac"
        assert module.repair_line("a \u9225? b") == "a \u2014 b"

    def test_the_repair_is_idempotent(self):
        module = repair_module()
        once = module.repair_line("a \u9225? b and " + "\u5317\u4eac".encode("utf-8").decode("gbk"))
        assert module.repair_line(once) == once


class TestTheLauncherToleratesTheBom:
    def test_the_reader_strips_a_leading_bom(self):
        text = LAUNCHER.read_text(encoding="utf-8-sig")
        read = [ln for ln in text.splitlines() if "::ReadAllText($path)" in ln]
        assert read, "the launcher no longer reads the task file with [IO.File]::ReadAllText"
        assert "0xFEFF" in read[0], (
            "the task file is read but its BOM is not trimmed, so U+FEFF would enter the prompt"
        )
