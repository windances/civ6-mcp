#!/usr/bin/env python3
"""Extract one military-production attempt's numbers from the raw record.

An *attempt* is one played match.  Its raw record is two files the loop already writes:

    .civ6-mcp-data/diary_<game>.jsonl   one snapshot row per player per turn (the economy)
    .civ6-mcp-data/log_<game>_*.jsonl   one row per tool call, with the tool's own reply text
                                        (the rules that failed, the orders that were refused,
                                        the city that was taken)

Nothing here is new instrumentation: the point is that the two files already hold every number an
attempt is judged on, and this turns them into the same table every time, so two attempts can be
compared without re-deriving anything by hand.

    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_911679432
    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_911679432 --step 10 --json
    .venv\\Scripts\\python.exe scripts/experiment-report.py --game china_911679432 --verdict
    .venv\\Scripts\\python.exe scripts/experiment-report.py --list

Reported, per attempt:

  * the 10-turn economy table (science/culture/gold/pop/districts/wonders/improvements/...)
  * the military table - unit composition at each boundary, so the establishment's growth is visible
  * **the establishment** - the first turn the army matches `prompts/tactics/01-unit-production.md`'s
    table, checked on every turn rather than on the tenth, plus the first turn each role existed;
    this is one of the two numbers the attempt is judged on, and it is measured here rather than
    taken from the session's own account of itself
  * **the verdict** - the A1 predictions in `docs/experiments/001-attempt-A1.md`, answered from the
    record (`--verdict` prints only this)
  * **the production orders** - what the empire *asked for*, from the log's `set_city_production`
    and `purchase_item` calls: the first order in each category and the first turn a siege unit was
    ordered. The diary holds what the empire **has** and the log holds what it **chose**, and the
    doctrine is a claim about the choosing
  * **the doctrine checks** - the claims in `prompts/tactics/01` a log can settle without a judgement
    call: H5 (no ram and no tower is ever bought), H6 (how many cities were asked for units), H4
    (upgrades against new builds) and H1/H2 (the order the roles were asked for). Plus the diary's own
    `ESTABLISHMENT:` line beside the record's numbers, so a self-report the record does not support is
    visible as a MISMATCH instead of being read as fact
  * the capture line - which turn a city was kept, from the tool reply, not from the prose
  * the rule table - `CHECK FAILED [id]` counts, i.e. which doctrine rules the attempt violated
  * the refusal table - STOPPED_MID_PATH and friends, i.e. what the orders cost
  * the process table - tool calls per turn (the attempt's own cost)
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / ".civ6-mcp-data"

# The economy columns, in the order they are worth reading.  Every one of them is a field the diary
# already stores per turn (see civ_mcp.diary); the list is short on purpose.
ECONOMY = (
    "science",
    "culture",
    "gold",
    "gold_per_turn",
    "faith",
    "military",
    "pop",
    "cities",
    "districts",
    "wonders",
    "improvements",
    "territory",
    "techs_completed",
    "civics_completed",
    "tourism",
    "era_score",
)

REFUSALS = (
    "STOPPED_MID_PATH",
    "STOPPED_SHORT",
    "BLOCKED",
    "NO_MOVES",
    "ZOC",
    "TOO FAR",
    "NO_LOS",
    "ERR:",
)

CAPTURE_RE = re.compile(r"\b(KEEP|RAZE|LIBERATE_FOUNDER|LIBERATE_PREVIOUS)\|", re.I)
RULE_RE = re.compile(r"CHECK FAILED \[([a-z0-9\-]+)\]")
ACHIEVED_RE = re.compile(r"CHECK ACHIEVED[^\n]*?\[([a-z0-9\-]+)\]")
ORDER_RE = re.compile(r'"item_name":\s*"([A-Za-z_0-9]+)"')

# The establishment table in `prompts/tactics/01-unit-production.md`, expressed as roles rather than
# unit names: a role is filled by whatever member of its upgrade line the era allows, so the same
# check reads correctly in the Ancient era and in the Industrial one.  `anticav` and `recon` are not
# in the table - they are counted because a session may screen with them, and the review has to be
# able to say so instead of reporting a phantom shortfall.
ESTABLISHMENT = {"siege": 2, "melee": 2, "ram": 1, "ranged": 4, "cavalry": 1}
ROLES: dict[str, tuple[str, ...]] = {
    "siege": ("CATAPULT", "TREBUCHET", "BOMBARD", "ARTILLERY", "ROCKET_ARTILLERY"),
    "melee": (
        "WARRIOR",
        "SWORDSMAN",
        "MAN_AT_ARMS",
        "MUSKETMAN",
        "LINE_INFANTRY",
        "INFANTRY",
        "MECHANICAL_INFANTRY",
    ),
    "anticav": ("SPEARMAN", "PIKEMAN", "AT_CREW"),
    "ram": ("BATTERING_RAM", "SIEGE_TOWER"),
    "ranged": ("SLINGER", "ARCHER", "CROSSBOWMAN", "FIELD_CANNON", "CROUCHING_TIGER"),
    "cavalry": ("HORSEMAN", "KNIGHT", "CAVALRY", "CUIRASSIER", "TANK", "MODERN_ARMOR"),
    "recon": ("SCOUT", "RANGER", "SKIRMISHER"),
}


# --------------------------------------------------------------------------- raw record


def games() -> list[str]:
    """Every game key that has a diary, newest first."""
    out = []
    for path in DATA.glob("diary_*.jsonl"):
        key = path.stem[len("diary_") :]
        out.append((path.stat().st_mtime, key))
    return [key for _, key in sorted(out, reverse=True)]


def diary_rows(game: str) -> dict[int, dict]:
    """The agent's own rows, keyed by turn (last write per turn wins).

    A game with no diary yet - a match that has just been created and not played - is not an error:
    it is an attempt with no rows, and the caller prints exactly that.
    """
    path = DATA / f"diary_{game}.jsonl"
    by_turn: dict[int, dict] = {}
    if not path.exists():
        return by_turn
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not row.get("is_agent"):
                continue
            turn = row.get("turn")
            if isinstance(turn, int):
                by_turn[turn] = row
    return by_turn


def log_rows(game: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(DATA.glob(f"log_{game}_*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    rows.sort(key=lambda r: r.get("ts") or 0)
    return rows


# --------------------------------------------------------------------------- tables


def _first_turn(by_turn: dict[int, dict]) -> int:
    return min(by_turn) if by_turn else 1


def _last_turn(by_turn: dict[int, dict]) -> int:
    return max(by_turn) if by_turn else 1


def boundaries(by_turn: dict[int, dict], step: int) -> list[int]:
    """The turns to print: the first turn, then every multiple of `step`, then the last turn."""
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    turns = [first]
    turns += [t for t in range(((first // step) + 1) * step, last + 1, step)]
    if last not in turns:
        turns.append(last)
    return sorted(set(turns))


def economy_table(by_turn: dict[int, dict], step: int) -> list[dict]:
    rows = []
    for turn in boundaries(by_turn, step):
        row = by_turn[turn]
        entry = {"turn": turn}
        for key in ECONOMY:
            entry[key] = row.get(key)
        entry["units_total"] = row.get("units_total")
        entry["trade"] = row.get("trade_routes")
        entry["exploration_pct"] = row.get("exploration_pct")
        rows.append(entry)
    return rows


def deltas(by_turn: dict[int, dict]) -> dict[str, object]:
    """Total and per-turn change between the first and last turn of the attempt."""
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    a, b = by_turn[first], by_turn[last]
    span = max(1, last - first)
    total: dict[str, float] = {}
    per_turn: dict[str, float] = {}
    for key in ECONOMY:
        try:
            delta = float(b.get(key) or 0) - float(a.get(key) or 0)
        except (TypeError, ValueError):
            continue
        total[key] = round(delta, 2)
        per_turn[key] = round(delta / span, 3)
    return {"span": span, "total": total, "per_turn": per_turn}


def composition(by_turn: dict[int, dict], step: int) -> list[tuple[int, dict]]:
    rows = []
    for turn in boundaries(by_turn, step):
        comp = by_turn[turn].get("unit_composition") or {}
        rows.append((turn, comp))
    return rows


def role_counts(comp: dict | None) -> dict[str, int]:
    """Unit types to the establishment's roles. Civilians and great people fall out on the floor."""
    counts = {role: 0 for role in ROLES}
    for unit, number in (comp or {}).items():
        name = str(unit).upper()
        for role, types in ROLES.items():
            if name in types:
                counts[role] += int(number or 0)
                break
    return counts


def establishment(by_turn: dict[int, dict]) -> dict:
    """The first turn the army matches the table, or how short it stood on the last turn read.

    Every turn is checked, not every tenth: the number this returns is one of the two the attempt is
    judged on, and a ten-turn table cannot see a table that filled on T47.
    """
    last_turn: int | None = None
    short: dict[str, tuple[int, int]] = {}
    for turn in sorted(by_turn):
        counts = role_counts(by_turn[turn].get("unit_composition"))
        short = {r: (counts[r], need) for r, need in ESTABLISHMENT.items() if counts[r] < need}
        last_turn = turn
        if not short:
            return {"turn": turn, "counts": counts, "short": {}, "last_turn": turn}
    counts = role_counts(by_turn[last_turn].get("unit_composition")) if last_turn else {}
    return {"turn": None, "counts": counts, "short": short, "last_turn": last_turn}


def first_role_turn(by_turn: dict[int, dict], role: str) -> int | None:
    """The first turn the empire owned any unit of that role - the weakest form of 'it exists'."""
    for turn in sorted(by_turn):
        if role_counts(by_turn[turn].get("unit_composition")).get(role):
            return turn
    return None


# --------------------------------------------------------------------------- production orders
#
# The diary says what the empire *has*; the log says what it *asked for*. The doctrine is a claim
# about the order of the asking ("anything the assault is missing, first"), so the requests are the
# measurement and the inventory is only the cross-check.

ORDER_TOOLS = ("set_city_production", "purchase_item")
ORDER_CATEGORIES = {"UNIT": "units", "DISTRICT": "districts", "BUILDING": "buildings",
                    "PROJECT": "projects", "WONDER": "wonders"}


def unit_type_of(item_name: str) -> str:
    """`UNIT_CROUCHING_TIGER` -> `CROUCHING_TIGER`; anything else passes through unchanged."""
    name = str(item_name or "").upper()
    return name[len("UNIT_"):] if name.startswith("UNIT_") else name


def role_of_item(item_name: str) -> str | None:
    unit = unit_type_of(item_name)
    for role, types in ROLES.items():
        if unit in types:
            return role
    return None


def orders(rows: list[dict]) -> list[tuple[int, str, str]]:
    """Every production order and purchase in the log, as (turn, item_name, item_type).

    Sorted by **turn**, not by timestamp. The log holds every session of the game - including the
    branches a rollback abandoned - so rows from different sessions interleave and a later timestamp
    can carry an earlier turn. "The first siege unit was ordered on T38" has to mean the earliest
    turn, which list order alone does not give.
    """
    out: list[tuple[int, str, str]] = []
    for row in rows:
        if row.get("tool") not in ORDER_TOOLS:
            continue
        params = row.get("params") or {}
        name = params.get("item_name") or params.get("item") or ""
        if not name:
            match = ORDER_RE.search(json.dumps(params, ensure_ascii=False))
            name = match.group(1) if match else ""
        if name:
            out.append((row.get("turn") or 0, str(name).upper(), str(params.get("item_type") or "")))
    out.sort(key=lambda entry: entry[0])
    return out


def first_order_turn(rows: list[dict], role: str) -> int | None:
    """The first turn a unit of that role was *ordered* - the doctrine's own quantity."""
    for turn, name, _kind in orders(rows):
        if role_of_item(name) == role:
            return turn
    return None


def order_summary(rows: list[dict]) -> dict:
    """The first order in each category, and how many of each the attempt made."""
    counts: collections.Counter = collections.Counter()
    firsts: dict[str, tuple[int, str]] = {}
    for turn, name, kind in orders(rows):
        category = ORDER_CATEGORIES.get(kind.upper(), kind.lower() or "other")
        counts[category] += 1
        firsts.setdefault(category, (turn, name))
    return {"counts": dict(counts), "firsts": firsts, "total": sum(counts.values())}


# --------------------------------------------------------------------------- doctrine checks
#
# `prompts/tactics/01-unit-production.md` makes claims a log can settle without a judgement call:
# a unit that is forbidden to buy, a role that must be asked for first, a city count, an upgrade
# count. They are counts rather than opinions about a turn, which is what makes them checkable.

FORBIDDEN_UNITS = ("BATTERING_RAM", "SIEGE_TOWER")  # H5, human instruction 2026-09-26


def forbidden_orders(rows: list[dict]) -> list[tuple[int, str, str]]:
    """Every order or purchase of a unit the doctrine forbids - each one violates H5."""
    return [
        (turn, name, kind)
        for turn, name, kind in orders(rows)
        if unit_type_of(name) in FORBIDDEN_UNITS
    ]


def military_city_spread(rows: list[dict]) -> dict:
    """How many distinct cities were asked to build a military unit (H6: one war city)."""
    per_city: collections.Counter = collections.Counter()
    for row in rows:
        if row.get("tool") not in ORDER_TOOLS:
            continue
        params = row.get("params") or {}
        if str(params.get("item_type") or "").upper() != "UNIT":
            continue
        if role_of_item(params.get("item_name") or ""):
            per_city[str(params.get("city_id"))] += 1
    return {"cities": len(per_city), "per_city": dict(per_city)}


def upgrades(rows: list[dict]) -> list[tuple[int, str]]:
    """`upgrade_unit` calls in turn order - H4's 'an old unit plus gold is a new unit'."""
    out = [
        (row.get("turn") or 0, str((row.get("params") or {}).get("unit_id") or ""))
        for row in rows
        if row.get("tool") == "upgrade_unit"
    ]
    out.sort(key=lambda entry: entry[0])
    return out


def role_order_sequence(rows: list[dict]) -> list[tuple[int, str, str]]:
    """The first turn each role was asked for as a *unit order*, earliest first (H1/H2)."""
    firsts: dict[str, tuple[int, str]] = {}
    for turn, name, kind in orders(rows):
        if str(kind).upper() != "UNIT":
            continue
        role = role_of_item(name)
        if role and role not in firsts:
            firsts[role] = (turn, name)
    return sorted((turn, role, name) for role, (turn, name) in firsts.items())


SELF_REPORT_RE = re.compile(
    r"ESTABLISHMENT:\s*siege\s*(\d+)\s*/\s*2.*?melee\s*(\d+)\s*/\s*2.*?ram\s*(\d+)\s*/\s*1"
    r".*?ranged\s*(\d+)\s*/\s*4.*?cavalry\s*(\d+)\s*/\s*1",
    re.I | re.S,
)


def self_reports(by_turn: dict[int, dict]) -> list[dict]:
    """The diary's own `ESTABLISHMENT:` lines, beside what the record says for the same turn.

    The task asks the session to write
    `ESTABLISHMENT: siege a/2 melee b/2 ram c/1 ranged d/4 cavalry e/1 at T<n>`. The instrument
    computes the same numbers from `unit_composition`, so the two can be compared - and a claim the
    record does not support is exactly the failure this check exists to catch. A turn without such a
    line is not a failure: the line is requested every ten turns, not every turn.
    """
    out: list[dict] = []
    for turn in sorted(by_turn):
        text = (by_turn[turn].get("reflections") or {}).get("strategic") or ""
        match = SELF_REPORT_RE.search(text)
        if not match:
            continue
        claimed = {role: int(match.group(i)) for i, role in enumerate(ESTABLISHMENT, start=1)}
        actual = role_counts(by_turn[turn].get("unit_composition"))
        out.append(
            {
                "turn": turn,
                "claimed": claimed,
                "actual": actual,
                "mismatch": {
                    role: (claimed[role], actual[role])
                    for role in ESTABLISHMENT
                    if claimed[role] != actual[role]
                },
            }
        )
    return out


def rule_turns(rows: list[dict]) -> dict[str, list[int]]:
    """Which turns each rule was red on, deduplicated: a turn can be evaluated more than once."""
    out: dict[str, set[int]] = collections.defaultdict(set)
    for row in rows:
        for rule in RULE_RE.findall(json.dumps(row, ensure_ascii=False)):
            out[rule].add(row.get("turn") or 0)
    return {rule: sorted(turns) for rule, turns in sorted(out.items())}


def verdict(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> list[tuple[str, bool, str]]:
    """The attempt's predictions, answered from the record.

    The defaults are A1's own limits (`docs/experiments/001-attempt-A1.md`): establishment by T60,
    first city kept by T80, fewer than ten turns under the gold floor before the first city falls,
    and a siege unit early. **They are passed in, not baked in** - a later attempt states its own
    numbers, and a window inside an attempt that is not the attempt's end would otherwise be judged
    against limits it was never meant to meet.

    P1 is deliberately weaker than the doctrine's claim: the diary holds what the empire *owns*, not
    what a queue is building, so this measures the first turn a siege unit existed rather than the
    turn it was ordered.
    """
    est = establishment(by_turn)
    cap = captures(rows)
    keep_turn = min((t for t, _ in cap), default=None)
    horizon = keep_turn if keep_turn is not None else expect_est
    carry = [t for t in rule_turns(rows).get("carrying-capacity", []) if t <= horizon]
    owned = first_role_turn(by_turn, "siege")
    ordered = first_order_turn(rows, "siege")
    early = max(1, expect_est * 3 // 4)
    # The order is the doctrine's own quantity; ownership is the fallback for a siege unit that was
    # bought or inherited rather than queued, and the label says which one answered.
    siege_turn = ordered if ordered is not None else owned
    how = "ordered" if ordered is not None else "owned"
    return [
        (
            f"P1 a siege unit early ({how} one by T{early})",
            bool(siege_turn and siege_turn <= early),
            f"first siege unit {how} {'T' + str(siege_turn) if siege_turn else 'never'}",
        ),
        (
            f"P2 establishment complete by T{expect_est}",
            bool(est["turn"] and est["turn"] <= expect_est),
            f"establishment {'T' + str(est['turn']) if est['turn'] else 'not reached by T' + str(est['last_turn'])}",
        ),
        (
            f"P3 first enemy city kept by T{expect_city}",
            bool(keep_turn and keep_turn <= expect_city),
            f"first keep {'T' + str(keep_turn) if keep_turn else 'none'}",
        ),
        (
            f"P4 gold floor red on <{expect_gold_red} turns",
            len(carry) < expect_gold_red,
            f"{len(carry)} red turn(s) up to T{horizon}",
        ),
    ]


def print_doctrine(by_turn: dict[int, dict], rows: list[dict]) -> None:
    """The doctrine's mechanical claims, and whether the diary's own account matches the record."""
    print("\n-- doctrine checks (from the log; prompts/tactics/01) --")

    forbidden = forbidden_orders(rows)
    if forbidden:
        for turn, name, kind in forbidden:
            print(f"  H5 VIOLATED: {name} ordered on T{turn} ({kind}) - no ram and no tower is bought")
    else:
        print("  H5 clean: neither a ram nor a siege tower was ever ordered or bought")

    spread = military_city_spread(rows)
    if spread["cities"]:
        worst = ", ".join(
            f"city {city}: {count}"
            for city, count in sorted(spread["per_city"].items(), key=lambda kv: -kv[1])[:4]
        )
        print(f"  H6 war cities: {spread['cities']} distinct cities were asked for military units ({worst})")
    else:
        print("  H6 war cities: no military unit has been ordered yet")

    ups = upgrades(rows)
    if ups:
        print(f"  H4 upgrades: {len(ups)} upgrade_unit call(s), first on T{ups[0][0]}")
    else:
        print("  H4 upgrades: none")

    sequence = role_order_sequence(rows)
    if sequence:
        print("  H1/H2 the order of asking: " + ", ".join(f"{role} T{turn}" for turn, role, _ in sequence))
    else:
        print("  H1/H2 the order of asking: no role-mapped unit has been ordered yet")

    reports = self_reports(by_turn)
    if not reports:
        print("  self-report: no ESTABLISHMENT line in the diary yet (it is asked for every ten turns)")
    for report in reports:
        if report["mismatch"]:
            detail = ", ".join(
                f"{role} claimed {claimed} vs {actual} held"
                for role, (claimed, actual) in report["mismatch"].items()
            )
            print(f"  self-report T{report['turn']}: MISMATCH - {detail}")
        else:
            print(f"  self-report T{report['turn']}: agrees with the record")


def print_verdict(
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> None:
    est = establishment(by_turn)
    print("-- establishment (prompts/tactics/01-unit-production.md) --")
    print("  the table: " + "  ".join(f"{role} {need}" for role, need in ESTABLISHMENT.items()))
    if est["turn"]:
        counts = "  ".join(f"{role}={est['counts'].get(role, 0)}" for role in ESTABLISHMENT)
        print(f"  COMPLETE at T{est['turn']}   {counts}")
    else:
        short = "  ".join(f"{role} {have}/{want}" for role, (have, want) in sorted(est["short"].items()))
        print(f"  NOT complete at T{est['last_turn']}   short: {short or '(none)'}")
        if set(est["short"]) == {"ram"}:
            print(
                "    (only the ram is missing - and both ram and siege tower go obsolete at "
                "CIVIC_CIVIL_ENGINEERING, so from that civic on the table's ram line cannot be filled)"
            )
    print(
        f"  screens (melee + anti-cavalry): "
        f"{est['counts'].get('melee', 0) + est['counts'].get('anticav', 0)}"
        f"   recon: {est['counts'].get('recon', 0)}"
    )
    for role in ESTABLISHMENT:
        turn = first_role_turn(by_turn, role)
        print(f"  first {role:<8s}: {'T' + str(turn) if turn else 'never'}")

    summary = order_summary(rows)
    if summary["total"]:
        print("\n-- production orders (what the empire asked for, from the log) --")
        for category, (turn, name) in sorted(summary["firsts"].items(), key=lambda kv: kv[1][0]):
            print(f"  first {category:<10s}: T{turn:<4} {name}")
        print("  counts: " + "  ".join(f"{k} {v}" for k, v in sorted(summary["counts"].items())))
        ordered = first_order_turn(rows, "siege")
        if ordered is not None:
            print(f"  the siege train was first ordered on T{ordered}")
        first_military = next(
            ((turn, name) for turn, name, _kind in orders(rows) if role_of_item(name)), None
        )
        if first_military:
            print(f"  the army began on T{first_military[0]} ({first_military[1]})")

    print_doctrine(by_turn, rows)

    print(f"\n-- verdict (limits: establishment T{expect_est}, city T{expect_city}, "
          f"gold floor {expect_gold_red}) --")
    for name, held, detail in verdict(by_turn, rows, expect_est, expect_city, expect_gold_red):
        print(f"  {'HELD      ' if held else 'FALSIFIED '} {name}  [{detail}]")


def rule_counts(rows: list[dict]) -> tuple[collections.Counter, list[tuple[int, str]]]:
    counts: collections.Counter = collections.Counter()
    achieved: list[tuple[int, str]] = []
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for rule in RULE_RE.findall(blob):
            counts[rule] += 1
        for rule in ACHIEVED_RE.findall(blob):
            achieved.append((row.get("turn") or 0, rule))
    return counts, achieved


def refusal_counts(rows: list[dict]) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for name in REFUSALS:
            n = blob.count(name)
            if n:
                counts[name] += n
    return counts


def captures(rows: list[dict]) -> list[tuple[int, str]]:
    """City keeps/razes, deduplicated - the same reply appears in both `result` and its summary."""
    seen: set[tuple[int, str]] = set()
    out: list[tuple[int, str]] = []
    for row in rows:
        blob = json.dumps(row, ensure_ascii=False)
        for match in CAPTURE_RE.finditer(blob):
            snippet = blob[match.start() : match.end() + 40]
            key = (row.get("turn") or 0, snippet[:28])
            if key in seen:
                continue
            seen.add(key)
            out.append((row.get("turn") or 0, snippet))
    return out


def tool_calls(rows: list[dict]) -> collections.Counter:
    return collections.Counter(row.get("tool") for row in rows)


# --------------------------------------------------------------------------- printing


def print_text(
    game: str,
    step: int,
    by_turn: dict[int, dict],
    rows: list[dict],
    expect_est: int = 60,
    expect_city: int = 80,
    expect_gold_red: int = 10,
) -> None:
    first, last = _first_turn(by_turn), _last_turn(by_turn)
    print(f"== attempt {game}: T{first} -> T{last} ==")
    civ = by_turn[first].get("civ")
    print(f"civ: {civ}  era: {by_turn[last].get('era')}  government: {by_turn[last].get('government')}")

    print("\n-- economy --")
    header = ["turn"] + list(ECONOMY[:8]) + ["districts", "wonders", "improvements"]
    print("  ".join(f"{h:>11s}" for h in header))
    for entry in economy_table(by_turn, step):
        cells = [f"{entry['turn']:>11d}"]
        for key in header[1:]:
            value = entry.get(key)
            cells.append(f"{value:>11}" if value is not None else f"{'-':>11}")
        print("  ".join(cells))

    delta = deltas(by_turn)
    print("\n-- window delta (whole attempt) --")
    print(f"  span: {delta['span']} turns")
    for key, value in delta["total"].items():  # type: ignore[union-attr]
        rate = delta["per_turn"][key]  # type: ignore[index]
        print(f"  {key:>18s}: {value:+9.2f}   ({rate:+.3f}/turn)")

    print("\n-- military composition --")
    for turn, comp in composition(by_turn, step):
        if not comp:
            print(f"  T{turn:<4} (none)")
            continue
        body = ", ".join(f"{name}:{n}" for name, n in sorted(comp.items(), key=lambda kv: -kv[1]))
        print(f"  T{turn:<4} {body}")

    counts, achieved = rule_counts(rows)
    print("\n-- rules (CHECK FAILED counts) --")
    if counts:
        for rule, n in counts.most_common():
            print(f"  {n:>4d}  {rule}")
    else:
        print("  (no failures recorded)")
    if achieved:
        print("  achieved:")
        for turn, rule in achieved:
            print(f"  T{turn:<4} {rule}")

    refusals = refusal_counts(rows)
    print("\n-- refusals --")
    for name, n in refusals.most_common():
        print(f"  {n:>4d}  {name}")

    cap = captures(rows)
    print("\n-- captures --")
    if cap:
        for turn, text in cap:
            print(f"  T{turn:<4} {text.strip()}")
    else:
        print("  (no city captured or kept)")

    calls = tool_calls(rows)
    total = sum(calls.values())
    print("\n-- process --")
    print(f"  tool calls: {total} over {last - first + 1} turns = {total / max(1, last - first + 1):.1f}/turn")
    print("  most used: " + ", ".join(f"{t}:{n}" for t, n in calls.most_common(8)))

    print()
    print_verdict(by_turn, rows, expect_est, expect_city, expect_gold_red)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", help="game key, e.g. china_-1894041591")
    ap.add_argument("--step", type=int, default=10, help="turn step for the tables (default 10)")
    ap.add_argument("--from", dest="start", type=int, help="first turn to report (inclusive)")
    ap.add_argument("--to", dest="end", type=int, help="last turn to report (inclusive)")
    ap.add_argument("--json", action="store_true", help="emit the tables as JSON")
    ap.add_argument("--list", action="store_true", help="list the game keys that have a diary")
    ap.add_argument("--verdict", action="store_true",
                    help="print only the establishment and the verdict")
    ap.add_argument("--expect-est", type=int, default=60,
                    help="the attempt's own establishment deadline, in turns (default 60: A1's)")
    ap.add_argument("--expect-city", type=int, default=80,
                    help="the attempt's own first-city deadline (default 80: A1's)")
    ap.add_argument("--expect-gold-red", type=int, default=10,
                    help="how many turns under the gold floor the attempt allows (default 10: A1's)")
    args = ap.parse_args()

    if args.list or not args.game:
        for key in games():
            by_turn = diary_rows(key)
            print(f"{key}  T{_first_turn(by_turn)} -> T{_last_turn(by_turn)}  ({len(by_turn)} turns)")
        return 0

    sys.stdout.reconfigure(encoding="utf-8")
    by_turn = diary_rows(args.game)
    if not by_turn:
        print(f"no diary rows for {args.game}", file=sys.stderr)
        return 2
    rows = log_rows(args.game)
    if args.start is not None:
        by_turn = {t: r for t, r in by_turn.items() if t >= args.start}
        rows = [r for r in rows if (r.get("turn") or 0) >= args.start]
    if args.end is not None:
        by_turn = {t: r for t, r in by_turn.items() if t <= args.end}
        rows = [r for r in rows if (r.get("turn") or 0) <= args.end]
    if not by_turn:
        print("no diary rows in that turn range", file=sys.stderr)
        return 2

    if args.json:
        counts, achieved = rule_counts(rows)
        payload = {
            "game": args.game,
            "first_turn": _first_turn(by_turn),
            "last_turn": _last_turn(by_turn),
            "economy": economy_table(by_turn, args.step),
            "delta": deltas(by_turn),
            "composition": [{"turn": t, "units": c} for t, c in composition(by_turn, args.step)],
            "rules": dict(counts),
            "rule_turns": rule_turns(rows),
            "achieved": achieved,
            "refusals": dict(refusal_counts(rows)),
            "captures": captures(rows),
            "tool_calls": dict(tool_calls(rows)),
            "establishment": establishment(by_turn),
            "orders": order_summary(rows),
            "doctrine": {
                "forbidden_orders": forbidden_orders(rows),
                "military_city_spread": military_city_spread(rows),
                "upgrades": upgrades(rows),
                "role_order_sequence": role_order_sequence(rows),
                "self_reports": self_reports(by_turn),
            },
            "verdict": [
                {"prediction": name, "held": held, "detail": detail}
                for name, held, detail in verdict(
                    by_turn, rows, args.expect_est, args.expect_city, args.expect_gold_red
                )
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.verdict:
        print(f"== attempt {args.game}: T{_first_turn(by_turn)} -> T{_last_turn(by_turn)} ==")
        print_verdict(by_turn, rows, args.expect_est, args.expect_city, args.expect_gold_red)
        return 0

    print_text(args.game, args.step, by_turn, rows, args.expect_est, args.expect_city, args.expect_gold_red)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
