"""The strategy the agent reads is a preset, and the switcher knows it.

Two copies of one strategy exist in this repository, and only the second one runs:

| Copy | Who reads it |
|---|---|
| `prompts/strategies/<preset>/directive.md` | nobody - it is the editable source |
| the `DIRECTIVE:BEGIN/END` block inside `.dsh/skills/civ6-orchestrator/SKILL.md` | the agent, at session start |

`scripts/use-strategy.ps1` writes the second from the first, so nothing else keeps them
in step. Measured 2026-09-27 the two had silently drifted: `prompts/workers/` matched
`china-conquest` and the switcher therefore reported it as active, while the block was
38 lines behind the preset and missing the whole three-phase section (analysis ->
staging -> execution) that the human instruction of 2026-09-26 added, plus carrying a
foreign-missionary passage naming a civilisation that had been eliminated at T164. The
block is the copy that reaches the agent, so a half-applied preset is not active, it is
stale - which is why the switcher now compares both destinations and why these tests
pin both of them.

`prompts/workers/` is the inert destination: measured 2026-09-19, a running session
never read those files. It is still checked here, because a preset whose role files came
from one strategy and whose block came from another is two strategies half-applied.

A block written by `scripts/set-strategy.*` is a deliberate human override, not a
preset, and it says so on its first line - so an override is not mistaken for drift, and
a silent mismatch still fails.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / ".dsh" / "skills" / "civ6-orchestrator" / "SKILL.md"
STRATEGIES = ROOT / "prompts" / "strategies"
WORKERS = ROOT / "prompts" / "workers"
README = STRATEGIES / "README.md"
SWITCHER = ROOT / "scripts" / "use-strategy.ps1"
SH_SWITCHER = ROOT / "scripts" / "use-strategy.sh"
SET_SWITCHER = ROOT / "scripts" / "set-strategy.ps1"
SET_SH_SWITCHER = ROOT / "scripts" / "set-strategy.sh"

# The first line scripts/set-strategy.* put in an ad-hoc block. Every writer, both
# switchers and this test hold the same literal: that is what makes "the human replaced
# the strategy on purpose" a different state from "the block drifted from its preset".
AD_HOC_LINE = (
    "<!-- ad-hoc directive from the human, not a preset: switching presets replaces it -->"
)

# The four roles are fixed by contracts/worker-proposal.schema.json; the same set is
# in the switcher's $roles and enforced by scripts/qualify-static.mjs.
ROLES = ("strategy", "military-map", "economy-cities", "diplomacy-victory")

# The shape the switcher writes and reads. Kept here rather than imported, because the
# point of TestThePatternsAgree is to compare two independent implementations.
BLOCK = re.compile(r"(?s)<!-- DIRECTIVE:BEGIN -->\s*(.*?)\s*<!-- DIRECTIVE:END -->")


def presets() -> list[str]:
    return sorted(path.name for path in STRATEGIES.iterdir() if path.is_dir())


def preset_directives() -> dict[str, str]:
    """Every preset's directive body, trimmed, keyed by preset name."""
    found: dict[str, str] = {}
    for name in presets():
        path = STRATEGIES / name / "directive.md"
        if path.exists():
            found[name] = path.read_text(encoding="utf-8-sig").strip()
    return found


def skill_directive() -> str:
    """The directive body inside SKILL.md, trimmed."""
    match = BLOCK.search(SKILL.read_text(encoding="utf-8-sig"))
    assert match, f"SKILL.md has no DIRECTIVE:BEGIN/END block: {SKILL}"
    return match.group(1).strip()


def is_ad_hoc(block: str) -> bool:
    """True when the block says it was injected ad-hoc rather than coming from a preset."""
    return block.startswith(AD_HOC_LINE)


def switcher_source() -> str:
    return SWITCHER.read_text(encoding="utf-8-sig")


def function_body(name: str) -> str:
    """The body of a top-level PowerShell function, up to its closing brace."""
    match = re.search(
        r"function " + name + r" \{(.*?)\n\}", switcher_source(), re.S
    )
    assert match, f"scripts/use-strategy.ps1 has no top-level function {name}"
    return match.group(1)


def role_files_match(name: str) -> bool:
    """True when prompts/workers/ is exactly this preset's four role files."""
    for role in ROLES:
        live = WORKERS / f"{role}.md"
        source = STRATEGIES / name / f"{role}.md"
        if not live.exists() or not source.exists():
            return False
        if live.read_bytes() != source.read_bytes():
            return False
    return True


class TestTheBlockInTheSkillIsAPreset:
    def test_the_block_is_present_and_substantial(self):
        # A few characters would satisfy "identical to some preset" if a preset were
        # ever emptied, and an empty block is exactly the failure that reads as "the
        # strategy is the skill's own text".
        block = skill_directive()
        assert len(block) >= 100, f"the directive block is only {len(block)} chars"

    def test_the_block_is_a_preset_or_declares_itself_ad_hoc(self):
        block = skill_directive()
        if is_ad_hoc(block):
            # Deliberate: scripts/set-strategy.* writes human text here, and re-applying
            # a preset rewrites the whole block, marker included.
            assert len(block) - len(AD_HOC_LINE) >= 20, (
                "the block carries the ad-hoc marker and nothing else"
            )
            return
        directives = preset_directives()
        matched = [name for name, body in directives.items() if body == block]
        sizes = ", ".join(f"{name}={len(body)}" for name, body in sorted(directives.items()))
        assert matched, (
            f"the SKILL.md directive block ({len(block)} chars) is neither a preset's "
            f"directive.md nor marked ad-hoc (presets: {sizes}); apply the intended one "
            "with scripts\\use-strategy.ps1 <preset>"
        )

    def test_every_preset_can_be_compared(self):
        # The switcher's both-destinations rule skips the block for a preset without a
        # directive.md, which would let such a preset report as active on role files
        # alone - the very bug this file exists for.
        assert set(presets()) == set(preset_directives()), (
            "a preset directory has no directive.md, so it cannot be reported as active "
            f"the way the others are: {sorted(set(presets()) - set(preset_directives()))}"
        )

    def test_the_live_block_and_the_live_role_files_are_the_same_preset(self):
        # Either both destinations agree, or prompts/workers/ is hand-edited and belongs
        # to no preset at all. Workers from preset A with the block of preset B is the
        # state that hid the drift: the switcher called it active.
        block = skill_directive()
        if is_ad_hoc(block):
            return  # an ad-hoc override makes no claim about prompts/workers/
        matched = [name for name, body in preset_directives().items() if body == block]
        assert matched, "no preset matches the live block (see the test above)"
        from_roles = [name for name in presets() if role_files_match(name)]
        assert from_roles in ([], matched), (
            f"prompts/workers/ holds {from_roles} while the live SKILL.md block is "
            f"{matched}; apply one preset so both destinations agree"
        )


class TestTheSwitcherComparesBothDestinations:
    def test_the_active_check_consults_the_skill_block(self):
        body = function_body("Get-CurrentPreset")
        assert "Get-SkillDirective" in body, (
            "Get-CurrentPreset decides 'active' without reading SKILL.md, so a preset "
            "whose block never arrived reports as active (measured 2026-09-27)"
        )
        assert "directive.md" in body, "the preset's directive.md is not compared"

    def test_the_skill_block_reader_reads_the_skill_file(self):
        body = function_body("Get-SkillDirective")
        assert "$skillPath" in body, "$skillPath is not the file Get-SkillDirective reads"
        assert "$marker" in body, "Get-SkillDirective does not use the shared $marker pattern"

    def test_the_marker_pattern_is_defined_once(self):
        # The apply path and the active check must read the same block: two definitions
        # could drift apart and report a preset as applied that is not the live one.
        definitions = re.findall(r"^\$marker\s*=", switcher_source(), re.M)
        assert len(definitions) == 1, f"$marker is defined {len(definitions)} times"

    def test_the_marker_pattern_is_the_four_schema_roles(self):
        match = re.search(r"^\$roles\s*=\s*@\((.*?)\)", switcher_source(), re.M)
        assert match, "scripts/use-strategy.ps1 has no $roles assignment"
        declared = tuple(sorted(re.findall(r"'([^']+)'", match.group(1))))
        assert declared == tuple(sorted(ROLES)), (
            f"the switcher's roles {declared} differ from the schema's {tuple(sorted(ROLES))}"
        )


class TestTheBashSwitcherMatchesThePowerShellOne:
    """scripts/use-strategy.sh is the Git Bash path to the same two destinations.

    It carried the same role-files-only bug, and one of its own: the preset files hold a
    UTF-8 BOM, which the bash injection wrote into the *middle* of SKILL.md. A block
    starting with U+FEFF matches no preset in either shell (U+FEFF is whitespace to
    neither .NET's Trim nor Python's strip), so the .sh could desynchronise the two
    destinations on its own. Both fixes are pinned here, because Git Bash cannot run
    inside the agent sandbox (it needs a signal pipe) and the file would otherwise ship
    unexecuted.
    """

    def test_the_bash_active_check_consults_the_skill_block(self):
        match = re.search(
            r"current_preset\(\) \{(.*?)\n\}", SH_SWITCHER.read_text(encoding="utf-8-sig"), re.S
        )
        assert match, "scripts/use-strategy.sh has no current_preset() function"
        assert "skill_block" in match.group(1), (
            "the bash active check decides without reading SKILL.md, so it reports a "
            "stale preset as active - the bug measured 2026-09-27 in the .ps1"
        )
        assert "directive.md" in match.group(1), "the preset's directive.md is not compared"

    def test_the_bash_injection_strips_the_preset_bom(self):
        source = SH_SWITCHER.read_text(encoding="utf-8-sig")
        assert "strip_bom()" in source, "scripts/use-strategy.sh has no strip_bom helper"
        assert re.search(r'strip_bom "\$directive" > "\$body"', source), (
            "the bash injection writes the preset file verbatim, so its BOM lands inside "
            "the block and the block then matches no preset"
        )

    def test_both_switchers_read_the_same_markers_and_verify_the_write(self):
        for path in (SWITCHER, SH_SWITCHER):
            source = path.read_text(encoding="utf-8-sig")
            assert "<!-- DIRECTIVE:BEGIN" in source, f"{path.name} does not find the block"
            assert "<!-- DIRECTIVE:END -->" in source, f"{path.name} does not close the block"
            assert "does not read back" in source, (
                f"{path.name} reports a write as done without reading the block back"
            )


class TestThePatternsAgree:
    def test_the_switchers_pattern_captures_the_same_body_as_this_test(self):
        # The switcher's $marker is a .NET regex; this file's BLOCK is a Python one. The
        # syntax used here is valid in both, so running the switcher's pattern through
        # Python proves the two readers see the same body - without spawning PowerShell.
        match = re.search(r"^\$marker\s*=\s*'(.*)'\s*$", switcher_source(), re.M)
        assert match, "scripts/use-strategy.ps1 has no single-quoted $marker pattern"
        shared = re.search(match.group(1), SKILL.read_text(encoding="utf-8-sig"))
        assert shared, f"the switcher's pattern does not match SKILL.md: {match.group(1)}"
        assert shared.group(1).strip() == skill_directive()


class TestAnAdHocDirectiveDeclaresItself:
    """The other two writers of the block: scripts/set-strategy.*.

    They inject human text, so the block is no preset's directive - and before this the
    state was invisible, which is the same question as the drift above ("which strategy is
    actually live?"). Its first line now answers it.

    Both scripts also had a defect of their own, measured on a fixture copy of SKILL.md:
    the PowerShell one wrote with `WriteAllText` and no encoding, which strips the BOM the
    file needs - the bug already fixed once in use-strategy.ps1, and the encoding gate
    fails on it - and the bash one copied a `-File` source verbatim, so the BOM of a
    Chinese directive landed inside the block.
    """

    def test_both_ad_hoc_writers_carry_this_tests_marker(self):
        for path in (SET_SWITCHER, SET_SH_SWITCHER):
            assert path.exists(), f"{path} is gone; this test has to move with it"
            assert AD_HOC_LINE in path.read_text(encoding="utf-8-sig"), (
                f"{path.name} injects a block without the marker, so a deliberate "
                "override becomes indistinguishable from a stale preset"
            )

    def test_both_ad_hoc_writers_verify_the_write_landed(self):
        for path in (SET_SWITCHER, SET_SH_SWITCHER):
            assert "does not read back" in path.read_text(encoding="utf-8-sig"), (
                f"{path.name} reports the injection as done without reading the block back"
            )

    def test_the_bash_ad_hoc_writer_strips_a_source_bom(self):
        assert "sed '1s/^\\xEF\\xBB\\xBF//' \"$value\"" in SET_SH_SWITCHER.read_text(
            encoding="utf-8-sig"
        ), "set-strategy.sh copies a -File source verbatim, so its BOM lands in the block"

    def test_both_switchers_report_an_ad_hoc_block_distinctly(self):
        for path in (SWITCHER, SH_SWITCHER):
            assert "ad-hoc directive" in path.read_text(encoding="utf-8-sig"), (
                f"{path.name} reports an ad-hoc block as if it were a stale preset"
            )

    def test_the_writers_pick_the_bom_from_the_content(self):
        # The encoding rule is content-based: a document holding a non-ASCII byte carries a BOM, a
        # pure-ASCII one must not. The skill is ASCII (text_encoding.ASCII_ONLY), so a writer that
        # always added a BOM left a stray one on every switch - measured 2026-09-28.
        pattern = "New-Object System.Text.UTF8Encoding ([regex]::IsMatch($skill, '[^\\x00-\\x7F]'))"
        for path in (SWITCHER, SET_SWITCHER):
            assert pattern in path.read_text(encoding="utf-8-sig"), (
                f"{path.name} decides the BOM by hand instead of from the content it writes"
            )

    def test_the_ad_hoc_writers_refuse_chinese(self):
        # The mirror is where Chinese belongs; the block DSH serves is English (human instruction
        # 2026-09-28), and a Chinese block would fail the gate a moment after it was written.
        assert "the strategy text is not ASCII" in SET_SWITCHER.read_text(encoding="utf-8-sig")
        sh = SET_SH_SWITCHER.read_text(encoding="utf-8-sig")
        assert "the strategy text is not ASCII" in sh
        assert "tr -d '\\000-\\177'" in sh, (
            "set-strategy.sh does not count non-ASCII bytes, so a Chinese -File would be injected"
        )


class TestTheReadmeListsEveryPreset:
    def test_the_available_presets_table_names_every_preset(self):
        readme = README.read_text(encoding="utf-8-sig")
        section = re.search(r"(?s)## Available presets(.*?)\n## ", readme)
        assert section, "prompts/strategies/README.md has no '## Available presets' section"
        listed = set(re.findall(r"^\| `([a-z0-9-]+)`", section.group(1), re.M))
        assert listed == set(presets()), (
            f"the preset table lists {sorted(listed)} but the directory holds "
            f"{presets()}; china-conquest was the one missing when this test was added, "
            "and it is the strategy the agent actually runs"
        )
