"""Assemble an advisor brief, pasting the governing doctrine from the files themselves.

An advisor is dispatched with no filesystem - the role file says so in its own words ("you hold no tools
and no filesystem") and the stored briefs repeat it - so every rule the advisor must obey has to be
**inside the message**. That makes a brief a *copy*, and a copy drifts: measured 2026-09-30, the
rehearsal brief at `.tools/_advisor-brief.md` pastes a revision of `tactics/02` and `tactics/05` that is
missing one whole section of each - `## If the contact happens while the army is still assembling` and
`## The end-of-turn warning that enforces the first of those` - because the paste was made by hand and
nothing checked it. The sections that go missing are exactly the ones added after the paste was taken,
so the doctrine an advisor never sees is the doctrine that is newest.

**This is the one place that reads the doctrine from disk**, so a brief cannot carry an older revision
than the file. Every pasted section is headed with its source path and the file's **sha256**, and
`tests/test_advisor_brief.py` asserts three things about a generated brief: the paste is byte-identical
to the file, the digest is the file's digest today, and **every heading of the source survives** - the
completeness check that would have caught the drift above.

The fence is sized from the content (one backtick longer than the longest run inside it), because these
files contain fenced blocks of their own and a fixed ``` would end the paste early.

Usage:
  python scripts/advisor-brief.py --role military-map --tactics 04,05,06
  python scripts/advisor-brief.py --role economy-cities --tactics 08 --snapshot .tmp/snap.json
  python scripts/advisor-brief.py --tactics 07 --signals .tmp/checks.txt --out .tmp/brief.md
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TACTIC_DIR = ROOT / "prompts" / "tactics"
PRESET_DIR = ROOT / "prompts" / "strategies"
DOCTRINE_HEADING = "## The doctrine you are held to, verbatim from the file"


class UnknownTactic(SystemExit):
    """Raised with the list of files that do exist, because a typo here is silent otherwise."""


def available() -> list[str]:
    return sorted(p.stem for p in TACTIC_DIR.glob("*.md") if p.name != "README.md")


def resolve_tactic(spec: str) -> pathlib.Path:
    """`07`, `7`, `07-pre-war-analysis` or a full path -> the file, or exit naming what exists.

    The bare-number form is accepted with or without its leading zero because **PowerShell coerces
    it**: `--tactics 04,05` reaches the process as `4`, `5` (a comma list is an array there, and
    `04` parses as the number 4) - measured 2026-09-30 on this very script. Rejecting `4` would make
    the tool look broken for a reason that has nothing to do with the tactic it was asked for.
    """
    text = spec.strip()
    if not text:
        raise UnknownTactic(f"empty tactic spec; available: {', '.join(available())}")
    candidate = pathlib.Path(text)
    if candidate.is_file():
        return candidate
    forms = [text]
    if text.isdigit():
        forms.append(text.zfill(2))
    if not text.endswith(".md"):
        for form in forms:
            for path in TACTIC_DIR.glob("*.md"):
                if path.stem == form or path.name == f"{form}.md" or path.stem.startswith(f"{form}-"):
                    return path
    raise UnknownTactic(f"no tactic file for {text!r}; available: {', '.join(available())}")


def read(path: pathlib.Path) -> str:
    # The tactics files carry a BOM (they hold Chinese); `utf-8-sig` drops it so the pasted text
    # starts at the file's first character rather than at a zero-width mark.
    return path.read_text(encoding="utf-8-sig")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fence_for(text: str) -> str:
    """A fence one backtick longer than the longest run inside the text, never shorter than three."""
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.lstrip().startswith("#")]


def section(path: pathlib.Path, relative_to: pathlib.Path = ROOT) -> str:
    """One doctrine section: the path, the file's digest, and the file's text inside a safe fence."""
    body = read(path)
    try:
        label = path.relative_to(relative_to).as_posix()
    except ValueError:
        label = path.as_posix()
    fence = fence_for(body)
    return (
        f"### {label} (sha256 {digest(body)})\n\n"
        f"{fence}\n{body.rstrip()}\n{fence}\n"
    )


def build_brief(
    tactic_specs: list[str],
    role: str | None = None,
    preset: str = "china-conquest",
    snapshot: pathlib.Path | None = None,
    signals: pathlib.Path | None = None,
    root: pathlib.Path = ROOT,
) -> str:
    """The whole brief. Nothing is summarised: the doctrine is the file, byte for byte."""
    globals_root = root
    parts: list[str] = []
    if role:
        role_path = PRESET_DIR / preset / f"{role}.md"
        if not role_path.is_file():
            raise UnknownTactic(f"no role file at {role_path.relative_to(root).as_posix()}")
        role_text = read(role_path)
        parts.append(
            f"You are the `{role}` advisor. You are read-only: you hold **no tools and no filesystem**.\n"
            f"Everything you may use is in this message. Return only JSON matching\n"
            f"`contracts/worker-proposal.schema.json` with `worker: \"{role}\"`.\n"
        )
        parts.append(
            f"## Your role instructions, verbatim from "
            f"`{role_path.relative_to(root).as_posix()}`\n\n"
            f"{fence_for(role_text)}\n{role_text.rstrip()}\n{fence_for(role_text)}\n"
        )
    if snapshot is not None:
        snap = snapshot.read_text(encoding="utf-8")
        parts.append(f"## The canonical snapshot\n\n{fence_for(snap)}\n{snap.rstrip()}\n{fence_for(snap)}\n")
    if signals is not None:
        sig = signals.read_text(encoding="utf-8")
        parts.append(
            f"## This turn's judgement signals\n\n{fence_for(sig)}\n{sig.rstrip()}\n{fence_for(sig)}\n"
        )
    parts.append(DOCTRINE_HEADING + "\n")
    parts.append(
        "Pasted from the files, not retyped: each section names its source and that source's sha256.\n"
    )
    for spec in tactic_specs:
        path = resolve_tactic(spec)
        if not str(path).startswith(str(globals_root)) and path.is_absolute():
            label = path.as_posix()
        parts.append(section(path, relative_to=globals_root))
    return "\n".join(parts).rstrip() + "\n"


SECTION_HEADING = re.compile(
    r"^### (?P<label>[^\s]+\.md) \(sha256 (?P<digest>[0-9a-f]{64})\)\s*$"
    # The hand-made briefs this check exists for use `#### <path>` and carry no digest - measured in
    # `.tools/_advisor-brief.md`. A brief that cannot say which revision it pasted is exactly the one
    # worth auditing, so the legacy shape is matched too and its missing digest is reported.
    r"|^#### (?P<legacy>[^\s]+\.md)\s*$",
    re.M,
)


def verify_brief(text: str, root: pathlib.Path = ROOT) -> list[str]:
    """Every way a generated brief can lie about the doctrine, as a list of problems.

    The generator and the check live together because the failure they exist for is a **hand-made
    paste**, and a hand-made paste is exactly what a reader cannot distinguish from a good one. This
    is the check that would have caught the measured case: `.tools/_advisor-brief.md` pastes a
    revision of `tactics/02` and `tactics/05` that is missing one whole section of each, and every
    heading-level difference is reported here by name.
    """
    problems: list[str] = []
    matches = list(SECTION_HEADING.finditer(text))
    if not matches:
        return ["no doctrine section found: a brief that pastes nothing cannot be checked"]
    for index, match in enumerate(matches):
        label = match.group("label") or match.group("legacy")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        lines = block.splitlines()
        start = next((n for n, line in enumerate(lines) if line.startswith("```")), None)
        fenced = start is not None and not any(line.strip() for line in lines[:start])
        if not fenced:
            # A hand-made brief pastes the file **unfenced**, straight after the heading (measured in
            # `.tools/_advisor-brief.md`), so its paste is the whole block up to the next heading -
            # and the fences it contains are the file's own, not delimiters.
            pasted = block
        else:
            fence = lines[start].rstrip()
            close = next((n for n in range(start + 1, len(lines)) if lines[n].rstrip() == fence), None)
            if close is None:
                problems.append(f"{label}: the fence is never closed (content holds the fence string)")
                continue
            pasted = "\n".join(lines[start + 1 : close])
        source = root / label
        if not source.is_file():
            problems.append(f"{label}: the brief names a file that does not exist")
            continue
        body = read(source)
        if match.group("digest") is None:
            problems.append(
                f"{label}: the section carries no sha256, so it cannot say which revision of the "
                f"file it pasted"
            )
        elif match.group("digest") != digest(body):
            problems.append(
                f"{label}: the digest in the brief is not the file's digest today - the paste is "
                f"from an older revision"
            )
        if pasted.strip() != body.strip():
            problems.append(f"{label}: the pasted text is not the file")
        missing = [h for h in headings(body) if h not in headings(pasted)]
        for heading in missing:
            problems.append(f"{label}: the paste is missing a whole section: {heading}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--role", default=None, help="advisor role; reads the preset's <role>.md")
    parser.add_argument("--preset", default="china-conquest")
    parser.add_argument("--tactics", default=None, help="comma-separated: 04,05,06 or full slugs")
    parser.add_argument("--snapshot", type=pathlib.Path, default=None)
    parser.add_argument("--signals", type=pathlib.Path, default=None)
    parser.add_argument("--out", type=pathlib.Path, default=None, help="default: stdout")
    parser.add_argument(
        "--check",
        type=pathlib.Path,
        default=None,
        help="verify an existing brief against the files instead of generating one; exit 1 on drift",
    )
    args = parser.parse_args(argv)

    if args.check is not None:
        sys.stdout.reconfigure(encoding="utf-8")
        problems = verify_brief(args.check.read_text(encoding="utf-8-sig"))
        if problems:
            print(f"{args.check}: {len(problems)} problem(s) - the pasted doctrine is not the file")
            for problem in problems:
                print(f"  {problem}")
            return 1
        print(f"{args.check}: the pasted doctrine is byte-identical to every file it names")
        return 0

    if not args.tactics:
        parser.error("--tactics is required unless --check is given")

    specs = [piece for piece in args.tactics.split(",") if piece.strip()]
    brief = build_brief(
        specs, role=args.role, preset=args.preset, snapshot=args.snapshot, signals=args.signals
    )
    if args.out is None:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(brief)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(brief, encoding="utf-8")
        print(f"wrote {args.out} ({len(brief)} chars, {len(specs)} tactic file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
