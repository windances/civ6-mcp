# TEMP TASK 008 — destroy the missionaries

added:     2026-09-26 (human instruction: 消灭传教士)
expires:   turn 160 — the same horizon as 007. Retire it early once no hostile religious unit is left
           anywhere we can see, or as `008-destroy-missionaries-expired-T160.md` with a count of what
           was killed and what is still walking around.
done when: **no hostile religious unit stands in our territory or on a road the army uses** — a
           `get_map_area` sweep of our cities, the 阿斯特拉罕 approach and the roads between them shows
           `count == 0` of MISSIONARY / APOSTLE / INQUISITOR belonging to a civ we are at war with —
           and the tool's answer to the attack is recorded either way (see the probe below).
overrides: the march and the city queues: a unit adjacent to a hostile religious unit may spend its
           attack on it instead of moving, and 007's staging tolerates a one-turn delay for that. It
           does **not** authorize a declaration of war on anybody (007 owns that), and it does **not**
           authorize killing the religious units of a civ we are at peace with — Egypt is a declared
           friend, and a condemned missionary is a diplomatic incident.
scope:     hostile religious units only: Missionaries first, Apostles and Inquisitors if they are the
           ones in the way. No city attacks, no pillaging, no change to research or civics, no peace
           offer, and nothing done to our own religious units (we have none — religion is `NONE`).

## Why this is a file and not a turn-check rule

There is no metric for "a religious unit is standing there": `metric()` reaches our own diary row plus
the combat metrics, and those count **military** classes (`enemies_melee_within_2` and friends). A
Missionary is `FORMATION_CLASS_RELIGIOUS` with `Combat = 0`, so it is invisible to every rule — and a
religious unit parked on a one-tile lane is exactly the thing that cost this campaign two turns before
(a Russian Missionary at (57,32) and an Egyptian Scout at (58,32) closed the x=57 corridor at T101).
The instruction therefore lives here, and the checkable part (the `use-your-attacks` rule) already
exists once a legal attack exists.

## What the tool can and cannot do — measure this first

`unit_action(action="attack", ...)` resolves the target tile by taking the first **hostile** unit and
falling back to a non-combat one when no combat unit is on the tile
(`src/civ_mcp/lua/units.py:348-370`), so a Missionary *is* reachable by that path. But the same
builder refuses an attack on a civ we are at peace with:

    ERR:NOT_AT_WAR|Cannot attack <unit> — you are at peace with <civ>. Declare war first or target a
    different unit.                     (src/civ_mcp/lua/units.py:411)

The game's own verb for this is **Condemn Heretic**, which the MCP does not expose — there is no
`condemn` action anywhere in `src/`. So:

1. **Probe it, do not assume.** The first time a hostile religious unit is adjacent to one of our
   military units, issue the attack and copy the exact reply into the diary's `tooling` line:
   * `NOT_AT_WAR` → expected while at peace; the kill waits for 007's declaration, or for the tool to
     grow a `condemn` verb.
   * an engine refusal (ATTACK_BLOCKED / NO_ENEMY / a Lua error) → the MCP cannot condemn at all, say
     so plainly, and treat that as the reason this task cannot be finished.
   * a kill → the path works; record the unit, the tile and the turn.
2. **Russia first.** Once 007's declaration is sent, Russian religious units become legal targets
   under the same attack path, and this task rides along with the war.
3. **Do not touch Egypt's or a city-state's.** A friend's missionary is not a target under this file.

## The order of work

1. **Find them.** A religious unit shows up in `get_map_area` (units on the tile) and in `get_units`
   if it is ours, but **not** in the BATTLE ASSESSMENT counts — so the sweep is the map read around
   each city, the 阿斯特拉罕 approach and the corridor roads, once every few turns while this is in
   force. They walk; a clean sweep last turn says nothing about this turn.
2. **Kill the one in the way, not the one that is convenient.** Priority is a missionary that blocks a
   lane the army or a Builder needs, or that stands inside our territory; a missionary wandering in
   open ground far from the route can wait.
3. **Attack with an adjacent military unit**, from the tile that does not expose it (a missionary of a
   civ we are at war with may have an escort — check `get_map_area` radius 1 before spending the
   attack, and prefer a ranged unit at range 1-2, which takes no retaliation).
4. **Record it**: unit type, owner, tile, turn, and the exact tool reply — including a refusal. A
   refusal recorded is worth more than a kill unrecorded, because it is what tells the next session
   whether the tool can do this at all.
5. **Then back to 007.** This task never postpones the war: it is a lane-clearing chore that rides
   along with it, and its `expires` is 007's.

## What this task is not

Not a religious strategy: we have no religion (`religion: NONE`, 0 cities converted) and this task
does not ask for one — it is about the missionaries that are in the way, not about spreading or
defending a faith. It is not a licence to attack Egypt, a city-state, or a barbarian unit, and it is
not a reason to leave the siege train unscreened while a unit goes hunting.
