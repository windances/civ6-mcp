Attempt **A8** of the military-production experiment (`docs/experiments/README.md`, section 3). A7 is
`007-attempt-A7.md` and the cross-attempt report is `RETRO-2026-09-29.md`; the design note this file is
built from is `drafts/A8-A9-city-count.md`, and A9 is registered but **not published** - it waits on this
attempt's result.

**The one variable: three cities, settled first, and the third one is an economy city.** The programme has
held the city count fixed at two in every attempt - no second Settler was ever ordered, and the three
third cities in the record were all **captured**. A8 adds the second Settler and gives the third city a
market queue instead of an army queue. Nothing else changes.

## Start: the shared start, and the one trap that has already cost this programme a session

0. `get_game_status`. **This attempt is measured from the experiment's shared start**:
   `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`. Playing A8 on another position makes its numbers
   incomparable with A1-A7, which is the one thing the experiment cannot afford - so **the first thing to
   get right is the load, and it is not one call.**

   **The trap, measured in the A5 handover (2026-09-30)**: `list_saves()` and `load_save(index)` are
   **two different lists**. `list_saves()` returns the **filesystem** scan, capped at the newest 25 - and
   the shared start is old by definition, so as soon as an attempt has played a session it falls off that
   list entirely. `load_save(index)` reads the **game's own Lua list**, whose order is not the scan's: in
   the measured case the scan showed the save at index 1 and the Lua list had it at **index 12**. Loading
   by the scan's index loads the wrong save or nothing.

   **The recipe that worked, in order**: if the save is missing from `list_saves()`, touch its mtime so the
   scan sees it again (its contents are unchanged - that was verified by hash); then drive the Lua list
   (`_list_saves_lua`) so the cache `load_save` reads is populated; then `load_save` by **that** index.
   The MCP-side half of this is now fixed (`load_save` populates the cache itself instead of answering
   `No save list cached`), so if you do see `No save list cached` say so in the diary - it means the fix
   is not in the running server.

   **Then verify the load before playing anything**: `get_game_overview` must read **turn 1**. If it reads
   any other turn, **stop and say so** - a whole attempt played on the wrong position is worse than no
   attempt, and it is not recoverable by arithmetic afterwards.

   **A8 may be resumed, and a resume is not a restart.** This attempt needs roughly sixty turns before its
   number exists and a hundred and ten to reach the horizon, which is longer than one session's budget has
   managed so far in this programme. If you are handed a game that is **already on this key at a turn past
   1**, the work below decides what to do - and **reloading the shared start over a run of A8's own, in
   progress, would discard it, which is the one mistake here that cannot be repaired**:

   1. **read `get_diary` first, then `get_cities`**, and say in the diary what you see;
   2. **is the position A8's own run in progress?** The diary's recent rows are this attempt's - the pin
      visible in the early turns, the second Settler ordered, the third city or its market under way.
      Then **continue from where it stands**, say which turn you picked it up on and what had already been
      spent, and do not load anything;
   3. **is the position A7's continuation?** It stands at T69 or later with **three cities, one of them
      耶路撒冷 kept at T60**, and the recent diary rows describe holding a baseline to T110. **That is the
      position this attempt must replace, and replacing it is expected**: A7's record is closed - its
      window ended at T110, task 039 is retired to `done/`, and its snapshot is
      `docs/experiments/A7-T110.json` - so **load the shared start and play A8 from T1**, saying in the
      diary which position you loaded over. **Do not play A8 on A7's position, and do not treat it as a
      blocker**: it is the state the handoff deliberately leaves behind, because the tuner has to be free
      before the shared start can be loaded;
   4. **is the game already on the shared start?** One city, turn 1, nothing in the log but the pre-game.
      **Then A8 starts here and nothing has to be loaded** - say so in the diary and begin with the pinned
      opening. **Look before you accept it, though**: if the position shows signs of having been played -
      units moved off the capital, a research or a production order the pin below does not ask for, a
      second city, or a leader or civ that is not China - then **reload
      `evals/saves/ATTEMPT-A1-T1-settled.Civ6Save`** and say in the diary what you replaced and why. A
      load can land and still leave a position altered by whatever tried to confirm it, so turn 1 alone is
      not sufficient evidence that the position is the one this file measures from;
   5. **is there no game loaded at all** - a main menu, a leader screen, `not_running` - **while A8 is
      already in progress?** Its own diary rows exist, its task is in force, and a `HANG:` line named the
      autosave the stall wrote. Then **the attempt crashed or was restarted mid-run, and the recovery is
      to load that autosave**: `load_game_save` by the `0_MCP_NNNN` name the hang printed, say in the
      diary which save you loaded and which turn it holds, and **continue from there** - a resumed turn
      inherits the previous session's plan. **Verify before playing**: the loaded position must be A8's
      (its cities, its pin, its diary rows). If it is A7's, or any other attempt's, **stop and report**
      rather than play on it;
   6. **nothing of A8's exists and no position can be identified** - a different match key, a menu with no
      attempt behind it - is the one case to **stop and report**: do not guess which position the task
      meant. **This is the narrow case, not the default**: a menu is not by itself a reason to stop when
      there is an attempt to resume.
1. Then `get_diary` and one `scripts\orient.py` read. On a fresh T1 position the diary's early rows belong
   to whichever attempt wrote them last, so say which turns you can actually read and treat the rest as
   unavailable rather than as A8's own history.

## The opening is pinned, and the pin's fifth slot is the variable

The first four orders are **unchanged from A3-A7**, so the opening stays comparable:

| order | item | why |
|---|---|---|
| 1 | `UNIT_SCOUT` | the pin's recon slot |
| 2 | `UNIT_SLINGER` | the pin |
| 3 | `UNIT_SETTLER` | the pin - **city #2**, founded about T21 (A7 measured T21 from a T6 order) |
| 4 | `UNIT_BUILDER` | the pin |
| 5 | **`UNIT_SETTLER`** | **the variable.** `UNIT_SETTLER` is 80 base with `COST_PROGRESSION_PREVIOUS_COPIES` +30 per copy, so copy #2 is 110 base / **74 Quick** - about one Catapult's production. Order it the turn the Builder completes, and say in the diary the turn it is ordered and the turn the city is founded |

## The third city: choose the nearest good site, because distance is the cost

**The site is chosen on the turn you order the second Settler, from your own `get_global_settle_advisor`
read. The rule: the highest-scoring legal site, preferring the nearest one within about 10 score of the
best.** Record the tile, the score, whether it has fresh water, and its hex distance from 西安. It is a rule
rather than a tile because of the arithmetic below - and because a tile named by a different position is not
a decision.

**What the programme knows about the land, and the blind spot in it.** The only read taken from a three-city
position is T69 of the A7 continuation: its top ten were all in one block **(x 39-42, y 25-29)**, #1 at
**(40,26), score 217, fresh water, defense 4**, with `STONE, HORSES, COPPER, BANANAS, MAIZE, WHEAT, FURS` in
radius, and nine of the ten with fresh water. **That read's blind spot is A8's opportunity**: it was taken
with **three** cities standing (西安, 成都 and the kept 耶路撒冷), and the advisor excludes everything within
3 tiles of a city - so it is strictly *more* restrictive than the position A8 chooses from, which has
**two**. A site four to six tiles from 西安 can be legal at T21 and simply never have appeared in a
three-city top ten. **Do not assume the far cluster is the only option: read, and see.**

**Why distance matters more than score here.** (40,26) is about **20 tiles from 西安** (about 10 from
耶路撒冷, which is itself 10 from the capital), and a two-move Settler over that ground walks **fifteen to
twenty turns**. Chain the measured pieces - the pinned Settler ordered T6 founded a city at T21; copy #2 is
110 base / **74 Quick**; and A7's Chengdu took **24 turns** from founding to its first siege-relevant order,
at **1.5x the capital's turn cost** - and a far site puts the third city at about **T48**, its Market at
about **T70**, and its first real contribution after that. **A satellite founded about T30 has a Market by
T50; a colony founded about T48 does not.** The claim below is written to survive both, and says which one
it is reading.

**And the city brings two things the core does not have**: **HORSES**, a strategic resource no A3-A7 city
held (the programme's `cavalry` row was filled by Heavy Chariots, which need none), and a second luxury
cluster (`FURS`, `DYES`) against an empire at `Amenities 5/2/2`.

### Confirm the site with your own read, because the pre-flight read was taken on an explored map

**A target read at T69 is not a guarantee at T21, and the difference is fog.** The read it comes from was
taken when the west was already open; A8 orders its second Settler around **T21**, when much of that corridor
may still be dark. Three things can therefore differ, and each has a stated answer:

- **run `get_global_settle_advisor` yourself on the turn you are about to order the Settler** - it is the
  same tool, and it is cheap. Apply the rule at the top of this section (best score, nearest within about
  10 of it), **settle the site it names, and record it in the diary with the tile, the score, the water and
  the distance from 西安, beside (40,26) and why one beat the other.** The variable is *the number of
  settled cities and the third one's economy queue*, not the tile - so a different site does not weaken the
  attempt, but **an unrecorded one would**, and a site chosen from a read taken with three cities standing
  is exactly the choice this section exists to avoid making blind;
- **send the recon unit down the corridor before the Settler commits.** Gate 0 of `tactics/07` applies to a
  settle site as much as to a city: you cannot settle what you have not seen, and a Settler that walks
  fifteen to twenty turns into fog and finds the tile taken has spent the variable's whole budget. Say in
  the diary which unit revealed which tiles and on what turn;
- **watch for foreign borders, a camp, and the `PrereqPopulation="2"` gate on the Settler itself** - a
  Settler costs `PopulationCost="1"`, so the city that builds it must be at pop 2 or more and loses one;
  `UNIT_SETTLER` is also `COST_PROGRESSION_PREVIOUS_COPIES`, so the second one is more expensive than the
  first (110 base against 80). Say what it actually cost.

**If the site turns out to be unusable**, the honest outcome is a third city somewhere legal plus the
record of why the intended one failed - not a second city and a quiet redefinition of the attempt.

**The third city's first four orders** (name them in the diary and hold to them): `BUILDING_MONUMENT` ->
`DISTRICT_COMMERCIAL_HUB` (check `get_district_advisor` for the river tile) -> `BUILDING_MARKET` ->
`UNIT_BUILDER`, with the Builder going to the Horses first.

## The claim, and it is about gold

**Hypothesis (falsifiable by numbers): a third city that is settled pays for itself where a third city that
is captured does not - and on the way it funds the second gun.**

**Say which unit is bought and which is built, on every purchase, because A6 and A8 buy different ones.**
A6 bought the **first** siege unit (T46, 320g); **A8 produces the first in the war city and buys the
second**, so the two attempts' purchase columns are not the same act - the compare block's own
`siege_order` caveat says exactly this about A6, and A8 has to state its side of it.

- **the two turns are set by the founding, not by the calendar.** Let **`F`** be the turn the third city is
  founded. The **purchase deadline** is **`max(T58, F+25)`**, and the **gold-floor turn** is **T50 if
  `F <= 28`**, otherwise **the ten-turn row at or after `F+22`**. **Name `F` and both turns in the diary on
  the turn the city is founded** - a claim whose window moves has to fix its window when it moves, not at
  review time, or every reading afterwards is a choice;
- the number: the **second** siege unit is **in hand by the purchase deadline, bought and not built** - A6
  bought its *first* at T46 for **320g** out of a 396g treasury (`PURCHASED|UNIT_CATAPULT|cost=320g`), and
  the programme's arithmetic said **two** were impossible before about T70 on the path it was computed from,
  which is the claim the third city's gold is supposed to break;
- and the floor: `gold_per_turn` at the **gold-floor turn** is **above A7's value at that same turn** - the
  merged A7 report reads **8.1 at T50, 4.1 at T60, 2.1 at T70 and 24.4 at T80**
  (`--game china_911679432 --run divine-amber-outpost-82,stormborn-azure-palisade-94`). The directive's own
  floor is **+10**, and across the programme only **A4** ever stood above it (`gpt_T40 13.9` against A7's
  6.1 and A6's 5.4), and A4's was bought with Pingala's science rather than a market. **This is the clause
  the third city's market is supposed to move - and be careful with it: A7's own curve reaches 24.4 by T80
  with no market at all, so a late high reading proves nothing;**
- **and the second number, which is the one that discriminates at the horizon**: at **T110**, A8's empire
  **`science`, `pop` and `gold_per_turn` each exceed A7's at T110.** Both runs end holding **three cities**,
  and the difference between them is **how the third was obtained**: A8 pays a Settler, a colony's buildings
  and a fifteen-to-twenty-turn walk; A7 paid a war. If a settled city compounds where a captured one does
  not, this is where it shows, and if it does not, this is where it shows too;
- and a **prediction to check, not a bar to clear**: **`gpt_T40` will be at or below A7's 6.1.** A third
  city founded about T30 has `BUILDING_MONUMENT` -> `DISTRICT_COMMERCIAL_HUB` -> `BUILDING_MARKET` to build
  at a young city's production, so at T40 it is a garrison and a Builder's maintenance with **no market
  yet** - it is *supposed* to cost gold before it pays. If T40 reads above A7's 6.1, say what paid for it,
  because the market cannot have;
- **the confound is already in the record, and it is A7's own curve**: the continuation's merged report
  reads `gpt` **8.1 at T50, 4.1 at T60, 2.1 at T70, 24.4 at T80 and 49.0 at T90** - so **A7 crosses the
  directive's +10 on its own, with no market at all**, on the strength of its Campus, twelve improved tiles
  and six districts. A8 therefore cannot claim the market merely because its `gpt` ends high. **Judge the
  floor at the gold-floor turn and compare it to A7's value at that same turn**, and if A8 is only ahead
  later, **say the market did not do it** - the T110 comparison above is the one that still has to hold;
- **falsified** if the second siege unit is not in hand by the purchase deadline, if it was built rather
  than bought, if `gpt` at the gold-floor turn is not above A7's value at that turn, or if any of A8's
  three T110 figures is at or below A7's. **Nothing here depends on the site being near**: if the third
  city is a far colony, the deadlines move out with it and the T110 comparison carries the claim.

If the treasury cannot fund a second purchase, **that is the answer**: say so, name the turn the gold
actually reached 320, and do not sell the plan by building it quietly instead - the attempt exists to
measure the funding arm, and an unaffordable purchase is a measurement, not a failure.

## Held exactly: everything else

- the corrected `tactics/01` establishment, `tactics/04` staging, `tactics/05` screening, `tactics/06`
  fire, and `tactics/08`'s **one war city** - A8 does **not** widen it the way A7 did; the third city's
  queue is economy, so the empire has its war city and its compounding cities;
- the standing directive `prompts/strategies/china-conquest/directive.md`; **never call `propose_peace`**
  and refuse every offer;
- **if the empire changes shape** - a new war, another city taken, a district or unit line the doctrine
  does not already ask for - record it in the diary that turn as a divergence from this file's posture. It
  is not forbidden; it has to be named, because A7 and A9 are compared against this run.

## The wonder obligation is deferred, on purpose, and this is the override

`dynasty-cycle-wonder` (`prompts/checks/turn-checks.md`) is live from T25 and **will print
`CHECK FAILED [dynasty-cycle-wonder]` from that turn on**: the empire holds zero wonders, which the rule
reads as half of China's civilisation ability forfeited. The directive's China section says a wonder is a
*research building* for China, and it is right.

**Accept the rule and build no wonder in this attempt.** A8's variable is the third city's **market**, and
the same city is where a wonder would go; building one here would make the attempt two variables and would
answer neither question. Say so in the diary **the first turn the rule fires**, in one line, and after that
mention it only when it changes something - this is `AGENTS.md`'s rule that a failing check is fixed or
accepted out loud. **The wonder is a real question and it is owed its own attempt**; it is not being
answered by silence here.

## The measurement

The experiment reads the diary's **per-10-turn economy rows**. Keep the five reflection fields every turn
and write the rows for **T10, T20, T30, T40, T50, T60, T70, T80, T90, T100 and T110** - the comparison
needs the same rows A7's continuation writes. What matters at T110, in numbers: `cities` (3 by design),
`pop`, `science`, `gold_per_turn`, `districts`, `improvements`, **the founding turn `F` and the two
deadlines derived from it**, the turn the second siege unit was bought, and the total gold spent on
purchases.

## End

The attempt ends the turn **turn 110 is reached**, because the claim's last number - A8's `science`, `pop`
and `gold_per_turn` against A7's at the same turn - cannot be read before then. The purchase is recorded
whenever it happens; it is not a reason to stop. On the final turn report:

- the purchase (the item, the price, the treasury before it, the turn) or that no second purchase happened
  and why, against the purchase deadline;
- `gpt` at the gold-floor turn beside A7's value at that turn, and the T110 rows beside A7's field by field
  - that pair is the comparison the two runs exist for;
- the third city: `F`, the tile and its score and distance, its first four orders, and what it had actually
  produced by T110;
- whether the empire's shape changed anywhere else, with the diary turn;
- whether any wonder was built (the expected answer is none, accepted).

Then retire this task with `--done` or `--expired` - **`--expired` if the window closed without the
purchase** - and hand back to the orchestrator.
