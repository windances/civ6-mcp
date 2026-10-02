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

from . import los
from .lua import models as m

# The roles that shoot from the ring, and therefore the roles a line-of-sight verdict matters for.
# `short-ranged` (a Crouching Tiger, range 1) is not here: it fires from the adjacent tile, where
# nothing can stand between it and the target.
_SHOOTERS = ("siege", "ranged")

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

# What one city's ring can usefully seat (the directive's establishment): up to 3 siege, 2 melee,
# 4 ranged - and the cavalry is counted in the melee bucket, because both are capture-capable
# front-line units and the plan does not need to tell them apart. Everything above these caps
# is surplus, and surplus has a job: see the ladder in `render`. These are **caps, not quotas**:
# siege is 1-3 by the arithmetic (human instruction 2026-09-30: 攻城使用2或3辆投石车，根据实际情况
# 而定，不写死，当地面和远程部队攻击力够的话，一辆也可以 - two or three by the situation, and one is
# enough when the ground and the ranged line cover it), so a plan with one gun is complete.
_ESTABLISHMENT = {"siege": 3, "melee": 3, "ranged": 3, "short-ranged": 1}


@dataclass
class Assignment:
    """One unit placed on one ring tile (or left where it is)."""

    unit: m.StagingUnit
    tile: m.StagingRingTile | None
    turns: int
    this_turn: bool
    note: str = ""
    # The line-of-sight verdict for a shooter's tile (`civ_mcp.los`), None for everyone else. A
    # ring tile that cannot fire is a walk, not a firing position: the row used to claim
    # `FIRE from here` for every distance-2 tile, which the map itself can answer.
    los: los.Verdict | None = None
    # True for a gun in the ring with no movement left: it cannot shoot this turn, so it is not a
    # shooter in position however clear its line is (`tactics/04`: arriving costs the shot).
    spent: bool = False
    # The route the unit takes there: the path's movement cost and how many turns it ends inside an
    # enemy zone of control (manual:875), with the first such tile and turn. -1/None means the
    # server did not report it. The arrival turn already counts a ZOC stop; these fields are what
    # lets the row say *why* the turn was spent.
    cost: int = -1
    zoc: int = -1
    zoc_at: tuple[int, int, int] | None = None

    @property
    def where(self) -> str:
        return f"({self.tile.x},{self.tile.y})" if self.tile else f"({self.unit.x},{self.unit.y})"


@dataclass
class StagingPlanResult:
    target: str = ""
    ring_size: int = 0
    # A camp is the same plan against a different object (no HP, no walls, no supply line): only the
    # surplus labels and the closing line change. See `lua/models.StagingPlan.camp`.
    camp: bool = False
    placed: list[Assignment] = field(default_factory=list)
    unplaced: list[m.StagingUnit] = field(default_factory=list)
    surplus: list[Assignment] = field(default_factory=list)
    recon: list[m.StagingUnit] = field(default_factory=list)
    rotation: list[Assignment] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    idle_tiles: list[m.StagingRingTile] = field(default_factory=list)
    opens_on: int = 0  # the turn the last shooter is in position (0 = this turn)
    supply_cut: int = 0
    supply_total: int = 0

    @property
    def shooters_in_place(self) -> int:
        """Shooters on a tile they can actually fire from, this turn.

        A shooter whose tile the map rules out is **not** in position, whatever its distance, and
        neither is a gun with no movement left: it is standing in the ring and cannot shoot again
        this turn, which is a different fact from a blocked line.
        """
        return sum(
            1
            for a in self.placed
            if a.unit.role in _SHOOTERS
            and a.tile
            and not a.spent
            and not (a.los and a.los.ruled_out)
        )


def _los_rank(unit: m.StagingUnit, tile: m.StagingRingTile, plan: m.StagingPlan) -> int:
    """0 for a firing tile the map does not rule out, 2 for one it says cannot fire.

    Only a **ruled-out** tile is demoted, and that is deliberate. A `maybe` (two candidate lines
    with one clear) and an unread tile both keep their distance preference, because the doctrine's
    choice of range 2 must not be overturned by a question the map cannot answer - and a server
    that sends no sight data has to keep the plan it produced before this verdict existed. What
    the verdict changes is that a gun is never *sent* to a tile that provably cannot shoot: it
    ranks below a tile that works, including the adjacent one.
    """
    if unit.role not in _SHOOTERS:
        return 0
    verdict = los.line_of_sight(tile, engine=plan.engine_fire.get(unit.unit_id))
    return 2 if verdict.ruled_out else 0


def _distance_rank(unit: m.StagingUnit, tile: m.StagingRingTile) -> int:
    """How well this tile suits this unit; lower is better."""
    preferred = _PREFERRED_DISTANCE.get(unit.role, (2, 1))
    return preferred.index(tile.distance) if tile.distance in preferred else len(preferred)


def _supply_hexes(ring: list[m.StagingRingTile]) -> list[m.StagingRingTile]:
    """The hexes the city draws its supply line from: every adjacent hex.

    The manual's rule (`manual:1066-1085`): a city heals while **any** adjacent hex is outside
    our zone of control, and a hex is cut when one of our fighting units stands on it or beside
    it. So the distance-1 ring tiles are the ones that matter, and one unit covers up to three
    of them - which is why closing a six-hex ring takes about three units, not six.
    """
    return [t for t in ring if t.distance == 1 and not t.blocked]


def supply_coverage(ring: list[m.StagingRingTile], units: list[m.StagingUnit]) -> tuple[int, int]:
    """(hexes cut, hexes total) if the listed units stand where they are.

    Mirrors the coverage test in `build_capture_check_query`: a hex counts as cut when one of
    our fighting units stands on it or on a tile adjacent to it.
    """
    hexes = _supply_hexes(ring)
    if not hexes:
        return 0, 0
    positions = {(u.x, u.y) for u in units}
    cut = 0
    for tile in hexes:
        if (tile.x, tile.y) in positions:
            cut += 1
            continue
        neighbours = {
            (tile.x + dx, tile.y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if (dx, dy) != (0, 0)
        }
        if positions & neighbours:
            cut += 1
    return cut, len(hexes)


def _candidates(plan: m.StagingPlan, unit: m.StagingUnit) -> list[m.StagingOption]:
    return [o for o in plan.options if o.unit_id == unit.unit_id]


def assign(plan: m.StagingPlan, turns_ahead: int = 2, rotate: bool = True) -> StagingPlanResult:
    """Greedy assignment: the units that decide the assault open pick their tile first.

    Greedy is the right shape here rather than an optimal solver, and deliberately so: the
    choice is constrained by a handful of distinct tiles, the roles have a strict preference,
    and a plan a human can read and check beats a plan that is optimal by a metric nobody
    wrote down. The ordering is what matters — the shooters and the capture unit get tiles
    before the screen does, because the screen has more tiles that will do.
    """
    result = StagingPlanResult(target=plan.target, ring_size=len(plan.ring))
    result.camp = getattr(plan, "camp", False)
    by_pos = {(t.x, t.y): t for t in plan.ring}
    taken: dict[tuple[int, int], str] = {}

    ordered = sorted(
        plan.units,
        key=lambda u: (_ROLE_PRIORITY.get(u.role, 9), -u.moves, u.unit_id),
    )
    # The assault force first, and only as many as the city needs: the directive's establishment
    # is 3 siege, 2 melee + 1 cavalry, 4 ranged. Everyone above that is surplus, and surplus
    # does not take a firing tile from a unit that needs one.
    left = dict(_ESTABLISHMENT)
    assault: list[m.StagingUnit] = []
    surplus_units: list[m.StagingUnit] = []
    recon: list[m.StagingUnit] = []
    for unit in ordered:
        if unit.role == "recon":
            # A Scout is not an assault unit: filing it as melee sent one to a ring tile
            # adjacent to the city on the first live run of this query.
            recon.append(unit)
        elif left.get(unit.role, 0) > 0:
            left[unit.role] -= 1
            assault.append(unit)
        else:
            surplus_units.append(unit)
    result.recon = recon

    # Rotation before placement (human instruction 2026-09-26: 多余部队还可以替换残血的扛伤部队).
    # A front-line unit at half health or worse does not take a ring tile — it is the unit the
    # city's strike or the enemy's field army kills (a 55 HP Horseman died attacking a walled city
    # at T154; a Knight went 52 -> 6 in one blow at T151). Its slot goes to the freshest spare of
    # the same role, and the wounded unit withdraws to heal (20/turn in a city, 15 in our
    # territory, 5 where it was hit).
    if rotate:
        for unit in list(assault):
            if unit.role not in ("melee", "short-ranged") or not unit.wounded:
                continue
            assault.remove(unit)
            left[unit.role] = left.get(unit.role, 0) + 1  # free the establishment slot
            relief = next((s for s in surplus_units if s.role == unit.role and not s.wounded), None)
            if relief is not None:
                surplus_units.remove(relief)
                assault.append(relief)
            result.rotation.append(
                Assignment(
                    unit=unit,
                    tile=None,
                    turns=0,
                    this_turn=False,
                    note=relief.unit_type if relief is not None else "",
                )
            )

    for unit in assault:
        options = [
            o
            for o in _candidates(plan, unit)
            if o.turns <= turns_ahead and (o.x, o.y) in by_pos
        ]
        # Prefer: arriving sooner, then a tile this unit can actually fire from, then the role's
        # distance, then not colliding with a tile another unit has already claimed this turn.
        # Line of sight comes before distance on purpose: a distance-2 tile with a wood between it
        # and the city is worth less to a Catapult than the adjacent tile it *can* shoot from, and
        # the measured 阿斯特拉罕 assault was lost to exactly that - one usable distance-2 tile.
        options.sort(
            key=lambda o: (
                o.turns,
                _los_rank(unit, by_pos[(o.x, o.y)], plan),
                _distance_rank(unit, by_pos[(o.x, o.y)]),
                # Two tiles that take the same number of turns are not equal: one may end a turn
                # inside an enemy zone of control on the way (manual:875), which is the difference
                # between a gun that arrives on time and one that arrives a turn late.
                max(o.zoc, 0),
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
        # A gun with no movement left is in the ring and cannot shoot this turn: the engine said so
        # (`CANFIRE ... spent`), and it is not a line-of-sight verdict, so the map rule still
        # answers for the tile - but the row and the count treat it as not firing this turn.
        spent = unit.unit_id in getattr(plan, "engine_spent", set())
        verdict = (
            los.line_of_sight(tile, engine=plan.engine_fire.get(unit.unit_id))
            if unit.role in _SHOOTERS
            else None
        )
        result.placed.append(
            Assignment(
                unit=unit,
                tile=tile,
                turns=chosen.turns,
                this_turn=chosen.this_turn,
                los=verdict,
                spent=spent,
                cost=chosen.cost,
                zoc=chosen.zoc,
                zoc_at=chosen.zoc_at,
            )
        )

    # The surplus, in the order the employment ladder in `render` gives: the supply hexes of
    # the ring first (each unit cuts the hex it stands on plus its ring neighbours), then depth
    # behind the ring for whoever is left.
    # The surplus, in the order the employment ladder in `render` gives. Supply hexes are for
    # units that can take a hit (they are adjacent to the city, inside its strike): melee,
    # anti-cavalry and cavalry - never a siege or ranged unit, which dies there. Then forward
    # staging toward the next objective, then depth behind the ring. An assault unit that could
    # not reach a ring tile is offered the next objective too, and only reported as unplaced if
    # there is nowhere for it to go.
    supply_tiles = [t for t in _supply_hexes(plan.ring) if (t.x, t.y) not in taken]
    supply_positions = {(t.x, t.y) for t in supply_tiles}
    current_ring = {(t.x, t.y) for t in plan.ring}
    no_tile = list(result.unplaced)
    result.unplaced = []

    def forward_option(unit: m.StagingUnit) -> m.StagingOption | None:
        candidates = sorted(
            (
                o
                for o in plan.next_options
                if o.unit_id == unit.unit_id
                and o.turns <= turns_ahead
                and (o.x, o.y) not in current_ring
                and (o.x, o.y) not in taken
            ),
            key=lambda o: (o.turns, max(o.zoc, 0), o.x, o.y),
        )
        return candidates[0] if candidates else None

    def place_forward(unit: m.StagingUnit) -> bool:
        option = forward_option(unit)
        if option is None:
            return False
        tile = next((t for t in plan.next_ring if (t.x, t.y) == (option.x, option.y)), None)
        if tile is None:
            return False
        taken[(option.x, option.y)] = f"{unit.unit_type} #{unit.unit_id} (advance)"
        result.surplus.append(
            Assignment(
                unit=unit,
                tile=tile,
                turns=option.turns,
                this_turn=option.this_turn,
                note="ADVANCE",
                cost=option.cost,
                zoc=option.zoc,
                zoc_at=option.zoc_at,
            )
        )
        return True

    def place_kill(unit: m.StagingUnit) -> bool:
        """Send a MOBILE surplus unit to a tile beside the unit we are eliminating.

        Human instruction 2026-09-26: 多余部队里机动性高的部队还可以集火消灭传教士. The damage is
        not the problem — a missionary has no combat strength and dies to one attack, or to a
        single `condemn` command from an adjacent military unit while at war. The problem is
        **catching** it: a religious unit that sees the column steps away, so the units sent are
        the ones with the movement to close (3+ moves: cavalry above all, which ignores zones of
        control) and the extras take its other neighbours so it has nowhere to step.
        """
        if unit.moves < 3 or not plan.kill_options:
            return False
        candidates = sorted(
            (o for o in plan.kill_options if o.unit_id == unit.unit_id and (o.x, o.y) not in taken),
            key=lambda o: (o.turns, max(o.zoc, 0), not o.this_turn, o.x, o.y),
        )
        if not candidates:
            return False
        option = candidates[0]
        tile = next((t for t in plan.kill_ring if (t.x, t.y) == (option.x, option.y)), None)
        if tile is None:
            return False
        taken[(option.x, option.y)] = f"{unit.unit_type} #{unit.unit_id} (kill)"
        result.surplus.append(
            Assignment(
                unit=unit,
                tile=tile,
                turns=option.turns,
                this_turn=option.this_turn,
                note="KILL",
                cost=option.cost,
                zoc=option.zoc,
                zoc_at=option.zoc_at,
            )
        )
        return True

    for unit in surplus_units:
        chosen = None
        if unit.role == "melee":
            for option in sorted(
                (o for o in _candidates(plan, unit) if o.turns <= turns_ahead),
                key=lambda o: (
                    o.turns,
                    max(o.zoc, 0),
                    0 if (o.x, o.y) in supply_positions else 1,
                ),
            ):
                if (option.x, option.y) in taken:
                    continue
                if (option.x, option.y) in supply_positions:
                    chosen = option
                    break
        if chosen is not None:
            tile = by_pos[(chosen.x, chosen.y)]
            taken[(chosen.x, chosen.y)] = f"{unit.unit_type} #{unit.unit_id} (supply)"
            supply_positions.discard((chosen.x, chosen.y))
            result.surplus.append(
                Assignment(
                    unit=unit,
                    tile=tile,
                    turns=chosen.turns,
                    this_turn=chosen.this_turn,
                    note="SUPPLY",
                    cost=chosen.cost,
                    zoc=chosen.zoc,
                    zoc_at=chosen.zoc_at,
                )
            )
            continue
        if place_kill(unit):
            continue
        if place_forward(unit):
            continue
        result.surplus.append(Assignment(unit=unit, tile=None, turns=0, this_turn=False))

    for unit in no_tile:
        if place_kill(unit):
            continue
        if not place_forward(unit):
            result.unplaced.append(unit)

    cut, total = supply_coverage(
        plan.ring, [a.unit for a in result.placed + result.surplus]
    )
    result.supply_cut, result.supply_total = cut, total
    result.idle_tiles = [t for t in plan.ring if (t.x, t.y) not in taken and not t.blocked]
    shooters = [
        a
        for a in result.placed
        if a.unit.role in ("siege", "ranged") and a.tile and not (a.los and a.los.ruled_out)
    ]
    # The assault opens when the last shooter can fire; a gun that is standing there spent fires
    # next turn, so it counts as one turn later rather than as ready now.
    result.opens_on = max(
        (a.turns + (1 if a.spent else 0) for a in shooters),
        default=0,
    )
    return result


def _rally_option(plan: m.StagingPlan | None, unit: m.StagingUnit, rally_tiles: dict):
    """The unit's best **assembly** tile outside the city's reach, if the plan found one.

    The doctrine stages outside the enemy's reach and then advances as one body - ``tactics/04``
    step 1 puts the rally *three tiles or more* from the target, because a city's strike and a
    Catapult both reach two. The ring assignment is the tile a unit **fires from**; this is the tile
    it should form up on first, and it comes from the same game pathing as everything else here.

    It exists because the plan was followed literally and the cost is measured: at 底比斯 the
    assault opened with 2 of 3 shooters in position and at 亚历山大 with **2 of 5**, the rest still
    walking. Returns ``None`` when no assembly tile is in reach, which is itself worth printing - a
    unit already standing on the ring has no assembly step left.

    The tiles come from ``plan.rally_ring`` / ``plan.rally_options`` (the Lua's distance-3 ring),
    **not** from the firing ring: nothing is ever assigned to an assembly tile, and a server that
    predates the rally ring sends neither and gets exactly the old behaviour.
    """
    if plan is None:
        return None
    best = None
    for option in getattr(plan, "rally_options", []) or []:
        if option.unit_id != unit.unit_id:
            continue
        tile = rally_tiles.get((option.x, option.y))
        if tile is None or tile.blocked:
            continue
        key = (option.turns, max(option.zoc, 0), option.path_len, tile.distance)
        if best is None or key < best[0]:
            best = (key, option, tile)
    return best


def _fire_note(assignment: Assignment) -> str:
    """The firing verdict, on the row that assigns the tile."""
    verdict = assignment.los
    if assignment.spent:
        return (
            " - NO SHOT THIS TURN: no movement left (it has already fired or moved), so it fires"
            " next turn - arriving costs the shot (`tactics/04`)"
        )
    if verdict is None or assignment.unit.role not in _SHOOTERS:
        return ""
    if verdict.state == los.FIRE:
        return " - FIRE from here" + (
            " (the game's own answer)" if verdict.source == "engine" else ""
        )
    if verdict.state == los.MAYBE:
        blockers = "; ".join(verdict.blockers)
        return f" - FIRE? one line is clear, another crosses {blockers}" if blockers else " - FIRE?"
    if verdict.state == los.NO:
        blockers = "; ".join(verdict.blockers)
        return f" - NO LINE OF SIGHT: {blockers}" if blockers else f" - NO LINE OF SIGHT: {verdict.reason}"
    return " - LOS unread: the map sent no sight data for this tile (server too old)"


def _route_note(assignment: Assignment) -> str:
    """What the march costs and where the engine ends a turn on the way, on the row that assigns it.

    Distance is not movement: a tile costs what the map says (Hills 2, Woods 2, Forest-on-Hills 3)
    and entering a tile in an enemy zone of control expends the rest of that turn's movement
    (manual:875; light and heavy cavalry are exempt, manual:735-737). The arrival turn on the row
    already counts both - this line says *why* the number is what it is, so the stop can be routed
    around instead of reported as a surprise. Measured before this existed: 232 `STOPPED_MID_PATH`
    results over T228-T299.
    """
    if assignment.zoc is None or assignment.zoc < 0:
        return ""
    if assignment.zoc == 0:
        if assignment.cost is not None and assignment.cost > 0:
            return f"  cost {assignment.cost} mp, no visible ZOC on the way"
        return ""
    where = (
        f"({assignment.zoc_at[0]},{assignment.zoc_at[1]}) on turn +{assignment.zoc_at[2]}"
        if assignment.zoc_at
        else "on the way"
    )
    return (
        f"  ZOC STOP at {where}: entering an enemy zone of control spends the rest of that turn's"
        f" movement (manual:875) - already counted in the arrival turn above, so route around it or"
        f" accept it"
    )


def _spare_firing_tiles(plan: m.StagingPlan | None, result: StagingPlanResult, unit: m.StagingUnit):
    """(turns, tile) for the ring tiles this unit can reach and the map says it can fire from.

    The answer to "so where does this gun stand instead": a tile nobody has claimed, with a clear
    line to the target, in the order it can get there.
    """
    if plan is None:
        return []
    claimed = {
        (a.tile.x, a.tile.y)
        for a in result.placed + result.surplus + result.rotation
        if a.tile is not None
    }
    ring_by_pos = {(t.x, t.y): t for t in plan.ring}
    found = []
    for option in plan.options:
        if option.unit_id != unit.unit_id or (option.x, option.y) in claimed:
            continue
        tile = ring_by_pos.get((option.x, option.y))
        if tile is None or tile.blocked:
            continue
        if los.line_of_sight(tile, engine=plan.engine_fire.get(unit.unit_id)).can_fire:
            found.append((option.turns, tile))
    found.sort(key=lambda pair: (pair[0], pair[1].distance))
    return found


def render(result: StagingPlanResult, plan: m.StagingPlan | None = None) -> str:
    """The plan as the table the doctrine asks for, one row per unit."""
    units = {u.unit_id: u for u in (plan.units if plan else [])}
    ring_tiles = {(t.x, t.y): t for t in (plan.ring if plan else [])}
    rally_tiles = {(t.x, t.y): t for t in (getattr(plan, "rally_ring", []) or [])}
    what = f"the camp at {result.target}" if result.camp else (result.target or "the target")
    # How many of the ring's tiles actually have a shot at the target. `18 firing tiles` is a count
    # of tiles; the number that matters is the one with a clear line - at 阿斯特拉罕 it was one.
    sight_data = any(t.between for t in (plan.ring if plan else []))
    los_tiles = (
        sum(
            1
            for t in (plan.ring if plan else [])
            if not t.blocked and los.line_of_sight(t).state == los.FIRE
        )
        if sight_data
        else 0
    )
    lines = [
        f"STAGING PLAN for {what} — {result.ring_size} firing tile(s)"
        + (f", {los_tiles} with line of sight" if sight_data else "")
        + (f", {len(rally_tiles)} assembly tile(s) at d3" if rally_tiles else "")
        + f", {len(result.placed)} unit(s) placed, {len(result.unplaced)} unplaced"
    ]
    if any(_rally_option(plan, a.unit, rally_tiles) for a in result.placed):
        lines.append(
            "  ASSEMBLY FIRST: `RALLY x,y dN` is a tile outside the city's two-tile strike to form"
            " up on, before the ring tile it fires from. Walking straight onto the ring is how an"
            " assault opens with half the train in position — measured T194 (2/3 shooters) and"
            " T215 (2/5, one Bombard still 21 tiles away)."
        )
    # The order the move calls go in, which no single row says. A column ordered nearest-first queues
    # behind itself: measured T228-T299, 232 `STOPPED_MID_PATH` results across 72 turns, and every
    # plan that left units unplaced named 6-9 of them.
    ordered = sorted(
        (a for a in result.placed if a.tile),
        key=lambda a: (-a.tile.distance, a.turns, a.unit.unit_id),
    )
    if len(ordered) > 1:
        lines.append(
            "  ISSUE THE MOVE CALLS IN THIS ORDER - furthest ring tile first, nearest last: "
            + " -> ".join(f"#{a.unit.unit_id}" for a in ordered)
            + ". Re-read `get_units` between them: a unit that stops mid-path blocks the one behind"
            " it, which is how 232 `STOPPED_MID_PATH` results happened over T228-T299."
        )
    for a in result.placed:
        when = "this turn" if a.this_turn else f"T+{a.turns}"
        rally = _rally_option(plan, a.unit, rally_tiles)
        leg = (
            f"  RALLY ({rally[1].x},{rally[1].y}) d{rally[2].distance} T+{rally[1].turns}"
            if rally
            else ""
        )
        lines.append(
            f"  {a.unit.unit_type:<22} #{a.unit.unit_id} ({a.unit.x},{a.unit.y}) moves {a.unit.moves}"
            f" -> {a.where} d{a.tile.distance}  arrive {when}  [{a.unit.role}]"
            f"{_fire_note(a)}"
            f"{_route_note(a)}"
            f"{leg}"
        )
    for unit in result.unplaced:
        far = unit.distance > 6
        lines.append(
            f"  {unit.unit_type:<22} #{unit.unit_id} ({unit.x},{unit.y}) moves {unit.moves}"
            + (
                f"  TOO FAR to matter for this assault (d{unit.distance}) — leave it on its own"
                f" task; it is not part of this plan."
                if far
                else f"  NO TILE IN REACH within {2} turns — send it to the rear of the ring to"
                f" cut the supply line, do not queue it in the corridor"
            )
        )
    for unit in result.recon:
        lines.append(
            f"  {unit.unit_type:<22} #{unit.unit_id} ({unit.x},{unit.y}) moves {unit.moves}"
            f"  RECON — never a ring tile: it has CS {unit.strength or '~10'} and dies to the"
            f" city's strike. Keep it scouting; the plan does not spend it."
        )
    if result.surplus:
        on_supply = [a for a in result.surplus if a.note == "SUPPLY"]
        advancing = [a for a in result.surplus if a.note == "ADVANCE"]
        killing = [a for a in result.surplus if a.note == "KILL"]
        depth = [a for a in result.surplus if a.note not in ("SUPPLY", "ADVANCE", "KILL")]
        lines.append(
            "  SURPLUS (the ring seats up to 3 siege / 3 melee-or-cavalry / 4 ranged - siege being"
            " 1-3 by the arithmetic, so one gun is a complete plan - and everything above the caps"
            " has a job, which is not a firing tile):"
        )
        for a in on_supply:
            if result.camp:
                lines.append(
                    f"    {a.unit.unit_type:<20} #{a.unit.unit_id} -> {a.where} d{a.tile.distance}"
                    f"  HOLD THE RING (a camp has no supply line to cut — this is where the second"
                    f" attacker stands and where the guard is stopped from stepping onto the camp)"
                    f"{_route_note(a)}"
                )
            else:
                lines.append(
                    f"    {a.unit.unit_type:<20} #{a.unit.unit_id} -> {a.where} d{a.tile.distance}"
                    f"  CUT THE SUPPLY LINE (stands on a hex the city heals from)"
                    f"{_route_note(a)}"
                )
        for a in killing:
            lines.append(
                f"    {a.unit.unit_type:<20} #{a.unit.unit_id} -> {a.where}"
                f"  HUNT THE MISSIONARY{' this turn' if a.this_turn else f' in {a.turns} turn(s)'}"
                f" — mobile unit only: one attacker kills it, and the extras take its other"
                f" neighbours so it cannot step away; `condemn` is one command from adjacent"
                f" (while at war, task 008)"
                f"{_route_note(a)}"
            )
        for a in advancing:
            lines.append(
                f"    {a.unit.unit_type:<20} #{a.unit.unit_id} -> {a.where} d{a.tile.distance}"
                f"  ADVANCE toward the next objective"
                f"{' this turn' if a.this_turn else f' in {a.turns} turn(s)'} — out of this city's"
                f" strike, and that much less marching when the next siege opens"
                f"{_route_note(a)}"
            )
        for a in depth:
            lines.append(
                f"    {a.unit.unit_type:<20} #{a.unit.unit_id}  DEPTH: hold behind the ring, out of"
                f" the city's two-tile strike — replace a screen casualty, or take the road the"
                f" enemy's reinforcements use"
            )
        if result.supply_total and not result.camp:
            lines.append(
                f"    supply hexes cut after this plan: {result.supply_cut}/{result.supply_total}"
                + (
                    " — the city stops healing"
                    if result.supply_cut >= result.supply_total
                    else " — it still heals ~20/turn, so the uncut hexes are the next units' work"
                )
            )
        lines.append(
            "    Ladder if there are more: supply hexes > the reinforcement road > forward staging"
            " toward the NEXT city or barbarian camp (pass its tile to the plan; the march is what"
            " the last deadline was lost to) > depth behind the ring > the garrison of a city we"
            " just took > pillage (cavalry ignores ZOC) > nothing. Never stack them on the ring:"
            " our own units are the usual thing blocking our own firing tiles."
        )
    if result.rotation:
        lines.append(
            "  ROTATION (a wounded front-line unit yields its slot to a fresh one and heals):"
        )
        for a in result.rotation:
            relief = a.note or "no fresh unit of the same role available"
            lines.append(
                f"    {a.unit.unit_type:<20} #{a.unit.unit_id} ({a.unit.hp}/{a.unit.max_hp} hp)"
                f"  WITHDRAW to heal — relieved by {relief}"
                + (
                    ""
                    if a.note
                    else " — no relief, and the enemy is stronger here than we are: break off"
                    " rather than feed the next unit in"
                )
            )
        lines.append(
            "    Order matters: put the relief on the tile the same turn the wounded unit leaves,"
            " attack with the wounded one BEFORE it withdraws if it has a target, and send it where"
            " it heals fastest (20/turn in a city, 15 in our territory, 5 where it was hit)."
        )
    if result.conflicts:
        lines.append("  CONFLICTS (one unit per tile — a second order is STACKING_CONFLICT):")
        lines.extend(f"    {c}" for c in result.conflicts)
    if result.idle_tiles:
        # A tile a unit is told to assemble on is not spare: the rally leg above already spends
        # it, and listing it here as free contradicts the row that just claimed it.
        rally_tiles = {
            (rally[1].x, rally[1].y)
            for a in result.placed
            if (rally := _rally_option(plan, a.unit, ring_tiles))
        }
        spare = [t for t in result.idle_tiles if (t.x, t.y) not in rally_tiles]
        if spare:
            lines.append(
                "  SPARE RING TILES: "
                + ", ".join(f"({t.x},{t.y}) d{t.distance}" for t in spare[:8])
                + (
                    " — take them with the unplaced units: occupying the ring keeps the guard from"
                    " stepping into it"
                    if result.camp
                    else " — take them with the unplaced units: occupying the ring stops the city's"
                    " ~20/turn heal"
                )
            )
    # A gun whose tile the map rules out is not a gun in position, and that is the difference
    # between "the assault opens on T+2" and "the assault opens on T+2 and lands nothing".
    stuck = [a for a in result.placed if a.los is not None and a.los.ruled_out]
    if stuck:
        lines.append(
            "  NO LINE OF SIGHT — the map puts a blocker between these guns and the target, and a"
            " firing tile that cannot fire is a wasted march (manual:999):"
        )
        for a in stuck:
            blockers = "; ".join(a.los.blockers) or a.los.reason
            spare = _spare_firing_tiles(plan, result, a.unit)
            alt = (
                f" - stand it on ({spare[0][1].x},{spare[0][1].y}) d{spare[0][1].distance} instead"
                f" (T+{spare[0][0]}), which the map says it can fire from"
                if spare
                else " - no reachable ring tile fires from here: bring it in and read `CANFIRE` next"
                " turn, or leave it out of the assault rather than marching it to a tile it cannot"
                " shoot from"
            )
            lines.append(f"    {a.unit.unit_type} #{a.unit.unit_id} -> {a.where}: {blockers}{alt}")
    spent_guns = [a for a in result.placed if a.spent and a.unit.role in _SHOOTERS]
    if spent_guns:
        lines.append(
            "  SPENT THIS TURN — these guns are in the ring with no movement left (already fired or"
            " moved), so they cannot fire again until next turn and the assault opens a turn later:"
        )
        lines.extend(f"    {a.unit.unit_type} #{a.unit.unit_id} at {a.where}" for a in spent_guns)
    if any(
        a.los is not None and a.los.source == "map" and a.unit.role in _SHOOTERS
        for a in result.placed
    ):
        lines.append(
            "  LINE OF SIGHT is read off the map (manual:999: Hills, Woods, Rainforest and"
            " Mountains between the two block a shot, and a unit on Hills sees over them unless the"
            " blocker is Hills+Woods). `FIRE` is clear; `FIRE?` is a tile with two candidate lines"
            " and only one of them clear. A gun already standing on a ring tile gets `CANFIRE` —"
            " the game's own answer, which overrides the map's."
        )
    # Zone of control, at plan level: the rows carry the tile and the turn, this says how much of
    # the plan is affected - the measured failure this fixes was a schedule that treated a ZOC stop
    # as an unexplained delay (232 `STOPPED_MID_PATH` results over T228-T299).
    stopped = [
        a for a in result.placed + result.surplus if a.tile and a.zoc is not None and a.zoc > 0
    ]
    if stopped:
        lines.append(
            f"  ZONE OF CONTROL on the march: {len(stopped)} of the routes above enter an enemy"
            " zone of control, which spends the rest of that turn's movement (manual:875 - light"
            " and heavy cavalry ignore it, manual:735-737). Their arrival turns already count the"
            " stop:"
        )
        lines.extend(
            f"    {a.unit.unit_type} #{a.unit.unit_id}"
            + (
                f" stops at ({a.zoc_at[0]},{a.zoc_at[1]}) on turn +{a.zoc_at[2]}"
                if a.zoc_at
                else " stops on the way"
            )
            + (f", {a.zoc} such turn(s)" if (a.zoc or 0) > 1 else "")
            for a in stopped
        )
    shooters = result.shooters_in_place
    when = "this turn" if result.opens_on == 0 else f"T+{result.opens_on}"
    if result.camp:
        lines.append(
            f"  WALK-IN OPENS on {when} with {shooters} shooter(s) in position."
            + (
                " A camp has no HP, no walls and no supply line — one military unit MOVES onto its"
                " tile and it is gone, so the pair that matters is a shooter and an **unspent**"
                " walk-in; the guard, not the camp, is the enemy."
                " A shooter that moves two tiles, crosses a river or climbs a hill fires NEXT turn."
                if shooters
                else " No shooter reaches a ring tile in time: the plan is the march, and the"
                " walk-in must arrive with movement left — never a Scout, Builder or Trader."
            )
        )
    else:
        lines.append(
            f"  ASSAULT OPENS on {when}"
            f" with {shooters} shooter(s) in position."
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
