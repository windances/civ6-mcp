"""Play the branch forward until Nationalism is adopted, so Corps can be tested end to end.

The human chose this over deferring: Nationalism cannot be granted (the culture object has no
progress setter - see `.tools/probes/grant-civic.lua`), so it has to be played, and the path runs
Medieval Faires -> Humanism -> The Enlightenment -> Nationalism.

The loop is deliberately boring and cautious. It ends a turn, reads the blockers the adapter
reports, resolves the ones it knows by name, and **stops and prints** anything else rather than
guessing. It never touches strategy: research takes the cheapest tech, civics take the Nationalism
chain in order, a city with an empty queue gets its cheapest option, promotions/governors/policies
take the first choice the game offers, diplomacy answers POSITIVE, and incoming deals are declined.

    .venv\\Scripts\\python.exe -u .tools\\grind-to-nationalism.py --turns 60

Writes a one-line-per-iteration log to .tools/grind-log.txt; stdout is the same stream live.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from civ_mcp.connection import GameConnection  # noqa: E402
from civ_mcp.game_state import GameState  # noqa: E402

CIVIC_CHAIN = [
    "CIVIC_MEDIEVAL_FAIRES",
    "CIVIC_HUMANISM",
    # Not optional: The Enlightenment needs Humanism *and* Diplomatic Service, and Nationalism
    # needs The Enlightenment. A first-available fallback picked Naval Tradition at T145 because
    # The Enlightenment was not yet available - measurable only from the game's own locked list.
    "CIVIC_DIPLOMATIC_SERVICE",
    "CIVIC_THE_ENLIGHTENMENT",
    "CIVIC_NATIONALISM",
]
LOG = pathlib.Path(".tools/grind-log.txt")


def say(line: str) -> None:
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


async def pick_research(gs) -> str:
    status = await gs.get_tech_civics()
    options = list(status.available_techs or [])
    if not options:
        return "no tech options"
    options.sort(key=lambda t: (t.turns, t.cost))
    return await gs.set_research(options[0].tech_type)


async def pick_civic(gs) -> str:
    """Keep the civic on the Nationalism chain, switching if something else is progressing."""
    status = await gs.get_tech_civics()
    available = {c.civic_type: c for c in (status.available_civics or [])}
    for wanted in CIVIC_CHAIN:
        if wanted in available:
            option = available[wanted]
            if (status.current_civic or "") == option.name:
                return f"already on {option.name}"
            return str(await gs.set_civic(wanted))
    return "no chain civic available (already adopted, or blocked)"


async def fill_queues(gs) -> str:
    cities, _ = await gs.get_cities()
    done = []
    for city in cities:
        if city.currently_building not in ("nothing", "CORRUPTED_QUEUE"):
            continue
        options = [o for o in await gs.list_city_production(city.city_id) if not o.is_repair]
        if not options:
            continue
        options.sort(key=lambda o: o.cost)
        pick = options[0]
        done.append(f"{city.name}:{pick.item_name}")
        await gs.set_city_production(city.city_id, pick.category, pick.item_name)
    return ", ".join(done) or "queues already full"


async def promote_someone(gs) -> str:
    units = await gs.get_units()
    for u in units:
        if not getattr(u, "needs_promotion", False):
            continue
        status = await gs.get_unit_promotions(u.unit_id)
        promos = list(getattr(status, "promotions", None) or [])
        if not promos:
            continue
        promo = promos[0]
        name = getattr(promo, "promotion_type", None) or getattr(promo, "name", None) or str(promo)
        return f"{u.unit_type} {u.unit_id} -> {name}: " + str(await gs.promote_unit(u.unit_id, name))
    return "nobody needs a promotion"


async def handle(gs, text: str) -> str:
    """Resolve the named blockers in *text*; return 'ok', 'stop', or a description."""
    kinds = sorted(set(re.findall(r"ENDTURN_BLOCKING_[A-Z_]+", text or "")))
    actions = []

    if "diplomacy encounter pending" in text:
        for session in await gs.get_diplomacy_sessions():
            pid = getattr(session, "other_player_id", None)
            actions.append(f"diplomacy {pid}: " + str(await gs.diplomacy_respond(pid, "POSITIVE")))
    if "incoming trade deal pending" in text or "[deal]" in text or "Deal from" in text:
        deals = await gs.get_pending_deals()
        if not deals:
            actions.append("deal: none pending (message said otherwise)")
        for deal in deals:
            actions.append(f"deal {deal.other_player_id}: "
                           + str(await gs.respond_to_deal(deal.other_player_id, False)))
    if "ENDTURN_BLOCKING_RESEARCH" in kinds:
        actions.append("research: " + str(await pick_research(gs)))
    if "ENDTURN_BLOCKING_CIVIC" in kinds:
        actions.append("civic: " + str(await pick_civic(gs)))
    if "ENDTURN_BLOCKING_PRODUCTION" in kinds:
        actions.append("production: " + str(await fill_queues(gs)))
    if "ENDTURN_BLOCKING_UNITS" in kinds or "ENDTURN_BLOCKING_STACKED_UNITS" in kinds:
        actions.append("units: " + str(await gs.skip_remaining_units()))
    if "ENDTURN_BLOCKING_UNIT_PROMOTION" in kinds:
        actions.append("promotion: " + str(await promote_someone(gs)))
    if "ENDTURN_BLOCKING_CONSIDER_RAZE_CITY" in kinds:
        actions.append("capture: " + str(await gs.resolve_city_capture("keep")))
    if "ENDTURN_BLOCKING_CONSIDER_DISLOYAL_CITY" in kinds:
        actions.append("disloyal: " + str(await gs.resolve_city_capture("keep")))
    if actions:
        return " | ".join(actions)
    if kinds:
        return "STOP|" + ",".join(kinds)
    if "Cannot end turn" in (text or ""):
        return "STOP|hard blocker with no recognisable type"
    # No hard blocker: the adapter is telling us something it already handled or something to
    # read - a World Congress free-vote fallback registration (T151), an auto-resolved units
    # blocker, the turn-start briefing. Ending again is the right next move.
    return "retry: informational output, ending turn again"


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=60)
    ap.add_argument("--stall-limit", type=int, default=8,
                    help="stop after this many iterations with no turn advance")
    args = ap.parse_args()

    conn = GameConnection()
    try:
        await conn.connect()
    except Exception as exc:  # noqa: BLE001
        say(f"could not connect to FireTuner: {exc}")
        return 1
    gs = GameState(conn)
    stalled = 0
    advanced = 0
    try:
        for i in range(1, args.turns * 6 + 20):
          try:
            ov = await gs.get_game_overview()
            adopted = "?"
            try:
                lines = await conn.execute_read(
                    'local p = Players[Game.GetLocalPlayer()] '
                    'local row = GameInfo.Civics["CIVIC_NATIONALISM"] '
                    'print("NAT|" .. tostring(row and p:GetCulture():HasCivic(row.Index)))'
                )
                adopted = next((l.split("|")[-1] for l in lines if l.startswith("NAT|")), "?")
            except Exception:  # noqa: BLE001
                pass
            if adopted == "true":
                say(f"[{i}] NATIONALISM ADOPTED at T{ov.turn} - stopping.")
                break

            # The overview's research/civic fields read "None" even when both are progressing
            # (seen for eight turns running), so the authoritative GameCore list decides. The
            # civic is re-checked every turn: it has to stay on the Nationalism chain, and the
            # fallback that first-available picks are not on it.
            status = await gs.get_tech_civics()
            note = " | civic: " + str(await pick_civic(gs))
            status = await gs.get_tech_civics()
            if (status.current_research or "None") == "None":
                note += " | research: " + str(await pick_research(gs))
                status = await gs.get_tech_civics()

            # A full-screen UI the adapter cannot read left FireTuner closed and hung this loop at
            # ~T171 while it held the only connection (screen "unrecognised (10 text boxes)").
            # Check every few turns, and bound the end_turn call so a hang is reported rather than
            # waited on forever.
            if i % 5 == 1:
                from civ_mcp import game_launcher as gl

                # Only "the tuner is gone" stops this: an unrecognised *screen* is normal while a
                # diplomacy encounter or the world congress is on screen, and stopping for that
                # made the loop quit in the middle of a normal session (T173).
                screen_status = await asyncio.to_thread(gl.game_status)
                if "FireTuner   : not listening" in screen_status:
                    say("STOPPING: FireTuner is not listening - clear the screen on the machine "
                        "(or restart_and_load) and run this again; progress is kept.")
                    say("  " + "\n  ".join(screen_status.splitlines()[:6]))
                    break

            text = await asyncio.wait_for(gs.end_turn(), timeout=240)
            m = re.search(r"Turn (\d+) -> (\d+)", text or "")
            if m:
                advanced += 1
                stalled = 0
                say(f"[{i}] T{m.group(1)} -> T{m.group(2)} | tech={status.current_research} "
                    f"civic={status.current_civic}{note}")
                continue

            stalled += 1
            result = await handle(gs, text or "")
            first = (text or "").strip().splitlines()
            headline = first[0][:120] if first else "(no output)"
            say(f"[{i}] T{ov.turn} blocked ({advanced} turns so far): {headline} -> {result}")
            if result.startswith("STOP|"):
                say("STOPPING for a human decision:")
                say("  " + ("\n  ".join(first[:8]) if first else "(no output)"))
                break
            if stalled >= args.stall_limit:
                say(f"STOPPING: {stalled} iterations without the turn advancing.")
                break
          except Exception as exc:  # noqa: BLE001 - an autonomous loop must not die on one turn
            stalled += 1
            say(f"[{i}] ERROR {type(exc).__name__}: {str(exc)[:200]} (continuing)")
            if stalled >= args.stall_limit:
                say(f"STOPPING: {stalled} iterations without progress.")
                break
    finally:
        await conn.disconnect()
    say(f"done: {advanced} turn(s) advanced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
