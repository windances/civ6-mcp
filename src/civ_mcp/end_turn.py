"""End-turn state machine — snapshot, blocker resolution, turn advancement."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import TYPE_CHECKING

import civ_mcp.narrate as nr
from civ_mcp import lua as lq
from civ_mcp.connection import LuaError
from civ_mcp.game_lifecycle import cleanup_old_autosaves, save_game

if TYPE_CHECKING:
    from civ_mcp.game_state import GameState

log = logging.getLogger(__name__)

# Metrics that describe the live battlefield rather than the stored diary row. A historical
# row cannot be asked about them, so `_context_from_row` fills them with zeros (the rules
# that use them are gated on `>= 1`, so zero means "rule not applicable to this row").
_CONTACT_METRIC_KEYS = (
    "attacks_this_turn",
    "unused_attacks",
    "damaged_this_turn",
    "local_superiority",
    "enemies_massed_on",
    "siege_units",
    "siege_exposed",
    "siege_in_city_range",
    "siege_city_distance_min",
    "garrisoned_units",
    "cities_over_garrison",
    "cities_guarded",
    "unexplained_stacks",
    "enemies_within_1",
    "enemies_within_2",
    "enemies_within_3",
    "enemies_cavalry_within_2",
    "enemies_anti_cavalry_within_2",
    "enemies_siege_within_2",
    "enemies_ranged_within_2",
    "enemies_melee_within_2",
    "weakest_enemy_hp_within_2",
)


# World Congress fallback voting.
#
# Every player gets one free vote per resolution (GlobalParameters /
# WorldCongress.GetVotesandFavorCost: costs[0] == 0); only the votes after
# that cost favor, cumulatively. The vote handler in lua/congress.py starts
# ``votesForThis`` at 1 with cost 0 and only raises it by walking
# ``for v = 2, min(maxWanted, maxV)``, so requesting exactly one vote costs
# nothing while still casting the free vote.
#
# The fallback is deliberately blind: option A and the first possible target.
# In Expansion2_Congress.xml option A is the "add / improve / buff" side of most
# resolutions (it adds diplomatic victory points, improves a luxury, buffs arms
# control), but not all of them - WC_RES_MERCENARY_COMPANIES and
# WC_RES_GLOBAL_ENERGY_TREATY put the ban on option A and the buff on option B.
# So a single vote on A is a least-bad default rather than a correct one, which
# is precisely why it is capped at the free vote and never allowed to spend
# favour: the half of the decision that costs something stays with the agent.
WC_FREE_VOTE_OPTION = 1  # 1 = option A
WC_FREE_VOTE_TARGET = 0  # 0-based index into PossibleTargets


def build_free_vote_fallback(resolutions: list) -> list[dict]:
    """One free vote per resolution, spending zero favor.

    Returns the preference list ``queue_wc_votes`` expects. An empty list
    means there was nothing to vote on.
    """
    return [
        {
            "hash": res.resolution_hash,
            "option": WC_FREE_VOTE_OPTION,
            "target": WC_FREE_VOTE_TARGET,
            "votes": 1,
        }
        for res in resolutions or []
    ]


def _turn_regression_allowed() -> bool:
    """True when a deliberate rollback to an earlier turn has been declared.

    Set ``CIV_MCP_ALLOW_TURN_REGRESSION=1`` in the MCP environment (see
    ``dsh/civ6.cordis.yml``) when the human intends to replay from an earlier
    save. The check below exists to catch an accidental wrong-save load, and it
    cannot tell that apart from a deliberate one.
    """
    return os.environ.get("CIV_MCP_ALLOW_TURN_REGRESSION", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _turn_regression_message(previous: int, turn_after: int, latest_autosave: str) -> str:
    """Advisory text for a turn that went backwards, from previous to turn_after.

    Deliberately states both readings and orders nothing. The old wording
    ("CRITICAL: ... Use load_game_save(...) to recover") was correct for an
    accidental wrong-save load and wrong for a deliberate rollback, and it could
    not tell the two apart - so it now hands the judgement back to the caller.
    """
    return (
        f"WARNING: the turn went backwards, from {previous} to {turn_after}.\n"
        f"If that was deliberate - a human rolled the game back, or you meant to "
        f"replay from an earlier point - carry on. This turn has already advanced "
        f"to {turn_after} and nothing needs loading.\n"
        f"If it was NOT deliberate, you are probably in the wrong save: the newest "
        f'position is {latest_autosave}, and load_game_save("{latest_autosave}") '
        f"returns to it.\n"
        f"Do not reload by reflex - work out which of the two this is before "
        f"acting, and say which you concluded in your diary."
    )


async def _check_mid_turn_world_congress(gs: GameState) -> str | None:
    """Vote and submit if a World Congress session is stalling the turn.

    The gate at the top of ``execute_end_turn`` only sees a session that is already
    open when ``ACTION_ENDTURN`` is sent. A **special session** (an emergency) can
    open *during* that call instead - after the gate has run - so no vote handler
    gets registered, and the game then waits for submissions that never arrive
    while the poll loop below only reads the turn number. Live example,
    2026-09-20 T169: capturing Russia's original capital convened a special
    session, the turn sat for the full 593s budget, and it only advanced because a
    human voted in the game UI. Nothing in the poll path had noticed.

    Voting here uses the direct vote operation (``WORLD_CONGRESS_RESOLUTION_VOTE``),
    which - unlike the ``WorldCongressStage1`` handler - works on a session that is
    already open. One vote per resolution is free; nothing here spends favour.

    Returns a short description when it acted, else None.
    """
    try:
        wc = await gs.get_world_congress()
    except Exception:
        log.debug("Mid-turn World Congress check failed", exc_info=True)
        return None
    if not wc.is_in_session:
        return None

    cast = 0
    for res in wc.resolutions or []:
        try:
            await gs.vote_world_congress(
                res.resolution_hash, WC_FREE_VOTE_OPTION, WC_FREE_VOTE_TARGET, 1
            )
            cast += 1
        except Exception:
            log.debug(
                "Mid-turn World Congress vote failed (res %s)",
                getattr(res, "resolution_hash", "?"),
                exc_info=True,
            )

    try:
        await gs.submit_congress()
    except Exception:
        log.debug("Mid-turn World Congress submit failed", exc_info=True)
        return None

    return (
        f"World Congress session was open mid-turn - cast {cast} free vote(s) "
        f"(option A, first target, 0 favour) and submitted it, so the turn could "
        f"advance. Review what passed with get_world_congress()."
    )


async def _check_mid_turn_diplomacy(
    gs: GameState,
    lua: str,
    turn_before: int | None,
) -> tuple[str | None, bool]:
    """Probe for AI diplomatic proposals during end_turn polling.

    Returns (message, advanced) where message is a string to return to the
    agent if diplomacy was found, or None if no diplomacy detected.
    ``advanced`` is True if the turn advanced during war-declaration handling.

    Handles war auto-dismiss, deal formatting, and session info.  Extracted
    from the Phase 3 inline logic so both the early probe (Phase 2, ~45s)
    and the full-timeout fallback (Phase 3) can share the same code.
    """
    try:
        mid_sessions = await gs.get_diplomacy_sessions()
        if not mid_sessions:
            return None, False

        # DiplomacyActionView text can take 1-2s to populate after session
        # opens during AI processing. If text is empty, retry once.
        if any(not s.dialogue_text for s in mid_sessions):
            await asyncio.sleep(2.0)
            mid_sessions = await gs.get_diplomacy_sessions()

        # Auto-dismiss war declarations — these are informational only
        # (you can't decline a war). Dismiss and report to the agent.
        war_sessions = [s for s in mid_sessions if s.is_at_war]
        if war_sessions:
            war_names = []
            for ws in war_sessions:
                close_lua = lq.build_diplomacy_respond(ws.other_player_id, "EXIT")
                await gs.conn.execute_write(close_lua)
                war_names.append(f"{ws.other_civ_name} ({ws.other_leader_name})")
                log.info(
                    "Auto-dismissed war declaration from %s",
                    ws.other_civ_name,
                )
            # Remove war sessions from the list
            mid_sessions = [s for s in mid_sessions if not s.is_at_war]
            # If only war sessions, resume polling (original ACTION_ENDTURN
            # is still in flight — do NOT re-send or turns will skip)
            if not mid_sessions:
                war_msg = ", ".join(war_names)
                advanced = False
                for _ in range(10):
                    await asyncio.sleep(2.0)
                    turn_after = await _get_turn_number(gs)
                    if (
                        turn_after is not None
                        and turn_before is not None
                        and turn_after > turn_before
                    ):
                        advanced = True
                        break
                if advanced:
                    return None, True  # turn advanced, caller handles snapshot
                # Original ACTION_ENDTURN was consumed — next call must re-send
                gs._pending_end_turn = False
                gs._pending_end_turn_from = None
                return (
                    f"WAR DECLARED by {war_msg}! Session dismissed.\n"
                    f"Turn did not advance — call end_turn again.\n"
                    f"Reassess: check unit positions, city defenses, and military strength."
                ), False

        if not mid_sessions:
            # All sessions were war declarations and turn advanced
            return None, True if war_sessions else False

        # Non-war sessions: format for agent
        session_info = []
        for s in mid_sessions:
            phase = (
                "deal"
                if s.deal_summary
                else ("goodbye" if s.buttons == "GOODBYE" else "active")
            )
            session_info.append(f"{s.other_civ_name} ({s.other_leader_name}) [{phase}]")
        has_deal = any(s.deal_summary for s in mid_sessions)
        lines: list[str] = []
        if war_sessions:
            war_names_str = ", ".join(f"{ws.other_civ_name}" for ws in war_sessions)
            lines.append(f"WAR DECLARED by {war_names_str}! (auto-dismissed)")
        lines.append(
            f"Turn paused — AI diplomatic proposal from {', '.join(session_info)}.",
        )
        for s in mid_sessions:
            if s.dialogue_text:
                lines.append(f'{s.other_civ_name} says: "{s.dialogue_text}"')
            if s.reason_text:
                lines.append(f"Reason: {s.reason_text}")
            if s.deal_summary:
                lines.append(f"Deal from {s.other_civ_name}: {s.deal_summary}")
        if has_deal:
            lines.append(
                "Use respond_to_trade(other_player_id=X, accept=True/False) to handle it, then end_turn again."
            )
        else:
            lines.append("Use respond_to_diplomacy to handle it, then end_turn again.")
        return "\n".join(lines), False
    except Exception:
        log.debug("Mid-turn diplomacy check failed", exc_info=True)
        return None, False


async def _get_turn_number(gs: GameState) -> int | None:
    """Read the current game turn number."""
    try:
        lines = await gs.conn.execute_read(
            'print(Game.GetCurrentGameTurn()); print("---END---")'
        )
        if lines:
            return int(lines[0])
    except (LuaError, ValueError, IndexError):
        pass
    return None


async def _check_victory_proximity(gs: GameState) -> list[lq.TurnEvent]:
    """Lightweight per-turn check for foreign victory threats."""
    events: list[lq.TurnEvent] = []
    lines = await gs.conn.execute_write(lq.build_victory_proximity_query())
    enabled: set[str] = set()
    for line in lines:
        if line.startswith("VENABLED|"):
            enabled.add(line.split("|", 1)[1])
    for line in lines:
        if line.startswith("REL_THREAT|"):
            if enabled and "VICTORY_RELIGIOUS" not in enabled:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                civ_name, rel_name = parts[1], parts[2]
                count, total = int(parts[3]), int(parts[4])
                if count >= total:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!!! RELIGIOUS VICTORY IMMINENT: {civ_name}'s {rel_name} is majority in ALL {total} civilizations!",
                        )
                    )
                elif count >= total - 1:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!! RELIGIOUS VICTORY THREAT: {civ_name}'s {rel_name} is majority in {count}/{total} civilizations!",
                        )
                    )
        elif line.startswith("DIPLO_THREAT|"):
            if enabled and "VICTORY_DIPLOMATIC" not in enabled:
                continue
            parts = line.split("|")
            if len(parts) >= 3:
                dvp = int(parts[2])
                if dvp >= 20:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!!! DIPLOMATIC VICTORY IMMINENT: {parts[1]} has {dvp}/20 DVP — wins immediately, does NOT wait for World Congress!",
                        )
                    )
                elif dvp >= 18:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!! DIPLOMATIC VICTORY THREAT: {parts[1]} has {dvp}/20 DVP — wins IMMEDIATELY at 20, does not wait for WC. Must strip DVP at next World Congress BEFORE they reach 20.",
                        )
                    )
                elif dvp >= 15:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!! DIPLOMATIC VICTORY THREAT: {parts[1]} has {dvp}/20 DVP!",
                        )
                    )
                else:
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="victory",
                            message=f"Diplomatic race: {parts[1]} has {dvp}/20 DVP.",
                        )
                    )
        elif line.startswith("SCI_THREAT|"):
            if enabled and "VICTORY_TECHNOLOGY" not in enabled:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                vp, needed = int(parts[2]), int(parts[3])
                if vp >= needed - 1:
                    events.append(
                        lq.TurnEvent(
                            priority=1,
                            category="victory",
                            message=f"!! SCIENCE VICTORY IMMINENT: {parts[1]} has {vp}/{needed} space race projects!",
                        )
                    )
                elif vp >= 1:
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="victory",
                            message=f"Science race: {parts[1]} has {vp}/{needed} space race projects.",
                        )
                    )
    return events


async def _check_empire_warnings(
    gs: GameState,
    snap: lq.TurnSnapshot | None,
) -> tuple[list[lq.TurnEvent], int | None]:
    """Lightweight alerts that compensate for the Sensorium Effect.

    Surfaces information a human player would notice via passive visual cues:
    scoreboard position, idle trade routes, resource caps, loyalty crises,
    military imbalance, and gold deficits.

    Returns (events, score) where score is the current game score if available.
    """
    events: list[lq.TurnEvent] = []
    game_score: int | None = None

    # --- Loyalty crisis (from snapshot cities) ---
    if snap:
        for cs in snap.cities.values():
            if cs.loyalty_per_turn < -5:
                turns_left = (
                    int(cs.loyalty / abs(cs.loyalty_per_turn))
                    if cs.loyalty_per_turn < 0
                    else 99
                )
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="city",
                        message=(
                            f"LOYALTY CRISIS: {cs.name} losing {cs.loyalty_per_turn:+.1f}/t "
                            f"(loyalty {cs.loyalty:.0f}) — will rebel in ~{turns_left} turns!"
                        ),
                    )
                )
            elif cs.loyalty < 30 and cs.loyalty_per_turn < 0:
                events.append(
                    lq.TurnEvent(
                        priority=2,
                        category="city",
                        message=f"LOYALTY WARNING: {cs.name} at {cs.loyalty:.0f} loyalty ({cs.loyalty_per_turn:+.1f}/t)",
                    )
                )

    # --- Resource cap (from snapshot stockpiles) ---
    if snap:
        for s in snap.stockpiles:
            net = s.per_turn - s.demand + s.imported
            if s.cap > 0 and s.amount >= s.cap and net > 0:
                events.append(
                    lq.TurnEvent(
                        priority=3,
                        category="economy",
                        message=(
                            f"RESOURCE CAP: {s.name} {s.amount}/{s.cap} ({net:+d}/t) "
                            f"— excess is wasted. Trade surplus or spend it."
                        ),
                    )
                )

    # --- Gold deficit (quick overview query) ---
    try:
        ov_lines = await gs.conn.execute_write(lq.build_overview_query())
        overview = lq.parse_overview_response(ov_lines)
    except Exception:
        log.debug("Overview query for warnings failed", exc_info=True)
        overview = None

    if overview:
        game_score = overview.score
        if (
            overview.gold_per_turn < 0
            and overview.gold < abs(overview.gold_per_turn) * 20
        ):
            turns_to_zero = (
                int(overview.gold / abs(overview.gold_per_turn))
                if overview.gold_per_turn < 0
                else 99
            )
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="economy",
                    message=(
                        f"DEFICIT: Gold {overview.gold_per_turn:+.0f}/t with {overview.gold:.0f} in treasury "
                        f"— bankrupt in ~{turns_to_zero} turns."
                    ),
                )
            )

    # --- Idle trade routes (lightweight Lua query) ---
    try:
        tr_lines = await gs.conn.execute_write(lq.build_trade_capacity_check())
        for line in tr_lines:
            if line.startswith("TRCAP|"):
                parts = line.split("|")
                cap, active = int(parts[1]), int(parts[2])
                idle = cap - active
                if idle > 0:
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="economy",
                            message=(
                                f"IDLE TRADE ROUTE: {idle} unused route "
                                f"{'capacity' if idle == 1 else 'capacities'} "
                                f"({active}/{cap} active). Build a Trader or assign an idle one."
                            ),
                        )
                    )
                break
    except Exception:
        log.debug("Trade capacity check failed", exc_info=True)

    # --- Scoreboard + military disparity (rival snapshot, every 5 turns) ---
    turn = snap.turn if snap else 0
    if turn > 0 and turn % 5 == 0:
        try:
            rival_lines = await gs.conn.execute_write(lq.build_rival_snapshot_query())
            rivals = lq.parse_rival_snapshot_response(rival_lines)
            if rivals and overview:
                our_sci = overview.science_yield
                # Compute science rankings
                all_sci = [(r.name, r.sci) for r in rivals] + [("You", our_sci)]
                all_sci.sort(key=lambda x: x[1], reverse=True)
                our_rank = next(i + 1 for i, (n, _) in enumerate(all_sci) if n == "You")
                leader_name, leader_sci = all_sci[0]
                if our_rank > 1 and len(all_sci) > 2:
                    events.append(
                        lq.TurnEvent(
                            priority=2,
                            category="scoreboard",
                            message=(
                                f"SCOREBOARD: Your science ({our_sci:.1f}/t) ranks "
                                f"{our_rank} of {len(all_sci)}. "
                                f"Leader: {leader_name} at {leader_sci:.1f}/t."
                            ),
                        )
                    )

                # Military disparity
                our_mil_lines = await gs.conn.execute_read(
                    "local me = Game.GetLocalPlayer(); "
                    "print(Players[me]:GetStats():GetMilitaryStrength()); "
                    'print("---END---")'
                )
                our_mil = 0
                if our_mil_lines:
                    try:
                        our_mil = int(float(our_mil_lines[0]))
                    except (ValueError, IndexError):
                        pass
                if our_mil > 0:
                    for r in rivals:
                        if r.mil >= our_mil * 2:
                            events.append(
                                lq.TurnEvent(
                                    priority=2,
                                    category="military",
                                    message=(
                                        f"MILITARY WARNING: {r.name} has {r.mil} military "
                                        f"({r.mil / our_mil:.1f}x ours at {our_mil})."
                                    ),
                                )
                            )
        except Exception:
            log.debug("Rival snapshot for warnings failed", exc_info=True)

    return events, game_score


# What the conquest directive says one city assault needs, and the unit types that count
# as each. The directive's own words: "about 2 siege, 2 melee, 1 ram or tower, 4 ranged
# (2 Crossbowman at range 2 and 2 Crouching Tiger at range 1) and 1 cavalry".
_WAR_TRAIN: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("siege", 2, ("CATAPULT", "TREBUCHET", "BOMBARD", "ARTILLERY")),
    ("melee", 2, ("WARRIOR", "SWORDSMAN", "MAN_AT_ARMS", "MUSKETMAN", "INFANTRY", "PIKEMAN", "SPEARMAN")),
    ("ram/tower", 1, ("BATTERING_RAM", "SIEGE_TOWER")),
    ("ranged", 4, ("SLINGER", "ARCHER", "CROSSBOWMAN", "FIELD_CANNON", "CROUCHING_TIGER")),
    ("cavalry", 1, ("HORSEMAN", "KNIGHT", "COURSER", "CUIRASSIER", "CAVALRY", "TANK")),
)

# Diary fields worth a 10-turn delta, and how to print them.
_REVIEW_METRICS: tuple[tuple[str, str, str], ...] = (
    ("science", "science", "{:+.1f}"),
    ("culture", "culture", "{:+.1f}"),
    ("gold_per_turn", "gold/turn", "{:+.1f}"),
    ("military", "military", "{:+.0f}"),
    ("pop", "pop", "{:+.0f}"),
    ("cities", "cities", "{:+.0f}"),
    ("districts", "districts", "{:+.0f}"),
    ("improvements", "improvements", "{:+.0f}"),
    ("wonders", "wonders", "{:+.0f}"),
    ("territory", "territory", "{:+.0f}"),
    ("techs_completed", "techs", "{:+.0f}"),
    ("civics_completed", "civics", "{:+.0f}"),
)


def _war_train_status(units: dict | None) -> tuple[str, list[str]]:
    """Our units counted by the roles an assault needs, and the shortfall named."""
    types = [(u.unit_type or "").upper() for u in (units or {}).values()]
    parts: list[str] = []
    missing: list[str] = []
    for role, wanted, unit_types in _WAR_TRAIN:
        have = sum(1 for t in types if any(t.endswith(name) or name in t for name in unit_types))
        parts.append(f"{role} {have}/{wanted}")
        if have < wanted:
            missing.append(f"{wanted - have} {role}")
    return ", ".join(parts), missing


def _ten_turn_review_text(
    turn: int,
    past: dict | None,
    now: dict | None,
    units: dict | None,
) -> str | None:
    """The every-10-turns review: what the window bought, what is still missing, ETA.

    Pure so it can be tested without a game: it only reads diary rows and the unit list.
    Returns None when there is no earlier row to compare against yet.
    """
    if not past or not now:
        return None
    past_turn = past.get("turn")
    lines = [
        f"10-TURN REVIEW (T{past_turn} -> T{turn}) — answer the three questions at the end "
        "of this block in THIS turn's diary."
    ]

    deltas: list[str] = []
    for key, label, fmt in _REVIEW_METRICS:
        before, after = past.get(key), now.get(key)
        if isinstance(before, (int, float)) and isinstance(after, (int, float)) and after != before:
            per_turn = (after - before) / max(1, turn - past_turn)
            deltas.append(f"{label} {fmt.format(after - before)} ({per_turn:+.2f}/t)")
    lines.append("  last 10 turns: " + ("; ".join(deltas) if deltas else "nothing moved"))

    reflections = past.get("reflections") or {}
    for field in ("planning", "hypothesis"):
        text = (reflections.get(field) or "").strip().replace("\n", " ")
        if text:
            lines.append(f"  you wrote at T{past_turn} ({field}): {text[:400]}")

    train, missing = _war_train_status(units)
    lines.append(
        f"  assault prerequisites (conquest directive): {train}"
        + (f" - MISSING {', '.join(missing)}" if missing else " - complete")
    )

    wonders = now.get("wonders")
    lines.append(
        f"  Dynastic Cycle: wonders built {wonders if isinstance(wonders, (int, float)) else '?'} "
        "(for China a wonder is a research building; zero forfeits the ability)"
    )

    pop, districts = now.get("pop"), now.get("districts")
    if isinstance(pop, (int, float)) and isinstance(districts, (int, float)):
        allowed = int(pop) // 3
        idle = allowed - int(districts)
        lines.append(
            f"  district slots: {int(districts)} districts for pop {int(pop)} "
            f"(allowed floor(pop/3)={allowed})"
            + (f" - {idle} slot(s) idle, growth is the district plan" if idle > 0 else "")
        )

    gpt, mil = now.get("gold_per_turn"), now.get("military")
    if isinstance(gpt, (int, float)):
        note = "ok" if gpt >= 10 else "BELOW the +10 the directive requires with the army counted"
        lines.append(
            f"  carrying capacity: gold/turn {gpt:+.1f}"
            + (f" with military {mil:.0f}" if isinstance(mil, (int, float)) else "")
            + f" - {note}"
        )

    rates = [
        f"{label} {((now.get(key) - past.get(key)) / max(1, turn - past_turn)):+.2f}/t"
        for key, label, _ in _REVIEW_METRICS
        if key in ("science", "culture", "military")
        and isinstance(past.get(key), (int, float))
        and isinstance(now.get(key), (int, float))
    ]
    if rates:
        lines.append(
            f"  projection at the window's rates ({', '.join(rates)}): hold the same rate and "
            f"T{turn + 10} looks like "
            + ", ".join(
                f"{label} {now[key] + 10 * (now[key] - past[key]) / max(1, turn - past_turn):.1f}"
                for key, label, _ in _REVIEW_METRICS
                if key in ("science", "military")
                and isinstance(past.get(key), (int, float))
                and isinstance(now.get(key), (int, float))
            )
            + ". State whether that reaches the milestone and by which turn."
        )

    lines.append(
        "  REQUIRED IN THIS TURN'S DIARY: (1) was this window efficient — where did the turns "
        "go, with numbers? (2) which prerequisite for the next goal is now in place and which "
        "is still missing? (3) does the planned completion turn still hold, and if not, what "
        "changes — target, build order, or the plan itself?"
    )
    return "\n".join(lines)


async def _agent_diary_rows(gs) -> list[dict]:
    """This game's agent rows, oldest first. Empty when the diary cannot be read."""
    from . import diary as diary_mod

    try:
        civ, seed = await gs.get_game_identity()
        rows = [
            r
            for r in diary_mod.read_diary_entries(diary_mod.diary_path(civ, seed))
            if r.get("is_agent") and isinstance(r.get("turn"), int)
        ]
    except Exception:
        log.debug("diary unreadable", exc_info=True)
        return []
    rows.sort(key=lambda r: r["turn"])
    return rows


def _latest_at_or_before(rows: list[dict], turn: int) -> dict | None:
    candidates = [r for r in rows if r["turn"] <= turn]
    return max(candidates, key=lambda r: r["turn"]) if candidates else None


async def _game_key(gs) -> str:
    try:
        civ, seed = await gs.get_game_identity()
        return f"{civ}_{seed}"
    except Exception:
        return "unknown"


async def _evaluate_checks(gs, turn: int, units: dict | None, now: dict | None):
    """One evaluation of the check file, with goals that have been achieved retired.

    Returns ``(run, achieved, retired, path, swept, backup)``. A rule marked ``once: true`` is
    a goal: the first turn its requirement holds it is recorded and never evaluated again, so
    the reminders that have been dealt with stop nagging while the standing ones keep watch.
    ``swept``/``backup`` report the achieved goals taken out of the file itself.
    """
    from . import turn_checks

    text, path = turn_checks.load_checks()
    if text is None or "<!--" not in text:
        return None, {}, {}, path, [], None

    if units is None:
        units = await _units_for_checks(gs, turn)
    if now is None:
        try:
            now = _latest_at_or_before(await _agent_diary_rows(gs), turn)
        except Exception:
            now = None
    researched = frozenset(
        str(name).upper()
        for key in ("techs", "civics")
        for name in ((now or {}).get(key) or [])
    )
    # An empty unit list is missing data, not an army of zero units. The diary row still
    # records what the army was, so the unit-count rules are answered from it rather than
    # counting 0 and firing four rules at once (seen live at T103-T104 and T106-T114, when
    # the agent concluded - correctly - that the reminders contradicted get_units).
    if not units:
        fallback = _context_from_row(now)
        if fallback is not None and fallback.units:
            units = fallback.units
            log.info("turn checks: snapshot had no units, using the diary row's composition")
        else:
            log.warning("turn checks: no unit list available for T%s at all", turn)
    # Contact metrics ride on top of the diary row: the row knows the yields, the live scan
    # knows where the enemy is and how many attacks this turn actually made. A failure here
    # must not cost the whole check run, and the rules read the keys as "no contact".
    metrics = dict(now or {})
    metrics["at_war"] = _at_war_from_row(now)
    try:
        metrics.update(await _contact_metrics(gs, turn, units))
    except Exception:
        log.debug("turn checks: contact metrics failed", exc_info=True)
        metrics.update({key: 0 for key in _CONTACT_METRIC_KEYS})
    context = turn_checks.CheckContext(
        turn=turn, units=units or {}, metrics=metrics, researched=researched
    )
    try:
        run = turn_checks.run_checks(text, context)
    except turn_checks.CheckError as exc:
        log.warning("turn checks in %s are malformed: %s", path, exc)
        return None, {"__broken__": str(exc)}, {}, path, [], None

    game_key = await _game_key(gs)
    retired = turn_checks.load_retired(game_key)
    achieved = {
        check.check_id: turn
        for check in run.checks
        if check.once and check.check_id in run.passed and check.check_id not in retired
    }
    if achieved:
        turn_checks.retire(game_key, achieved)
        retired.update(achieved)
        log.info("turn checks achieved and retired: %s", ", ".join(achieved))

    # Take the achieved goals out of the live file, with a timestamped copy first: what is
    # left in it is what still needs doing, and the history stays readable in archive/.
    swept, backup = turn_checks.sweep_achieved(
        path, retired, time.strftime("%Y%m%d-%H%M%S")
    )
    if swept:
        log.info("pruned achieved checks from %s: %s (backup %s)", path, ", ".join(swept), backup)
    return run, achieved, retired, path, swept, backup


async def _check_turn_checks(
    gs, turn: int, units: dict | None, now: dict | None
) -> list[lq.TurnEvent]:
    """Evaluate prompts/checks/turn-checks.md and report every failing rule.

    The file is the human's lever: a rule added there is enforced on every turn without
    touching this code, and a rule that fails appears in the turn result rather than
    depending on the agent remembering it at the right moment. One hard deadline motivated
    it - Battering Ram and Siege Tower go obsolete at CIVIC_CIVIL_ENGINEERING, a cliff edge
    that prose in a prompt had already failed to catch.
    """
    run, achieved, retired, path, swept, backup = await _evaluate_checks(gs, turn, units, now)
    if "__broken__" in achieved:
        return [
            lq.TurnEvent(
                priority=2,
                category="check",
                message=f"TURN CHECKS FILE IS BROKEN ({path}): {achieved['__broken__']}",
            )
        ]
    if run is None:
        return []

    log.info(
        "turn checks: %d evaluated, %d failing, %d retired",
        len(run.checks),
        len(run.failures),
        len(retired),
    )
    events = [
        lq.TurnEvent(
            priority=1 if check.level == "error" else 2,
            category="check",
            message=f"CHECK FAILED [{check.check_id}]: {check.message} (require: {reason})",
        )
        for check, reason in run.failures
        if check.check_id not in retired
    ]
    events.extend(
        lq.TurnEvent(
            priority=2,
            category="check",
            message=(
                f"CHECK ACHIEVED [{check_id}] at T{turn} - retired, it will not be checked "
                f"again (reopen it by giving the rule a new id in {path.name})"
            ),
        )
        for check_id in achieved
        if check_id != "__broken__"
    )
    if swept:
        events.append(
            lq.TurnEvent(
                priority=2,
                category="check",
                message=(
                    f"CHECK FILE PRUNED: achieved goal(s) {', '.join(swept)} removed from "
                    f"{path.name}; the file as it was is kept at {backup}. Deal with the "
                    f"{len(run.checks) - len(swept)} rule(s) still listed there."
                ),
            )
        )

    # What makes `answer-the-attack` actionable rather than a scolding: the enemy that is in
    # contact, which of them is killable right now, and how many of our units are already in
    # range to do it. Both scans are cached for the turn, so this costs nothing extra.
    if turn is not None:
        try:
            metrics = await _contact_metrics(gs, turn, units)
            assessment = _battle_assessment(metrics, await _threats_for_checks(gs, turn), turn)
        except Exception:
            log.debug("battle assessment failed", exc_info=True)
            assessment = None
        if assessment:
            events.append(lq.TurnEvent(priority=2, category="combat", message=assessment))
        try:
            posture = await _siege_posture_for_checks(gs, turn)
            posture_text = _siege_posture_event(posture, _siege_metrics(posture), turn)
        except Exception:
            log.debug("siege posture report failed", exc_info=True)
            posture_text = None
        if posture_text:
            events.append(lq.TurnEvent(priority=3, category="combat", message=posture_text))
        try:
            progress_text = _siege_progress_event(gs, turn)
        except Exception:
            log.debug("siege progress report failed", exc_info=True)
            progress_text = None
        if progress_text:
            events.append(lq.TurnEvent(priority=2, category="combat", message=progress_text))
        try:
            stacks = _garrison_metrics(gs, units).get("unexplained_stacks", 0)
        except Exception:
            stacks = 0
        if stacks:
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="data",
                    message=(
                        f"SNAPSHOT WARNING: {stacks} tile(s) hold more than one of our military"
                        f" units and are not one of our cities. Civ VI reports the units inside a"
                        f" city at the city tile, so a stack elsewhere is not a garrison - treat"
                        f" every position-based judgement (screens, distances, contact) as"
                        f" suspect until get_units is re-read."
                    ),
                )
            )
    return events


async def _check_ten_turn_review(
    gs, turn_after: int, units: dict | None, rows: list[dict] | None = None
) -> list[lq.TurnEvent]:
    """Every 10 turns: read the diary back and demand the three-question review.

    The agent has the strategy and the intent; what it cannot do reliably is notice that
    ten turns produced almost nothing (2026-09-20: science +6 in the 50 turns from T30 to
    T80, no wonder until T100, a siege train still absent at T120). The measurement is the
    MCP's job, the judgement is the agent's, and the diary is where it is checked.
    """
    from . import diary as diary_mod

    if rows is None:
        rows = await _agent_diary_rows(gs)
    if not rows:
        return []

    past = _latest_at_or_before(rows, turn_after - 10)
    now = _latest_at_or_before(rows, turn_after)
    text = _ten_turn_review_text(turn_after, past, now, units)
    if text is None:
        return []
    return [lq.TurnEvent(priority=1, category="review", message=text)]


def _siege_metrics(posture: list) -> dict:
    """Siege exposure: in enemy reach with nothing closer to the enemy than itself.

    "Tanky units in front, ranged behind, and the Catapults' tile is the one that must be
    protected" is a formation, and a formation is measurable: a siege unit that is within two
    tiles of an enemy while the front-line unit nearest to it is *not* closer to that enemy is
    the unit that will be attacked first, and the one that cannot afford it.
    """
    metrics = {
        "siege_units": len(posture or []),
        "siege_exposed": 0,
        "siege_in_city_range": 0,
        "siege_city_distance_min": 999,
    }
    for entry in posture or []:
        if getattr(entry, "exposed", False):
            metrics["siege_exposed"] += 1
        if int(getattr(entry, "city_distance", 999) or 999) <= 2:
            metrics["siege_in_city_range"] += 1
        metrics["siege_city_distance_min"] = min(
            metrics["siege_city_distance_min"], int(getattr(entry, "city_distance", 999) or 999)
        )
    return metrics


def _siege_posture_event(posture: list, metrics: dict, turn: int) -> str | None:
    """Name the exposed siege units, or say the train is in position and screened."""
    if not posture:
        return None
    exposed = int(metrics.get("siege_exposed", 0) or 0)
    closest_city = int(metrics.get("siege_city_distance_min", 999) or 999)
    if not exposed and closest_city > 3:
        return None  # staging far from any target: nothing to report yet
    lines = [f"SIEGE POSTURE (T{turn}) - front line in front, siege behind, at range 2:"]
    for entry in posture:
        where = f"{getattr(entry, 'unit_type', '?')}@({getattr(entry, 'x', '?')},{getattr(entry, 'y', '?')})"
        enemy = int(getattr(entry, "enemy_distance", 999) or 999)
        screen = getattr(entry, "screen_distance", 999)
        screen_enemy = getattr(entry, "screen_enemy_distance", 999)
        city = int(getattr(entry, "city_distance", 999) or 999)
        city_name = getattr(entry, "city_name", "") or "no visible enemy city"
        state = "EXPOSED - nothing closer to the enemy" if getattr(entry, "exposed", False) else "screened"
        lines.append(
            f"  {where}: enemy {enemy if enemy != 999 else 'none in sight'},"
            f" screen {screen if screen != 999 else 'none'} (its enemy {screen_enemy if screen_enemy != 999 else '-'}),"
            f" city {city if city != 999 else '-'} ({city_name}) - {state}"
        )
    if exposed:
        lines.append(
            "  Fix the formation before advancing: the screen moves up (or the siege unit back),"
            " so that what the enemy can reach first is the unit that can take it."
        )
    elif int(metrics.get("siege_in_city_range", 0) or 0):
        lines.append(
            "  In firing position with a screen. Order of work: siege knocks the walls, melee takes"
            " the city, ranged shoots the garrison."
        )
    return "\n".join(lines)


def _siege_progress_event(gs, turn: int) -> str | None:
    """Say what the assault is doing to the city, and shout when it is doing nothing.

    Every attack on a city tile records that city's HP (`GameState._record_city_hp`), so the
    one number that decides a siege can be reported back: how much is left, how much moved this
    turn, and - after three turns without a net drop - that the assault has stalled. Live, the
    Moscow assault ran twelve turns with no city number reported anywhere, which is how a
    stalled siege looks exactly like a progressing one.
    """
    history = getattr(gs, "_city_hp_history", None) or {}
    if not history:
        return None
    lines: list[str] = []
    for city, entries in history.items():
        recent = [(t, hp, mx) for t, hp, mx in entries if t >= turn - 3]
        if not recent:
            continue
        first_hp, last_hp, max_hp = recent[0][1], recent[-1][1], recent[-1][2]
        hit_this_turn = recent[-1][0] == turn
        moved = last_hp - first_hp
        head = f"  {city}: city hp {last_hp}/{max_hp}"
        if len(recent) >= 2:
            head += f" ({moved:+d} over {recent[-1][0] - recent[0][0] + 1} turn(s))"
        if hit_this_turn:
            head += " - hit this turn"
        lines.append(head)
        if len(recent) >= 3 and moved >= 0:
            lines.append(
                f"  SIEGE STALLED: {city} has not lost city HP in {len(recent)} recorded turns"
                f" ({first_hp} -> {last_hp}). The city heals about twenty points a turn, so fire"
                f" that does not out-damage the healing is fire that never happened. Fix the"
                f" assault (siege in position and screened, more attackers on the same target)"
                f" or break it off - do not keep feeding it."
            )
    if not lines:
        return None
    return f"SIEGE PROGRESS (T{turn}):\n" + "\n".join(lines)


def _is_military(unit) -> bool:
    """A unit that can fight, so a builder parked on a city tile is not a garrison."""
    return bool(getattr(unit, "combat_strength", 0) or getattr(unit, "ranged_strength", 0))


def _garrison_metrics(gs, units: dict | None) -> dict:
    """How many cities hold more than one unit, once the war is on.

    The human's rule: after war starts a city keeps **one** garrison and everything else goes
    to the front - a second unit on a city tile is doing nothing that the first one is not
    already doing, while the front is short a unit. Cities come from the snapshot, which now
    carries their coordinates, so "garrisoned" means standing on the city tile rather than
    somewhere near it.

    It also reports `unexplained_stacks`: several of our military units sharing a tile that is
    **not** one of our cities. In Civ VI the units inside a city are reported at the city's own
    tile, so a stack on a city tile is normal; a stack anywhere else is not, and it would make
    every position-based judgement (screens, distances, contact) unreliable. Stating that is
    cheaper than discovering it in a plan.
    """
    snapshot = getattr(gs, "_last_snapshot", None)
    cities = getattr(snapshot, "cities", None) or {}
    tiles = {
        (city.x, city.y)
        for city in cities.values()
        if getattr(city, "x", None) is not None
    }
    metrics = {"garrisoned_units": 0, "cities_over_garrison": 0, "cities_guarded": 0,
               "unexplained_stacks": 0}
    if not tiles:
        return metrics
    on_city: dict[tuple[int, int], int] = {}
    elsewhere: dict[tuple[int, int], int] = {}
    for unit in (units or {}).values():
        if not _is_military(unit):
            continue
        where = (getattr(unit, "x", None), getattr(unit, "y", None))
        if where in tiles:
            on_city[where] = on_city.get(where, 0) + 1
        elif isinstance(where[0], int) and isinstance(where[1], int) and where[0] >= 0:
            elsewhere[where] = elsewhere.get(where, 0) + 1
    metrics["garrisoned_units"] = sum(on_city.values())
    metrics["cities_guarded"] = len(on_city)
    metrics["cities_over_garrison"] = sum(1 for count in on_city.values() if count > 1)
    metrics["unexplained_stacks"] = sum(1 for count in elsewhere.values() if count > 1)
    return metrics


def _at_war_from_row(row: dict | None) -> int:
    """1 when the diary row records a war, 0 otherwise.

    ``diplo_states`` carries the game's own diplomatic state index per met civilization, and
    6 is WAR (0 ALLIED ... 5 DENOUNCED, 6 WAR). The row is the only place the check engine can
    read this from, and it is enough: the war-phase rules should not fire in peacetime.
    """
    states = (row or {}).get("diplo_states") or {}
    for entry in states.values():
        try:
            if int((entry or {}).get("state", -1)) == 6:
                return 1
        except (TypeError, ValueError):
            continue
    return 0


async def _contact_metrics(gs, turn: int, units: dict | None) -> dict:
    """How much enemy contact the army is in, and whether it acted on it.

    The rule the human asked for - "if enemy units are in the way while the army is
    assembling, attack them first, and prefer the counter unit" - cannot be checked from
    yields or unit counts. It needs two facts that are cheap to obtain and were not in the
    context: how close the nearest visible enemy is to *our* units (not to the nearest city,
    which the threat scan alone reports), and how many attacks were actually made this turn.

    ``promotion_class`` comes from the game itself (``PROMOTION_CLASS_*``), so "is there
    cavalry next to the army" is answered without a hardcoded unit-name table that would rot
    with each era. Missing data yields zeros, which switches the rules off rather than
    firing them.
    """
    metrics = {
        "enemies_within_1": 0,
        "enemies_within_2": 0,
        "enemies_within_3": 0,
        "enemies_cavalry_within_2": 0,
        "enemies_anti_cavalry_within_2": 0,
        "enemies_siege_within_2": 0,
        "enemies_ranged_within_2": 0,
        "enemies_melee_within_2": 0,
        "weakest_enemy_hp_within_2": 0,
        # How many of our fighting units are close enough to join the closest fight. One is a
        # trade, two or three is a kill; that is the difference between answering an attack
        # and winning the exchange.
        "local_superiority": 0,
        "enemies_massed_on": 0,
        "attacks_this_turn": int(getattr(gs, "_attacks_this_turn", 0) or 0),
        # A unit standing next to a killable enemy with moves left is the failure mode the
        # "attacks_this_turn >= 1" rule cannot see: two Catapults firing at a city satisfy it
        # while a 7 HP Swordsman is ignored one tile away (seen live at T111-T115).
        "unused_attacks": len(await _unused_attacks_for_checks(gs, turn)),
        # Who was hit during the AI turn, and how the army is distributed across the cities.
        "damaged_this_turn": len(getattr(gs, "_damaged_last_turn", None) or []),
        **_garrison_metrics(gs, units),
        **_siege_metrics(await _siege_posture_for_checks(gs, turn)),
    }
    threats = await _threats_for_checks(gs, turn)
    if not threats:
        return metrics
    for threat in threats:
        # The scan reports both distances with the game's own Map.GetPlotDistance; the
        # unit-only one is what "the enemy is standing next to the army" means. Cities are
        # only the fallback (no units on the map at all).
        unit_distance = int(getattr(threat, "unit_distance", 999) or 999)
        distance = unit_distance if unit_distance != 999 else int(threat.distance or 999)
        if distance <= 1:
            metrics["enemies_within_1"] += 1
        if distance <= 2:
            metrics["enemies_within_2"] += 1
            massed = int(getattr(threat, "friendly_within_2", 0) or 0)
            metrics["local_superiority"] = max(metrics["local_superiority"], massed)
            if massed >= 2:
                metrics["enemies_massed_on"] += 1
            klass = (getattr(threat, "promotion_class", "") or "").upper()
            # ANTI_CAVALRY is checked before CAVALRY: it is the counter *to* cavalry, and
            # "CAVALRY in ANTI_CAVALRY" would otherwise file it as one.
            if "ANTI_CAVALRY" in klass:
                metrics["enemies_anti_cavalry_within_2"] += 1
            elif "CAVALRY" in klass:
                metrics["enemies_cavalry_within_2"] += 1
            elif "SIEGE" in klass:
                metrics["enemies_siege_within_2"] += 1
            elif "RANGED" in klass:
                metrics["enemies_ranged_within_2"] += 1
            elif "MELEE" in klass:
                metrics["enemies_melee_within_2"] += 1
            hp = int(getattr(threat, "hp", 0) or 0)
            if hp and (
                metrics["weakest_enemy_hp_within_2"] == 0
                or hp < metrics["weakest_enemy_hp_within_2"]
            ):
                metrics["weakest_enemy_hp_within_2"] = hp
        if distance <= 3:
            metrics["enemies_within_3"] += 1
    return metrics


async def _unused_attacks_for_checks(gs, turn: int) -> list[str]:
    """Legal attacks left unused, cached per turn - the check path can run several times."""
    cached = getattr(gs, "_last_unused_attacks", None)
    if cached is not None and getattr(gs, "_last_unused_turn", None) == turn:
        return cached
    try:
        unused = await gs.unused_attacks()
    except Exception:
        log.debug("turn checks: unused-attack scan failed", exc_info=True)
        unused = []
    gs._last_unused_attacks = unused
    gs._last_unused_turn = turn
    return unused


async def _siege_posture_for_checks(gs, turn: int) -> list:
    """Siege positions, cached per turn - the check path can run several times a turn."""
    cached = getattr(gs, "_last_siege_posture", None)
    if cached is not None and getattr(gs, "_last_siege_posture_turn", None) == turn:
        return cached
    try:
        posture = await gs.siege_posture()
    except Exception:
        log.debug("turn checks: siege posture scan failed", exc_info=True)
        posture = []
    gs._last_siege_posture = posture
    gs._last_siege_posture_turn = turn
    return posture


async def _threats_for_checks(gs, turn: int) -> list:
    """Visible enemy units, cached per turn - the check path can run several times a turn."""
    cached = getattr(gs, "_last_threats", None)
    if cached is not None and getattr(gs, "_last_threats_turn", None) == turn:
        return cached
    try:
        lines = await gs.conn.execute_write(lq.build_threat_scan_query())
        threats = lq.parse_threat_scan_response(lines)
    except Exception:
        log.debug("turn checks: threat scan failed", exc_info=True)
        threats = None
    if threats is not None:
        gs._last_threats = threats
        gs._last_threats_turn = turn
    return threats or []


def _battle_assessment(metrics: dict, threats: list, turn: int) -> str | None:
    """The enemy in contact, read out for the decision the rule demands.

    "Assess the enemy, mass the nearby units, and annihilate" is a procedure, and every input
    it needs is already in the threat scan (class, combat strength, HP, distance) plus the
    count of our own fighting units in range. Printing it turns the rule from an instruction
    into a decision the agent can make in one step: which enemy is killable, with how many of
    our units, and where the counter unit is missing.

    It is printed when a unit was **attacked** and when enemy forces are **discovered** in
    contact during a war - the human's rule starts at discovery, not at the first hit. Outside
    a war the scan only fires on damage, so barbarian skirmishing does not turn into wallpaper.
    """
    if not (
        metrics.get("damaged_this_turn")
        or (metrics.get("at_war") and metrics.get("enemies_within_3"))
    ):
        return None
    in_range = [
        t
        for t in threats
        if int(getattr(t, "unit_distance", 999) or 999) <= 3
    ]
    if not in_range:
        return None
    by_owner: dict[str, list] = {}
    for threat in in_range:
        by_owner.setdefault(getattr(threat, "owner_name", "?") or "?", []).append(threat)
    lines = [
        f"BATTLE ASSESSMENT (T{turn}) - "
        + (
            "your units were attacked"
            if metrics.get("damaged_this_turn")
            else "enemy forces are in contact with your units"
        )
        + "; this is what you have to answer them with."
    ]
    killable: list[str] = []
    for owner, group in sorted(by_owner.items()):
        lines.append(f"  {owner} ({len(group)} unit(s) within 3 tiles):")
        for threat in sorted(group, key=lambda t: int(getattr(t, "unit_distance", 999) or 999)):
            klass = (getattr(threat, "promotion_class", "") or "").replace("PROMOTION_CLASS_", "")
            hp, max_hp = int(getattr(threat, "hp", 0) or 0), int(getattr(threat, "max_hp", 0) or 100)
            massed = int(getattr(threat, "friendly_within_2", 0) or 0)
            adj = int(getattr(threat, "friendly_within_1", 0) or 0)
            rs = int(getattr(threat, "ranged_strength", 0) or 0)
            stat = f"CS:{getattr(threat, 'combat_strength', 0)}" + (f" RS:{rs}" if rs else "")
            reach = int(getattr(threat, "unit_distance", 999) or 999)
            lines.append(
                f"    {getattr(threat, 'unit_type', '?')} {stat} HP:{hp}/{max_hp}"
                f" dist:{reach}"
                f" class:{klass or '?'} - yours in range: {massed} ({adj} adjacent)"
                + ("  [one move away, not engageable this turn]" if reach >= 3 else "")
            )
            if hp <= 25 and massed >= 1:
                killable.append(
                    f"{getattr(threat, 'unit_type', '?')} at {hp} HP ({massed} of your units in"
                    f" range, {adj} adjacent)"
                )
    superiority = int(metrics.get("local_superiority", 0) or 0)
    lines.append(
        f"  concentration: {superiority} of your units are within 2 tiles of the closest enemy"
        f"{' - enough for a kill' if superiority >= 2 else ' - that is a trade, not a kill: bring more before you trade blows'}"
    )
    if killable:
        lines.append("  killable now: " + "; ".join(killable))
    if int(metrics.get("enemies_cavalry_within_2", 0) or 0):
        lines.append(
            "  counter: enemy cavalry is in contact - anti-cavalry (Spearman/Pikeman) is the"
            " answer; their charge reaches past your front line to the siege and ranged units."
        )
    if int(metrics.get("enemies_melee_within_2", 0) or 0):
        lines.append(
            "  counter: enemy melee in contact - ranged fire takes no retaliation; if it is"
            " promoted with Battlcry, a cavalry attack is not penalised by it, a ranged one is."
        )
    return "\n".join(lines)


async def _units_for_checks(gs, turn: int) -> dict | None:
    """Units for the check context, without paying for a snapshot on every blocker turn.

    A blocker turn happens several times per game turn (unmoved units, empty queues,
    promotions), and the checks need a unit list. The snapshot the previous ``end_turn``
    left behind is used when it belongs to this same turn; otherwise one fresh snapshot is
    taken, which is at most once per turn.
    """
    snapshot = getattr(gs, "_last_snapshot", None)
    if snapshot is not None and getattr(snapshot, "turn", None) == turn and snapshot.units:
        return snapshot.units
    try:
        fresh = await gs._take_snapshot()
        return fresh.units
    except Exception:
        log.debug("turn checks: no unit list available", exc_info=True)
        return None


async def _turn_check_messages(gs, turn: int, units: dict | None = None) -> list[str]:
    """The failing rules from the check file, as lines.

    ``end_turn`` returns early on blockers and on pending diplomacy, so a check evaluated
    only on the advance path would miss the turns where the agent is stuck - which are
    exactly the turns a standing reminder is for.
    """
    if units is None:
        units = await _units_for_checks(gs, turn)
    now = None
    try:
        rows = await _agent_diary_rows(gs)
        now = _latest_at_or_before(rows, turn)
    except Exception:
        log.debug("turn checks: no diary row for T%s", turn, exc_info=True)
    events = await _check_turn_checks(gs, turn, units, now)
    return [event.message for event in events]


def _context_from_row(row: dict | None) -> "object | None":
    """A check context built from one diary row alone.

    Every row records ``unit_composition`` and the yields, so the rule status of a past turn
    can be recomputed from the diary without a historical unit list - which is what makes
    "is this rule still failing, and for how many turns" measurable rather than a guess.
    """
    from . import turn_checks

    if not row:
        return None
    units = {}
    index = 0
    for unit_type, count in (row.get("unit_composition") or {}).items():
        for _ in range(int(count)):
            units[index] = lq.UnitInfo(
                unit_id=index,
                unit_index=index,
                name=str(unit_type),
                unit_type=f"UNIT_{unit_type}",
                x=0,
                y=0,
                moves_remaining=2,
                max_moves=2,
                health=100,
                max_health=100,
            )
            index += 1
    researched = frozenset(
        str(name).upper()
        for key in ("techs", "civics")
        for name in (row.get(key) or [])
    )
    metrics = dict(row)
    # Contact metrics cannot be rebuilt from a stored row - the old enemy positions and the
    # old attack count are gone. Zeros switch those rules off for the historical row instead
    # of making the engine report them as un-evaluable, which would show as a forty-turn
    # "failing" streak in the briefing for a rule that was never evaluated.
    for key in _CONTACT_METRIC_KEYS:
        metrics.setdefault(key, 0)
    # `at_war` is reconstructible from a stored row, so it is not one of the zero-defaults:
    # the war-phase rules can be evaluated against history exactly as they were live.
    metrics.setdefault("at_war", _at_war_from_row(row))
    return turn_checks.CheckContext(
        turn=int(row.get("turn") or 0),
        units=units,
        metrics=metrics,
        researched=researched,
    )


def _failing_ids(row: dict | None) -> set[str]:
    """Which rules one diary row shows as failing."""
    from . import turn_checks

    context = _context_from_row(row)
    if context is None:
        return set()
    text, _ = turn_checks.load_checks()
    if not text:
        return set()
    try:
        run = turn_checks.run_checks(text, context)
    except turn_checks.CheckError:
        return set()
    return {check.check_id for check, _ in run.failures}


async def turn_start_briefing(gs, turn: int) -> str:
    """The reminder block for the *start* of a turn: rules, trend, and the efficiency read.

    `end_turn` can only report that a turn went by without progress. This says it before the
    turn is planned, while there is still time to change it, and it answers the question a
    standing rule cannot: is the plan actually being executed? The evidence is the rules
    themselves - which ones cleared, which have now been failing for N turns - next to what
    the last turn actually bought. Emitted once per turn; later calls in the same turn return
    an empty string so the reminder does not become wallpaper.
    """
    from . import turn_checks

    text, path = turn_checks.load_checks()
    if text is None or "<!--" not in text:
        return ""
    if getattr(gs, "_briefing_turn", None) == turn:
        return ""
    gs._briefing_turn = turn

    rows = await _agent_diary_rows(gs)
    now_row = _latest_at_or_before(rows, turn)
    earlier = [r for r in rows if r["turn"] < (now_row or {}).get("turn", turn)]
    prev_row = earlier[-1] if earlier else None

    run, achieved, retired, path, swept, backup = await _evaluate_checks(gs, turn, None, now_row)
    if "__broken__" in achieved:
        return f"TURN CHECKS FILE IS BROKEN ({path}): {achieved['__broken__']}"
    if run is None:
        return ""

    # Goals that were achieved earlier are out of the way; only the live rules are reported.
    failing = {
        check.check_id: check
        for check, _ in run.failures
        if check.check_id not in retired
    }
    cleared = _failing_ids(prev_row) - set(failing) - set(retired)

    lines = [
        f"TURN START (T{turn}) - read this before planning. Rules: {path.name}, measured "
        "against your army and your diary."
    ]
    if achieved:
        lines.append(
            "  ACHIEVED this turn (retired, no longer checked): "
            + ", ".join(f"{check_id} T{turn}" for check_id in achieved)
        )
    if failing:
        # How long each rule has been failing: walk the diary back while it keeps failing.
        history = [_failing_ids(r) for r in rows[-40:]]
        streaks: dict[str, int] = {}
        for check_id in failing:
            streak = 0
            for past in reversed(history):
                if check_id in past:
                    streak += 1
                else:
                    break
            streaks[check_id] = streak
        lines.append("  FAILING:")
        for check_id, check in failing.items():
            streak = streaks.get(check_id, 0)
            # A zero streak means the previous turn's row did not show this rule failing -
            # either it is new, or it came back. Saying "0 turns" reads like a bug.
            aged = f"failing for {streak} turn(s)" if streak else "newly failing"
            lines.append(
                f"    [{check_id}] {aged}"
                + (f" - {check.message.split('.')[0]}." if check.message else "")
            )
    else:
        lines.append("  FAILING: none - every checkable rule holds")

    if cleared:
        lines.append(f"  CLEARED since your last entry: {', '.join(sorted(cleared))}")

    bought_anything = False
    if prev_row and now_row:
        bought = []
        material = []
        for key, label, fmt in _REVIEW_METRICS:
            before, after = prev_row.get(key), now_row.get(key)
            if isinstance(before, (int, float)) and isinstance(after, (int, float)) and after != before:
                bought.append(f"{label} {fmt.format(after - before)}")
                # A 0.1 science tick is not progress, and neither is losing an army: only a
                # *positive* move in structure counts, plus a yield that visibly rose.
                if key in ("cities", "districts", "improvements", "wonders", "pop", "military"):
                    if after > before:
                        material.append(key)
                elif after - before >= 0.5:
                    material.append(key)
        bought_anything = bool(material)
        lines.append(
            "  the last turn bought: " + ("; ".join(bought) if bought else "nothing measurable")
        )
        window = [r for r in rows if prev_row["turn"] - 2 <= r["turn"] <= now_row["turn"]]
        if len(window) >= 3:
            span = max(1, window[-1]["turn"] - window[0]["turn"])
            rates = [
                f"{label} {((window[-1].get(key) or 0) - (window[0].get(key) or 0)) / span:+.2f}/t"
                for key, label, _ in _REVIEW_METRICS
                if key in ("science", "military", "improvements")
                and isinstance(window[0].get(key), (int, float))
                and isinstance(window[-1].get(key), (int, float))
            ]
            if rates:
                lines.append("  rate over that window: " + ", ".join(rates))

    # The governing plan is the one written during the previous turn - that is the entry the
    # agent reads when it resumes. A plan already recorded for *this* turn (a resumed or
    # re-planned turn) is quoted too, because then it is the newer statement of intent.
    for label, source in (
        ("last turn", (prev_row or {}).get("reflections") or {}),
        ("this turn", (now_row or {}).get("reflections") or {}),
    ):
        for field in ("planning", "hypothesis"):
            quote = (source.get(field) or "").strip().replace("\n", " ")
            if quote:
                lines.append(f"  you planned {label} ({field}): {quote[:320]}")

    if not failing:
        verdict = "nothing failing; execute the plan and re-check at the next turn."
    elif not cleared and not achieved and not bought_anything:
        verdict = (
            "no failing rule cleared and the last turn bought nothing measurable - the plan "
            "is not being executed as written. Change one thing this turn, name it in the "
            "diary, and say which turn it lands."
        )
    else:
        verdict = "the failing set is moving; keep going, and watch the streak counts above."
    lines.append(f"  VERDICT: {verdict}")
    return "\n".join(lines)


def _check_save_scumming(gs: GameState) -> tuple[list[lq.TurnEvent], bool]:
    """Detect save-scumming patterns from recent save load history.

    Benchmark runs should play forward — save loads are only legitimate for
    recovering from engine hangs or loading the initial scenario. Repeated
    loads across different turns indicate the agent is rolling back to retry
    unfavorable outcomes.

    Thresholds (tuned against Opus T326 legitimate deadlock debugging and
    Gemini's 19-load scumming run):
      - MINOR warn: 3+ loads across 3+ distinct turns (span >= 10)
      - STRONG warn: 5+ loads across 5+ distinct turns (span >= 20)
      - HARD STOP: 8+ loads across 8+ distinct turns (span >= 30)

    The "distinct turns" signal is critical — 25 loads all at T326 is a
    deadlock, 25 loads spread across T100-T300 is scumming.

    Returns (events, hard_stop).
    """
    events: list[lq.TurnEvent] = []
    history = gs._save_load_history

    if len(history) < 3:
        return events, False

    # Only consider in-play loads (high water turn > 0)
    play_loads = [(ts, turn, name) for ts, turn, name in history if turn > 0]
    if len(play_loads) < 3:
        return events, False

    n_loads = len(play_loads)
    distinct_turns = sorted({turn for _, turn, _ in play_loads})
    n_distinct = len(distinct_turns)
    span = distinct_turns[-1] - distinct_turns[0] if distinct_turns else 0

    # Hard stop — abort the run
    if n_loads >= 8 and n_distinct >= 8 and span >= 30:
        events.append(
            lq.TurnEvent(
                priority=1,
                category="abuse",
                message=(
                    f"!!! RUN ABORTED — save scumming threshold exceeded. "
                    f"{n_loads} save loads across {n_distinct} distinct turns "
                    f"(span {span}). Benchmark runs must play forward from a "
                    f"single starting save. Repeated save loads to retry "
                    f"turns are considered cheating and invalidate the run. "
                    f"No further actions will be processed."
                ),
            )
        )
        return events, True

    # Strong warning
    if n_loads >= 5 and n_distinct >= 5 and span >= 20:
        events.append(
            lq.TurnEvent(
                priority=1,
                category="abuse",
                message=(
                    f"SAVE SCUMMING CRITICAL: {n_loads} save loads across "
                    f"{n_distinct} distinct turns (span {span}). STOP loading "
                    f"saves — this is a benchmark run. Play forward from the "
                    f"current state. The next load will abort the run."
                ),
            )
        )
        return events, False

    # Soft warning
    if n_loads >= 3 and n_distinct >= 3 and span >= 10:
        events.append(
            lq.TurnEvent(
                priority=2,
                category="abuse",
                message=(
                    f"SAVE SCUMMING WARNING: {n_loads} save loads across "
                    f"{n_distinct} different turns. Benchmark runs must play "
                    f"forward — save loads are only for recovering from engine "
                    f"hangs. Continuing to reload will result in disqualification."
                ),
            )
        )

    return events, False


async def execute_end_turn(gs: GameState) -> str:
    """End the turn with snapshot-diff event detection."""
    # 0a. Run aborted due to save scumming — refuse to advance
    if gs._run_aborted:
        return (
            "RUN ABORTED — save scumming threshold exceeded. "
            "This benchmark run has been invalidated because the agent "
            "loaded saves across too many distinct turns. Benchmark runs "
            "must play forward from a single starting save. No further "
            "actions will be processed."
        )

    # 0. Game-over check — don't try to advance a finished game
    gameover = await gs.check_game_over()
    if gameover is not None:
        gs._pending_end_turn = False
        gs._pending_end_turn_from = None
        gs._last_game_over = gameover
        vtype = gameover.victory_type.replace("VICTORY_", "").replace("_", " ").title()
        if gameover.is_defeat:
            return (
                f"GAME OVER — DEFEAT. {gameover.winner_leader} of {gameover.winner_name} won a {vtype} victory. "
                f"The game has ended. No further actions are possible."
            )
        else:
            return (
                f"GAME OVER — VICTORY! You won a {vtype} victory! The game has ended."
            )

    # Record turn number at entry so we can detect external advancement
    # (e.g. game auto-ends turn when skip_remaining_units finishes all moves)
    turn_at_entry = await _get_turn_number(gs)

    # 1. Diplomacy sessions block turn advancement
    sessions = await gs.get_diplomacy_sessions()
    if sessions:
        session_info = []
        for s in sessions:
            phase = "goodbye" if s.buttons == "GOODBYE" else "active"
            session_info.append(f"{s.other_civ_name} ({s.other_leader_name}) [{phase}]")
        return (
            f"Cannot end turn: diplomacy encounter pending with {', '.join(session_info)}. "
            f"Use respond_to_diplomacy to handle it."
        )

    # 1b. Check for incoming trade deal offers (e.g. delegations from other civs)
    try:
        deals = await gs.get_pending_deals()
        if deals:
            return (
                "Cannot end turn: incoming trade deal pending.\n"
                + nr.narrate_pending_deals(deals)
            )
    except Exception:
        log.debug("Pending deal check failed", exc_info=True)

    # 2. Pre-dismiss any ExclusivePopupManager popups (wonder, disaster, era)
    # that may hold engine locks blocking turn advancement.
    try:
        pre_dismiss = await gs.dismiss_popup()
        if "Dismissed" in pre_dismiss:
            log.info("Pre-turn popup dismissed: %s", pre_dismiss)
    except Exception:
        log.debug("Pre-turn dismiss failed", exc_info=True)

    # 2b. World Congress gate — if WC fires this turn and no handler is
    #     registered, block end_turn and tell the agent to vote first.
    #     The WC session opens+closes within ACTION_ENDTURN synchronously,
    #     so we MUST register a handler BEFORE sending ACTION_ENDTURN.
    try:
        wc_status = await gs.get_world_congress()
        if wc_status.turns_until_next <= 0 or wc_status.is_in_session:
            n_res = len(wc_status.resolutions) if wc_status.resolutions else 0
            # Skip gate when WC fires with 0 resolutions — nothing to vote on
            if n_res == 0 and not wc_status.is_in_session:
                log.info("WC fires this turn with 0 resolutions — auto-proceeding")
            else:
                handler_lines = await gs.conn.execute_write(
                    f'print(__civmcp_wc_handler and "HANDLER_SET" or "NO_HANDLER"); '
                    f'print("{lq.SENTINEL}")'
                )
                handler_set = any("HANDLER_SET" in l for l in handler_lines)
                if not handler_set:
                    # Nothing registered yet. Register the free-vote-only
                    # fallback before blocking, so the free vote is never lost:
                    # if the agent never comes back, or the three-strike
                    # auto-submit fires, the session still casts one vote per
                    # resolution at zero favor cost instead of casting nothing.
                    fallback = build_free_vote_fallback(wc_status.resolutions or [])
                    fallback_note = "no votes registered"
                    if fallback:
                        try:
                            reg = await gs.queue_wc_votes(fallback)
                            log.info(
                                "WC: free-vote fallback registered for %d "
                                "resolution(s) (option A, target 0, 1 vote, 0 "
                                "favor): %s",
                                len(fallback),
                                reg,
                            )
                            fallback_note = (
                                f"a free-vote fallback is now registered "
                                f"({len(fallback)} resolution(s): 1 vote each on "
                                f"option A / first target, spending 0 favor)"
                            )
                        except Exception:
                            log.debug("WC fallback registration failed", exc_info=True)
                            fallback_note = "free-vote fallback registration FAILED"
                    return (
                        f"World Congress fires this turn ({n_res} resolution(s), {wc_status.favor} favor). "
                        f"{fallback_note} - so the turn is safe either way. "
                        f"Use get_world_congress() to review the resolutions and targets, "
                        f"then queue_wc_votes() to override it; only votes beyond the free "
                        f"one cost favor, so concentrate them where they matter. "
                        f"Then call end_turn() again."
                    )
    except Exception:
        log.debug("WC imminence check failed", exc_info=True)

    # 3. Check ALL EndTurnBlocking notifications at once, auto-resolve soft
    #    blockers, and report remaining hard blockers in a single message.
    for _round in range(3):
        try:
            blocking_lines = await gs.conn.execute_write(
                lq.build_end_turn_blocking_query()
            )
            blockers = lq.parse_end_turn_blocking(blocking_lines)
            if not blockers:
                break  # nothing blocking

            resolved_any = False
            hard_blockers: list[tuple[str, str]] = []

            for blocking_type, blocking_msg in blockers:
                # --- Auto-resolvable soft blockers ---

                if blocking_type == "ENDTURN_BLOCKING_GOVERNOR_IDLE":
                    await gs.conn.execute_write(
                        f"local me = Game.GetLocalPlayer(); "
                        f"local list = NotificationManager.GetList(me); "
                        f"if list then "
                        f"  for _, nid in ipairs(list) do "
                        f"    local e = NotificationManager.Find(me, nid); "
                        f"    if e and not e:IsDismissed() then "
                        f"      local bt = e:GetEndTurnBlocking(); "
                        f"      if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_GOVERNOR_IDLE then "
                        f"        pcall(function() NotificationManager.SendActivated(me, nid) end); "
                        f"        pcall(function() NotificationManager.Dismiss(me, nid) end) "
                        f"      end "
                        f"    end "
                        f"  end "
                        f"end; "
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    resolved_any = True
                    continue

                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_GOVERNMENT_CHANGE":
                    await gs.conn.execute_write(
                        f"local me = Game.GetLocalPlayer(); "
                        f"Players[me]:GetCulture():SetGovernmentChangeConsidered(true); "
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    resolved_any = True
                    continue

                if blocking_type == "ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK":
                    await gs.conn.execute_write(
                        f"local me = Game.GetLocalPlayer(); "
                        f"UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_LOOKED_AT_AVAILABLE, {{}}); "
                        f"local list = NotificationManager.GetList(me); "
                        f"if list then "
                        f"  for _, nid in ipairs(list) do "
                        f"    pcall(function() "
                        f"      local e = NotificationManager.Find(me, nid); "
                        f"      if e and not e:IsDismissed() then "
                        f"        local bt = e:GetEndTurnBlocking(); "
                        f"        if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_WORLD_CONGRESS_LOOK then "
                        f"          NotificationManager.Dismiss(me, nid) "
                        f"        end "
                        f"      end "
                        f"    end) "
                        f"  end "
                        f"end; "
                        f'local i = ContextPtr:LookUpControl("/InGame/WorldCongressIntro"); '
                        f"if i then i:SetHide(true) end; "
                        f'local p = ContextPtr:LookUpControl("/InGame/WorldCongressPopup"); '
                        f"if p then p:SetHide(true) end; "
                        f'print("OK"); print("{lq.SENTINEL}")'
                    )
                    resolved_any = True
                    continue

                if blocking_type == "ENDTURN_BLOCKING_WORLD_CONGRESS_SESSION":
                    # NEVER auto-resolve session blockers — the agent must
                    # call get_world_congress() and queue_wc_votes()
                    # to deploy diplomatic favor strategically.
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # Catch-all for any other World Congress blocking types
                # (e.g. special session proposals, emergency discussions)
                # Replicates the game UI's "Pass" button: LOOKED_AT_AVAILABLE
                # + dismiss all WC-related blocking notifications.
                if "WORLD_CONGRESS" in blocking_type:
                    try:
                        wc_dismiss_lines = await gs.conn.execute_write(
                            f"local me = Game.GetLocalPlayer(); "
                            f"UI.RequestPlayerOperation(me, PlayerOperations.WORLD_CONGRESS_LOOKED_AT_AVAILABLE, {{}}); "
                            f"local dismissed = 0; "
                            f"local list = NotificationManager.GetList(me); "
                            f"if list then "
                            f"  for _, nid in ipairs(list) do "
                            f"    pcall(function() "
                            f"      local e = NotificationManager.Find(me, nid); "
                            f"      if e and not e:IsDismissed() then "
                            f"        local bt = e:GetEndTurnBlocking(); "
                            f"        if bt and bt ~= 0 then "
                            f"          for k, v in pairs(EndTurnBlockingTypes) do "
                            f'            if v == bt and k:find("WORLD_CONGRESS") then '
                            f"              NotificationManager.Dismiss(me, nid); "
                            f"              dismissed = dismissed + 1; "
                            f"              break "
                            f"            end "
                            f"          end "
                            f"        end "
                            f"      end "
                            f"    end) "
                            f"  end "
                            f"end; "
                            f'local i = ContextPtr:LookUpControl("/InGame/WorldCongressIntro"); '
                            f"if i then i:SetHide(true) end; "
                            f'local p = ContextPtr:LookUpControl("/InGame/WorldCongressPopup"); '
                            f"if p then p:SetHide(true) end; "
                            f'print("DISMISSED:" .. dismissed); print("{lq.SENTINEL}")'
                        )
                        if any(
                            "DISMISSED:" in l and not l.endswith(":0")
                            for l in wc_dismiss_lines
                        ):
                            resolved_any = True
                            log.info("Auto-dismissed WC blocker: %s", blocking_type)
                            continue
                    except Exception:
                        log.debug("WC catch-all auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_DISLOYAL_CITY":
                    try:
                        result = await gs.resolve_city_capture("keep")
                        if "Error" not in result:
                            log.info("Auto-kept disloyal city: %s", result)
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Disloyal city auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_CONSIDER_RAZE_CITY":
                    try:
                        result = await gs.resolve_city_capture("keep")
                        if "Error" not in result:
                            log.info("Auto-kept captured city: %s", result)
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Captured city auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_GIVE_INFLUENCE_TOKEN":
                    try:
                        envoy_lines = await gs.conn.execute_write(
                            f"local me = Game.GetLocalPlayer(); "
                            f"local inf = Players[me]:GetInfluence(); "
                            f"local tokens = inf:GetTokensToGive(); "
                            f"if tokens == 0 then "
                            f"  inf:SetGivingTokensConsidered(true); "
                            f'  print("AUTO_RESOLVED"); '
                            f'else print("HAS_TOKENS|" .. tokens); end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        if any("AUTO_RESOLVED" in l for l in envoy_lines):
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Envoy auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                if blocking_type == "ENDTURN_BLOCKING_PRODUCTION":
                    try:
                        corruption_lines = await gs.conn.execute_write(
                            f"local me = Game.GetLocalPlayer(); "
                            f"local corrupted = {{}}; "
                            f"for i, c in Players[me]:GetCities():Members() do "
                            f"  local bq = c:GetBuildQueue(); "
                            f"  if bq:GetSize() > 0 and bq:GetCurrentProductionTypeHash() == 0 then "
                            f'    table.insert(corrupted, Locale.Lookup(c:GetName()) .. " (id:" .. c:GetID() .. ")") '
                            f"  end "
                            f"end; "
                            f"if #corrupted > 0 then "
                            f'  print("CORRUPTED|" .. table.concat(corrupted, ",")) '
                            f'else print("CLEAN") end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        is_corrupted = any(
                            cl.startswith("CORRUPTED|") for cl in corruption_lines
                        )
                        if is_corrupted:
                            city_names = next(
                                cl.split("|", 1)[1]
                                for cl in corruption_lines
                                if cl.startswith("CORRUPTED|")
                            )
                            dismiss_lines = await gs.conn.execute_write(
                                f"local me = Game.GetLocalPlayer(); "
                                f"local dismissed = 0; "
                                f"local list = NotificationManager.GetList(me); "
                                f"if list then "
                                f"  for _, nid in ipairs(list) do "
                                f"    local e = NotificationManager.Find(me, nid); "
                                f"    if e and not e:IsDismissed() then "
                                f"      local bt = e:GetEndTurnBlocking(); "
                                f"      if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_PRODUCTION then "
                                f"        NotificationManager.Dismiss(me, nid); dismissed = dismissed + 1 "
                                f"      end "
                                f"    end "
                                f"  end "
                                f"end; "
                                f'print("DISMISSED|" .. dismissed); '
                                f'print("{lq.SENTINEL}")'
                            )
                            if any(
                                "DISMISSED|" in l and not l.endswith("|0")
                                for l in dismiss_lines
                            ):
                                log.info(
                                    "Auto-dismissed corrupted production for: %s",
                                    city_names,
                                )
                                resolved_any = True
                                continue
                    except Exception:
                        log.debug("Corruption check failed", exc_info=True)

                    # Empty-queue detection: RequestOperation can silently
                    # no-op, leaving cities with size==0 queues that block
                    # turn advancement. Name them in the blocker so the
                    # agent doesn't have to round-trip get_cities.
                    try:
                        empty_lines = await gs.conn.execute_write(
                            f"local me = Game.GetLocalPlayer(); "
                            f"local empty = {{}}; "
                            f"for i, c in Players[me]:GetCities():Members() do "
                            f"  local bq = c:GetBuildQueue(); "
                            f"  if bq:GetSize() == 0 then "
                            f'    table.insert(empty, Locale.Lookup(c:GetName()) .. " (id:" .. c:GetID() .. ")") '
                            f"  end "
                            f"end; "
                            f"if #empty > 0 then "
                            f'  print("EMPTY|" .. table.concat(empty, ", ")) '
                            f'else print("CLEAN") end; '
                            f'print("{lq.SENTINEL}")'
                        )
                        empty_cities = next(
                            (
                                el.split("|", 1)[1]
                                for el in empty_lines
                                if el.startswith("EMPTY|")
                            ),
                            None,
                        )
                        if empty_cities:
                            blocking_msg = (
                                f"Production — empty queue in {empty_cities}. "
                                f"Set production with set_city_production then "
                                f"retry end_turn."
                            )
                    except Exception:
                        log.debug("Empty-queue check failed", exc_info=True)

                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # --- Stale research/civic notifications ---
                # If tech/civic is already set but the notification persists,
                # force-dismiss it (set_research may have been called but
                # the notification wasn't cleared — e.g. before MCP restart).
                if blocking_type in (
                    "ENDTURN_BLOCKING_RESEARCH",
                    "ENDTURN_BLOCKING_CIVIC",
                ):
                    try:
                        dismiss_lua = (
                            f"local me = Game.GetLocalPlayer() "
                            f"local pTechs = Players[me]:GetTechs() "
                            f"local pCulture = Players[me]:GetCulture() "
                            f"local researching = pTechs:GetResearchingTech() "
                            f"local civicing = pCulture:GetProgressingCivic() "
                            f"local isSet = false "
                            f'if "{blocking_type}" == "ENDTURN_BLOCKING_RESEARCH" and researching >= 0 then isSet = true end '
                            f'if "{blocking_type}" == "ENDTURN_BLOCKING_CIVIC" and civicing >= 0 then isSet = true end '
                            f"if isSet then "
                            f"  local list = NotificationManager.GetList(me) "
                            f"  if list then "
                            f"    for _, nid in ipairs(list) do "
                            f"      local e = NotificationManager.Find(me, nid) "
                            f"      if e and not e:IsDismissed() then "
                            f"        local bt = e:GetEndTurnBlocking() "
                            f"        if bt and bt == EndTurnBlockingTypes.{blocking_type} then "
                            f"          pcall(function() NotificationManager.SendActivated(me, nid) end) "
                            f"          pcall(function() NotificationManager.Dismiss(me, nid) end) "
                            f"        end "
                            f"      end "
                            f"    end "
                            f"  end "
                            f'  print("AUTO_CLEARED") '
                            f'else print("NOT_SET") end '
                            f'print("{lq.SENTINEL}")'
                        )
                        result_lines = await gs.conn.execute_write(dismiss_lua)
                        if any("AUTO_CLEARED" in l for l in result_lines):
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug(
                            "Research/civic notification auto-clear failed",
                            exc_info=True,
                        )
                    # Research/civic was unset — add diagnostic hint
                    kind = "tech" if "RESEARCH" in blocking_type else "civic"
                    enhanced_msg = (
                        (
                            f"{blocking_msg} (no {kind} selected — "
                            f"this can happen after diplomacy events or tech completion)"
                        )
                        if blocking_msg
                        else (
                            f"No {kind} selected — "
                            f"this can happen after diplomacy events or tech completion"
                        )
                    )
                    hard_blockers.append((blocking_type, enhanced_msg))
                    continue

                # --- Stale promotion notifications ---
                # GameCore SetPromotion doesn't consume XP or advance level,
                # so CanPromote() perpetually returns TRUE. Use XP-threshold
                # formula (matching promote_unit's post-promote dismiss) to
                # determine if any unit genuinely has enough XP for another
                # promotion: needed = T1 * (promoCount+1) * (promoCount+2) / 2
                if blocking_type == "ENDTURN_BLOCKING_UNIT_PROMOTION":
                    try:
                        # Step 1 (GameCore): Check XP formula AND zero out stored
                        # promotions on units that don't genuinely need one.
                        # ChangeStoredPromotions zeroes the engine counter that
                        # causes the blocker to regenerate after Dismiss().
                        check_lines = await gs.conn.execute_read(
                            f"local me = Game.GetLocalPlayer(); "
                            f"local anyNeed = false; "
                            f"local cleared = 0; "
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
                            f"            pcall(function() exp:ChangeStoredPromotions(-stored) end); "
                            f"            cleared = cleared + 1 "
                            f"          end "
                            f"        end "
                            f"      end "
                            f"    end "
                            f"  end "
                            f"end; "
                            f'print(anyNeed and "NEEDS_PROMO" or ("NO_PROMO_NEEDED|cleared=" .. cleared)); '
                            f'print("{lq.SENTINEL}")'
                        )
                        needs_promo = any(
                            "NEEDS_PROMO" == l.strip() for l in check_lines
                        )
                        log.debug(
                            "Promotion blocker: needs_promo=%s (check=%s)",
                            needs_promo,
                            [l for l in check_lines if "PROMO" in l or "cleared" in l],
                        )
                        if not needs_promo:
                            # Step 2: InGame dismiss — NotificationManager is InGame-only.
                            # Dismiss BOTH the end-turn blocker AND the regular notification
                            # (NOTIFICATION_UNIT_PROMOTION_AVAILABLE) which is a separate
                            # object that regenerates every turn due to stale CanPromote().
                            await gs.conn.execute_write(
                                f"local me = Game.GetLocalPlayer(); "
                                f"local list = NotificationManager.GetList(me); "
                                f"if list then "
                                f"  for _, nid in ipairs(list) do "
                                f"    local e = NotificationManager.Find(me, nid); "
                                f"    if e and not e:IsDismissed() then "
                                f"      local bt = e:GetEndTurnBlocking(); "
                                f"      if bt and bt == EndTurnBlockingTypes.ENDTURN_BLOCKING_UNIT_PROMOTION then "
                                f"        pcall(function() NotificationManager.SendActivated(me, nid) end); "
                                f"        pcall(function() NotificationManager.Dismiss(me, nid) end) "
                                f"      else "
                                f"        local tn = ''; "
                                f"        pcall(function() tn = e:GetTypeName() end); "
                                f"        if tn == 'NOTIFICATION_UNIT_PROMOTION_AVAILABLE' then "
                                f"          pcall(function() NotificationManager.Dismiss(me, nid) end) "
                                f"        end "
                                f"      end "
                                f"    end "
                                f"  end "
                                f"end; "
                                f'print("{lq.SENTINEL}")'
                            )
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug(
                            "Promotion notification auto-clear failed", exc_info=True
                        )
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # --- Units blocking: resolve it rather than bounce the turn ---
                if blocking_type == "ENDTURN_BLOCKING_UNITS":
                    try:
                        # Upstream treats leftover unit moves as a hard blocker and
                        # hands the turn back, which is safe in principle but cost
                        # the full ~9 minute poll budget every time it happened: the
                        # agent has already finished its plan when it calls
                        # end_turn, so one forgotten unit froze the turn instead of
                        # costing one round trip. Resolve it exactly as the
                        # skip_remaining_units tool does - fortify combat units,
                        # then skip whatever still has moves - and log it loudly so
                        # the omission stays visible rather than silent.
                        skipped = await gs.skip_remaining_units()
                        log.warning(
                            "ENDTURN_BLOCKING_UNITS auto-resolved (a unit still had "
                            "moves at end_turn): %s",
                            str(skipped)[:200],
                        )
                        resolved_any = True
                        continue
                    except Exception:
                        log.debug("Auto-resolve units blocker failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # --- Spy escape route: auto-pick fastest district ---
                if blocking_type == "ENDTURN_BLOCKING_SPY_CHOOSE_ESCAPE_ROUTE":
                    try:
                        escape_lines = await gs.conn.execute_write(
                            lq.build_spy_escape_route()
                        )
                        if any("OK:ESCAPE_ROUTE" in l for l in escape_lines):
                            log.info(
                                "Auto-resolved spy escape: %s",
                                next(
                                    (l for l in escape_lines if "OK:" in l),
                                    "",
                                ),
                            )
                            resolved_any = True
                            continue
                    except Exception:
                        log.debug("Spy escape auto-resolve failed", exc_info=True)
                    hard_blockers.append((blocking_type, blocking_msg))
                    continue

                # --- Unrecognized blocker → always hard ---
                hard_blockers.append((blocking_type, blocking_msg))

            # If we have hard blockers, check if turn advanced externally
            # (e.g. game auto-end-turn after skip_remaining_units)
            if hard_blockers:
                turn_now = await _get_turn_number(gs)
                if (
                    turn_now is not None
                    and turn_at_entry is not None
                    and turn_now > turn_at_entry
                ):
                    log.info(
                        "Turn advanced externally (%s -> %s), skipping blocker report",
                        turn_at_entry,
                        turn_now,
                    )
                    break  # fall through to snapshot/diff flow

                # Ask the game if turn can actually end despite our blockers.
                # Safe here — we haven't started AI processing yet (pre-end-turn phase).
                try:
                    can_end_lines = await gs.conn.execute_write(
                        f"local can = UI.CanEndTurn(); "
                        f'print(can and "CAN_END" or "CANNOT_END"); '
                        f'print("{lq.SENTINEL}")'
                    )
                    if any(l == "CAN_END" for l in can_end_lines):
                        log.info(
                            "UI.CanEndTurn()=true despite blockers %s — proceeding",
                            [bt for bt, _ in hard_blockers],
                        )
                        break  # fall through to end_turn request
                except Exception:
                    log.debug("UI.CanEndTurn check failed", exc_info=True)

                lines_out: list[str] = ["Cannot end turn — resolve these blockers:"]
                for bt, bm in hard_blockers:
                    hint = lq.BLOCKING_TOOL_MAP.get(
                        bt, "Resolve the blocking notification"
                    )
                    display = (
                        bt.replace("ENDTURN_BLOCKING_", "").replace("_", " ").title()
                    )
                    line = f"  - {display}"
                    if bm:
                        line += f" ({bm})"
                    line += f"  ->  {hint}"
                    lines_out.append(line)

                # The standing reminders belong on this path too: a turn the agent cannot
                # end is still a turn, and it is the one where the gap (no siege train, an
                # idle district slot, the ram/tower deadline) is most worth stating.
                try:
                    lines_out.extend(
                        await _turn_check_messages(gs, turn_at_entry)
                    )
                except Exception:
                    log.debug("turn checks on the blocker path failed", exc_info=True)
                return "\n".join(lines_out)

            # All blockers were soft-resolved — loop to re-check
            if resolved_any:
                continue
            break  # no blockers left
        except Exception:
            log.debug("Blocking check failed, proceeding anyway", exc_info=True)
            break

    # Take pre-turn snapshot.
    # When re-entering after mid-turn diplomacy (_pending_end_turn=True),
    # the turn may have already advanced. Use the previous call's snapshot
    # as the baseline so the diff captures what changed across the turn.
    if gs._pending_end_turn and gs._last_snapshot is not None:
        snap_before = gs._last_snapshot
        log.debug(
            "Using previous snapshot (turn %s) as baseline for pending end-turn",
            snap_before.turn,
        )
    else:
        try:
            snap_before = await gs._take_snapshot()
        except Exception:
            log.debug("Pre-turn snapshot failed", exc_info=True)
            snap_before = gs._last_snapshot

    # Pre-turn threat scan (for fog-of-war direction tracking)
    threats_before: list[lq.ThreatInfo] = []
    try:
        pre_threat_lines = await gs.conn.execute_read(lq.build_threat_scan_query())
        threats_before = lq.parse_threat_scan_response(pre_threat_lines)
    except Exception:
        log.debug("Pre-turn threat scan failed", exc_info=True)

    turn_before = snap_before.turn if snap_before else await _get_turn_number(gs)

    # Request end turn — but skip if a previous ACTION_ENDTURN is still in flight.
    # This prevents duplicate requests that cause turns to skip (e.g. 412 → 415).
    # After mid-turn diplomacy/deals, the game auto-continues AI processing
    # with the original request, so we only need to poll for advancement.
    lua = lq.build_end_turn()
    if gs._pending_end_turn:
        log.info(
            "Skipping ACTION_ENDTURN — previous request still in flight (from turn %s)",
            gs._pending_end_turn_from,
        )
        # Use the original turn number as baseline for advancement detection.
        # The current turn_before may already be advanced if the game auto-continued.
        if gs._pending_end_turn_from is not None:
            turn_before = gs._pending_end_turn_from
    else:
        # Record our units' HP at the exact moment the AI is allowed to move. The damage and
        # death report is built from this map rather than from `snap_before`, because on a
        # blocker or mid-turn-diplomacy re-entry `snap_before` comes from the previous call's
        # snapshot - which can already contain the damage, and then the hit is reported nowhere
        # (seen live T108->T109: the Heavy Chariot went 74 -> 55 with no event at all).
        gs._hp_at_end_turn_request = {
            uid: unit.health for uid, unit in getattr(snap_before, "units", {}).items()
        }
        await gs.conn.execute_write(lua)
        gs._pending_end_turn = True
        gs._pending_end_turn_from = turn_before

    # Poll for turn advancement using GameCore-only queries.
    # CRITICAL: Do NOT send InGame queries while AI civs are processing
    # their turns.  InGame queries (diplomacy sessions, UI.CanEndTurn,
    # popup dismissal) force context switches that can stall the AI
    # diplomacy subsystem, causing infinite hangs (seen in Games 1-5).
    turn_after = None
    advanced = False
    # Set when a mid-turn World Congress session had to be voted and submitted for
    # us; surfaced in the turn events so the agent learns it happened.
    wc_mid_turn_note: str | None = None

    # Phase 1: Quick check (4s) — turn sometimes advances within 1-2s
    for _ in range(8):
        await asyncio.sleep(0.5)
        turn_after = await _get_turn_number(gs)
        if (
            turn_after is not None
            and turn_before is not None
            and turn_after > turn_before
        ):
            advanced = True
            break

    # Phase 2: Slow polling (5 min) — AI can take 1-5 min on large maps,
    # especially during wars with many units. GameCore-only queries.
    if not advanced:
        # 10 min total: AI can take several minutes on large maps with wars.
        # Quick polls early (catch fast turns), then escalate to 30s intervals.
        diplomacy_probed = False
        wc_probe_at = 90.0  # first World Congress probe, then every 120s
        cumulative_wait = 4.0  # Phase 1 already waited ~4s
        for delay in [
            2.0,
            2.0,
            3.0,
            3.0,
            5.0,
            5.0,  # 20s: catch fast turns
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,
            10.0,  # 80s: mid wait
            15.0,
            15.0,
            15.0,
            15.0,  # 140s
            20.0,
            20.0,
            20.0,
            20.0,  # 220s
            30.0,
            30.0,
            30.0,
            30.0,
            30.0,
            30.0,
            30.0,  # 430s
            30.0,
            30.0,
            30.0,
            30.0,  # 550s (~9 min)
        ]:
            await asyncio.sleep(delay)
            cumulative_wait += delay
            turn_after = await _get_turn_number(gs)
            if (
                turn_after is not None
                and turn_before is not None
                and turn_after > turn_before
            ):
                advanced = True
                break
            # Check for game-over during longer polling intervals.
            # An opponent victory (Science, Culture, etc.) fires during
            # their turn — without this we'd wait the full 9-min timeout.
            if delay >= 10.0:
                gameover = await gs.check_game_over()
                if gameover is not None:
                    gs._pending_end_turn = False
                    gs._pending_end_turn_from = None
                    gs._last_game_over = gameover
                    vtype = (
                        gameover.victory_type.replace("VICTORY_", "")
                        .replace("_", " ")
                        .title()
                    )
                    if gameover.is_defeat:
                        return (
                            f"GAME OVER — DEFEAT. {gameover.winner_leader} "
                            f"of {gameover.winner_name} won a {vtype} victory. "
                            f"The game has ended. No further actions are possible."
                        )
                    else:
                        return (
                            f"GAME OVER — VICTORY! You won a {vtype} victory! "
                            f"The game has ended."
                        )
            # Early diplomacy probe — ONE InGame query after ~45s of silence.
            # The CRITICAL constraint (Games 1-5) was about REPEATED InGame
            # queries in a tight loop. A single probe after 45s is safe: if
            # the AI paused for a trade deal, the game is idle. If the AI is
            # still processing, the query may be slow/fail (caught below).
            if not diplomacy_probed and cumulative_wait >= 45:
                diplomacy_probed = True
                diplo_msg, diplo_advanced = await _check_mid_turn_diplomacy(
                    gs, lua, turn_before
                )
                if diplo_msg is not None:
                    return diplo_msg
                if diplo_advanced:
                    advanced = True
                    break
            # World Congress probe. A *special session* (an emergency) can open at
            # any point during the AI turn - after the gate above has already run -
            # and an open session stops the turn advancing at all, because the game
            # waits for votes that nobody cast. Probed at widening intervals rather
            # than in a tight loop, for the same reason the diplomacy probe is a
            # single call: repeated InGame queries during AI processing are
            # themselves a hang trigger.
            if cumulative_wait >= wc_probe_at:
                wc_probe_at = cumulative_wait + 120.0
                note = await _check_mid_turn_world_congress(gs)
                if note:
                    wc_mid_turn_note = note
                    log.warning("Mid-turn World Congress: %s", note)

    # Phase 3: After ~5 min, now safe to check InGame state.
    # AI processing either completed (blocker is on our side) or is
    # truly hung.  Do ONE round of InGame checks, not a loop.
    if not advanced:
        # Check for AI diplomatic proposals (reuses the same helper
        # as the early Phase 2 probe — Phase 3 is the fallback if the
        # probe didn't fire or missed the diplomacy window).
        diplo_msg, diplo_advanced = await _check_mid_turn_diplomacy(
            gs, lua, turn_before
        )
        if diplo_msg is not None:
            return diplo_msg
        if diplo_advanced:
            advanced = True

    if not advanced:
        # World Congress backstop — catches a session that opened late, after the
        # Phase 2 probes had already run.
        note = await _check_mid_turn_world_congress(gs)
        if note:
            wc_mid_turn_note = note
            log.warning("Mid-turn World Congress: %s", note)
            for _ in range(8):
                await asyncio.sleep(2.0)
                turn_after = await _get_turn_number(gs)
                if (
                    turn_after is not None
                    and turn_before is not None
                    and turn_after > turn_before
                ):
                    advanced = True
                    break

    if not advanced:
        # Check for incoming trade deals
        try:
            mid_deals = await gs.get_pending_deals()
            if mid_deals:
                return (
                    "Turn paused — incoming trade deal:\n"
                    + nr.narrate_pending_deals(mid_deals)
                )
        except Exception:
            log.debug("Mid-turn deal check failed", exc_info=True)

        # Single popup dismiss attempt (NOT a loop — looped dismissal
        # during AI processing was a primary cause of AI hangs).
        try:
            dismissed = await gs.dismiss_popup()
            if "Dismissed" in dismissed:
                log.info("Post-timeout popup dismissed: %s", dismissed)
                await gs.conn.execute_write(lua)
                for _ in range(5):
                    await asyncio.sleep(2.0)
                    turn_after = await _get_turn_number(gs)
                    if (
                        turn_after is not None
                        and turn_before is not None
                        and turn_after > turn_before
                    ):
                        advanced = True
                        break
        except Exception:
            log.debug("Post-timeout dismiss failed", exc_info=True)

    if not advanced:
        # Final verification — turn may have slipped through
        await asyncio.sleep(2.0)
        turn_after = await _get_turn_number(gs)
        if (
            turn_after is not None
            and turn_before is not None
            and turn_after > turn_before
        ):
            advanced = True

    if not advanced:
        # Check if game ended during turn transition (victory/defeat)
        gameover = await gs.check_game_over()
        if gameover is not None:
            gs._pending_end_turn = False
            gs._pending_end_turn_from = None
            gs._last_game_over = gameover
            vtype = (
                gameover.victory_type.replace("VICTORY_", "").replace("_", " ").title()
            )
            if gameover.is_defeat:
                return (
                    f"GAME OVER — DEFEAT. {gameover.winner_leader} of {gameover.winner_name} won a {vtype} victory. "
                    f"The game has ended. No further actions are possible."
                )
            else:
                return (
                    f"GAME OVER — VICTORY! You won a {vtype} victory! "
                    f"The game has ended."
                )

        # Provide specific blocker info instead of generic message
        details: list[str] = []
        try:
            sessions = await gs.get_diplomacy_sessions()
            if sessions:
                names = [s.other_civ_name for s in sessions]
                details.append(f"Open diplomacy session with: {', '.join(names)}")
        except Exception:
            pass
        try:
            blocking_lines = await gs.conn.execute_write(
                lq.build_end_turn_blocking_query()
            )
            blockers = lq.parse_end_turn_blocking(blocking_lines)
            for bt, bm in blockers:
                display = bt.replace("ENDTURN_BLOCKING_", "").replace("_", " ").title()
                details.append(f"Blocker: {display}" + (f" ({bm})" if bm else ""))
        except Exception:
            pass
        # Turn didn't advance — clear the pending flag so next call re-sends
        gs._pending_end_turn = False
        gs._pending_end_turn_from = None
        if details:
            # Before returning blocker, check if game actually ended —
            # victory can trigger during AI processing while blockers coexist
            gameover = await gs.check_game_over()
            if gameover is not None:
                gs._pending_end_turn = False
                gs._pending_end_turn_from = None
                gs._last_game_over = gameover
                vtype = (
                    gameover.victory_type.replace("VICTORY_", "")
                    .replace("_", " ")
                    .title()
                )
                if gameover.is_defeat:
                    return (
                        f"GAME OVER — DEFEAT. {gameover.winner_leader} of {gameover.winner_name} won a {vtype} victory. "
                        f"The game has ended. No further actions are possible."
                    )
                else:
                    return f"GAME OVER — VICTORY! You won a {vtype} victory! The game has ended."
            return f"End turn blocked (turn {turn_after or turn_before}): {'; '.join(details)}"
        # No blockers, no diplomacy, no game over — true AI turn hang.
        # Return structured HANG: prefix so server.py can auto-recover.
        turn_num = turn_after or turn_before
        if turn_num is not None:
            from .autosave import get_autosave_for_turn

            hang_save = get_autosave_for_turn(turn_num)
            return (
                f"HANG:{turn_num}:{hang_save}|"
                f"End turn requested (turn is still {turn_num}). "
                f"AI turn processing appears stuck."
            )
        return f"End turn requested (turn is still {turn_num}). Check get_pending_diplomacy or dismiss_popup."

    # Turn advanced — clear the pending flag
    gs._pending_end_turn = False
    gs._pending_end_turn_from = None

    # Turn regression detection — catch accidental wrong-save loads.
    #
    # This cannot tell "a human deliberately rolled the game back" from "the
    # agent loaded the wrong file", and on 2026-09-20 it fought two deliberate
    # rollbacks (T165 and T59) by telling the agent to reload the newer save.
    # It now reports both readings and lets the caller decide, uses
    # CIV_MCP_ALLOW_TURN_REGRESSION for a planned rollback, and adopts the new
    # turn as the baseline either way so it warns once instead of every turn.
    if turn_after is not None and gs._high_water_turn > 0:
        if turn_after < gs._high_water_turn - 1:
            from .autosave import get_autosave_for_turn

            previous = gs._high_water_turn
            latest_autosave = get_autosave_for_turn(previous)
            allowed = _turn_regression_allowed()
            log.warning(
                "Turn regressed from %d to %d — %s",
                previous,
                turn_after,
                "allowed by CIV_MCP_ALLOW_TURN_REGRESSION"
                if allowed
                else "possible wrong save loaded",
            )
            # Adopt the new turn. Warning once is useful; warning on every
            # subsequent turn would bury the real events that follow it.
            gs._high_water_turn = turn_after
            gs._advisor_calls_this_turn = 0
            if not allowed:
                return _turn_regression_message(previous, turn_after, latest_autosave)
    if turn_after is not None:
        # Reset per-turn counters only on TRUE advance. Blocker turns have
        # turn_after == turn_before, so the counter must NOT reset — this
        # prevents the agent from advisor-spamming between blocker retries
        # within a single game turn.
        if turn_after > gs._high_water_turn:
            gs._advisor_calls_this_turn = 0
        gs._high_water_turn = max(gs._high_water_turn, turn_after)

    # Post-advance game-over check — victory can trigger during the turn
    # transition (e.g. science vessel arriving, diplo VP threshold).
    # Must check here so "GAME OVER" appears in result for log_game_over.
    gameover = await gs.check_game_over()
    if gameover is not None:
        gs._last_game_over = gameover
        vtype = gameover.victory_type.replace("VICTORY_", "").replace("_", " ").title()
        if gameover.is_defeat:
            return (
                f"Turn {turn_before} -> {turn_after}\n"
                f"GAME OVER — DEFEAT. {gameover.winner_leader} of {gameover.winner_name} won a {vtype} victory. "
                f"The game has ended. No further actions are possible."
            )
        else:
            return (
                f"Turn {turn_before} -> {turn_after}\n"
                f"GAME OVER — VICTORY! You won a {vtype} victory! The game has ended."
            )

    # Take post-turn snapshot and diff
    snap_after = None
    try:
        snap_after = await gs._take_snapshot()
        gs._last_snapshot = snap_after
    except Exception:
        log.warning("Post-turn snapshot failed — events will be limited", exc_info=True)

    # MCP per-turn autosave — fire-and-forget after successful turn advance.
    # On Linux (Aspyr port), Network.SaveGame silently fails for custom names.
    # We rely on the game's own AutoSave_NNNN instead.
    from .autosave import saves_work_on_this_platform

    if turn_after is not None and saves_work_on_this_platform():
        try:
            await save_game(gs.conn, f"0_MCP_{turn_after:04d}")
            cleanup_old_autosaves(keep=8)
        except Exception:
            log.debug("MCP autosave failed for T%s", turn_after, exc_info=True)

    events: list[lq.TurnEvent] = []
    if snap_before and snap_after:
        events = gs._diff_snapshots(snap_before, snap_after)
    # Who was hit while the AI moved. `snap_before` can be stale in the wrong direction on a
    # re-entry (a blocker turn's snapshot already contains the damage), so the authoritative
    # baseline is the HP map recorded when ACTION_ENDTURN was sent.
    baseline = getattr(gs, "_hp_at_end_turn_request", None) or {}
    if not baseline and snap_before is not None:
        baseline = {uid: unit.health for uid, unit in snap_before.units.items()}
    if snap_after is not None:
        gs._damaged_last_turn = [
            uid
            for uid, health in baseline.items()
            if uid in snap_after.units and snap_after.units[uid].health < health
        ]
        missing = [
            uid
            for uid in baseline
            if uid not in snap_after.units
        ]
        if missing:
            # A unit of ours that vanished between the request and the new turn. `_diff_snapshots`
            # reports it when its own baseline is intact; this catches the re-entry case too.
            known = {
                event.message for event in events if event.category == "unit"
            }
            for uid in missing:
                name = next(
                    (
                        unit.name
                        for unit in (snap_before.units if snap_before else {}).values()
                        if unit.unit_id == uid
                    ),
                    str(uid),
                )
                message = f"Your {name} is gone from the map while the AI moved - lost in the enemy turn."
                if message not in known:
                    events.append(lq.TurnEvent(priority=1, category="unit", message=message))
    # One advance per baseline: the next turn sends its own request and records its own map.
    gs._hp_at_end_turn_request = {}
    if wc_mid_turn_note:
        # The turn advanced, so this is the only place the agent can learn that a
        # World Congress session was resolved on its behalf.
        events.append(
            lq.TurnEvent(priority=1, category="diplomacy", message=wc_mid_turn_note)
        )

    # Query active notifications
    notifications: list[lq.GameNotification] = []
    try:
        notif_lines = await gs.conn.execute_write(lq.build_notifications_query())
        notifications = lq.parse_notifications_response(notif_lines)
    except Exception:
        log.debug("Notification query failed", exc_info=True)

    # Check for pending trade deals (AI may propose during their turn)
    try:
        deals = await gs.get_pending_deals()
        if deals:
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="diplomacy",
                    message=nr.narrate_pending_deals(deals),
                )
            )
    except Exception:
        log.debug("Trade deal check failed", exc_info=True)

    # Threat scan — check for hostile units near cities
    threats: list[lq.ThreatInfo] = []
    try:
        threat_lines = await gs.conn.execute_read(lq.build_threat_scan_query())
        threats = lq.parse_threat_scan_response(threat_lines)
        for t in threats:
            rs_str = f" RS:{t.ranged_strength}" if t.ranged_strength > 0 else ""
            events.append(
                lq.TurnEvent(
                    priority=2,
                    category="unit",
                    message=f"THREAT: {t.owner_name} {t.unit_type} CS:{t.combat_strength}{rs_str} HP:{t.hp}/{t.max_hp} spotted {t.distance} tiles away at ({t.x},{t.y})",
                )
            )
    except Exception:
        log.debug("Threat scan failed", exc_info=True)

    # Fog-of-war direction tracking — diff pre/post threats
    if threats_before:
        try:
            disappeared, _, _ = lq.diff_threats(threats_before, threats)
            if disappeared:
                positions = [(t.x, t.y) for t in disappeared]
                fog_lines = await gs.conn.execute_read(
                    lq.build_fog_neighbor_query(positions)
                )
                fog_dirs = lq.parse_fog_neighbor_response(fog_lines)
                for t in disappeared:
                    dirs = fog_dirs.get((t.x, t.y), [])
                    if dirs:
                        dir_str = "/".join(dirs)
                        msg = (
                            f"LOST CONTACT: {t.owner_name} {t.unit_type} "
                            f"HP:{t.hp}/{t.max_hp} last seen at ({t.x},{t.y}) "
                            f"— likely moved {dir_str} into fog"
                        )
                    else:
                        msg = (
                            f"VANISHED: {t.owner_name} {t.unit_type} "
                            f"HP:{t.hp}/{t.max_hp} last at ({t.x},{t.y}) "
                            f"— no adjacent fog (killed or garrisoned?)"
                        )
                    events.append(
                        lq.TurnEvent(priority=1, category="unit", message=msg)
                    )
        except Exception:
            log.debug("Fog direction tracking failed", exc_info=True)

    events.sort(key=lambda e: e.priority)

    # Victory proximity check (every turn — lightweight)
    try:
        victory_events = await _check_victory_proximity(gs)
        events.extend(victory_events)
    except Exception:
        log.warning("Victory proximity check failed", exc_info=True)

    # Turn checks from prompts/checks/turn-checks.md - every turn, not every tenth. The
    # agent reads the file once; the MCP evaluates it against the live state on each turn,
    # so a rule with a deadline (the ram/tower cliff at CIVIC_CIVIL_ENGINEERING) cannot be
    # missed because nobody remembered it that turn.
    diary_rows = await _agent_diary_rows(gs)
    try:
        events.extend(
            await _check_turn_checks(
                gs,
                turn_after if turn_after is not None else turn_before,
                snap_after.units if snap_after else None,
                _latest_at_or_before(diary_rows, turn_after if turn_after is not None else turn_before),
            )
        )
    except Exception:
        log.debug("turn checks failed", exc_info=True)

    # The attack count belongs to the turn that just ended. Reset it *after* the checks have
    # read it, so a blocker turn earlier in the turn still sees the attacks made so far.
    if turn_after is not None:
        gs._attacks_this_turn = 0

    # Every 10 turns: full victory progress snapshot, and the window review.
    if turn_after is not None and turn_after % 10 == 0:
        try:
            vp = await gs.get_victory_progress()
            summary = nr.narrate_victory_progress(vp)
            events.append(
                lq.TurnEvent(
                    priority=3,
                    category="victory",
                    message=f"10-TURN VICTORY SNAPSHOT (T{turn_after}):\n{summary}",
                )
            )
        except Exception:
            log.debug("10-turn victory check failed", exc_info=True)

        # The window review reads the diary back - what the last 10 turns actually bought,
        # which prerequisite is still missing, and whether the stated rate reaches the
        # milestone. It has to be automatic: the failure mode it exists for (T30-T80 with
        # science flat, no wonder, no siege train) is invisible turn by turn.
        try:
            events.extend(
                await _check_ten_turn_review(
                    gs, turn_after, snap_after.units if snap_after else None, diary_rows
                )
            )
        except Exception:
            log.debug("10-turn review failed", exc_info=True)

    # Growth alerts from post-turn city state
    if snap_after:
        for cs in snap_after.cities.values():
            if cs.food_surplus < 0:
                events.append(
                    lq.TurnEvent(
                        priority=1,
                        category="city",
                        message=f"STARVING: {cs.name} ({cs.food_surplus:+.1f} food/t) — will lose population!",
                    )
                )
            elif cs.food_surplus == 0 and cs.turns_to_grow <= 0:
                events.append(
                    lq.TurnEvent(
                        priority=2,
                        category="city",
                        message=f"STAGNANT: {cs.name} (0 food surplus) — needs farm, granary, or trade route",
                    )
                )
            elif cs.turns_to_grow > 15:
                events.append(
                    lq.TurnEvent(
                        priority=3,
                        category="city",
                        message=f"SLOW GROWTH: {cs.name} ({cs.turns_to_grow}t to next pop, {cs.food_surplus:+.1f}/t)",
                    )
                )

    # Empire-wide warnings (scoreboard, idle trade, loyalty, military, gold)
    game_score = None
    try:
        warning_events, game_score = await _check_empire_warnings(gs, snap_after)
        events.extend(warning_events)
    except Exception:
        log.debug("Empire warnings failed", exc_info=True)

    # Save scumming detection
    try:
        scum_events, hard_stop = _check_save_scumming(gs)
        events.extend(scum_events)
        if hard_stop:
            gs._run_aborted = True
    except Exception:
        log.debug("Save scumming check failed", exc_info=True)

    events.sort(key=lambda e: e.priority)
    return gs._build_turn_report(
        turn_before,
        turn_after,
        events,
        notifications,
        stockpiles=snap_after.stockpiles if snap_after else None,
        score=game_score,
    )
