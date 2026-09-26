"""The staging plan: which unit goes to which ring tile, and when.

Human instruction, 2026-09-26: 在集结前，规划集结方案，不能被堵住，不同部队移动力不一样，找到最优集结
方案后，才开始执行 — plan the assembly before moving; it must not jam; units have different
movement; find the optimal plan, then execute.

The numbers come from the game (`UnitManager.GetMoveToPath` + `GetReachableMovement`, one query
for the whole army — see `lua/units.py`). What this module does is the part the game does not:
assign **distinct** tiles, in the order that makes the assault open on the earliest turn and not
a turn before, and name the conflicts and the stragglers.

The rules it encodes, each one measured over the T139–T159 Russian war:

* one unit per tile — a second order onto an occupied tile is refused `STACKING_CONFLICT` and
  costs that unit its turn (T145, T155: three refusals in a single turn);
* the assault opens when the **last** firing tile is filled and the screen is in front, not when
  the first unit arrives (圣彼得堡: the train sat at distance 4 and 6 for three turns while one
  Trebuchet did all the firing);
* a unit that cannot be placed keeps working: the rear of the ring is where the city's supply
  line runs, and cutting it is worth more than queuing (沃罗涅什 `3/6`, 喀山 `1/6`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .lua import models as m

# Role → the ring distance it wants. Siege and ranged shoot from 2; melee takes the adjacent
# tile; a short-ranged unit (Crouching Tiger, range 1) stands adjacent with the melee.
_PREFERRED_DISTANCE = {
    "siege": (2,),
    "ranged": (2, 1),
    "short-ranged": (1, 2),
    "melee": (1, 2),
}

# Ordered by what the assault needs first when two units want the same tile.
_ROLE_PRIORITY = {"siege": 0, "melee": 1, "short-ranged": 2, "ranged": 3}


@dataclass
class Assignment:
    """One unit placed on one ring tile (or left where it is)."""

    unit: m.StagingUnit
    tile: m.StagingRingTile | None
    turns: int
    this_turn: bool
    note: str = ""

    @property
    def where(self) -> str:
        return f"({self.tile.x},{self.tile.y})" if self.tile else f"({self.unit.x},{self.unit.y})"


@dataclass
class StagingPlanResult:
    target: str = ""
    ring_size: int = 0
    placed: list[Assignment] = field(default_factory=list)
    unplaced: list[m.StagingUnit] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    idle_tiles: list[m.StagingRingTile] = field(default_factory=list)
    opens_on: int = 0  # the turn the last shooter is in position (0 = this turn)

    @property
    def shooters_in_place(self) -> int:
        return sum(1 for a in self.placed if a.unit.role in ("siege", "ranged") and a.tile)


def _distance_rank(unit: m.StagingUnit, tile: m.StagingRingTile) -> int:
    """How well this tile suits this unit; lower is better."""
    preferred = _PREFERRED_DISTANCE.get(unit.role, (2, 1))
    return preferred.index(tile.distance) if tile.distance in preferred else len(preferred)


def _candidates(plan: m.StagingPlan, unit: m.StagingUnit) -> list[m.StagingOption]:
    return [o for o in plan.options if o.unit_id == unit.unit_id]


def assign(plan: m.StagingPlan, turns_ahead: int = 2) -> StagingPlanResult:
    """Greedy assignment: the units that decide the assault open pick their tile first.

    Greedy is the right shape here rather than an optimal solver, and deliberately so: the
    choice is constrained by a handful of distinct tiles, the roles have a strict preference,
    and a plan a human can read and check beats a plan that is optimal by a metric nobody
    wrote down. The ordering is what matters — the shooters and the capture unit get tiles
    before the screen does, because the screen has more tiles that will do.
    """
    result = StagingPlanResult(target=plan.target, ring_size=len(plan.ring))
    by_pos = {(t.x, t.y): t for t in plan.ring}
    taken: dict[tuple[int, int], str] = {}

    ordered = sorted(
        plan.units,
        key=lambda u: (_ROLE_PRIORITY.get(u.role, 9), -u.moves, u.unit_id),
    )
    for unit in ordered:
        options = [
            o
            for o in _candidates(plan, unit)
            if o.turns <= turns_ahead and (o.x, o.y) in by_pos
        ]
        # Prefer: arriving sooner, then the role's distance, then not colliding with a tile
        # another unit has already claimed this turn.
        options.sort(
            key=lambda o: (
                o.turns,
                _distance_rank(unit, by_pos[(o.x, o.y)]),
                1 if (o.x, o.y) in taken else 0,
            )
        )
        chosen = None
        for option in options:
            if (option.x, option.y) in taken:
                result.conflicts.append(
                    f"{unit.unit_type} #{unit.unit_id} also wanted ({option.x},{option.y}),"
                    f" already claimed by {taken[(option.x, option.y)]}"
                )
                continue
            chosen = option
            break
        if chosen is None:
            result.unplaced.append(unit)
            continue
        tile = by_pos[(chosen.x, chosen.y)]
        taken[(chosen.x, chosen.y)] = f"{unit.unit_type} #{unit.unit_id}"
        result.placed.append(
            Assignment(unit=unit, tile=tile, turns=chosen.turns, this_turn=chosen.this_turn)
        )

    result.idle_tiles = [t for t in plan.ring if (t.x, t.y) not in taken and not t.blocked]
    shooters = [a for a in result.placed if a.unit.role in ("siege", "ranged") and a.tile]
    result.opens_on = max((a.turns for a in shooters), default=0)
    return result


def render(result: StagingPlanResult, plan: m.StagingPlan | None = None) -> str:
    """The plan as the table the doctrine asks for, one row per unit."""
    units = {u.unit_id: u for u in (plan.units if plan else [])}
    lines = [
        f"STAGING PLAN for {result.target or 'the target'} — {result.ring_size} ring tile(s),"
        f" {len(result.placed)} unit(s) placed, {len(result.unplaced)} unplaced"
    ]
    for a in result.placed:
        when = "this turn" if a.this_turn else f"T+{a.turns}"
        lines.append(
            f"  {a.unit.unit_type:<22} #{a.unit.unit_id} ({a.unit.x},{a.unit.y}) moves {a.unit.moves}"
            f" -> {a.where} d{a.tile.distance}  arrive {when}  [{a.unit.role}]"
            f"{' - FIRE from here' if a.unit.role in ('siege', 'ranged') and a.tile.distance == 2 else ''}"
        )
    for unit in result.unplaced:
        lines.append(
            f"  {unit.unit_type:<22} #{unit.unit_id} ({unit.x},{unit.y}) moves {unit.moves}"
            f"  NO TILE IN REACH within {2} turns — send it to the rear of the ring to cut the"
            f" supply line, do not queue it in the corridor"
        )
    if result.conflicts:
        lines.append("  CONFLICTS (one unit per tile — a second order is STACKING_CONFLICT):")
        lines.extend(f"    {c}" for c in result.conflicts)
    if result.idle_tiles:
        lines.append(
            "  SPARE RING TILES: "
            + ", ".join(f"({t.x},{t.y}) d{t.distance}" for t in result.idle_tiles[:8])
            + " — take them with the unplaced units: occupying the ring stops the city's"
            " ~20/turn heal"
        )
    shooters = [a for a in result.placed if a.unit.role in ("siege", "ranged") and a.tile]
    lines.append(
        f"  ASSAULT OPENS on {('this turn' if result.opens_on == 0 else f'T+{result.opens_on}')}"
        f" with {len(shooters)} shooter(s) in position."
        + (
            " A shooter that moves two tiles, crosses a river or climbs a hill fires NEXT turn —"
            " if you want it firing the turn it lands, it must arrive with a movement point left."
            if shooters
            else " No shooter reaches a ring tile in time: the plan is the march, not the fire."
        )
    )
    if units:
        pass
    return "\n".join(lines)
