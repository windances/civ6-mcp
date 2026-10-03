"""Organise the data directory into one directory per playthrough, and verify the split.

Everything a session stores resolves off ``{civ}_{seed}`` inside one flat data directory, so two
playthroughs share the diary's *location* even when their keys differ, and the retired-goal state
lives in a single file keyed by match. This collects each playthrough's artefacts into
``runs/<run_id>/`` so nothing is shared except what is genuinely global (`branches/`, the
diagnostics), and then checks the result.

    runs.py inventory            # what is here, grouped by playthrough
    runs.py plan                 # what the migration would move, and where (no writes)
    runs.py apply                # do it
    runs.py verify               # prove the runs do not overlap

Nothing is deleted. `apply` moves files into their run and writes a manifest per run plus a
``current`` pointer; it is idempotent, so a second run reports "already in place".
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from civ_mcp import run_manifest  # noqa: E402

DATA = pathlib.Path(
    os.environ.get("CIV_MCP_DATA_DIR", ROOT / ".civ6-mcp-data")
).resolve()

KINDS = ("diary", "log", "spatial", "mapturns", "mapstatic")

# Files that belong to no single playthrough: they describe the machine, the session, or a
# rolled-back branch archive, and every run should keep seeing them.
SHARED = {
    "branches", "hang_diagnosis.jsonl", "A1-snapshot-T12.json", "resume-task.en.txt",
    "loc-en-names.json", "runs", "current",
}


def classify(name: str) -> tuple[str, str, int, str] | None:
    """``(kind, civ, seed, run_id)`` for a per-playthrough file, else None.

    Split on the underscore and take the first integer as the seed: a civ name never carries one and
    a legacy run id looks like ``iron-garnet-mesa-39`` - which does end in digits, so the *first*
    integer is what identifies the seed, not the last.
    """
    stem = name
    for suffix in (".jsonl", ".json"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    else:
        return None
    kind = next((k for k in KINDS if stem.startswith(f"{k}_")), None)
    if kind is None:
        return None
    parts = stem[len(kind) + 1:].split("_")
    if parts and parts[-1] == "cities":
        parts = parts[:-1]
    seed_index = None
    for i, part in enumerate(parts):
        if re.fullmatch(r"-?\d+", part):
            seed_index = i
            break
    if seed_index is None or seed_index == 0:
        return None
    civ = "_".join(parts[:seed_index])
    seed = int(parts[seed_index])
    run_id = "_".join(parts[seed_index + 1:])
    return kind, civ, seed, run_id


def run_id_for(civ: str, seed: int, existing: dict[str, dict]) -> str:
    for rid, manifest in existing.items():
        if manifest.get("civ") == civ and int(manifest.get("seed") or 0) == seed:
            return rid
    return f"{civ}-{seed}"


def inventory(data: pathlib.Path) -> tuple[dict[str, list[str]], list[str]]:
    """``({match_key: [filenames]}, [shared filenames])`` for one flat data directory."""
    grouped: dict[str, list[str]] = collections.defaultdict(list)
    shared: list[str] = []
    for path in sorted(data.iterdir()):
        if path.name in SHARED or path.is_dir():
            continue
        info = classify(path.name)
        if info is None:
            shared.append(path.name)
            continue
        kind, civ, seed, _ = info
        grouped[f"{civ}_{seed}"].append(path.name)
    return grouped, shared


def load_state(data: pathlib.Path) -> dict:
    path = data / "turn-checks-state.json"
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def existing_runs(root: pathlib.Path) -> dict[str, dict]:
    runs = root / "runs"
    found: dict[str, dict] = {}
    if runs.is_dir():
        for entry in sorted(runs.iterdir()):
            manifest = run_manifest.load(entry)
            if manifest:
                found[entry.name] = manifest
    # A manifest at the root predates the layout; it names the run the flat files belong to.
    root_manifest = run_manifest.load(root)
    if root_manifest:
        found.setdefault(root_manifest["run_id"], root_manifest)
    return found


def build_plan(root: pathlib.Path) -> dict:
    grouped, shared = inventory(root)
    state = load_state(root)
    known = existing_runs(root)

    plan: dict[str, dict] = {}
    for key, files in sorted(grouped.items()):
        civ, seed = key.rsplit("_", 1)
        rid = run_id_for(civ, int(seed), known)
        manifest = known.get(rid) or {}
        plan[rid] = {
            "run_id": rid,
            "civ": civ,
            "seed": int(seed),
            "label": manifest.get("label") or f"migrated from {key}",
            "files": files,
            "state": state.get(key, {}),
        }
    return {"runs": plan, "shared": shared, "state_keys": sorted(state), "root": root}


def target_for(run_id: str, name: str) -> str:
    """Where a file goes inside its run directory: the run directory itself.

    Not a `diary/` subdirectory. `diary.DIARY_DIR`, `heartbeat.HEARTBEAT_PATH` and
    `turn_checks.state_path()` all resolve `CIV_MCP_DATA_DIR` **directly**, and the run directory is
    what that variable points at - so a file in `runs/<id>/diary/` is a file the tooling will never
    look for. The run directory is already the isolation boundary; a subdirectory inside it adds a
    mismatch and no isolation. `saves/` is the exception: it is a holding area for phase 3 and
    nothing resolves a save path from the data directory.
    """
    return name


def show_plan(plan: dict) -> None:
    root = plan["root"]
    print(f"data directory : {root}")
    print(f"playthroughs   : {len(plan['runs'])}")
    for rid, entry in plan["runs"].items():
        print(f"\n  {rid}")
        print(f"    identity   : {entry['civ']}_{entry['seed']}")
        print(f"    label      : {entry['label']}")
        print(f"    files      : {len(entry['files'])}")
        for name in entry["files"]:
            size = (root / name).stat().st_size if (root / name).exists() else 0
            print(f"      -> runs/{rid}/{target_for(rid, name)}   ({size / 1024:.0f} KB)")
        if entry["state"]:
            print(f"    retired goals: {entry['state']}")
    if plan["shared"]:
        print(f"\n  shared (left at the root): {plan['shared']}")
    loose = [k for k in plan["state_keys"] if k not in {e['civ'] + '_' + str(e['seed']) for e in plan['runs'].values()}]
    if loose:
        print(f"  state keys matching no files here: {loose}")


def apply(plan: dict) -> int:
    root = plan["root"]
    runs_root = root / "runs"
    created = moved = 0
    for rid, entry in plan["runs"].items():
        run_dir = runs_root / rid
        if not run_dir.exists():
            created += 1
        (run_dir / "diary").mkdir(parents=True, exist_ok=True)
        (run_dir / "telemetry").mkdir(parents=True, exist_ok=True)
        (run_dir / "saves").mkdir(parents=True, exist_ok=True)

        manifest = run_manifest.load(run_dir) or run_manifest.make(
            rid, entry["label"], entry["civ"], entry["seed"],
            notes=f"migrated from {entry['civ']}_{entry['seed']}",
        )
        manifest["label"] = entry["label"]
        manifest["civ"] = entry["civ"]
        manifest["seed"] = entry["seed"]
        run_manifest.save(manifest, run_dir)

        for name in entry["files"]:
            source = root / name
            if not source.exists():
                continue
            destination = run_dir / target_for(rid, name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                continue
            shutil.move(str(source), str(destination))
            moved += 1

        state_path = run_dir / "turn-checks-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        state[f"{entry['civ']}_{entry['seed']}"] = entry["state"]
        # newline="": text mode would rewrite every \n as os.linepsep on Windows.
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8", newline=""
        )

    # The old flat state file is now split across the runs; keep it as a record rather than delete.
    old_state = root / "turn-checks-state.json"
    if old_state.exists():
        shutil.move(str(old_state), str(root / "turn-checks-state.pre-runs.json"))

    # The root manifest becomes the first run's; leaving it would name the root as a run too.
    root_manifest = root / "run.json"
    if root_manifest.exists():
        shutil.move(str(root_manifest), str(root / "run.pre-runs.json"))

    current = plan.get("current") or next(iter(plan["runs"]), "")
    (root / "current").write_text(current + "\n", encoding="utf-8", newline="")
    print(f"\ncreated {created} run director(ies), moved {moved} file(s), current -> {current}")
    return 0


def verify(root: pathlib.Path) -> int:
    """Prove the runs do not overlap: distinct directories, distinct manifests, distinct state."""
    runs_root = root / "runs"
    if not runs_root.is_dir():
        print("no runs/ directory - nothing is organised yet")
        return 1
    seen: dict[str, str] = {}
    problems: list[str] = []
    print(f"data directory : {root}")
    current = (root / "current").read_text(encoding="utf-8").strip() if (root / "current").exists() else "(none)"
    print(f"current        : {current}")
    for run_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        manifest = run_manifest.load(run_dir)
        if manifest is None:
            problems.append(f"{run_dir.name}: no manifest")
            continue
        key = f"{manifest.get('civ')}_{manifest.get('seed')}"
        files = sorted(p.name for p in run_dir.rglob("*") if p.is_file())
        print(f"\n  {run_dir.name}")
        print(f"    identity : {key}")
        print(f"    label    : {manifest.get('label')}")
        print(f"    files    : {len(files)}")
        for name in files[:6]:
            print(f"      {name}")
        # Isolation assertions.
        if key in seen:
            problems.append(f"{run_dir.name}: identity {key} also used by {seen[key]}")
        seen[key] = run_dir.name
        for other in runs_root.iterdir():
            if other.is_dir() and other != run_dir and (other.name in files or run_dir.name in
                                                        [p.name for p in other.iterdir()]):
                problems.append(f"{run_dir.name}: overlaps {other.name}")
        state = run_dir / "turn-checks-state.json"
        if state.exists():
            keys = sorted(json.loads(state.read_text(encoding="utf-8")))
            if keys and keys != [key]:
                problems.append(f"{run_dir.name}: state keys {keys} are not exactly {key}")
            else:
                print(f"    state    : {keys}")
    leftovers = [
        p.name for p in root.iterdir()
        if p.is_file() and p.name not in SHARED and classify(p.name)
    ]
    if leftovers:
        problems.append(f"per-playthrough files left at the root: {leftovers}")
    print()
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK: {len(seen)} run(s), no shared diary, no shared state, no file at the root belonging "
          f"to any of them")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("verb", choices=("inventory", "plan", "apply", "verify"))
    ap.add_argument("--current", default="", help="which run `apply` should point `current` at")
    args = ap.parse_args()

    root = DATA
    if args.verb == "inventory":
        grouped, shared = inventory(root)
        print(f"data directory : {root}")
        for key, files in sorted(grouped.items()):
            print(f"  {key:<24} {len(files):>3} file(s)")
        print(f"  shared: {shared}")
        return 0

    plan = build_plan(root)
    plan["current"] = args.current
    if args.verb == "plan":
        show_plan(plan)
        return 0
    if args.verb == "apply":
        show_plan(plan)
        return apply(plan)
    return verify(root)


if __name__ == "__main__":
    raise SystemExit(main())
