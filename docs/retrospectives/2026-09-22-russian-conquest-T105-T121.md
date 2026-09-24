# Retrospective — the Russian conquest, T105–T121 (hand-played, no MCP telemetry)

Reviewed 2026-09-22. This run was played in the game window: `.civ6-mcp-data` has no log, diary
row or heartbeat for T100–T121, so the entire record comes from Civ VI's own logs
(`%LOCALAPPDATA%\Firaxis Games\...\Logs`) — `CombatLog.csv`, `DiplomacySummary.csv`,
`Player_Stats.csv`, `UnitOperations.log`, `Player_WarWeariness.csv`. Reproduce with
`python .tools/battle-report.py` and `python .tools/civ6log.py`.

It is the same game (`seed -1894041591`) and the third attempt at the same campaign: the first
two were the agent's abandoned T101–T116 grind and the T118–T128 bombardment that withdrew.
**This one took four cities and eliminated Russia.**

## 1. What happened

`DiplomacySummary.csv`, every city China took:

| Turn | City | Taken from |
|---|---|---|
| T109 | 阿斯特拉罕 Astrakhan | Russia |
| T112 | 莫斯科 Moscow | Russia |
| T117 | 圣彼得堡 St Petersburg | Russia — **Russia is eliminated**, its stats rows stop at T116 |
| T121 | 莫斯科 Moscow | **Free City (player 62)** — our own captured Moscow had revolted |

The free-city row appears in `Player_Stats.csv` at **T116** (1 city, pop 3) and is gone after the
T121 re-capture. So Moscow — captured at T112 — **revolted four turns later**, and retaking it
cost T118–T121.

## 2. The fighting, per turn (China)

`CombatLog.csv`, attacker/defender damage both sides:

| Turn | our attacks | damage dealt | of which to a city | retaliation we took | enemy attacks on us | damage they did |
|---|---|---|---|---|---|---|
| 105 | 1 | 19 | 0 | 0 | 0 | 0 |
| 106 | 6 | 228 | 10 | 41 | 1 | 9 |
| 107 | 3 | 66 | 21 | 0 | 0 | 0 |
| 108 | 8 | 216 | 111 | 69 | 1 | 39 |
| 109 | 6 | 139 | 139 | 49 | 1 | 27 |
| 110 | 1 | 29 | 29 | 30 | 1 | 35 |
| 111 | 5 | 187 | 143 | 42 | 1 | 46 |
| 112 | 4 | 184 | 184 | 23 | 1 | 22 |
| 113 | 4 | 189 | 0 | 0 | 0 | 0 |
| 116 | 11 | 238 | 182 | 183 | 2 | 100 |
| 117 | 6 | 178 | 159 | 11 | 1 | 68 |
| 118 | 1 | 20 | 0 | 51 | 2 | 131 |
| 119 | 2 | 29 | 12 | 0 | 0 | 0 |
| 120 | 3 | 172 | 85 | 11 | 0 | 0 |
| 121 | 3 | 174 | 174 | 23 | 0 | 0 |
| **total** | **64** | **2068** | **1249** | **533** | — | **477** |

138 damage per attack-turn, in a campaign that spent **1010 damage** in return and still grew the
army (land units 14 → 20). Targets, by the defender object ids in the log: 524294 = Astrakhan
(T106–T109), 327683 = Moscow (T110–T112), 65536 = St Petersburg (T116–T117), 131072 = Moscow as a
free city (T120–T121).

What the army did that the previous attempts did not:

- **It massed.** 6, 8, 11 attacks in a turn (T106, T108, T116) where the agent's runs managed 1–3.
- **It finished the field army before the city.** T113 (4 attacks, 189 damage, zero to the city)
  and T118–T119 are turns spent killing Warriors and Man-at-Arms, not chipping a wall.
- **It upgraded the siege.** Catapults 1703949/1769482 fired T106–T117; **Trebuchets**
  2228240/2293764 appear at T120–T121 and did 70/64/67 in a turn, and the city fell the same turn
  a melee unit (Heavy Chariot 2097157, 43 damage, 23 taken) went in.
- **It took the city with a melee unit** — four times. No 0 HP city was left standing for its
  healing to undo.

## 3. What it cost, and why

- **The revolt was the expensive part.** Moscow was captured at T112 and revolting by T116. The
  re-capture took T118–T121: 9 of the 64 attacks (~395 damage) and four turns of the army's time
  that St Petersburg's garrison would otherwise have faced. `Player_Stats` shows Moscow at pop 3,
  far from our core, with no governor and no garrison — the three things that hold a city.
  The directive already says "leave a garrison in every captured city and report its loyalty",
  but **nothing measures it**: no rule, no metric, no event. The previous turn's retro found the
  same class of gap for the capture step itself.
- **Man-at-Arms (CS 45) is a wall for this army.** T116–T119: our Archers did 11–20 per shot at
  it, a Spearman took **79** in one hit, and an Archer took **82**. The Man-at-Arms was killed, but
  by attrition at 5:1 cost. Our melee was still Warrior/Spearman tier — the same mismatch the
  T101–T116 review found with the promoted Swordsman, still unmeasured by any rule.
- **The siege upgrade came late.** Trebuchets (Military Engineering) only fired from T120, after
  11 turns of Catapult work. Nothing in the rule set looks at whether a siege unit *can* upgrade.
- **War weariness climbed 1150 → 1366** on the Russian war (`Player_WarWeariness.csv`, ~50/turn
  while attacking), a production cost the campaign paid for 13 turns.

## 4. Comparison with the two earlier attempts at the same campaign

| | T101–T116 (agent, abandoned) | T118–T128 (agent, t1 line) | **T105–T121 (this run, by hand)** |
|---|---|---|---|
| attacks | 19 | 15 in the city phase | **64** |
| damage per attack-turn | ~27 | 77–83 | **138** |
| cities taken | 0 | 0 | **4 (three Russian, one re-taken)** |
| enemy civ removed | no | no | **yes (Russia, T117)** |
| siege tier at the end | Catapults, one at range 1 | Catapults | **Trebuchets** |
| capture step | never (0 HP city healed back) | never (`NO_ENEMY` / `CAPTURE_MOVE` refused) | **four times, by melee** |
| own city lost | no | no | **Moscow revolted (T116), retaken T121** |

The adapter fix from the previous turn removes the *mechanical* reason the agent could not finish
a city; this run shows what the rest of the doctrine looks like when it works, and where the next
hole is: loyalty.

## 5. Proposed optimizations, in priority order

**A. Measure loyalty, and make "hold what you take" a rule.** *(implemented)* A city we capture far
from home is a city in revolt waiting to happen — Moscow went from ours (T112) to a Free City
(T116) with nothing in the turn result saying so.
- `CityLoyalty` + `build_loyalty_check_query` read each of our cities' pool, per-turn pressure, the
  game's own turns-to-conversion estimate, the governor assigned to it (from
  `Player:GetGovernors():GetGovernorList()` / `Governor:GetAssignedCity()`) and the garrison, plus
  `City:GetLoyaltyAdvice()` verbatim.
- metrics `cities_low_loyalty`, `lowest_loyalty`, `low_loyalty_without_governor`,
  `cities_falling_loyalty`, `nearest_loyalty_flip`.
- event `LOYALTY WARNING` naming every city at risk with the numbers and the game's own advice.
- rule `hold-what-you-take`: fails while a city below 50 loyalty has **neither a governor in it nor
  a unit on its tile** — exactly the state Moscow was in.

The API was not guessed: the game's own UI uses it (`DLC/Expansion2/UI/CityPanelCulture.lua`,
`CityBannerManager.lua` — `City:GetCulturalIdentity()`, `GetLoyaltyPerTurn()`,
`GetTurnsToConversion()`), and the repo's existing `get_cities` query already reads the same pool,
so the field names come from two independent places. It still wants a live run
(`.tools/live-capture-test.py --loyalty`) once a game is open, because the query runs in the
InGame context and only the game can confirm the governor list API in that context.

**B. Measure the melee matchup, not just the melee count.** *(implemented)* `melee-screen` counts
Warriors and Man-at-Arms alike. `_matchup_metrics` now reports `strongest_enemy_melee_cs` (enemy
land melee within three tiles) against `our_best_melee_cs`, plus `melee_upgrades_available` and
`min_melee_upgrade_cost`; `BATTLE ASSESSMENT` adds a `MATCHUP:` line when their melee is CS 35+
and five points ahead of ours, naming the unit and the price of the upgrade; the rule
`match-their-melee` fails while that is true and we have neither an upgraded melee unit nor an
attack going in this turn. Evidence: T116–T119 above, and the promoted Swordsman of T101–T116.

**C. Nudge the siege upgrade.** *(implemented)* `UnitInfo` already carries `can_upgrade`,
`upgrade_target` and `upgrade_cost`; `_siege_upgrade_metrics` adds `siege_upgrades_available` and
`min_siege_upgrade_cost`, the rule `upgrade-the-siege` fails during a war while an affordable
siege upgrade is waiting, and the turn result carries an `UPGRADE AVAILABLE` block listing each
unit, its target and its price. Trebuchets from T120 instead of T108 is the difference between
1249 city damage over 13 turns and the same total in eight.

**D. Keep what already works.** The two habits this run shows — mass every attacker in range, and
spend whole turns on the field army rather than the walls — are exactly what `mass-on-contact`,
`use-your-attacks` and `finish-the-wounded` now ask for; the T105–T121 evidence is the strongest
argument yet that they are the right rules. What none of them says is what to do *after* the
capture, which is finding A.

Captured by `tests/test_matchup_rules.py` (24 cases) and `tests/test_loyalty_rules.py` (19 cases);
suite 585 passing, 19 rules. Pinned in `AGENTS.md` and `SETUP-WINDOWS.md`, and in the directive,
the skill's directive block and `tactics/06-…md` (what to do after a capture).

## 6. Caveat on verification

The game is closed (only Steam is running) and this run's turns have no MCP telemetry, so any of
A–C would ship unverified against the live game until a session plays again. The loyalty API in
particular (`city:GetLoyalty()`, turns-to-revolt) has to be checked in-game before a rule depends
on it — `.tools/live-capture-test.py` is the harness for that check.

## 7. Manual verification (2026-09-24): three corrections

The 25th anniversary manual was extracted (`.tools/pdf-text.py` → `.tools/manuals/manual.clean.txt`,
searchable mid-turn through `search_knowledge`) and checked against what this repo assumes. It
confirmed most of it — 200 HP cities, melee-enters-tile capture, support units cannot attack,
ranged takes no damage and cannot capture, flanking +2 per adjacent unit, fortification capping
after two turns, city strength not degrading with damage — and corrected three things:

| Correction | Manual | Was | Now |
|---|---|---|---|
| River crossing penalty | *RIVERS → OFFENSIVE PENALTY*: **-5** | `river -2` in the estimator | `river -5` (`lua/units.py`), pinned by test |
| Garrisons inside cities | *GARRISON UNITS IN CITIES*: the garrison's strength is added to the city's and it **takes no damage**; it dies only if the city falls | "ranged shoots the garrison" in the directive, the skill, `tactics/06`, `tactics/01` and the SIEGE POSTURE advice | "ranged shoots the city's HP", with the garrison a target only when it steps out |
| City healing | *HEALING DAMAGE TO CITIES*: heals "as long as it has a supply line", i.e. while **any adjacent hex** is outside our zone of control | "the city heals about twenty points a turn", unconditionally | conditional phrasing everywhere, plus a **measurement**: each enemy city's `supply:C/T` is scanned, reported in `SIEGE PROGRESS` (`supply line 4/6 cut`), and `SIEGE STALLED` names cutting the supply line as the first fix |

The supply-line count is the one that changes play: cutting every adjacent hex stops a twenty-point
heal outright, which is far cheaper than finding twenty extra damage a turn. It rides in the scan
that already reports the city's HP pool, walls and melee reach, so it costs no extra query.

