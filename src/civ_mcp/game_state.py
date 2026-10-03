"""High-level game state API with server-side narration.

Wraps GameConnection + lua into typed async methods that return
both structured data and human-readable narrated text. Has ZERO MCP
dependency — enabling multi-agent architectures where specialist servers
import the same GameState class but expose different tool subsets.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import re

from typing import TYPE_CHECKING

from civ_mcp import lua as lq
from civ_mcp.connection import GameConnection
from civ_mcp.localization import english_output
from civ_mcp.narrate import (
    narrate_combat_estimate,
    narrate_move_discoveries,
    narrate_settle_candidates,
    narrate_sight,
    narrate_test_trade,
)

if TYPE_CHECKING:
    from civ_mcp.spatial import SpatialTracker

log = logging.getLogger(__name__)

# The marker `skip_remaining_units` returns when it refuses to sweep units that still have a
# legal attack. `end_turn` matches on it, because the alternative - sweeping and reporting -
# is what discarded four attacks over the T139-T152 Russian war.
SKIP_REFUSED = "REFUSED|"


def clears_blockers(fn):
    """Clear the popup layer before a deliberate game action.

    A blocking popup does not only hold the turn - **it silently eats the next
    game action**. Measured on the live branch at T103: the same
    `set_city_production` call answered
    `SILENT_FAILURE|... appeared to set but the game engine did not persist it
    (NOT_SET|current=nil|expected=BUILDING_ETEMENANKI)` three times while 22
    popups (a cinematic camera, a natural-disaster screen and the invites) sat
    on the stack, and the identical call landed
    `PRODUCING|BUILDING_ETEMENANKI|6 turns` on the first attempt after
    `dismiss_popup` had emptied it.

    So the guard belongs on **every** deliberate write, not only on `move_unit`
    and `attack_unit` (which had it because the same thing was measured on
    them). It is cheap: on an empty layer `dismiss_popup` answers
    `No popups to dismiss.` in ~0.7s measured on this branch, less than one Lua
    round trip, and it never closes a diplomacy session or a deal view (it
    reports `PENDING|` instead), so it cannot answer for the agent.
    """

    @functools.wraps(fn)
    async def wrapper(self, *args, **kwargs):
        await self._clear_action_blockers()
        return await fn(self, *args, **kwargs)

    wrapper._clears_blockers = True  # type: ignore[attr-defined]
    return wrapper


class GameState:
    """High-level async API for Civ 6 game state + actions."""

    @property
    def local_player_id(self) -> int:
        """Our own player id, for anything that has to name us as a target.

        The World Congress free-vote fallback is the caller that needs it: a
        resolution whose effect grants something to "the chosen player" is only
        worth a vote when the chosen player is us. Read-only on purpose - the
        id comes from the game, never from a caller.
        """
        return self._local_player_id

    def __init__(self, connection: GameConnection):
        self.conn = connection
        self.spatial: SpatialTracker | None = None
        self._last_snapshot: lq.TurnSnapshot | None = None
        self._game_identity: tuple[str, int] | None = None  # (civ_type, seed)
        self._diary_written_turn: int | None = (
            None  # guard against double-write per turn
        )
        self._end_turn_blocked: bool = False  # last end_turn hit a blocker (diplo/WC)
        self._pending_end_turn: bool = False  # ACTION_ENDTURN already in flight
        self._pending_end_turn_from: int | None = (
            None  # turn number when ACTION_ENDTURN was sent
        )
        self._high_water_turn: int = 0  # highest turn seen (for regression detection)
        self._local_player_id: int = 0  # human player (always 0 in single-player)
        self._hang_retry_active: bool = False  # guard against recursive hang recovery
        self._last_game_over: lq.GameOverStatus | None = (
            None  # captured by execute_end_turn for server.py
        )
        # (ts, turn, save_name) for each successful save load — used to detect
        # save scumming in _check_save_scumming(). Bounded to last 50 entries.
        self._save_load_history: list[tuple[float, int, str]] = []
        self._run_aborted: bool = False  # set when save scumming threshold is exceeded
        # Per-turn advisor call budget — prevents compulsive advisor loops
        # (e.g. Gemini Pro's 1,567 get_wonder_advisor calls in a single turn).
        # Reset in execute_end_turn on successful turn advance.
        self._advisor_calls_this_turn: int = 0
        # Attacks actually executed during the current turn. The check engine reads it:
        # "there is an enemy two tiles from the army and nothing attacked it" is only
        # measurable if the attacks are counted where they happen. end_turn resets it after
        # the checks have run.
        self._attacks_this_turn: int = 0
        # Units that were ordered somewhere and stopped short of it this turn. A column ordered
        # nearest-first queues behind itself; measured T228-T299 this happened 232 times in 72 turns.
        self._move_stops_this_turn: int = 0
        # Attacks that resolved as a melee attack against a unit that is not on land this turn. A
        # melee land unit cannot attack enemies at sea (manual:723), so such an attack deals nothing
        # however the engine acknowledges it - it is a no-op the agent reads as a hit. The Lua now
        # refuses it (`ERR:MELEE_CANNOT_ATTACK_AT_SEA`); this counter exists so the rule engine can
        # shout if that refusal is ever bypassed again. Measured T222-T237 on this branch: seven of
        # them, the target's HP unchanged every time, and two of our units sunk in the water.
        self._attacks_landed_nothing: int = 0
        # Enemy city HP seen from our own attacks, per city name: (turn, hp, max_hp). Read by
        # end_turn's siege-progress report.
        self._city_hp_history: dict[str, list[tuple[int, int, int]]] = {}
        # Our units' HP at the moment ACTION_ENDTURN was sent, so the damage report cannot miss
        # a hit just because a blocker re-entry moved the snapshot baseline.
        self._hp_at_end_turn_request: dict[int, int] = {}
        # One-shot warning from the most recent advisor call, consumed and
        # cleared by the server wrapper.
        self._advisor_budget_warning: str | None = None

    async def get_game_identity(self) -> tuple[str, int]:
        """Return (civ_type_lower, random_seed) for the current game.

        Always queries the game so we detect new-game loads.  When the
        identity changes, all per-game cached state is reset.
        """
        code = (
            "local me = Game.GetLocalPlayer() "
            "local cfg = PlayerConfigurations[me] "
            'print("GAMESEED|" .. cfg:GetCivilizationTypeName() '
            '.. "|" .. tostring(GameConfiguration.GetValue("GAME_SYNC_RANDOM_SEED"))) '
            'print("---END---")'
        )
        lines = await self.conn.execute_write(code)
        for line in lines:
            if line.startswith("GAMESEED|"):
                parts = line.split("|")
                civ = parts[1].replace("CIVILIZATION_", "").lower()
                seed = int(parts[2])
                new_id = (civ, seed)
                if self._game_identity is not None and new_id != self._game_identity:
                    log.info("Game changed: %s → %s", self._game_identity, new_id)
                    self._last_snapshot = None
                    self._diary_written_turn = None
                    self._last_game_over = None
                    self._save_load_history = []
                    self._run_aborted = False
                    self._advisor_calls_this_turn = 0
                    self._advisor_budget_warning = None
                self._game_identity = new_id
                return self._game_identity
        return ("unknown", 0)

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    @english_output
    async def get_game_overview(self) -> lq.GameOverview:
        # InGame context needed for GetFavor() (nil in GameCore)
        lines = await self.conn.execute_write(lq.build_overview_query())
        ov = lq.parse_overview_response(lines)
        # Bootstrap: capture baseline snapshot for first end_turn diff
        if self._last_snapshot is None:
            try:
                self._last_snapshot = await self._take_snapshot(ov)
            except Exception:
                log.debug("Failed to bootstrap snapshot", exc_info=True)
        return ov

    async def get_diary_snapshot(self) -> lq.DiarySnapshot:
        """Full per-turn snapshot for diary JSONL. InGame context."""
        lines = await self.conn.execute_write(lq.build_diary_full_query())
        return lq.parse_diary_full_response(lines)

    @english_output
    async def get_rival_snapshot(self) -> list[lq.RivalSnapshot]:
        """Lightweight per-rival stats for diary entries."""
        lines = await self.conn.execute_write(lq.build_rival_snapshot_query())
        return lq.parse_rival_snapshot_response(lines)

    async def check_game_over(self) -> lq.GameOverStatus | None:
        """Check if the game has ended (victory/defeat screen showing).

        Tries InGame context first (full detection with UI checks).
        Falls back to GameCore context (read-only, survives defeat screen)
        when InGame fails — this catches victories that freeze the InGame UI.
        """
        try:
            lines = await self.conn.execute_write(lq.build_gameover_check())
            return lq.parse_gameover_response(lines)
        except Exception:
            log.debug("Game-over check failed in InGame, trying GameCore")
        # Fallback: GameCore-only check (survives defeat screen)
        try:
            lines = await self.conn.execute_read(lq.build_gameover_check_gamecore())
            return lq.parse_gameover_response(lines)
        except Exception:
            log.debug("Game-over check failed in GameCore too", exc_info=True)
            return None

    @english_output
    async def get_units(self) -> list[lq.UnitInfo]:
        lines = await self.conn.execute_write(lq.build_units_query())
        return lq.parse_units_response(lines)

    @english_output
    async def get_builder_tasks(
        self,
    ) -> tuple[list[lq.BuilderTask], list[lq.BuilderInfo]]:
        lines = await self.conn.execute_write(lq.build_builder_tasks_query())
        return lq.parse_builder_tasks(lines)

    @english_output
    async def get_spies(self) -> list[lq.SpyInfo]:
        lines = await self.conn.execute_write(lq.build_get_spies_query())
        return lq.parse_spies_response(lines)

    @clears_blockers
    async def spy_travel(self, unit_index: int, target_x: int, target_y: int) -> str:
        lua = lq.build_spy_travel(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def spy_mission(
        self, unit_index: int, mission_type: str, target_x: int, target_y: int
    ) -> str:
        lua = lq.build_spy_mission(unit_index, mission_type, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @english_output
    async def get_threat_scan(self) -> list[lq.ThreatInfo]:
        lines = await self.conn.execute_read(lq.build_threat_scan_query())
        return lq.parse_threat_scan_response(lines)

    async def get_pathing_estimate(
        self, unit_index: int, target_x: int, target_y: int
    ) -> lq.PathingEstimate:
        lines = await self.conn.execute_write(
            lq.build_pathing_estimate_query(unit_index, target_x, target_y)
        )
        return lq.parse_pathing_estimate(lines)

    async def staging_plan(
        self,
        target_x: int,
        target_y: int,
        next_x: int | None = None,
        next_y: int | None = None,
        kill_x: int | None = None,
        kill_y: int | None = None,
    ) -> lq.StagingPlan:
        """The ring around a target city, our units, and every unit's path to every ring tile.

        One query, not one per (unit, tile): the plan decides which unit takes which tile in
        which turn, and those movement numbers have to come from the game's own pathfinding.
        ``next_x``/``next_y`` add the next objective's ring so surplus units can be pushed toward
        it; ``kill_x``/``kill_y`` add the ring around a unit to eliminate (a missionary).
        """
        lines = await self.conn.execute_write(
            lq.build_staging_plan_query(target_x, target_y, next_x, next_y, kill_x, kill_y)
        )
        return lq.parse_staging_plan_response(lines)

    async def target_report(self, target_x: int, target_y: int, radius: int = 3) -> lq.TargetReport:
        """One target, read the way `tactics/07` asks about it: two queries, one answer.

        The probe is anchored on the **target** rather than on our army, so it works before a
        declaration and while the target is still in fog; the plan is the same `staging_plan` the
        assault will be run on, so the ring, the line-of-sight verdicts and our arrival turns are
        the numbers the fighting will actually use.
        """
        lines = await self.conn.execute_write(
            lq.build_target_probe_query(target_x, target_y, radius)
        )
        tile, city, enemies = lq.parse_target_probe_response(lines)
        if tile is None:
            # The tile itself failed to read (`ERR:INVALID_TARGET`): report it as fog rather than
            # inventing a target, and let the narration say the target is not on the map.
            tile = lq.TargetTile(x=target_x, y=target_y, visibility="fog")
        plan = await self.staging_plan(target_x, target_y)
        return lq.TargetReport(tile=tile, city=city, enemies=enemies, plan=plan)

    async def reinforcements(self, target_x: int, target_y: int) -> lq.ReinforcementReport:
        """What is in the plan, and what the production queues are adding to it.

        `tactics/07` step 3 asks how long the target takes and what it costs; the answer has a leg
        nothing joined - a unit being built is `get_cities`' countdown in one place and a map
        distance in another. This is the staging plan (what we have) plus one query over our
        queues, with the march figure labelled as the estimate it is (pathfinding needs a unit, and
        this one does not exist yet).
        """
        plan = await self.staging_plan(target_x, target_y)
        lines = await self.conn.execute_write(lq.build_reinforcement_query(target_x, target_y))
        return lq.ReinforcementReport(
            target=f"{target_x},{target_y}",
            plan=plan,
            building=lq.parse_reinforcement_response(lines),
        )

    @english_output
    async def get_victory_progress(self) -> lq.VictoryProgress:
        lines = await self.conn.execute_write(lq.build_victory_progress_query())
        return lq.parse_victory_progress_response(lines)

    @english_output
    async def get_cities(self) -> tuple[list[lq.CityInfo], list[str]]:
        lines = await self.conn.execute_write(lq.build_cities_query())
        return lq.parse_cities_response(lines)

    @english_output
    async def visible_foreign_cities(self) -> list[lq.CitySighting]:
        """Every foreign city we can see right now - at war or not, city-state or major.

        The capture-readiness scan is war-scoped, so this is the only read that answers "what has the
        map just shown us". `end_turn` diffs it across turns into its `NEW TARGET` block; the first
        scan in a process seeds the comparison silently.
        """
        lines = await self.conn.execute_write(lq.build_visible_foreign_cities_query())
        return lq.parse_visible_foreign_cities_response(lines)

    @english_output
    async def get_map_area(
        self, center_x: int, center_y: int, radius: int = 2
    ) -> list[lq.TileInfo]:
        lines = await self.conn.execute_read(
            lq.build_map_area_query(center_x, center_y, radius)
        )
        return lq.parse_map_response(lines)

    @english_output
    async def get_strategic_map(self) -> lq.StrategicMapData:
        lines = await self.conn.execute_read(lq.build_strategic_map_query())
        return lq.parse_strategic_map_response(lines)

    @english_output
    async def get_diplomacy(self) -> list[lq.CivInfo]:
        # Uses InGame context for GetDiplomaticAI access
        lines = await self.conn.execute_write(lq.build_diplomacy_query())
        return lq.parse_diplomacy_response(lines)

    @english_output
    async def get_tech_civics(self) -> lq.TechCivicStatus:
        lines = await self.conn.execute_read(lq.build_tech_civics_query())
        return lq.parse_tech_civics_response(lines)

    @english_output
    async def get_empire_resources(
        self,
    ) -> tuple[
        list[lq.ResourceStockpile],
        list[lq.OwnedResource],
        list[lq.NearbyResource],
        dict[str, int],
    ]:
        # InGame context needed for GetResourceStockpileCap etc.
        lines = await self.conn.execute_write(lq.build_empire_resources_query())
        return lq.parse_empire_resources_response(lines)

    # ------------------------------------------------------------------
    # Action methods (run in InGame context for UnitManager access)
    # ------------------------------------------------------------------

    #: Markers a partial move leaves in its own result line. `STOPPED_MID_PATH` is written by
    #: `move_unit` below; `STOPPED_SHORT` comes from the same Lua reply on a path the engine stops
    #: early. Both mean the unit is not where it was sent.
    _STOP_MARKERS = ("STOPPED_MID_PATH", "STOPPED_SHORT")

    #: Reasons that explain a partial move by the unit's **own movement budget or the terrain**, and
    #: therefore say nothing about a column queueing behind itself. Measured over the two experiment
    #: attempts (2026-09-29): A1 took 76 stops and A2 11, and **seven in ten of them carried
    #: `moves exhausted`** - a mv2 unit crossing hills or forest, which is what the terrain costs - while
    #: `impassable mountain` and the Shipbuilding refusal accounted for most of the rest. **Not one stop
    #: in either attempt named another unit.** Counting them all made `issue-the-calls-furthest-first` a
    #: terrain meter: it fired on A1 eight times and on A2's first half once, and the rate tracked how
    #: much the army moved rather than whether it jammed (A2's second half, with a bigger army and less
    #: marching, read a *lower* stop rate). The fix is this filter, not a lower threshold.
    _SELF_EXPLAINED_STOP_REASONS = (
        "moves exhausted",
        "impassable mountain",
        "need shipbuilding",
        "no moves",
    )

    @staticmethod
    def _stop_reason(result: str) -> str | None:
        """The parenthetical reason a stop carries, lowercased; `None` when it carries none.

        A stop with **no** reason is counted: the tool could not say why the unit is not where it was
        sent, which is exactly the case the rule exists for.
        """
        match = re.search(r"STOPPED_(?:MID_PATH|SHORT)\s*\(([^)]*)\)", result)
        if not match:
            return None
        return match.group(1).strip().lower()

    def note_move_stops(self, result: str) -> None:
        """Count the partial moves that are a **jam**, not a movement budget spent on terrain.

        Called for every tool result from the dispatch wrapper rather than from `move_unit`, because
        the marker is also produced by paths that never reach this class's own post-processing. The
        reason filter and the measurement behind it are on `_SELF_EXPLAINED_STOP_REASONS`.
        """
        if not any(marker in result for marker in self._STOP_MARKERS):
            return
        reason = self._stop_reason(result)
        if reason is not None and any(known in reason for known in self._SELF_EXPLAINED_STOP_REASONS):
            return
        self._move_stops_this_turn += 1

    def note_attack_result(self, result: str, est=None) -> str:
        """Count an attack that could not have landed, and say so in the reply. Returns the warning.

        The one shape that is knowable here without a live read is **a melee attack on a target that
        is not on land**: manual:723 says a melee land unit cannot attack enemies at sea, so the
        engine's `OK:MELEE_ATTACK` line is an acknowledgement, not a hit. Measured T222-T237 on this
        branch: seven such attacks on Dutch Caravels, the target's HP identical every time
        (57 -> 57 and 100 -> 100 for seventeen turns) and two of our units lost while standing in the
        water. The Lua refuses the order now, so this is a counter the rules can watch rather than a
        path the agent should ever reach.
        """
        if not result.startswith("MELEE_ATTACK"):
            return ""
        domain = getattr(est, "defender_domain", "") if est is not None else ""
        if domain != "DOMAIN_SEA":
            return ""
        self._attacks_landed_nothing += 1
        return (
            "!!! ATTACK LANDED NOTHING: this order resolved as a melee attack on a unit at sea, and "
            "a melee land unit cannot attack enemies at sea (manual:723). The engine acknowledged "
            "the command and dealt no damage. Fire with a ranged unit from two tiles away (manual:725: "
            "ranged units always use ranged combat) or use a naval unit - and get the melee unit out "
            "of the water before their ships answer."
        )

    @clears_blockers
    async def move_unit(self, unit_index: int, target_x: int, target_y: int) -> str:
        lua = lq.build_move_unit(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        # Post-move: read actual position from GameCore (move is async in InGame)
        if result.startswith("MOVING_TO") or result.startswith("CAPTURE_MOVE"):
            try:
                pos_lines = await self.conn.execute_read(
                    lq.build_unit_position_query(
                        unit_index,
                        move_target_x=target_x,
                        move_target_y=target_y,
                    )
                )
                for line in pos_lines:
                    if line.startswith("POS|") and "GONE" not in line:
                        parts = line.split("|")
                        now_x, now_y = int(parts[1]), int(parts[2])
                        result += f"|now_at:{now_x},{now_y}"
                        from_match = re.search(r"\|from:(\d+),(\d+)", result)
                        if from_match:
                            from_x = int(from_match.group(1))
                            from_y = int(from_match.group(2))
                            if now_x == from_x and now_y == from_y:
                                reason = lq.parse_blocked_diagnostic(pos_lines)
                                result += f"|BLOCKED ({reason})"
                            else:
                                dx = now_x - from_x
                                dy = (
                                    now_y - from_y
                                )  # positive dy = south (higher Y = south in Civ 6)
                                result += f"|(moved dx:{dx:+d} dy:{dy:+d})"
                                tgt_match = re.search(
                                    r"(?:MOVING_TO|CAPTURE_MOVE)\|(\d+),(\d+)", result
                                )
                                if tgt_match:
                                    tx, ty = (
                                        int(tgt_match.group(1)),
                                        int(tgt_match.group(2)),
                                    )
                                    if (now_x, now_y) != (tx, ty):
                                        result += f"|STOPPED_MID_PATH (moves exhausted)"
                                    elif result.startswith("CAPTURE_MOVE") and (
                                        self._city_owner_on_own_tile(pos_lines)
                                    ):
                                        # A CAPTURE_MOVE that ended on the target tile, with a city
                                        # there that is now ours, *is* the capture. Live T122 the
                                        # response stopped at `now_at:54,40` and the caller had to
                                        # infer the capture from the city list going 6 -> 7.
                                        result += "|CITY TAKEN - resolve keep/raze with city_action"
                        break
            except Exception:
                pass
        # Post-move: visibility diff for discovery feedback, and what is in sight from where the
        # unit stopped. The sight block does not depend on novelty: a unit that walks up to a
        # foreign city must say so in the same message, whether or not the session had already
        # revealed the tile (measured: the novelty-gated block never once reported a city or a camp
        # in 158 recorded sessions, while 70 of them contained moves that resolved).
        blocked = "|BLOCKED" in result
        if not blocked and self.spatial is not None and self.spatial._revealed_seeded:
            try:
                # Extract actual position from result
                now_match = re.search(r"now_at:(\d+),(\d+)", result)
                if now_match:
                    vis_x, vis_y = int(now_match.group(1)), int(now_match.group(2))
                    vis_lines = await self.conn.execute_read(
                        lq.build_post_move_visibility_query(vis_x, vis_y)
                    )
                    vis_tiles = lq.parse_post_move_visibility(vis_lines)
                    all_revealed = {(x, y) for x, y, _ in vis_tiles}
                    newly_revealed = self.spatial.mark_revealed(all_revealed)
                    if newly_revealed:
                        new_tile_data = [
                            (x, y, m)
                            for x, y, m in vis_tiles
                            if (x, y) in newly_revealed
                        ]
                        discovery_text = narrate_move_discoveries(
                            new_tile_data, len(newly_revealed)
                        )
                        if discovery_text:
                            result += "\n" + discovery_text
                        # Record discovery event in spatial tracker
                        await self.spatial.record_discovery(
                            "unit_action",
                            (vis_x, vis_y),
                            newly_revealed,
                            0,
                        )
                    sight = narrate_sight(vis_tiles, (vis_x, vis_y))
                    if sight:
                        result += "\n" + sight
            except Exception:
                log.debug("Post-move visibility diff failed", exc_info=True)
        return result

    def _city_owner_on_own_tile(self, pos_lines: list[str]) -> bool:
        """Did the unit end its move standing in one of *our* cities?

        The position query adds an ``ONCITY|<id>|owner:<pid>|<name>`` line when the tile it landed
        on holds a city. A CAPTURE_MOVE that ends on its target with our owner on the city tile is
        a completed capture, so the caller can say so instead of leaving the agent to infer it.
        """
        for line in pos_lines or []:
            if line.startswith("ONCITY|"):
                for part in line.split("|"):
                    if part.startswith("owner:"):
                        try:
                            return int(part.split(":", 1)[1]) == self._local_player_id
                        except ValueError:
                            return False
        return False

    @clears_blockers
    async def attack_unit(self, unit_index: int, target_x: int, target_y: int) -> str:
        # Pre-attack: run combat estimator
        estimate_str = ""
        est: lq.CombatEstimate | None = None
        try:
            est_lua = lq.build_combat_estimate_query(unit_index, target_x, target_y)
            est_lines = await self.conn.execute_write(est_lua)
            est = lq.parse_combat_estimate(est_lines, 0, 0)
            if est:
                estimate_str = narrate_combat_estimate(est) + "\n"
        except Exception as e:
            log.debug("Combat estimate failed: %s", e)
        lua = lq.build_attack_unit(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        # Combat followup: the game engine processes combat asynchronously
        # after RequestOperation.  Lua state within the same turn frame
        # does NOT reflect post-combat HP regardless of how long we wait.
        # Strategy: use the combat estimate as authoritative damage source
        # and only query the tile to detect if the target was eliminated.
        is_melee = result.startswith("MELEE_ATTACK")
        is_air = result.startswith("AIR_ATTACK")
        if result.startswith("RANGE_ATTACK") or is_melee or is_air:
            self._attacks_this_turn += 1
            pre_hp = _extract_pre_hp(result)
            est_dmg = est.est_damage_to_defender if est else None
            local_id = self._local_player_id

            # Brief delay then check if target still exists on the tile
            await asyncio.sleep(0.3 if not is_melee else 0.5)
            followup: list[str] = []
            try:
                followup = await self.conn.execute_write(
                    lq.build_attack_followup_query(target_x, target_y)
                )
            except Exception as e:
                log.debug("Attack followup read failed: %s", e)

            try:
                followup_str = _format_attack_followup(followup, local_id)
                city_def = _extract_city_defense(followup)

                # Check if target was eliminated (no enemy units on tile). A city tile with no
                # garrison unit in it has *no* UNIT line at all, so this read on its own calls a
                # perfectly healthy city dead: live T120, four hits on the Free City of Moscow
                # each answered "damage dealt:200 (killed)" and "Post-combat: Target eliminated"
                # while the city went 200 -> 90 and kept standing. A city is only gone when the
                # CITY_DEF line is gone with it.
                enemy_units = [
                    l
                    for l in followup
                    if l.startswith("UNIT|") and f"owner:{local_id}" not in l
                ]
                eliminated = not enemy_units and city_def is None

                # Build damage report from estimate (authoritative) or followup
                post_hp = _extract_post_hp(followup, local_id)
                damage_info = ""
                if city_def is not None and pre_hp is not None:
                    # For a city the pool is the progress - and it is the *only* progress for an
                    # unwalled one. The followup read can lag the attack by a frame, so a real
                    # delta wins and the estimate is the fallback; "killed" is never a city answer.
                    city_hp, city_max = city_def[2], city_def[3]
                    if city_hp < pre_hp:
                        damage_info = f"|damage dealt:{pre_hp - city_hp}"
                        followup_str = f"city {city_hp}/{city_max}"
                    elif est_dmg and est_dmg > 0:
                        capped = min(est_dmg, pre_hp)
                        damage_info = f"|est damage dealt:~{capped}"
                        followup_str = (
                            f"~{pre_hp - capped}/{pre_hp} (estimate - the city read lags the hit)"
                        )
                    else:
                        # Do NOT say "none": measured in attempt A2 (T66-T67), this branch printed
                        # `damage dealt:none read` on both shots of the turn whose pool the next
                        # SIEGE PROGRESS block read as `130/200 (-70 over 2 turn(s))` - the damage had
                        # landed and the read was a turn behind it. The same string had already been
                        # recorded as misleading three times (`docs/task-history.md:377`, the naval
                        # no-op retrospective, task 021's table). It says what it knows: this read did
                        # not move, and the pool is the record.
                        damage_info = (
                            f"|damage not visible in this read (city still {city_hp}/{city_max} on this "
                            f"frame - a later read is the fact)"
                        )
                        followup_str = (
                            f"city {city_hp}/{city_max} (this read unchanged; judge from SIEGE PROGRESS)"
                        )
                elif eliminated and pre_hp is not None:
                    damage_info = f"|damage dealt:{pre_hp} (killed)"
                    followup_str = "Target eliminated"
                elif pre_hp is not None and post_hp is not None and post_hp < pre_hp:
                    # Followup reflects real change (can happen for city attacks)
                    damage_info = f"|damage dealt:{pre_hp - post_hp}"
                elif est_dmg and est_dmg > 0 and pre_hp is not None:
                    # Followup stale — use estimate as best available
                    capped_dmg = min(est_dmg, pre_hp)
                    est_post = pre_hp - capped_dmg
                    damage_info = f"|est damage dealt:~{capped_dmg}"
                    followup_str = (
                        f"~{est_post}/{pre_hp} (estimate — verify with get_units)"
                    )

                if city_def:
                    w_hp, w_max, g_hp, g_max = city_def
                    # A city's own HP must be reported whether or not it has walls. The old
                    # `if w_max > 0` guard threw the whole line away for an unwalled city - and
                    # an unwalled city is exactly the case where the city HP pool is the only
                    # progress there is. Seen live T105-T116: twelve turns of Catapult fire at
                    # Moscow with no city number reported anywhere, so neither side of the
                    # table could tell whether the assault was working.
                    walls = f"{w_hp}/{w_max}" if w_max > 0 else "none"
                    damage_info += f"|city hp: {g_hp}/{g_max}, walls: {walls}"
                    self._record_city_hp(est, g_hp, g_max)

                result += damage_info + "\n  Post-combat: " + followup_str
            except Exception as e:
                log.debug("Attack followup formatting failed: %s", e)
        # A melee attack on a unit at sea cannot have landed (manual:723). The Lua refuses the order
        # now; if this still happens, the reply says so at the top of the damage report and the turn's
        # `attacks_landed_nothing` metric counts it, so a rule can shout.
        warning = self.note_attack_result(result, est)
        if warning:
            return estimate_str + result + "\n" + warning
        return estimate_str + result

    @clears_blockers
    async def city_attack(self, city_id: int, target_x: int, target_y: int) -> str:
        lua = lq.build_city_attack(city_id, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if result.startswith("CITY_RANGE_ATTACK"):
            pre_hp = _extract_pre_hp(result)
            await asyncio.sleep(0.3)
            followup: list[str] = []
            try:
                followup = await self.conn.execute_write(
                    lq.build_attack_followup_query(target_x, target_y)
                )
            except Exception:
                followup = []
            try:
                followup_str = _format_attack_followup(followup)
                post_hp = _extract_post_hp(followup)
                damage_info = ""
                if pre_hp is not None and post_hp is not None and post_hp < pre_hp:
                    damage_info = f"|damage dealt:{pre_hp - post_hp}"
                elif not any(l.startswith("UNIT|") for l in followup):
                    if pre_hp is not None:
                        damage_info = f"|damage dealt:{pre_hp} (killed)"
                    followup_str = "Target eliminated"

                result += damage_info + "\n  Post-combat: " + followup_str
            except Exception as e:
                log.debug("City attack followup failed: %s", e)
        return result

    @clears_blockers
    async def resolve_city_capture(self, action: str) -> str:
        lua = lq.build_resolve_city_capture(action)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def found_city(self, unit_index: int) -> str:

        lua = lq.build_found_city(unit_index)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)

        if result.startswith("FOUNDED|"):
            # Extract coordinates from "FOUNDED|x,y"
            parts = result.split("|")[1].split(",")
            x, y = int(parts[0]), int(parts[1])
            # Verify city was actually created (RequestOperation is async)
            verify_lua = lq.build_verify_city_at(x, y)
            verify_lines = await self.conn.execute_read(verify_lua)
            verified = lq.parse_verify_city_at(verify_lines)
            if not verified:
                # Retry once — popup may have blocked the async operation
                try:
                    await self.dismiss_popup()
                    lines = await self.conn.execute_write(lua)
                    retry_result = _action_result(lines)
                    if retry_result.startswith("FOUNDED|"):
                        verify_lines = await self.conn.execute_read(verify_lua)
                        if lq.parse_verify_city_at(verify_lines):
                            result = retry_result
                            verified = True
                except Exception:
                    log.debug(
                        "found_city retry after popup dismiss failed", exc_info=True
                    )
                if not verified:
                    result = (
                        f"Error: FOUND_FAILED|Founding at {x},{y} was requested but "
                        "city did not appear despite popup dismissal."
                    )

        # On settle failure, run the settle advisor to suggest alternatives
        if result.startswith("Error: CANNOT_FOUND") or result.startswith(
            "Error: FOUND_FAILED"
        ):
            try:
                advisor_result = await self.get_settle_advisor(unit_index)
                result += "\n\n" + advisor_result
            except Exception as e:
                log.debug("Settle advisor failed: %s", e)
        return result

    @english_output
    async def get_settle_advisor(self, unit_index: int) -> str:
        lua = lq.build_settle_advisor_query(unit_index)
        lines = await self.conn.execute_read(lua)
        candidates = lq.parse_settle_advisor_response(lines)
        if candidates:
            return narrate_settle_candidates(candidates)
        # Auto-fallback to global scan when no local candidates
        try:
            global_candidates = await self.get_global_settle_scan()
            if global_candidates:
                header = "No valid settle locations within 5 tiles. Best sites on revealed map:\n"
                return header + narrate_settle_candidates(global_candidates[:5])
        except Exception:
            log.debug("Global settle fallback failed", exc_info=True)
        return "No valid settle locations found within 5 tiles or on revealed map."

    @english_output
    async def get_global_settle_scan(self) -> list[lq.SettleCandidate]:
        lua = lq.build_global_settle_scan()
        lines = await self.conn.execute_read(lua)
        return lq.parse_settle_advisor_response(lines)

    @clears_blockers
    async def condemn_heretic(self, unit_index: int) -> str:
        """Destroy an adjacent enemy religious unit (Condemn Heretic).

        A game **command**, not an attack: the engine picks the adjacent religious unit and the
        game refuses it outright against a civ we are not at war with
        (`LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION`). The Lua reports every
        adjacent candidate before firing, so a condemnation is never anonymous.
        """
        lua = lq.build_condemn_heretic(unit_index)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if not result.startswith("CONDEMNED"):
            return result
        tx = ty = None
        for line in lines:
            if line.startswith("OK:CONDEMNED") and "verify_tile:" in line:
                try:
                    coords = line.split("verify_tile:", 1)[1].split("|", 1)[0].split(",")
                    tx, ty = int(coords[0]), int(coords[1])
                except (ValueError, IndexError):
                    tx = ty = None
                break
        if tx is None:
            return result
        # The command resolves in the game core; re-read the tile rather than trusting the request.
        await asyncio.sleep(0.4)
        try:
            verify = await self.conn.execute_read(lq.build_attack_followup_query(tx, ty))
        except Exception as exc:  # pragma: no cover - the read is best-effort
            log.debug("condemn verification failed: %s", exc)
            return result
        still = [ln for ln in verify if ln.startswith("UNIT|")]
        if still:
            return f"{result} | STILL THERE: {'; '.join(still)} - re-read next turn before assuming the kill"
        return f"{result} | tile ({tx},{ty}) now empty"

    @clears_blockers
    async def pillage_tile(
        self, unit_index: int, target_x: int | None = None, target_y: int | None = None
    ) -> str:
        """Pillage the improvement or district the unit stands on (the game's `UNITOPERATION_PILLAGE`).

        The standing order the toolkit could not carry out: the directive's answer to a rival's faith
        income is to pillage the Holy Site, and the staging ladder offers "pillage (cavalry ignores
        ZOC)" as a rung for surplus units. With no coordinates it acts on the unit's own tile, which
        is where the operation is legal.
        """
        lua = lq.build_pillage_unit(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def fortify_unit(self, unit_index: int) -> str:
        lua = lq.build_fortify_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if result.startswith("SLEEPING"):
            return "Unit is sleeping (this unit type cannot fortify)"
        return result

    @clears_blockers
    async def skip_unit(self, unit_index: int) -> str:
        lua = lq.build_skip_unit(unit_index)
        lines = await self.conn.execute_read(lua)
        return _action_result(lines)

    def city_hp_history(self) -> dict[str, list[tuple[int, int, int]]]:
        """Enemy city HP we have actually seen, per city, as (turn, hp, max_hp)."""
        return dict(self._city_hp_history)

    def _record_city_hp(self, estimate, hp: int, max_hp: int) -> None:
        """Remember the target city's HP from an attack we just made.

        `end_turn` reads this to say whether the assault is progressing; without it a siege can
        run for a dozen turns with nothing on either side of the table able to tell whether the
        city was losing a single point (live, T105-T116).
        """
        name = str(getattr(estimate, "target_city", "") or "").strip()
        if not name or max_hp <= 0:
            return
        turn = int(getattr(self._last_snapshot, "turn", 0) or self._high_water_turn or 0)
        history = self._city_hp_history.setdefault(name, [])
        if history and history[-1][0] == turn and history[-1][1] == hp:
            return  # same reading twice in one turn adds nothing
        history.append((turn, int(hp), int(max_hp)))
        if len(history) > 30:
            del history[:-30]

    async def unused_attacks(self) -> list[str]:
        """Units that still have moves and a legal attack they have not used.

        Read-only, but run in the **InGame** context: the legality test is built on
        `UnitManager.CanStartOperation`, which does not exist in GameCore (measured live
        2026-09-25: sent through `execute_read` the query died on
        `function expected instead of nil` at that call, and because this method swallows the
        exception by design the answer was silently an empty list). Same context as the
        `>> CAN ATTACK` hints in `get_units`, whose legality test this mirrors exactly - so the
        two can never disagree.
        """
        try:
            lines = await self.conn.execute_write(lq.build_unused_attack_query())
        except Exception as e:
            log.debug("Unused-attack scan failed: %s", e)
            return []
        return lq.parse_unused_attack_response(lines)

    async def siege_posture(self) -> list:
        """Our siege units with their distances to the enemy, their screen and the target city.

        Read-only. What "stage outside enemy range, front line in front, siege behind" means is
        geometry, and the game is asked for it rather than inferred from coordinates.
        """
        try:
            lines = await self.conn.execute_read(lq.build_siege_posture_query())
        except Exception as e:
            log.debug("Siege posture scan failed: %s", e)
            return []
        return lq.parse_siege_posture_response(lines)

    async def capture_readiness(self) -> list:
        """Visible enemy cities, and whether one of our melee units can take them now.

        Read-only, but run in the InGame context: reading an enemy city's districts and their
        damage pools is an InGame-only API (the same reason `build_attack_followup_query` runs
        there). Sent through `execute_write` like the threat scan, which is also read-only.

        The last step of an assault has no damage number attached to it: a melee unit walks onto
        the city's own tile once its HP pool is empty. Only melee-class units can do it and only
        from that tile, so "how many of ours are adjacent" *is* the answer to whether the city
        falls this turn. Live, Moscow sat at `city hp: 0/200` for four turns with a Spearman two
        tiles away, healed about twenty points a turn, and the siege had to be fought again from
        nothing.
        """
        try:
            lines = await self.conn.execute_write(lq.build_capture_check_query())
        except Exception as e:
            log.debug("Capture-readiness scan failed: %s", e)
            return []
        return lq.parse_capture_readiness_response(lines)

    async def city_loyalty(self) -> list:
        """Our cities' loyalty, the pressure on each, and what is holding it up.

        Read-only, InGame context (the loyalty and governor APIs the game's own city panel
        uses). A city can leave the empire without an enemy touching it - live, Moscow was
        captured at T112 and had revolted into a Free City by T116, with no governor and no
        garrison, which cost four turns and nine attacks to undo.
        """
        try:
            lines = await self.conn.execute_write(lq.build_loyalty_check_query())
        except Exception as e:
            log.debug("Loyalty scan failed: %s", e)
            return []
        return lq.parse_loyalty_response(lines)

    @clears_blockers
    async def skip_remaining_units(self, force: bool = False) -> str:
        # Look for attacks that are about to be thrown away *before* finishing moves: after
        # this call the units are fortified and the attack is gone for the turn. Seen live at
        # T109-T116, where a Heavy Chariot sat next to a 7 HP Swordsman for seven turns and
        # was swept up by this call every time without anyone being told.
        #
        # Naming it was not enough. Measured over the T139-T152 Russian war, four attacks were
        # discarded by this sweep and each cost a unit-turn: a Crossbowman pair on the galley
        # at (50,23) on T145, a Horseman adjacent to its target on T148, and a Man-at-Arms
        # twice (T151, and T152 with the second attack ELITE_GUARD grants). So the default is
        # now to refuse: the units are left alone, the attacks are named, and finishing the
        # turn anyway takes an explicit force=True. A refusal is what makes `use-your-attacks`
        # answerable - the rule fires after the fact, this happens before it.
        unused = await self.unused_attacks()
        if unused and not force:
            listed = "\n".join(f"  {entry}" for entry in unused)
            return (
                f"{SKIP_REFUSED}UNUSED ATTACK ({len(unused)} unit(s) have a legal attack and "
                f"have not taken it):\n{listed}\n"
                "  Nothing was swept. Order the attack(s), or call this again with "
                "force=True to discard them on purpose."
            )
        # First try to fortify/heal combat units (InGame context)
        fortify_result = ""
        try:
            lua_fort = lq.build_fortify_remaining_units()
            fort_lines = await self.conn.execute_write(lua_fort)
            fortify_result = _action_result(fort_lines)
        except Exception as e:
            log.debug("Fortify remaining failed: %s", e)
        # Then skip anything still with moves (GameCore context)
        lua = lq.build_skip_remaining_units()
        lines = await self.conn.execute_read(lua)
        skip_result = _action_result(lines)
        parts = [p for p in (fortify_result, skip_result) if p and not p.startswith("Error")]
        report = "\n".join(parts) if parts else skip_result
        if unused:
            listed = "\n".join(f"  {entry}" for entry in unused)
            report += (
                f"\nUNUSED ATTACK ({len(unused)} unit(s) had a legal attack and did not take it):"
                f"\n{listed}\n  These moves are now finished for the turn (force=True)."
            )
        return report

    @clears_blockers
    async def automate_explore(self, unit_index: int) -> str:
        lua = lq.build_automate_explore(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def heal_unit(self, unit_index: int) -> str:
        lua = lq.build_heal_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def alert_unit(self, unit_index: int) -> str:
        lua = lq.build_alert_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def sleep_unit(self, unit_index: int) -> str:
        lua = lq.build_sleep_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def delete_unit(self, unit_index: int) -> str:
        lua = lq.build_delete_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def improve_tile(self, unit_index: int, improvement_name: str) -> str:
        lua = lq.build_improve_tile(unit_index, improvement_name)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def remove_feature(self, unit_index: int) -> str:
        lua = lq.build_remove_feature(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def repair_improvement(self, unit_index: int) -> str:
        lua = lq.build_repair_improvement(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def remove_improvement(self, unit_index: int) -> str:
        lua = lq.build_remove_improvement(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def sacrifice_builder_charges(self, unit_index: int) -> str:
        lua = lq.build_sacrifice_builder_charges(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    async def build_route(self, unit_index: int) -> str:
        lua = lq.build_build_route(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def set_city_production(
        self,
        city_id: int,
        item_type: str,
        item_name: str,
        target_x: int | None = None,
        target_y: int | None = None,
    ) -> str:
        itype = item_type.upper()

        lua = lq.build_produce_item(city_id, item_type, item_name, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)

        # If CanStartOperation failed but CanProduce passed, verify via readback
        if any("MAYBE:" in l for l in lines):
            try:
                verify_lines = await self.conn.execute_read(
                    lq.build_verify_production(city_id, item_name)
                )
                if any("CONFIRMED" in l for l in verify_lines):
                    turns = ""
                    for vl in verify_lines:
                        if vl.startswith("CONFIRMED|"):
                            turns = vl.split("|", 1)[1]
                    return f"PRODUCING|{item_name}|{turns} (bypassed stale CanStartOperation)"
                else:
                    hint = ""
                    if itype == "DISTRICT":
                        hint = f" Tried ({target_x},{target_y})."
                        try:
                            placements = await self.get_district_advisor(
                                city_id, item_name
                            )
                            if isinstance(placements, list) and placements:
                                alts = ", ".join(
                                    f"({p.x},{p.y}) Adj +{p.total_adjacency}"
                                    for p in placements[:5]
                                )
                                hint += f" Valid tiles: {alts}."
                        except Exception:
                            pass
                        hint += " Use get_district_advisor for details."
                    elif itype == "BUILDING":
                        # Check if Lua reported pillaged districts
                        pillaged_dists = ""
                        for ml in lines:
                            if "PILLAGED:" in ml:
                                pillaged_dists = ml.split("PILLAGED:", 1)[1]
                                break
                        if pillaged_dists:
                            hint = (
                                f" Prerequisite district is pillaged:"
                                f" {pillaged_dists}. Repair it first via"
                                " set_city_production(city_id, 'DISTRICT',"
                                " 'DISTRICT_NAME', x, y) — use get_cities"
                                " to find district coordinates."
                            )
                        else:
                            bld_info = item_name.replace("BUILDING_", "")
                            hint = (
                                f" Hint: {bld_info} may require a completed"
                                " district or prerequisite building."
                            )
                    return f"Error: CANNOT_START|{item_name} cannot start.{hint}"
            except Exception:
                log.debug("Production readback failed", exc_info=True)
                return f"Error: CANNOT_START|{item_name} (readback failed)"

        # OK-path verification. RequestOperation is fire-and-forget; even
        # when CanStartOperation returned true it can silently no-op if the
        # queue is in a degenerate state. Round-trip read to confirm.
        if result.startswith("PRODUCING|"):
            try:
                verify_lines = await self.conn.execute_read(
                    lq.build_verify_production(city_id, item_name)
                )
                if any("CONFIRMED" in vl for vl in verify_lines):
                    return result
                not_set = next(
                    (vl for vl in verify_lines if vl.startswith("NOT_SET|")),
                    "NOT_SET|unknown",
                )
                return (
                    f"Error: SILENT_FAILURE|{item_name} appeared to set but "
                    f"the game engine did not persist it ({not_set}). Retry "
                    f"the same call, or use purchase_item to force-commit "
                    f"with gold/faith."
                )
            except Exception:
                log.debug("OK-path production verify failed", exc_info=True)

        return result

    @clears_blockers
    async def purchase_item(
        self,
        city_id: int,
        item_type: str,
        item_name: str,
        yield_type: str = "YIELD_GOLD",
    ) -> str:
        lua = lq.build_purchase_item(city_id, item_type, item_name, yield_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @english_output
    async def list_city_production(self, city_id: int) -> list[lq.ProductionOption]:
        lua = lq.build_city_production_query(city_id)
        # Must use InGame context — bq:CanProduce() throws "Not Implemented" in GameCore
        lines = await self.conn.execute_write(lua)
        return lq.parse_city_production_response(lines)

    @clears_blockers
    async def set_research(self, tech_name: str) -> str:
        lua = lq.build_set_research(tech_name)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if "RESEARCHING" in result:
            # Verify InGame actually accepted it by comparing tech INDEX.
            # RequestPlayerOperation is fire-and-forget — it can silently no-op
            # while GetResearchingTech() still returns the OLD tech's index (!= -1).
            verify = await self.conn.execute_read(
                f"local me = Game.GetLocalPlayer(); "
                f"local idx = nil; "
                f"for row in GameInfo.Technologies() do "
                f'if row.TechnologyType == "{tech_name}" then idx = row.Index; break end '
                f"end; "
                f"local cur = Players[me]:GetTechs():GetResearchingTech(); "
                f"print(cur == idx and 'MATCH' or 'MISMATCH:'..tostring(cur)..'~='..tostring(idx)); "
                f'print("{lq.SENTINEL}")'
            )
            matched = verify and verify[0] == "MATCH"
            if not matched:
                # InGame silently failed — fall back to GameCore
                gc_lua = lq.build_set_research_gamecore(tech_name)
                gc_lines = await self.conn.execute_read(gc_lua)
                return _action_result(gc_lines)
        return result

    @clears_blockers
    async def set_civic(self, civic_name: str) -> str:
        lua = lq.build_set_civic(civic_name)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if "PROGRESSING" in result:
            # Verify InGame actually accepted it by comparing civic INDEX.
            verify = await self.conn.execute_read(
                f"local me = Game.GetLocalPlayer(); "
                f"local idx = nil; "
                f"for row in GameInfo.Civics() do "
                f'if row.CivicType == "{civic_name}" then idx = row.Index; break end '
                f"end; "
                f"local cur = Players[me]:GetCulture():GetProgressingCivic(); "
                f"print(cur == idx and 'MATCH' or 'MISMATCH:'..tostring(cur)..'~='..tostring(idx)); "
                f'print("{lq.SENTINEL}")'
            )
            matched = verify and verify[0] == "MATCH"
            if not matched:
                # InGame silently failed — fall back to GameCore
                lua_gc = lq.build_set_civic_gamecore(civic_name)
                gc_lines = await self.conn.execute_read(lua_gc)
                return _action_result(gc_lines)
        return result

    # ------------------------------------------------------------------
    # Diplomacy methods
    # ------------------------------------------------------------------

    async def get_diplomacy_sessions(self) -> list[lq.DiplomacySession]:
        lua = lq.build_diplomacy_session_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_diplomacy_sessions(lines)

    @clears_blockers
    async def diplomacy_respond(self, other_player_id: int, response: str) -> str:
        # Capture dialogue text BEFORE response to detect goodbye phase
        pre_sessions = await self.get_diplomacy_sessions()
        pre_text = ""
        for s in pre_sessions:
            if s.other_player_id == other_player_id:
                pre_text = s.dialogue_text
                break

        # Phase 1: Send AddResponse only (no CloseSession — engine handles lifecycle)
        lua = lq.build_diplomacy_respond(other_player_id, response.upper())
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)

        # EXIT and error paths return immediately
        if "SESSION_CLOSED" in result or result.startswith("Error"):
            return result

        # Phase 2: Give engine ~9 frames (0.3s at 30fps) to process the
        # response and transition/close the session, then check state in
        # a separate TCP round-trip (same-frame checks see stale state).
        await asyncio.sleep(0.3)
        check_lines = await self.conn.execute_write(
            lq.build_check_diplomacy_session_state(other_player_id)
        )
        if not any("SESSION_OPEN" in l for l in check_lines):
            return f"OK:RESPONDED|{response.upper()}|SESSION_CLOSED"

        # Phase 3: Session still open — check if dialogue text changed.
        # If unchanged, we're in the goodbye phase. Auto-close.
        post_sessions = await self.get_diplomacy_sessions()
        post_text = ""
        for s in post_sessions:
            if s.other_player_id == other_player_id:
                post_text = s.dialogue_text
                break

        if not post_sessions:
            # Session disappeared between checks (race condition)
            return f"OK:RESPONDED|{response.upper()}|SESSION_CLOSED"

        if post_text == pre_text:
            # Dialogue unchanged → goodbye phase. Force close.
            log.info(
                "Goodbye phase detected (text unchanged) for player %d — auto-closing",
                other_player_id,
            )
            close_lua = lq.build_diplomacy_respond(other_player_id, "EXIT")
            await self.conn.execute_write(close_lua)
            return f"OK:RESPONDED|{response.upper()}|SESSION_CLOSED (auto-closed goodbye phase)"

        # Include the new dialogue text so the agent can see what the leader said
        post_reason = ""
        for s in post_sessions:
            if s.other_player_id == other_player_id:
                post_reason = s.reason_text
                break
        dialogue_note = f'\nLeader says: "{post_text}"'
        if post_reason:
            dialogue_note += f'\nReason/agenda: "{post_reason}"'
        return f"OK:RESPONDED|{response.upper()}|SESSION_CONTINUES{dialogue_note}"

    @clears_blockers
    async def send_diplomatic_action(self, other_player_id: int, action: str) -> str:
        if action.upper() == "OPEN_BORDERS":
            # Session-based OPEN_BORDERS causes AI turn hang.
            # Route through the trade deal API instead (mutual open borders).
            return await self.propose_trade(
                other_player_id,
                offer_items=[{"type": "AGREEMENT", "subtype": "OPEN_BORDERS"}],
                request_items=[{"type": "AGREEMENT", "subtype": "OPEN_BORDERS"}],
            )
        is_war = action.upper().endswith("_WAR") and action.upper().startswith(
            "DECLARE_"
        )
        lua = lq.build_send_diplo_action(other_player_id, action.upper())
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)

        if is_war and not result.startswith("ERR:"):
            # War session left open for ~8s so the leader animation plays.
            # Background task will close session + dismiss DiplomacyActionView.
            asyncio.create_task(self._cleanup_war_diplomacy(other_player_id))

        return result

    async def _cleanup_war_diplomacy(self, other_player_id: int) -> None:
        """Background: dismiss war declaration diplomacy view after animation.

        Two-phase cleanup (must be separate Lua calls — the engine fires
        OnDiplomacySessionClosed asynchronously so the view needs a frame
        to transition from CONVERSATION_MODE to OVERVIEW_MODE):
        1. CloseSession — view transitions to OVERVIEW_MODE
        2. NaturalWonderPopup trick — forces Close() from OVERVIEW_MODE
        """
        await asyncio.sleep(8)
        try:
            # Phase 1: close session → view goes to OVERVIEW_MODE
            lua1 = lq.build_war_close_session(other_player_id)
            await self.conn.execute_write(lua1)

            # Let engine process OnDiplomacySessionClosed
            await asyncio.sleep(1)

            # Phase 2: force-dismiss the OVERVIEW_MODE view
            lua2 = lq.build_war_dismiss_view()
            await self.conn.execute_write(lua2)
        except Exception as e:
            log.warning("War diplomacy cleanup failed: %s", e)

    # ------------------------------------------------------------------
    # Trade deal methods (InGame context)
    # ------------------------------------------------------------------

    async def get_deal_options(self, other_player_id: int) -> lq.DealOptions:
        lua = lq.build_deal_options_query(other_player_id)
        lines = await self.conn.execute_write(lua)
        return lq.parse_deal_options_response(lines)

    async def get_pending_deals(self) -> list[lq.PendingDeal]:
        lua = lq.build_pending_deals_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_pending_deals_response(lines)

    @clears_blockers
    async def respond_to_deal(self, other_player_id: int, accept: bool) -> str:
        lua = lq.build_respond_to_deal(other_player_id, accept)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def propose_trade(
        self,
        other_player_id: int,
        offer_items: list[dict],
        request_items: list[dict],
    ) -> str:
        lua = lq.build_propose_trade(other_player_id, offer_items, request_items)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        # Dismiss diplomacy UI left open by the trade session.
        # After CloseSession, the game transitions DiplomacyActionView to
        # OVERVIEW_MODE (intel screen). Need a brief delay for the C++ UI
        # state machine to settle, then dismiss it in a separate call.
        await asyncio.sleep(0.3)
        try:
            await self.conn.execute_write(
                'pcall(function() ContextPtr:LookUpControl("/InGame/DiplomacyActionView"):SetHide(true) end) '
                "pcall(function() Events.HideLeaderScreen() end) "
                "LuaEvents.DiplomacyActionView_ShowIngameUI() "
                f'print("{lq.SENTINEL}")'
            )
        except Exception:
            pass
        return result

    async def test_trade(
        self,
        other_player_id: int,
        offer_items: list[dict],
        request_items: list[dict],
    ) -> str:
        lua = lq.build_test_trade(other_player_id, offer_items, request_items)
        lines = await self.conn.execute_write(lua)
        result = lq.parse_test_trade_response(lines)
        return narrate_test_trade(result)

    @clears_blockers
    async def propose_peace(self, other_player_id: int) -> str:
        lua = lq.build_propose_peace(other_player_id)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if result.startswith("Error"):
            return result
        # War state is async — verify with a second round-trip
        verify_lines = await self.conn.execute_write(
            lq.build_check_war_state(other_player_id)
        )
        at_peace = any("AT_PEACE" in l for l in verify_lines)
        name = result.split("|", 1)[1] if "|" in result else f"player {other_player_id}"
        if at_peace:
            return f"ACCEPTED|Peace established with {name}"
        else:
            return f"REJECTED|{name} rejected your peace offer"

    @clears_blockers
    async def form_alliance(self, other_player_id: int, alliance_type: str) -> str:
        lua = lq.build_form_alliance(other_player_id, alliance_type.upper())
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Policy methods (InGame context)
    # ------------------------------------------------------------------

    @english_output
    async def get_policies(self) -> lq.GovernmentStatus:
        lua = lq.build_policies_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_policies_response(lines)

    @clears_blockers
    async def set_policies(self, assignments: dict[int, str]) -> str:
        # Read the slots before the change. The engine will not tell anyone that a policy which
        # halves every upgrade just left the government, and the bill for that arrives later.
        before: set[str] = set()
        try:
            existing = await self.get_policies()
            before = {s.current_policy for s in existing.slots if s.current_policy}
        except Exception:
            log.debug("policy pre-read failed", exc_info=True)
        lua = lq.build_set_policies(assignments)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if not result.startswith("Error"):
            # Post-verify: RequestPolicyChanges can silently no-op (e.g. during era transitions)
            status = await self.get_policies()
            slot_map = {s.slot_index: s.current_policy for s in status.slots}
            mismatches = []
            for idx, pol in assignments.items():
                expected = None if pol.upper() == "NONE" else pol
                actual = slot_map.get(idx)
                if actual != expected:
                    wanted = "EMPTY" if expected is None else pol
                    got = actual or "EMPTY"
                    mismatches.append(f"slot {idx} (wanted {wanted}, got {got})")
            if mismatches:
                result += (
                    f"\nWARN:SILENT_FAILURE — engine rejected: {', '.join(mismatches)}. "
                    "Try a different policy or retry next turn."
                )
            after = {s.current_policy for s in status.slots if s.current_policy}
            result += self._upgrade_discount_note(before, after)
        return result

    # The one policy whose removal changes the price of every pending upgrade.
    UPGRADE_DISCOUNT_POLICY = "POLICY_PROFESSIONAL_ARMY"

    def _upgrade_discount_note(self, before: set[str], after: set[str]) -> str:
        """Warn when a policy change drops the card that halves every unit upgrade.

        Measured T201: the free policy window traded `POLICY_PROFESSIONAL_ARMY` - the game's own
        text is "50% discount on all unit upgrades" - for `POLICY_MEDINA_QUARTER` (+2 housing in
        cities with 3+ districts) to clear a housing hard stop in 西安, and every pending offer
        doubled with it: Knight -> Cuirassier 115g -> 230g, Crossbowman -> Field Cannon 155g ->
        310g, Spearman -> Pikeman 190g -> 380g. Twelve turns later two of them were bought anyway:
        540g paid where 270g would have done. The trade may still be right - it just has to be a
        decision rather than a side effect.
        """
        if self.UPGRADE_DISCOUNT_POLICY not in before:
            return ""
        if self.UPGRADE_DISCOUNT_POLICY in after:
            return ""  # still in the government, possibly in a different slot
        return (
            f"\nNOTE:UPGRADE_DISCOUNT_LOST — this change takes "
            f"{self.UPGRADE_DISCOUNT_POLICY} ('50% discount on all unit upgrades') out of the "
            f"government, so every pending upgrade now costs double. Check `UPGRADE AVAILABLE` "
            f"before accepting that trade: measured T201-T217, losing it cost 270g on the next "
            f"two purchases (115 -> 230 and 155 -> 310)."
        )

    # ------------------------------------------------------------------
    # Governor methods (InGame context)
    # ------------------------------------------------------------------

    @english_output
    async def get_governors(self) -> lq.GovernorStatus:
        lua = lq.build_governors_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_governors_response(lines)

    @clears_blockers
    async def appoint_governor(self, governor_type: str) -> str:
        lua = lq.build_appoint_governor(governor_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def assign_governor(self, governor_type: str, city_id: int) -> str:
        lua = lq.build_assign_governor(governor_type, city_id)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def promote_governor(self, governor_type: str, promotion_type: str) -> str:
        lua = lq.build_promote_governor(governor_type, promotion_type)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if "PROMOTED" in result:
            # Verify promotion actually applied (RequestPlayerOperation is async)
            verify = await self.conn.execute_write(
                f"local me = Game.GetLocalPlayer(); "
                f"local pGovs = Players[me]:GetGovernors(); "
                f'local gov = GameInfo.Governors["{governor_type}"]; '
                f'local promo = GameInfo.GovernorPromotions["{promotion_type}"]; '
                f"if gov and promo then "
                f"  local g = pGovs:GetGovernor(gov.Hash); "
                f"  if g and g:HasPromotion(promo.Index) then "
                f'    print("VERIFIED") '
                f"  else "
                f'    print("ERR:PROMOTION_FAILED|{promotion_type} was not applied") '
                f"  end "
                f"else "
                f'  print("ERR:LOOKUP_FAILED") '
                f"end; "
                f'print("{lq.SENTINEL}")'
            )
            if any("ERR:" in l for l in verify):
                return _action_result(verify)
        return result

    # ------------------------------------------------------------------
    # Promotion methods
    # ------------------------------------------------------------------

    @english_output
    async def get_unit_promotions(self, unit_id: int) -> lq.UnitPromotionStatus:
        unit_index = unit_id % 65536
        lua = lq.build_unit_promotions_query(unit_index)
        lines = await self.conn.execute_read(lua)
        return lq.parse_unit_promotions_response(lines)

    @clears_blockers
    async def promote_unit(self, unit_id: int, promotion_type: str) -> str:
        unit_index = unit_id % 65536
        lua = lq.build_promote_unit(unit_index, promotion_type)
        lines = await self.conn.execute_read(lua)  # GameCore context
        result = _action_result(lines)
        # GameCore SetPromotion doesn't clear the InGame NEEDS_PROMOTION
        # notification, which blocks end_turn until dismissed.
        # Use XP-threshold formula (matching end_turn handler) to decide
        # whether any unit still genuinely needs a promotion before dismissing.
        if not result.startswith("Error"):
            try:
                await self.conn.execute_write(
                    f"local me = Game.GetLocalPlayer(); "
                    f"local anyNeed = false; "
                    f"for i, u in Players[me]:GetUnits():Members() do "
                    f"  if u:GetX() ~= -9999 then "
                    f"    local ok, exp = pcall(function() return u:GetExperience() end); "
                    f"    if ok and exp then "
                    f"      local ui = GameInfo.Units[u:GetType()]; "
                    f'      local promClass = ui and ui.PromotionClass or ""; '
                    f'      if promClass ~= "" then '
                    f"        local promoCount = 0; "
                    f"        for p in GameInfo.UnitPromotions() do "
                    f"          if p.PromotionClass == promClass and exp:HasPromotion(p.Index) then "
                    f"            promoCount = promoCount + 1 "
                    f"          end "
                    f"        end; "
                    f"        local t1 = exp:GetExperienceForNextLevel(); "
                    f"        local xp = exp:GetExperiencePoints(); "
                    f"        local needed = t1 * (promoCount + 1) * (promoCount + 2) / 2; "
                    f"        if xp >= needed then "
                    f"          anyNeed = true "
                    f"        else "
                    f"          local stored = 0; "
                    f"          pcall(function() stored = exp:GetStoredPromotions() end); "
                    f"          if stored > 0 then "
                    f"            pcall(function() exp:ChangeStoredPromotions(-stored) end) "
                    f"          end "
                    f"        end "
                    f"      end "
                    f"    end "
                    f"  end "
                    f"  if anyNeed then break end "
                    f"end; "
                    f"if not anyNeed then "
                    f"  local list = NotificationManager.GetList(me); "
                    f"  if list then "
                    f"    for _, nid in ipairs(list) do "
                    f"      local e = NotificationManager.Find(me, nid); "
                    f"      if e and not e:IsDismissed() then "
                    f"        local bt = e:GetEndTurnBlocking(); "
                    f"        if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_UNIT_PROMOTION then "
                    f"          pcall(function() NotificationManager.SendActivated(me, nid) end); "
                    f"          pcall(function() NotificationManager.Dismiss(me, nid) end) "
                    f"        else "
                    f"          local tn = ''; "
                    f"          pcall(function() tn = e:GetTypeName() end); "
                    f"          if tn == 'NOTIFICATION_UNIT_PROMOTION_AVAILABLE' then "
                    f"            pcall(function() NotificationManager.Dismiss(me, nid) end) "
                    f"          end "
                    f"        end "
                    f"      end "
                    f"    end "
                    f"  end "
                    f"end; "
                    f'print("OK"); print("{lq.SENTINEL}")'
                )
            except Exception:
                pass  # non-fatal — end_turn blocker handler will catch it
        return result

    # ------------------------------------------------------------------
    # City-state / Envoy methods (InGame context)
    # ------------------------------------------------------------------

    @english_output
    async def get_city_states(self) -> lq.EnvoyStatus:
        lua = lq.build_city_states_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_city_states_response(lines)

    @clears_blockers
    async def send_envoy(self, city_state_player_id: int) -> str:
        lua = lq.build_send_envoy(city_state_player_id)
        lines = await self.conn.execute_write(lua)
        result = _action_result(lines)
        if result.startswith("OK:ENVOY_SENT"):
            # Verify token actually decremented (async race condition workaround)
            await asyncio.sleep(0.1)
            try:
                verify_lines = await self.conn.execute_write(
                    f"local me = Game.GetLocalPlayer(); "
                    f"print(Players[me]:GetInfluence():GetTokensToGive()); "
                    f'print("{lq.SENTINEL}")'
                )
                if verify_lines and verify_lines[0].strip().lstrip("-").isdigit():
                    actual = int(verify_lines[0].strip())
                    result += f" (verified remaining: {actual})"
            except Exception:
                log.debug("Envoy verification failed", exc_info=True)
        return result

    # ------------------------------------------------------------------
    # Pantheon methods (InGame context)
    # ------------------------------------------------------------------

    @english_output
    async def get_pantheon_status(self) -> lq.PantheonStatus:
        lua = lq.build_pantheon_status_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_pantheon_status_response(lines)

    @clears_blockers
    async def choose_pantheon(self, belief_type: str) -> str:
        lua = lq.build_choose_pantheon(belief_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Religion founding methods (InGame context)
    # ------------------------------------------------------------------

    async def get_religion_founding_status(self) -> lq.ReligionFoundingStatus:
        lua = lq.build_religion_beliefs_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_religion_beliefs_response(lines)

    @clears_blockers
    async def found_religion(
        self, religion_type: str, follower_belief: str, founder_belief: str
    ) -> str:
        lua = lq.build_found_religion(religion_type, follower_belief, founder_belief)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Unit upgrade methods (InGame context)
    # ------------------------------------------------------------------

    async def check_unit_upgrade(self, unit_id: int) -> str:
        unit_index = unit_id % 65536
        lua = lq.build_unit_upgrade_query(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def upgrade_unit(self, unit_id: int) -> str:
        unit_index = unit_id % 65536
        lua = lq.build_upgrade_unit(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Dedications / Commemorations
    # ------------------------------------------------------------------

    @english_output
    async def get_dedications(self) -> lq.DedicationStatus:
        lua = lq.build_dedications_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_dedications_response(lines)

    @clears_blockers
    async def choose_dedication(self, dedication_index: int) -> str:
        lua = lq.build_choose_dedication(dedication_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # District / wonder advisor (with per-turn budget)
    # ------------------------------------------------------------------

    # Pathological loops (Gemini Pro's 1,567 calls in one turn) motivate a
    # per-turn budget. Opus averages 2-4 advisor calls/turn so 20 leaves
    # 5x headroom for legitimate exploration.
    ADVISOR_BUDGET_SOFT = 10
    ADVISOR_BUDGET_HARD = 20

    def _advisor_budget_check(self) -> tuple[str | None, str | None]:
        """Check advisor budget. Returns (hard_error, soft_warning).

        - hard_error: short-circuit string if budget exceeded (caller returns it)
        - soft_warning: string to prepend to the result, or None
        """
        # Increment unconditionally — the hard-cap path stays sticky until
        # the end-of-turn reset, and reporting the true call count is more
        # honest for logs and telemetry.
        self._advisor_calls_this_turn += 1
        n = self._advisor_calls_this_turn
        if n > self.ADVISOR_BUDGET_HARD:
            return (
                f"ERR:ADVISOR_BUDGET_EXCEEDED|You have made {n} advisor calls "
                f"this turn (limit {self.ADVISOR_BUDGET_HARD}). The advisors "
                f"rank placements; they are not for brute-forcing every "
                f"wonder or district. Make a decision with the information "
                f"you already have, skip this step, or end your turn. Budget "
                f"resets next turn.",
                None,
            )
        if n >= self.ADVISOR_BUDGET_SOFT:
            return (
                None,
                f"ADVISOR BUDGET WARNING: {n}/{self.ADVISOR_BUDGET_HARD} "
                f"advisor calls this turn. Consolidate your queries — the "
                f"advisors rank placements, not iterate through options.",
            )
        return None, None

    @english_output
    async def get_district_advisor(
        self, city_id: int, district_type: str
    ) -> list[lq.DistrictPlacement] | str:
        """Returns placements list, or an error string if placement is impossible."""
        hard_err, soft_warn = self._advisor_budget_check()
        if hard_err:
            return hard_err
        lua = lq.build_district_advisor_query(city_id, district_type)
        lines = await self.conn.execute_write(lua)
        # Check for error bail lines (parser only looks for DPLOT| and silently
        # discards errors, losing the actual reason for failure)
        for line in lines:
            if line.startswith("ERR:"):
                return line  # propagate the specific error to the agent
        # Warning only attaches to the success path — error-string returns
        # bypass the server wrapper's narration branch and would otherwise
        # leave a stale warning for the next advisor call.
        self._advisor_budget_warning = soft_warn
        return lq.parse_district_advisor_response(lines)

    @english_output
    async def get_wonder_advisor(
        self, city_id: int, wonder_name: str
    ) -> list[lq.WonderPlacement] | str:
        """Returns placements list, or an error string if budget exceeded."""
        hard_err, soft_warn = self._advisor_budget_check()
        if hard_err:
            return hard_err
        lua = lq.build_wonder_advisor_query(city_id, wonder_name)
        lines = await self.conn.execute_write(lua)
        # Warning only attaches to the success path (same reason as above)
        self._advisor_budget_warning = soft_warn
        return lq.parse_wonder_advisor_response(lines)

    # ------------------------------------------------------------------
    # Tile purchase methods (InGame context)
    # ------------------------------------------------------------------

    @english_output
    async def get_purchasable_tiles(self, city_id: int) -> list[lq.PurchasableTile]:
        lua = lq.build_purchasable_tiles_query(city_id)
        lines = await self.conn.execute_write(lua)
        return lq.parse_purchasable_tiles_response(lines)

    @clears_blockers
    async def purchase_tile(self, city_id: int, x: int, y: int) -> str:
        lua = lq.build_purchase_tile(city_id, x, y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Government change (InGame context)
    # ------------------------------------------------------------------

    @clears_blockers
    async def change_government(self, government_type: str) -> str:
        lua = lq.build_change_government(government_type)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Great People (InGame context)
    # ------------------------------------------------------------------

    @english_output
    async def get_great_people(self) -> list[lq.GreatPersonInfo]:
        lua = lq.build_great_people_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_great_people_response(lines)

    async def get_gp_advisor(self, unit_index: int) -> lq.GPAdvisorResult | None:
        lua = lq.build_gp_advisor_query(unit_index)
        lines = await self.conn.execute_write(lua)
        return lq.parse_gp_advisor_response(lines)

    @clears_blockers
    async def recruit_great_person(self, individual_id: int) -> str:
        lua = lq.build_recruit_great_person(individual_id)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    @clears_blockers
    async def patronize_great_person(
        self, individual_id: int, yield_type: str = "YIELD_GOLD"
    ) -> str:
        lua = lq.build_patronize_great_person(individual_id, yield_type)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    @english_output
    async def get_religion_status(self) -> lq.ReligionStatus:
        lines = await self.conn.execute_write(lq.build_religion_status_query())
        return lq.parse_religion_status_response(lines)

    @clears_blockers
    async def reject_great_person(self, individual_id: int) -> str:
        lua = lq.build_reject_great_person(individual_id)
        lines = await self.conn.execute_write(lua)
        return lines[0] if lines else "No response"

    # ------------------------------------------------------------------
    # Trade route methods (InGame context)
    # ------------------------------------------------------------------

    @english_output
    async def get_trade_routes(self) -> lq.TradeRouteStatus:
        lua = lq.build_trade_routes_query()
        lines = await self.conn.execute_write(
            lua
        )  # InGame context (GetOutgoingRoutes is InGame-only)
        return lq.parse_trade_routes_response(lines)

    @english_output
    async def get_trade_destinations(
        self, unit_index: int
    ) -> list[lq.TradeDestination]:
        lua = lq.build_trade_destinations_query(unit_index)
        lines = await self.conn.execute_write(lua)
        return lq.parse_trade_destinations_response(lines)

    @clears_blockers
    async def make_trade_route(
        self, unit_index: int, target_x: int, target_y: int
    ) -> str:
        lua = lq.build_make_trade_route(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Great Person activation (InGame context)
    # ------------------------------------------------------------------

    @clears_blockers
    async def activate_great_person(self, unit_index: int) -> str:
        lua = lq.build_activate_great_person(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def spread_religion(self, unit_index: int) -> str:
        lua = lq.build_spread_religion(unit_index)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Trader teleport (InGame context)
    # ------------------------------------------------------------------

    @clears_blockers
    async def teleport_to_city(
        self, unit_index: int, target_x: int, target_y: int
    ) -> str:
        lua = lq.build_teleport_to_city(unit_index, target_x, target_y)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # World Congress (InGame context)
    # ------------------------------------------------------------------

    async def get_world_congress(self) -> lq.WorldCongressStatus:
        lua = lq.build_world_congress_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_world_congress_response(lines)

    @clears_blockers
    async def vote_world_congress(
        self, resolution_hash: int, option: int, target_index: int, num_votes: int
    ) -> str:
        lua = lq.build_congress_vote(resolution_hash, option, target_index, num_votes)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def submit_congress(self) -> str:
        lua = lq.build_congress_submit()
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    @clears_blockers
    async def queue_wc_votes(self, votes: list[dict]) -> str:
        """Store agent voting preferences and register WC event handler."""
        lua = lq.build_register_wc_voter(votes=votes)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # City yield focus (InGame context)
    # ------------------------------------------------------------------

    @clears_blockers
    async def set_city_focus(self, city_id: int, focus: str) -> str:
        lua = lq.build_set_yield_focus(city_id, focus)
        lines = await self.conn.execute_write(lua)
        return _action_result(lines)

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    @english_output
    async def get_notifications(self) -> list[lq.GameNotification]:
        lua = lq.build_notifications_query()
        lines = await self.conn.execute_write(lua)
        return lq.parse_notifications_response(lines)

    # ------------------------------------------------------------------
    # Snapshot-diff for turn event detection
    # ------------------------------------------------------------------

    async def _take_snapshot(
        self, overview: lq.GameOverview | None = None
    ) -> lq.TurnSnapshot:
        """Capture current game state for diffing."""
        if overview is None:
            ov_lines = await self.conn.execute_write(lq.build_overview_query())
            overview = lq.parse_overview_response(ov_lines)

        # InGame, not GameCore: `build_units_query` is documented InGame and its line-of-sight
        # filter calls `UnitManager.CanStartOperation`, which GameCore does not have. Read there,
        # the query died with "function expected instead of nil" and the whole unit list was lost -
        # live T122, the post-turn snapshot right after Moscow was captured answered
        # "turn checks: no unit list available for T122 at all". The cities query in this same
        # function already reads InGame.
        unit_lines = await self.conn.execute_write(lq.build_units_query())
        units = lq.parse_units_response(unit_lines)

        city_lines = await self.conn.execute_write(lq.build_cities_query())
        cities, _ = lq.parse_cities_response(city_lines)

        try:
            stk_lines = await self.conn.execute_write(lq.build_stockpile_query())
            stockpiles = lq.parse_stockpile_response(stk_lines)
        except Exception:
            log.debug("Stockpile query failed", exc_info=True)
            stockpiles = []

        return lq.TurnSnapshot(
            turn=overview.turn,
            units={u.unit_id: u for u in units},
            cities={
                c.city_id: lq.CitySnapshot(
                    city_id=c.city_id,
                    name=c.name,
                    population=c.population,
                    currently_building=c.currently_building,
                    x=c.x,
                    y=c.y,
                    food_surplus=c.food_surplus,
                    turns_to_grow=c.turns_to_grow,
                    loyalty=c.loyalty,
                    loyalty_per_turn=c.loyalty_per_turn,
                )
                for c in cities
            },
            current_research=overview.current_research,
            current_civic=overview.current_civic,
            stockpiles=stockpiles,
        )

    @staticmethod
    def _diff_snapshots(
        before: lq.TurnSnapshot, after: lq.TurnSnapshot
    ) -> list[lq.TurnEvent]:
        """Compare two snapshots and generate events."""
        events: list[lq.TurnEvent] = []

        # --- Unit events ---
        for uid, ub in before.units.items():
            if uid not in after.units:
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="unit",
                        message=f"Your {ub.name} ({ub.unit_type}) was killed! Last seen at ({ub.x},{ub.y}).",
                    )
                )
            else:
                ua = after.units[uid]
                dmg = ub.health - ua.health
                if dmg > 0:
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="unit",
                            message=f"Your {ua.name} ({ua.unit_type}) took {dmg} damage! HP: {ua.health}/{ua.max_health} at ({ua.x},{ua.y}).",
                        )
                    )
                elif dmg < 0:
                    events.append(
                        lq.TurnEvent(
                            priority=3,
                            category="unit",
                            message=f"Your {ua.name} ({ua.unit_type}) healed {-dmg} HP. HP: {ua.health}/{ua.max_health}.",
                        )
                    )

        for uid, ua in after.units.items():
            if uid not in before.units:
                events.append(
                    lq.TurnEvent(
                        priority=3,
                        category="unit",
                        message=f"New unit: {ua.name} ({ua.unit_type}) at ({ua.x},{ua.y}).",
                    )
                )

        # --- City events ---
        for cid, cb in before.cities.items():
            if cid not in after.cities:
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="city",
                        message=f"City {cb.name} was lost!",
                    )
                )
            else:
                ca = after.cities[cid]
                if ca.population > cb.population:
                    events.append(
                        lq.TurnEvent(
                            priority=3,
                            category="city",
                            message=f"{ca.name} grew to population {ca.population}.",
                        )
                    )
                if (
                    cb.currently_building != "NONE"
                    and ca.currently_building != cb.currently_building
                ):
                    now = ca.currently_building
                    if now in ("NONE", "nothing"):
                        now = "nothing"
                    elif now == "CORRUPTED_QUEUE":
                        now = "nothing (queue invalidated — set new production)"
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="city",
                            message=f"{ca.name} finished building {cb.currently_building}. Now: {now}.",
                        )
                    )

        for cid, ca in after.cities.items():
            if cid not in before.cities:
                events.append(
                    lq.TurnEvent(
                        priority=2,
                        category="city",
                        message=f"New city founded: {ca.name}!",
                    )
                )

        # --- Research/civic events ---
        if (
            before.current_research != "None"
            and after.current_research != before.current_research
        ):
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="research",
                    message=f"Research complete: {before.current_research}! Now: {after.current_research}.",
                )
            )

        if (
            before.current_civic != "None"
            and after.current_civic != before.current_civic
        ):
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="civic",
                    message=f"Civic complete: {before.current_civic}! Now: {after.current_civic}.",
                )
            )

        # --- Stockpile events ---
        before_stk = {s.name: s for s in before.stockpiles}
        after_stk = {s.name: s for s in after.stockpiles}
        for name, sa in after_stk.items():
            sb = before_stk.get(name)
            if sb and sb.amount > 0 and sa.amount == 0:
                net = sa.per_turn - sa.demand + sa.imported
                events.append(
                    lq.TurnEvent(
                        priority=2,
                        category="resources",
                        message=f"DEPLETED: {name} stockpile hit 0 ({net:+d}/t) — units requiring {name} may be disbanded.",
                    )
                )

        events.sort(key=lambda e: e.priority)
        return events

    @staticmethod
    def _build_turn_report(
        turn_before: int,
        turn_after: int,
        events: list[lq.TurnEvent],
        notifications: list[lq.GameNotification],
        stockpiles: list[lq.ResourceStockpile] | None = None,
        score: int | None = None,
    ) -> str:
        """Format turn events and notifications into a scannable report."""
        header = f"Turn {turn_before} -> {turn_after}"
        if score is not None:
            header += f" | Score: {score}"
        lines = [header]

        if stockpiles:
            visible = [
                s for s in stockpiles if s.amount > 0 or s.per_turn > 0 or s.demand > 0
            ]
            if visible:
                parts = []
                for s in visible:
                    net = s.per_turn - s.demand + s.imported
                    parts.append(f"{s.name} {s.amount}/{s.cap} ({net:+d}/t)")
                lines.append(f"Resources: {', '.join(parts)}")

        if events:
            lines.append("")
            lines.append("== Events ==")
            icons = {1: "!!!", 2: ">>", 3: "--"}
            for e in events:
                icon = icons.get(e.priority, "--")
                lines.append(f"  {icon} {e.message}")

        # Use the enriched is_action_required field from the parser
        action_required = [n for n in notifications if n.is_action_required]
        # Only show informational notifications from the last 2 turns — older ones
        # are stale (e.g. "Wonder Completed" from 3 turns ago) and clutter the report.
        recent_cutoff = (turn_after or 0) - 2
        info_notifs = [
            n
            for n in notifications
            if not n.is_action_required and n.turn >= recent_cutoff
        ]

        if action_required:
            lines.append("")
            lines.append("== Action Required ==")
            for n in action_required:
                hint = f"  -> Use: {n.resolution_hint}" if n.resolution_hint else ""
                lines.append(f"  * {n.message}{hint}")

        if info_notifs:
            lines.append("")
            lines.append("== Notifications ==")
            for n in info_notifs:
                lines.append(f"  - {n.message}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    async def end_turn(self) -> str:
        """End the turn with snapshot-diff event detection."""
        from civ_mcp.end_turn import execute_end_turn

        return await execute_end_turn(self)

    async def dismiss_popup(self) -> str:
        """Dismiss any blocking popup or UI overlay."""
        from civ_mcp.game_lifecycle import dismiss_popup

        return await dismiss_popup(self.conn)

    async def _clear_action_blockers(self) -> str:
        """Best-effort popup clear in front of a deliberate write.

        Never raises and never fails an action: a popup layer the game will not
        let us clear is a reason to *try* the action anyway, not a reason to
        refuse it. The reply is dropped on the floor because every caller
        reports its own outcome, and a `No popups to dismiss.` line in front of
        every result would be noise. What it must not do is hide a
        `PENDING|DiplomacyActionView` - an open session is the caller's to
        answer, and `end_turn` is what names it.
        """
        try:
            return await self.dismiss_popup()
        except Exception:
            log.debug("Pre-action popup dismiss failed", exc_info=True)
            return ""

    async def list_saves(self) -> str:
        """List available save files."""
        from civ_mcp.game_lifecycle import list_saves

        return await list_saves(self.conn)

    async def load_save(self, save_index: int) -> str:
        """Load a save file by index."""
        import time
        from civ_mcp.game_lifecycle import load_save

        result = await load_save(self.conn, save_index)
        if not result.startswith(("Error", "ERR", "FAILED")):
            self._record_save_load(f"index:{save_index}")
        return result

    async def load_game_save(self, save_name: str) -> str:
        """Load a save file by name (no list_saves prerequisite)."""
        from civ_mcp.game_lifecycle import load_game_save

        result = await load_game_save(self.conn, save_name)
        if not result.startswith(("Error", "ERR", "FAILED")):
            self._record_save_load(save_name)
        return result

    def _record_save_load(self, save_name: str) -> None:
        """Record a successful save load for scumming detection."""
        import time

        ts = time.time()
        turn = self._high_water_turn
        self._save_load_history.append((ts, turn, save_name))
        # Keep bounded
        if len(self._save_load_history) > 50:
            self._save_load_history = self._save_load_history[-50:]

    async def execute_lua(self, code: str, context: str = "gamecore") -> str:
        """Escape hatch: run arbitrary Lua code."""
        from civ_mcp.game_lifecycle import execute_lua

        return await execute_lua(self.conn, code, context)


def _action_result(lines: list[str]) -> str:
    """Parse OK:/ERR: prefixed action responses.

    Scans all lines for the first OK:/ERR: prefix, since LuaEvent
    callbacks (e.g. ShowIngameUI → BulkHide debug prints) can inject
    spurious output before the actual result line.
    """
    if not lines:
        return "Action completed (no response)."
    for line in lines:
        if line.startswith("OK:"):
            return line[3:]
        if line.startswith("ERR:"):
            return f"Error: {line[4:]}"
    # No OK/ERR found — return all lines for debugging
    return "\n".join(lines)


def _format_attack_followup(lines: list[str], attacker_owner: int = 0) -> str:
    """Format the GameCore follow-up read after an attack.

    Filters out units belonging to ``attacker_owner`` so that after a melee
    kill (where the attacker moves onto the target tile) we don't misreport
    our own unit's HP as the defender's.

    Also includes city wall/garrison HP when attacking a walled city.
    """
    parts = []
    for line in lines:
        if line.startswith("UNIT|"):
            fields = line.split("|")
            if len(fields) >= 4:
                # fields: UNIT|TYPE|hp/max|owner:N
                owner_str = fields[3]  # "owner:N"
                try:
                    owner_id = int(owner_str.split(":")[1])
                except (IndexError, ValueError):
                    owner_id = -1
                label = "(yours) " if owner_id == attacker_owner else ""
                parts.append(f"{label}{fields[1]} {fields[2]}")
            elif len(fields) >= 3:
                parts.append(f"{fields[1]} {fields[2]}")
    city_def = _extract_city_defense(lines)
    if city_def:
        wall_hp, wall_max, gar_hp, gar_max = city_def
        if gar_max > 0:
            parts.append(f"City hp {gar_hp}/{gar_max}")
        parts.append(f"Walls {wall_hp}/{wall_max}" if wall_max > 0 else "Walls none")
    if not parts:
        return "Target eliminated"
    return ", ".join(parts)


def _extract_pre_hp(result: str) -> int | None:
    """Extract pre-attack enemy HP from attack result line."""
    import re

    # Ranged/city: pre_hp:80/100
    m = re.search(r"pre_hp:(\d+)/", result)
    if m:
        return int(m.group(1))
    # Melee: enemy HP:100 -> 80/100
    m = re.search(r"enemy HP:(\d+) ->", result)
    if m:
        return int(m.group(1))
    # Melee against a city whose tile holds no garrison: city HP:0 -> 0/200
    m = re.search(r"city HP:(\d+) ->", result)
    if m:
        return int(m.group(1))
    return None


def _extract_post_hp(followup_lines: list[str], attacker_owner: int = 0) -> int | None:
    """Extract post-combat *enemy* HP from followup query lines.

    Followup format: UNIT|UNIT_TYPE|hp/max|owner:N
    Skips units belonging to ``attacker_owner`` (after melee kill, attacker
    occupies the target tile and would otherwise be misread as defender).
    Returns HP of first enemy unit found (None if eliminated).
    """
    for line in followup_lines:
        if line.startswith("UNIT|"):
            parts = line.split("|")
            if len(parts) >= 4:
                try:
                    owner_id = int(parts[3].split(":")[1])
                except (IndexError, ValueError):
                    owner_id = -1
                if owner_id == attacker_owner:
                    continue  # our unit, not the target
            if len(parts) >= 3:
                hp_part = parts[2].split("/")[0]
                try:
                    return int(hp_part)
                except ValueError:
                    pass
    return None


def _extract_city_defense(
    followup_lines: list[str],
) -> tuple[int, int, int, int] | None:
    """Extract wall and garrison HP from CITY_DEF followup line.

    Returns ``(wall_hp, wall_max, garrison_hp, garrison_max)`` or *None*
    when the target tile has no city defenses.
    """
    for line in followup_lines:
        if line.startswith("CITY_DEF|"):
            # CITY_DEF|wall:74/100|garrison:197/200
            wall_hp = wall_max = gar_hp = gar_max = 0
            for part in line.split("|")[1:]:
                if part.startswith("wall:"):
                    hp, mx = part[5:].split("/")
                    wall_hp, wall_max = int(hp), int(mx)
                elif part.startswith("garrison:"):
                    hp, mx = part[9:].split("/")
                    gar_hp, gar_max = int(hp), int(mx)
            return (wall_hp, wall_max, gar_hp, gar_max)
    return None
