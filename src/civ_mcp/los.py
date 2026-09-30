"""Line of sight: the manual's rule, applied to the map's own numbers.

The rule is the manual's (`manual:999`):

    A unit cannot see a target if a blocking object is between the two units, such as a Mountain,
    Hill, or a Woods tile. A unit can always see into a tile, even if it contains blocking terrain,
    but it cannot see objects in tiles past the blocking terrain. Units on Hills can see over
    blocking terrain, unless the blocking terrain contains both Hills and Woods or Hills and
    Rainforest.

The numbers are the game's. Every terrain and feature carries a ``SightThroughModifier``
(`Base/Assets/Gameplay/Data/Terrains.xml` and `Features.xml`): Hills 1, Woods and Rainforest 1,
Mountains 2, the tall Natural Wonders 2, flat ground nothing. A Hills+Woods tile therefore sums to
**2**, which is exactly the manual's exception - a unit on a hill sees over plain woods and over a
plain hill, but not over woods on a hill. Impassable tiles (Mountains, the Natural Wonders, Ice) are
read as ``-1``: the manual calls those impenetrable, so no shot crosses one whatever the numbers say.

This module exists because the one thing the plan could not answer is the one thing that decides
whether a firing tile is worth walking to. Two measured cases: at 阿斯特拉罕 only one of the
distance-2 tiles had line of sight, and 圣彼得堡 opened with one Trebuchet firing while two guns
stood at distance 4 and 6. The staging plan's rows used to claim `FIRE from here` for **any**
distance-2 tile, which is a guess about the map that the map itself can answer.

What is deliberately *not* claimed here is a single definite answer where the map leaves two. A
hex tile at distance 2 has either one or two tiles strictly between it and the target, and which one
the engine draws its line through is not something the map data states - so when one candidate line
is clear and the other is blocked the verdict is `maybe`, and the row says to verify on arrival. The
engine's own answer (`get_staging_plan` asks it as `CANFIRE` for every gun already on a ring tile)
**overrides** this module: that is a reading, not a prediction, and it is how the model gets checked
against the game tile by tile as a train arrives.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lua import models as m

# The four answers a firing tile can get. `maybe` is not hedging for its own sake: it is the case
# where the map leaves two candidate lines and only one of them is clear.
FIRE = "fire"
MAYBE = "maybe"
NO = "no"
UNKNOWN = "unknown"

# Short labels for the plan's rows.
_LABEL = {FIRE: "FIRE", MAYBE: "FIRE?", NO: "NO LOS", UNKNOWN: "LOS unread"}

# A unit on a hill sees over a blocker of level 1; anything else sees only level 0.
_HILL_SIGHT = 1


@dataclass(frozen=True)
class Verdict:
    """Whether a unit on this tile can shoot the target, and why."""

    state: str
    reason: str
    blockers: tuple[str, ...] = ()
    # Where the answer came from: "engine" (the game's own CanStartOperation - a reading),
    # "range" (adjacent, nothing between), "map" (this module's rule) or "none" (no answer).
    source: str = "map"

    @property
    def can_fire(self) -> bool:
        return self.state == FIRE

    @property
    def ruled_out(self) -> bool:
        return self.state == NO

    @property
    def label(self) -> str:
        return _LABEL.get(self.state, "LOS unread")


def _blocker_name(x: int, y: int, level: int) -> str:
    if level < 0:
        return f"impassable terrain at ({x},{y})"
    if level >= 2:
        return f"hills with woods at ({x},{y})"
    if level == 1:
        return f"hills or woods at ({x},{y})"
    return f"({x},{y})"


def line_of_sight(
    tile: m.StagingRingTile | None,
    engine: bool | None = None,
) -> Verdict:
    """Can a shooter standing on `tile` fire at the ring's target?

    ``engine`` is the game's own answer for the unit's **current** tile, when the query asked for
    it, and it wins over everything below: a reading beats a prediction. Pass ``None`` when the
    engine was not asked (the unit is not in range yet, or the server predates `CANFIRE`).
    """
    if engine is not None:
        if engine:
            return Verdict(
                FIRE,
                "the game's own answer: it can fire at the target from where it stands",
                source="engine",
            )
        return Verdict(
            NO,
            "the game refuses the shot from where it stands (no line of sight, or the unit is"
            " spent)",
            source="engine",
        )
    if tile is None:
        return Verdict(UNKNOWN, "no tile assigned yet", source="none")
    where = f"({tile.x},{tile.y})"
    if tile.distance <= 1:
        return Verdict(
            FIRE,
            f"adjacent to the target: nothing can stand between {where} and it",
            source="range",
        )
    if not tile.between:
        return Verdict(
            UNKNOWN,
            f"the map did not report what lies between {where} and the target (a server that"
            f" predates the sight data)",
            source="none",
        )
    shooter_level = _HILL_SIGHT if tile.hills else 0
    clear = [b for b in tile.between if b[2] >= 0 and b[2] <= shooter_level]
    blocked = [b for b in tile.between if b not in clear]
    blockers = tuple(_blocker_name(bx, by, level) for bx, by, level in blocked)
    if not blocked:
        return Verdict(
            FIRE,
            f"the eyes from {where} clear every tile between it and the target",
            source="map",
        )
    if not clear:
        return Verdict(
            NO,
            f"every line from {where} to the target crosses {', '.join(blockers)}",
            blockers=blockers,
            source="map",
        )
    return Verdict(
        MAYBE,
        f"one line from {where} is clear and another crosses {', '.join(blockers)} - the engine"
        f" draws one of them, so this is a maybe until a unit stands there and `CANFIRE` answers",
        blockers=blockers,
        source="map",
    )
