# China's kit, and whether the five attempts played it

**This is an audit, not an attempt.** No new game was started and no attempt variable was run; the
question it answers is whether the A3-A7 military-production programme took China's four unique
advantages into account. It is written from the eight session logs under `.civ6-mcp-data/`, the
install's own gameplay files, `prompts/strategies/china-conquest/directive.md` and
`prompts/checks/turn-checks.md`, and it is the source for section 10 of `RETRO-2026-09-29.md`.

**The short answer: the kit was written into the directive in detail, and it was then removed from the
place that enforces it - so in practice no, it was not played.** Across eight sessions and roughly 340
turns the programme ordered **zero** wonders, built **zero** Great Wall segments, never researched the
technology that unlocks its unique unit, and never used its leader ability. The reason is not that the
doctrine was silent: it is that the one rule that would have nagged about it had already retired itself
for a *different match*, and a retirement trace carries no match key.

## 1. The kit, in the install's own numbers

| part | the install's own line | what it does | what it costs |
|---|---|---|---|
| **Dynastic Cycle** (civilisation ability) | `Base/Assets/Gameplay/Data/Civilizations.xml:2297-2311` attaches `TRAIT_CIVIC_BOOST`, `TRAIT_TECHNOLOGY_BOOST`, `TRAIT_CIVIC_BOOST_WONDER_ERA`, `TRAIT_TECHNOLOGY_BOOST_WONDER_ERA`; the ruleset's own text is `Expansion2_Civilizations.xml:73` -> `<Text>[ICON_TechBoosted] Eurekas and [ICON_CivicBoosted] Inspirations provide 50% of civics and technologies instead of 40%. When completing a wonder receive a random [ICON_TechBoosted] Eureka and [ICON_CivicBoosted] Inspiration from the era of the wonder, if available.</Text>` | two clauses: **+10 points on every Eureka and Inspiration**, and **a wonder is a research building** - finishing one pays a random Eureka *and* a random Inspiration of that wonder's era | clause 1 is free and constant; clause 2 costs one wonder in one city |
| **Great Wall** (unique improvement) | `Base/Assets/Gameplay/Data/Improvements.xml:56` - `PrereqTech="TECH_MASONRY" ... BuildInLine="true" BuildOnFrontier="true" DefenseModifier="4" GrantFortification="2"`, plus `GreatWall_Gold` / `GreatWall_Culture` yields (`:67-68`) | the only improvement in the game that adds **Defence** (+4) and **Fortification** (+2), on border tiles, in a line | **Builder charges, not city production** - it competes with nothing in a build queue |
| **Crouching Tiger** (unique unit) | `Base/Assets/Gameplay/Data/Units.xml:799` - `Cost="140" Maintenance="3" Combat="30" RangedCombat="50" Range="1" ... PrereqTech="TECH_MACHINERY"` | RangedCombat **50** against the Crossbowman's **40**, for **140** hammers against 180 (both at `TECH_MACHINERY`, `Units.xml`), and it upgrades into the Field Cannon - but **Range 1**, so it must stand adjacent, where the target city's own 2-range strike reaches it (measured at **43 damage** in this programme) | 140 hammers, and one of the four `ranged` slots in the establishment |
| **Thirty-Six Stratagems** (Qin (Unifier) leader ability) | `DLC/RulersOfChina/Data/RulersOfChina_Leaders.xml:16,19,134,489`; the text is `<Text>Melee units receive the Convert Barbarians action. This action converts Barbarian units into your units, but it removes the melee unit.</Text>` | swaps a melee unit for an adjacent barbarian - a **unit-tier** lever, not a production one | one melee unit, and a barbarian standing next to it |

Two nearby facts the programme also never used, both from `RulersOfChina_Leaders.xml`:
**Terracotta Army is Qin (Unifier)'s favoured wonder** (`:103`), and **Masonry is his favoured
technology** (`:121`) - the same technology the Great Wall is gated on. Terracotta Army itself
(`Base/Assets/Gameplay/Data/Buildings.xml:164`: `Cost="400"`, `PrereqTech="TECH_CONSTRUCTION"`,
`IsWonder="true"`, `AdjacentDistrict="DISTRICT_ENCAMPMENT"`, flat Grassland or Plains, on an Encampment
with a Barracks or Stable) reads `<Text>All current units gain a promotion level.</Text>` - a free
promotion for the whole army, which is the one kit-adjacent item that acts directly on military
quality.

## 2. What each part actually did, from the eight session logs

Every count below is a raw `str.count` over the eight A3-A7 logs, `log_china_911679432_*.jsonl`,
reproduced by `.tmp/china-kit-counts.py`:

| measurement | total over the 8 sessions | reading |
|---|---|---|
| `wonders built 0` lines in the 10-turn review | **29** (A3.1 x1, A3.2 x4, A3.3 x1, A4 x6, A5 x6, A6 x6, A7 x5) | the loop printed the forfeit at **every** window, and the number was never anything but zero |
| world wonders ever ordered (`set_city_production` / `purchase_item`) | **0** | Dynastic Cycle's second clause paid nothing, in any attempt |
| `CROUCHING_TIGER` anywhere in any log | **0** | the unique unit was never built, and never named |
| `IMPROVEMENT_GREAT_WALL` anywhere in any log | **0** | the unique improvement was never built |
| `Great Wall` (the readable name) anywhere | **8**, all inside `get_tech_civics`' own unlock line | it appeared only as something Masonry *would* unlock: `Masonry (TECH_MASONRY) [ANCIENT] -> Battering Ram, Ancient Walls, Pyramids, Great Wall, Nubian Pyramid` |
| `TERRACOTTA` anywhere in any log | **0** | Qin's favoured wonder was never considered |
| `dynasty-cycle-wonder` (the check id) anywhere | **0** | **the rule never fired once** - see section 3 |

**And the two prerequisites were never met, which is the harder fact.** Section-aware parsing of every
`get_tech_civics` row (`.tmp/china-kit-audit3.py`) shows:

- **`TECH_MACHINERY` was never completed in any attempt.** It sat `locked` (needs Iron Working and
  Engineering) at every read through T43, and the closest any attempt came was A3, which *ordered* it at
  **T69** - two turns before that session's T72 end, with the T70 read still listing it as `available`.
  **The Crouching Tiger was never buildable**, so "never built" is not a decision the programme made.
- **`TECH_MASONRY` was begun late in every attempt** - T43 (A3.2), **T34 (A4)**, T67 (A5), T50 (A6),
  T66 (A7); in A3's own sessions it landed between T68 and T70. A4 therefore held the Great Wall's gate
  from roughly **T36 for thirty turns** and built no segment, while `directive.md:22-24` says in as many
  words that Wall segments cost no city production and that surplus Builder charges should go into them
  rather than expire.
- **`TECH_CONSTRUCTION`** (Terracotta Army's gate) was reached at **T66** (A3.3) and **T71** (A5) - the
  last turns of the two longest sessions - and nowhere else.
- **The leader ability never surfaced either.** No log contains a `Convert` action, a convertible-barbarian
  report, or a `CONVERT` gate answer; the only `convert` hits in the corpus are the religion block's
  `0 cities converted`.

## 3. Why: the obligation was deleted from the loop by another match

`directive.md` is not the gap. Its first line is *"Play the two abilities this leader actually has, not a
generic domination plan"*, and lines 4-56 name all four parts, with the 50%-not-60% correction written
out, the sentence **"For China a wonder is therefore a *research building*"**, the instruction to
**"build cheap Ancient and Classical wonders deliberately, for the boosts, even when their own effects
are marginal"**, the Wall's zero-production cost, the Tiger's Range-1 pairing rule, and the
human-assisted conversion.

The gap is one layer down, and it is mechanical:

1. A `once: true` goal named **`dynasty-cycle-wonder`** existed to enforce it - `when: turn() >= 60`,
   `require: metric(wonders) >= 1`, message *"No wonder built. For China a wonder is a research building
   ... Zero wonders forfeits the civilisation ability for the whole game."* Its block is preserved in
   `prompts/checks/archive/turn-checks-20260926-012524.md`.
2. In the file it was **gone**, replaced by
   `<!-- achieved T99: dynasty-cycle-wonder (original in archive/turn-checks-20260926-012524.md) -->`.
3. The turn that achieved it belongs to a **different match**. The persisted retirement state,
   `.civ6-mcp-data/turn-checks-state.json`, is keyed by match:
   `{"china_-1894041591": {"ram-tower-before-civil-engineering": 99, "dynasty-cycle-wonder": 99}}`.
   The experiment replays `china_911679432` - a T1 branch of the same save, and **not** that key.
4. **A retirement trace carries no match key, and the file is shared by every match.** So one match's
   achievement deleted the rule for all of them, and nothing on the file could tell that the retirement
   did not apply. The rule appears in **zero** of the eight logs.
5. The repo had already measured this exact consequence three days earlier.
   `scripts/rollback-to-turn.py:139-144` says of a T132 -> T59 rollback: *"Both goals were absent from
   the rule file for the whole replay, which silently dropped the directive's only hard deadline (the
   ram/tower window that closes at `CIVIC_CIVIL_ENGINEERING`) and its wonder goal (zero wonders forfeits
   Dynastic Cycle)."* The A3-A7 attempts started by loading a T1 save through the MCP's `load_save` -
   not through `scripts/rollback-to-turn.py` - so neither `restore_achieved_goals` nor
   `unretire_goals_after` ever ran, and the `achieved T99` line stood.
6. **The test suite could not catch it, because its fixture hides it.** `tests/conftest.py:64-66` builds
   every test's check file with `restore_achieved(...)`, deliberately, so that tests do not depend on
   which goals this playthrough has retired. The consequence is that
   `tests/test_turn_check_hook.py:110-118` - *"T60 of the live game: no ram, no siege, no wonder - the
   standing reminders must fire"* - asserts `dynasty-cycle-wonder` fires **against a file the live game
   never had**. Green suite, dead rule.

The instrumentation was not blind either: `end_turn.py:726` already lists `CROUCHING_TIGER` in the
`ranged` row the establishment counts, and `end_turn.py:875-879` prints the Dynastic Cycle line every
ten turns - *"wonders built 0 (for China a wonder is a research building; zero forfeits the ability)"* -
29 times, with no failure semantics attached. So the missing piece was never measurement. It was a rule
that had been deleted by a match that no longer existed.

## 4. The honest half: two of the four forfeits were defensible

A kit audit that only counts misses would misrepresent the programme, so the trade-offs the attempts
never wrote down are written down here instead.

**The wonder clause probably would not have bought the assault.** Where both numbers exist, the research
gate opened well before the army was ready: Engineering was owned at **T43** (A3, A4, A5), **T46** (A6)
and **T45** (A7), while the establishment completed at **T53, T54, T57, T54 and T54** - a gap of **8 to
14 turns**. The binding constraint in this programme was production time, not research, so a free Eureka
and Inspiration from a wonder could not have pulled the first keep earlier on its own. Its value is in
the *later* technologies and in compounding, which a 60-75 turn window does not reach. That is an
argument for the programme's research path, and it should have been written down as one - not left as an
unexamined omission.

**Terracotta Army would plausibly have made the real failure worse.** The programme's ending problem was
not unit quality but **concentration**: A6 ended with `SIEGE FIRE: 1/2` and 耶路撒冷 at 200/200, and A7
with `SIEGE FIRE: 1/3`. `Tactics/06` exists because the siege pieces were not in position. Terracotta
Army costs **400** hammers - **3.3 Catapults** at 120 each - and buys one promotion level on the units
that already exist. Trading 3.3 siege pieces for a promotion on eleven units attacks precisely the
wrong side of a concentration problem. **The right conclusion is still "do not build it inside a
60-turn window"; the defect is that no attempt reached that conclusion or recorded it.**

**What was unambiguously free and still skipped is the Great Wall.** It is the only item in the kit that
costs no city production at all. In A4 the gate (`TECH_MASONRY`) was researched from **T34**, and the
attempt ended at T66 with zero segments built - and A5 spent two Builder charges on forest chops in the
same window. The Wall is not army production; it is defence bought with charges that were being spent on
something else, on the frontier of cities that the programme's own records show were left at
`walls: none`.

## 5. What this does to the programme's claims

- **The intra-programme comparisons hold.** China's kit is constant across A3-A7 - one save, one civ, one
  leader - so the differential findings are untouched: A7's second war city is worth about three turns
  and not half, A6's purchase turned out free, A5's chops did not buy the five-turn advance. Nothing in
  sections 1b, 6, 7, 8 or 9 of the retro needs revising.
- **The absolute turn numbers are China's, with clause 1 switched on.** Every Eureka the programme took
  was worth 50% instead of 40%. The gate turns (`T43`/`T45`/`T46`) are therefore **earlier than a generic
  civilisation's would be**, and the report must not be read as a generic-civ timeline; clause 1 is small
  and diffuse but it points the same way as the whole research path.
- **The programme's headline claim needs a qualifier.** "The optimal military production strategy" as
  measured is a statement about **this civilisation with its unique advantages switched off** - a
  generic-civ production result wearing a China label. It is a real result; it is not a claim about
  playing China.
- **And the choice of China was never tested.** The one China-specific question the design could have
  asked - is a wonder worth more than three Catapults under Dynastic Cycle? - was never asked, in a
  programme whose whole purpose was to tune a military production optimum against a fixed doctrine.

## 6. Where the corrections went

| correction | sink | state |
|---|---|---|
| `dynasty-cycle-wonder` restored to `prompts/checks/turn-checks.md`, with the gate moved 60 -> 25 and the boost figure corrected 60% -> 50% to match `Expansion2_Civilizations.xml:73` | **L2, a check rule** | **LANDED 2026-09-30**, with two new tests in `tests/test_turn_checks.py`: every retirement trace must still resolve to its archived block, and the China wonder obligation must be live or recoverable |
| a retirement trace must carry the match key it retired for, so one match's achievement cannot delete a rule for another | **L1, code + test** | staged in section 5 of the retro, with the measured case above; deliberately not landed, because it changes the format `scripts/rollback-to-turn.py` and `turn_checks.restore_achieved` both parse, and no live game can verify it in this session |
| the China kit needs a *decision* with a turn in it, not only a description - the wonder slot belongs to a compounding city (`tactics/08`), the Wall's charges to the builder priority list, and the Tiger's `Range 1` to the establishment table | **L5, a tactic** | staged in section 5 of the retro |
| A8: one wonder, one variable - the cheapest Ancient or Classical wonder ordered in a second city before T45, measured against A4's T43 gate, A7's T54 establishment and its T60 keep | **the next attempt** | proposed, not published |
