"""Check the directive and its copy inside the skill are still the same text.

`scripts/use-strategy.ps1` (line 141-145) injects `prompts/strategies/<preset>/directive.md`
into the `DIRECTIVE:BEGIN/END` block of `.dsh/skills/civ6-orchestrator/SKILL.md`. Editing one
without the other leaves the running agent reading a stale strategy, and nothing in the test
suite reads the skill file - so this check exists to be run by hand after touching either.
"""

import hashlib
import pathlib
import re

DIRECTIVE = pathlib.Path("prompts/strategies/china-conquest/directive.md")
SKILL = pathlib.Path(".dsh/skills/civ6-orchestrator/SKILL.md")

block = re.search(
    r"<!-- DIRECTIVE:BEGIN -->(.*?)<!-- DIRECTIVE:END -->",
    SKILL.read_text(encoding="utf-8"),
    re.DOTALL,
)
if block is None:
    raise SystemExit(f"{SKILL} has no DIRECTIVE:BEGIN/END block")

in_skill = block.group(1).strip()
in_file = DIRECTIVE.read_text(encoding="utf-8").strip()
print("identical:", in_skill == in_file)
print(f"directive.md  {len(in_file)} chars, md5 {hashlib.md5(in_file.encode()).hexdigest()}")
print(f"SKILL.md body {len(in_skill)} chars, md5 {hashlib.md5(in_skill.encode()).hexdigest()}")
if in_skill != in_file:
    for i, (a, b) in enumerate(zip(in_skill.splitlines(), in_file.splitlines()), 1):
        if a != b:
            print(f"first difference at line {i}:\n  skill: {a!r}\n  file : {b!r}")
            break
    raise SystemExit(1)
