# TEMP TASK 020 - take Brussels: 战前分析, 攻城集结, then the general assault

added:     2026-09-27 (human instruction: 占领布鲁塞尔，进行战前分析，攻城集结后总攻)
expires:   turn 248 - sixteen turns from T232, where the match stands (`.civ6-mcp-data/heartbeat.json`
           reads `turn 232` and the newest diary entry is T232). The count is from the queue and not
           from the calendar: reconnaissance 1-2 turns (the city is at (69,29) but its four numbers have
           never been read at war), the march and staging 4-8 (the train stands around (72,33)-(74,34),
           and a siege piece cannot move and fire in the same turn), the walls and the pool 3-6 with the
           shooters that can actually bear, and one turn to hold what is taken. A hard stop: if it has
           not fallen by T248, retire this file as `020-take-brussels-expired-T248.md` with where the
           train stood, what the city read, and what blocked it.
done when: **Brussels is ours** - the tile at (69,29) reads `[CITY_CENTER] (owned by 中国)` with one of
           our units standing on it (`hold-what-you-take`), the city appears in `get_cities`, and
           `get_city_states` no longer lists 布鲁塞尔 as a city-state - its player id read as **19** at
           T220. The diary carries the ledger: the four numbers re-read at war and which of them came
           from a probe attack, the staging table with its overrides, the shots per turn and the tile
           each shot came from, and the cost paid. Retire it as `020-take-brussels-done-T<n>.md` the
           turn the city is ours.
overrides: **the directive's city-state rule, for this one city, on the human's instruction.** The
           doctrine (`prompts/strategies/china-conquest/directive.md:494-513`) says city-states are not
           conquest targets and may be attacked only for a stated reason; **the human has said otherwise
           for 布鲁塞尔, and that instruction is the reason of record** - the diary records it as such and
           invents no strategic justification, exactly as 016 did for 埃里温
           (`docs/task-history.md:107-113`). What it unlocks: war on **player 19 and nothing else** (not
           喀布尔, 格拉纳达 or 哈图沙, not the Netherlands' six unseen cities, not the camp at (48,35)),
           and the **siege train plus one melee capture unit lent to it**.
           **019 is displaced on one point and untouched on the rest**: 019's northern bearing exists to
           find the four unmet civilizations, and this file takes that bearing's objective instead - but
           019's two Rangers stay 019's instrument and are **not** diverted here. The T228-T229 plan to
           flip Brussels' suzerainty with 周达观's 3 envoys is **cancelled**, because he cannot activate
           on enemy territory (measured T231: `BLOCKED (tile is enemy territory but movement still
           blocked)`); his envoys go to 格拉纳达 instead, and **no further envoy is spent on Brussels**.
           **The T230 review's "no new unit and no new gold building" line stands**: the establishment
           already exists (siege 5/3, melee 4/2, ranged 5/4, cavalry 2/1), so this file authorizes **no
           new unit** - if the analysis finds a real gap it is reported, and filling it is
           `tactics/01`'s decision and not this file's. **It does not override**: the Dutch war (no peace
           is offered, `propose_peace` stays forbidden, and the manual says a city-state will not accept
           peace while its suzerain is at war with us - so this war has no exit but the capture),
           `one-garrison-per-city`, `use-your-attacks`, the eastern-shore defence against the Dutch navy,
           the science and Sewer line outside the cities the assault needs, or Chichen Itza and
           布鲁内列斯基's two charges.
scope:     Brussels, its ring, any unit the Netherlands levies out of it, and the train lent to it. Not
           the Netherlands' six unseen cities (they stay 019's question), not another city-state, not a
           barbarian camp, and not a second front.

## What is known, and what has never been read (T219-T232)

| fact | reading | source |
|---|---|---|
| the city | **city-state 布鲁塞尔 at (69,29)**, player **19** | T219 reconnaissance; T220 `assign_governor` refusal naming id 19 |
| its type and bonus | **Industrial**; suzerain bonus **+15% Production towards wonders in all our cities** | game's own files: `Gameplay/Data/Civilizations.xml:115` (`INDUSTRIAL`), `Text/en_US/Leaders_Text.xml:438-439` (`LOC_LEADER_TRAIT_BRUSSELS_DESCRIPTION`) |
| its suzerain | the **Netherlands**, the only civilization we are at war with | T228 diary ("Netherlands suzerain ... its bonus is wonder production") |
| our envoys there | **4** (2 at T220, 3 at T229, 4 at T232) - and the suzerain needs the most tokens with at least 3 | T232 snapshot; manual `INFLUENCE LEVELS` (`manual:1963-1965`) |
| are we at war with it | **yes, already** - a city-state "will automatically follow its Suzerain into war and peace, matching the diplomatic state of the Suzerain" | manual `manual:1969`; and measured T231: 周达观 was refused at its border as **enemy territory** |
| the four numbers | **never read** - no walls, pool, garrison or ring figure exists anywhere in the diary | - |
| the train | 5 Bombards, 5 Field Cannons, 3 Line Infantry, 1 Cavalry, 1 Cuirassier, 1 Spearman; the Bombards around (72,33)-(74,34), 塞纳 holds a Line Infantry | T224-T232 diary; **re-read positions and ids before ordering anything** |
| the sea | the Dutch navy has worked our eastern shore since T223 (five units damaged, three farms pillaged at T224), and 周达观 could not walk around Brussels' border | T223-T232 diary |
| 019's clock | its two Rangers land about **T239** | T231-T232 planning |

**Two things follow from the table, and both decide the plan.**

1. **No declaration step.** Brussels matches the Netherlands' war state, so it is already hostile and an
   attack needs no declaration and no waiting turn. Confirm it with one read rather than assuming it
   (`get_city_states` for its type and envoys, and the first attack's own reply): the diary's T231
   `enemy territory` refusal is the evidence, and a refusal that says `NOT_AT_WAR` would be the
   correction.
2. **There is no exit but the capture.** The manual: "a city-state will always accept a peace deal as
   long as the suzerain of the city-state is not at war with you" (`manual:1959`). The Netherlands is at
   war with us, so Brussels cannot be peaced out - and the directive forbids peace anyway. A half-done
   assault therefore leaves levied units on our border for the rest of the game.

## Gate 0 - reconnaissance (侦察), before any move

- **Read the coordinate this session.** A coordinate copied from an old diary has already been wrong
  once (`prompts/tasks/tmp/done/001-clear-the-camp-done-T84.md`), and (69,29) is a T219 reading.
- **Read the four numbers, and name the source of each**: walls / HP pool / garrison (the city tile's
  own unit list, not the ring) / ring. `get_diplomacy` lists civilizations and **not** city-states, so
  a city-state's figures have to come from the tile read and from **result lines**.
- **Probe-then-train on the walls.** 016's rule for this exact case: a city-state's walls are
  **unreadable until something hits them**, so the first melee attack is what produces the wall number
  - do not budget the siege from a guess.
- **GROUND gate: land or water?** Brussels is on the north coast and 周达观 could not walk to it. If
  the only approach is by sea, **the train does not go** until that lane is clear of the Dutch navy: an
  embarked siege unit is CS 10-ish and a passenger (T225: it cannot even make a ranged attack, and a
  blind `move` embarks with no warning - the destination tile's own yield line, `F:1 P:0 G:1`, is the
  only tell). Report a water-only approach as a blocker instead of drowning the train.
- **Expect a levy.** The suzerain can pay gold to take control of a city-state's units
  (`manual:1971-1973`), which is how 埃里温's Man-at-Arms came onto our ring. Levied units die when the
  city falls, so they are a cost to absorb, not a reason to delay.

## 战前分析 - the gates, once it is visible (tactics/07)

1. The four numbers above, each with the source that produced it.
2. Defenders by class and HP within two tiles, and the counter for each - **and remember that a Bombard
   cannot attack a unit at all** (`ERR:SIEGE_CANNOT_ATTACK_UNITS`): levied units are the Field Cannons'
   and the melee's work, the Bombards' is the city.
3. The turn count said out loud **from shots that have landed**, not from the plan.
4. Can we hold it? The city arrives with an empty queue (an end-turn blocker) and possibly poor loyalty
   next to a Dutch suzerainty; a governor or a garrison goes in the turn it falls
   (`hold-what-you-take`), and its queue is set the same turn.
5. **Write down what the capture deletes**: +15% wonder production for **both** sides, our 4 envoys
   there, and the Netherlands' suzerainty over it. That is the price the human's instruction has already
   accepted; record it so the ledger shows it was known.

## 攻城集结 - the staging, in this order

Run **`get_staging_plan(69,29)`** and write one row per unit - where it is now, its movement, the one
tile it goes to, the `get_pathing_estimate` cost, the arrival turn, its role, whether it can fire from
there - **before the first `unit_action`**. Calling the tool is not writing the table. The three staging
rules (never two units on one tile, name the corridor, fill the **last** firing tile first) are
`prompts/tactics/04-staging-out-of-range.md` step 3b, and 018 measured six ways this map overrides the
plan - all six still hold:

- a **siege unit posted at d1 is refused** (it fires from d2 and dies at d1, measured T163);
- **`arrive T+n` does not know our own units jam the corridor** - issue **one move per call** and re-read
  `get_units` between them (T159/T161 landed units 1-2 tiles short; T194 `BLOCKED` and
  `STOPPED_MID_PATH`);
- **a firing tile is a proposal until a shot from it succeeds**, and a refusal is not a verdict on the
  tile - re-test a refused tile on a later turn (T194);
- **a shooter that spends its movement cannot shoot** (`NO_MOVES|... Ranged attacks require movement`,
  T194) - check the terrain cost (`[mv:2]`, `[mv:3]`) before posting a 2-move siege unit;
- **entering a Zone of Control costs that turn's attack** (`ZOC|... cannot attack until next turn`);
- **a unit id is not durable across an upgrade** - re-read `get_units` after every `upgrade_unit`
  (T200: an order aimed at an upgraded unit was executed by a different one).

## 攻城执行 - the fire order

1. **Walls first if there are any**, pool second, and take the wall number from the first melee attack's
   own result line.
2. **Record each shot's `city hp:` from its result line - then read the city again a call later.** The
   immediate post-combat line is an estimate or a stale read even when the damage landed (T194, and the
   T216 capture itself), and the estimate header describes the matchup, not the legality (T223: a shot
   that could not reach printed `LIKELY KILL`).
3. **The melee attacks from d1 the turn the pool reaches 0** - and that attack takes the city and moves
   the unit in, so resolve it with `city_action` the same turn or the turn will not end. **One capture
   attack per tile per turn**: a second attack after the flip hits our own city (measured T216).
4. **Cut what heals**: a city heals roughly twenty points a turn with an uncut supply line (T195).
5. **Do not shoot the garrison inside the city** - it takes no damage there and the city keeps its
   bonus; it becomes a target when it steps out.

## Hold it, and report

Governor or garrison the turn it falls, set its empty queue the same turn, and report: the four numbers
with their sources, the staging table with its overrides, the shots per turn and the tile each came
from, the capture resolution and the tile the capturing unit stood on, the cost in units and turns, and
**what the capture deleted** (the +15% wonder production, our 4 envoys, the Dutch suzerainty). If it
expires, say where the train stood, what the city read, and what blocked it - a water-only approach, the
Dutch navy, or the walls.

## Why this is a file and not a turn-check rule

Every mechanical half already has a rule or a tactic: `siege-train`, `screen-the-siege`,
`mass-on-contact`, `take-the-city`, `hold-what-you-take`, `use-your-attacks`, `finish-the-wounded`,
`cut-the-supply`, and `tactics/07` for the analysis. What no metric carries is **that this city is an
objective at all** - the standing doctrine says it is not, the human has said it is, and that reversal
has to travel to the turn loop as a file with the human's instruction written in it as the reason of
record.

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 020 --done --turn 224 --no-commit --note "Task 020 was retired as done: 布鲁塞尔 (69,29) reads [CITY_CENTER] owned by 中国 with our Cuirassier standing on it, it is in get_cities (pop 7, id 1310739) and it is off get_city_states; the assault ledger is the rolled-back run's (wall probe walls 200/200 at T235, fire from (68,31),(69,31),(70,31),(71,30) plus a Line Infantry attack from (69,28) across T236-T237)."
     at: 2026-09-28T20:36:02+08:00
     status: done at T224
     chinese backup: none
-->
