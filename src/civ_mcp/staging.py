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
        return sum(1 for a in self.placed if a.unit.role in ("siege", "ranged") and a.tile)


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
            key=lambda o: (o.turns, o.x, o.y),
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
                unit=unit, tile=tile, turns=option.turns, this_turn=option.this_turn, note="ADVANCE"
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
            key=lambda o: (o.turns, not o.this_turn, o.x, o.y),
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
                unit=unit, tile=tile, turns=option.turns, this_turn=option.this_turn, note="KILL"
            )
        )
        return True

    for unit in surplus_units:
        chosen = None
        if unit.role == "melee":
            for option in sorted(
                (o for o in _candidates(plan, unit) if o.turns <= turns_ahead),
                key=lambda o: (o.turns, 0 if (o.x, o.y) in supply_positions else 1),
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
                    unit=unit, tile=tile, turns=chosen.turns, this_turn=chosen.this_turn, note="SUPPLY"
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
    shooters = [a for a in result.placed if a.unit.role in ("siege", "ranged") and a.tile]
    result.opens_on = max((a.turns for a in shooters), default=0)
    return result


def _rally_option(plan: m.StagingPlan | None, unit: m.StagingUnit, ring_tiles: dict):
    """The unit's best ring tile **outside** the city's reach, if the plan found one.

    The doctrine stages outside the enemy's reach and then advances as one body - ``tactics/04``
    step 1 puts the rally *three tiles or more* from the target, because a city's strike and a
    Catapult both reach two. The ring assignment below is the tile a unit **fires from**; this is
    the tile it should form up on first, and it comes from the same game pathing as everything
    else here.

    It exists because the plan was followed literally and the cost is measured: at 底比斯 the
    assault opened with 2 of 3 shooters in position and at 亚历山大 with **2 of 5**, the rest still
    walking. Returns ``None`` when no tile at distance >= 3 is in reach, which is itself worth
    printing - a unit already standing on the ring has no assembly step left.
    """
    if plan is None:
        return None
    best = None
    for option in plan.options:
        if option.unit_id != unit.unit_id:
            continue
        tile = ring_tiles.get((option.x, option.y))
        if tile is None or tile.distance < 3:
            continue
        key = (option.turns, option.path_len, tile.distance)
        if best is None or key < best[0]:
            best = (key, option, tile)
    return best


def render(result: StagingPlanResult, plan: m.StagingPlan | None = None) -> str:
    """The plan as the table the doctrine asks for, one row per unit."""
    units = {u.unit_id: u for u in (plan.units if plan else [])}
    ring_tiles = {(t.x, t.y): t for t in (plan.ring if plan else [])}
    what = f"the camp at {result.target}" if result.camp else (result.target or "the target")
    lines = [
        f"STAGING PLAN for {what} — {result.ring_size} ring tile(s),"
        f" {len(result.placed)} unit(s) placed, {len(result.unplaced)} unplaced"
    ]
    if any(_rally_option(plan, a.unit, ring_tiles) for a in result.placed):
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
        rally = _rally_option(plan, a.unit, ring_tiles)
        leg = (
            f"  RALLY ({rally[1].x},{rally[1].y}) d{rally[2].distance} T+{rally[1].turns}"
            if rally
            else ""
        )
        lines.append(
            f"  {a.unit.unit_type:<22} #{a.unit.unit_id} ({a.unit.x},{a.unit.y}) moves {a.unit.moves}"
            f" -> {a.where} d{a.tile.distance}  arrive {when}  [{a.unit.role}]"
            f"{' - FIRE from here' if a.unit.role in ('siege', 'ranged') and a.tile.distance == 2 else ''}"
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
                )
            else:
                lines.append(
                    f"    {a.unit.unit_type:<20} #{a.unit.unit_id} -> {a.where} d{a.tile.distance}"
                    f"  CUT THE SUPPLY LINE (stands on a hex the city heals from)"
                )
        for a in killing:
            lines.append(
                f"    {a.unit.unit_type:<20} #{a.unit.unit_id} -> {a.where}"
                f"  HUNT THE MISSIONARY{' this turn' if a.this_turn else f' in {a.turns} turn(s)'}"
                f" — mobile unit only: one attacker kills it, and the extras take its other"
                f" neighbours so it cannot step away; `condemn` is one command from adjacent"
                f" (while at war, task 008)"
            )
        for a in advancing:
            lines.append(
                f"    {a.unit.unit_type:<20} #{a.unit.unit_id} -> {a.where} d{a.tile.distance}"
                f"  ADVANCE toward the next objective"
                f"{' this turn' if a.this_turn else f' in {a.turns} turn(s)'} — out of this city's"
                f" strike, and that much less marching when the next siege opens"
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
    shooters = [a for a in result.placed if a.unit.role in ("siege", "ranged") and a.tile]
    when = "this turn" if result.opens_on == 0 else f"T+{result.opens_on}"
    if result.camp:
        lines.append(
            f"  WALK-IN OPENS on {when} with {len(shooters)} shooter(s) in position."
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
