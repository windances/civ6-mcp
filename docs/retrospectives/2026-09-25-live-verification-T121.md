# Live verification, 2026-09-25 — the T121 save, and two bugs the adapter had shipped

Everything below was measured against the running game, not reasoned about: Civ VI (DX12, pid
24460), FireTuner on 4318, the hand-played save `秦始皇（大一统） 121 公元125年` loaded through
`load_game_save` (46s, menu path), T121, 中国, 7 cities, 17 units, military score 276. Nothing was
ordered, nothing was ended, no save was written.

The point of the exercise was to close the live-verification debt from the city-capture, loyalty
and supply-line work. It closed part of it and found two bugs in code that had already passed its
tests — both of them invisible without a game, and both of them the kind that mislead a decision
rather than crash.

## 1. Launching the game from a confined sandbox cannot work

`launch_game()` reported `WARNING: Game launched (process after 0s) but FireTuner port did not
open within 180s`, and the direct EXE (`CivilizationVI_DX12.exe`) died inside 25s. Neither was a
crash, a missing DirectX build, or Steam being down — Steam was running, `EnableTuner 1` was set
(`AppOptions.txt:75`), and app 289070 resolves through the `D:\SteamLibrary` library.

The process exits before writing a single log line: after the attempts, the newest file under
`%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\Logs` was still 2026-09-22. The same
tree refuses a write probe under `workspace-write`:

```
[sandbox: file access denied under workspace-write mode]
```

The game keeps its profile, cache and logs there and its saves under `Documents\My Games` — both
outside the session workspace — so a confined launch dies at startup by construction. Launched
with `danger-full-access`, the port was open within 45s. See SETUP-WINDOWS.md ("Launching needs the
wider sandbox mode"), which had recorded the symptom on an earlier date; this run supplied the
mechanism.

## 2. `GetTurnsToConversion()` is not a revolt countdown

`build_loyalty_check_query` read `City:GetCulturalIdentity():GetTurnsToConversion()` and treated it
as "turns until this city revolts". It is only that while the city is *losing* loyalty. The game's
own banner reads two calls together (`DLC/Expansion2/UI/CityBanners/CityBannerManager.lua:2355-2358`):

```lua
local nTurns = pCulturalIdentity:GetTurnsToConversion();
local eOutcome = pCulturalIdentity:GetConversionOutcome();
if (eOutcome == IdentityConversionOutcome.LOSING_LOYALTY and nTurns < 20) then
    eNextOwner = pCulturalIdentity:GetPotentialTransferPlayer();   -- the warning icon
```

and `LoyaltySupport.lua:29-38` spells the two meanings out: while `GAINING_LOYALTY` the same figure
counts turns until the pool is *full*.

The live reading, T121, one turn after the human retook Moscow by hand:

```
OUTCOME|589830|莫斯科|loyalty:50.0|per_turn:15.0|turns:4|outcome:2/GAINING_LOYALTY
```

Our output for that city said `50/100 +15.0/turn, flips in 4` — a revolt countdown for a city that
was four turns from a full pool. The enum values are `STABLE=0, LOSING_LOYALTY=1,
GAINING_LOYALTY=2` (probed live; `IdentityConversionOutcome` resolves in the InGame state), and
`GetPotentialTransferPlayer()` returns `62 / 自由城市` — the game's own answer to *who takes it*.
Fixed: the query now prints the outcome and the next owner, `CityLoyalty.losing` prefers the game's
word over the sign of the pressure, `turns_to_revolt` is zero unless the city is draining, and the
LOYALTY WARNING prints the direction next to any countdown (`losing 7.8/turn, revolts in 4 ->
自由城市` vs `gaining 15.0/turn, full in 4`).

## 3. `gsub("%c", " ")` was eating bytes out of Chinese text

The game's loyalty advice reached the adapter as `提升此城的 ... 宜居度，让人民增加幸� 感`. The
cause is the advice sanitiser: `%c` is not locale-neutral. The C locale and CP1252 both classify
`0x81 0x8D 0x8F 0x90 0x9D` as control codes, and those byte values occur inside CJK UTF-8
sequences, so the class removed one byte out of some characters and left the rest — which the
client then decoded as invalid UTF-8 (`errors="replace"` → U+FFFD).

Byte counts, live, per city (`.tools/probes/loyalty-encoding.lua`):

```
ADVICE|65536|len:540,540,540|high:366,346,366|pct_removed:0|safe_removed:0
```

`high` is the count of bytes ≥ 0x80 in the raw string, the `%c`-sanitised string and the proposed
one: 366 in, 346 out, 366 preserved. Twenty high bytes lost per call, on every city. The fix keeps
only what can actually break a protocol line — TAB/LF/CR, built with `string.char` so no escape can
be misread as a pattern class — and the same advice now arrives whole:

```
提升此城的 [ICON_Amenities] 宜居度，让人民增加幸福感。
```

The test that had *asserted* `%c` was wrong (`assert 'gsub("%c", " ")' in lua`) is now the test
that forbids it.

## 4. The report itself: a caller inside a loop leaked a coroutine

`live-capture-test.py` calls `game_status()` from inside `asyncio.run`, and every such call printed

```
RuntimeWarning: coroutine '_game_probe.<locals>.probe' was never awaited
```

on stderr. `asyncio.run(probe())` refuses to nest only *after* `probe()` has built its coroutine,
so the nesting guard in the `except RuntimeError` arm came too late. The loop is now detected
before anything is constructed. A warning on stderr is not cosmetic for an MCP client reading the
same pipe.

## 5. `supply:C/T` verified against the board, hex by hex

T121 had no enemy city both visible and at war, so the supply arithmetic could not be measured
there. `AutoSave_0113` (loaded by hand; T113, 6 cities, 19 units, at war with Russia) does have one:

```
CAPTURE_READY|圣彼得堡|56,43|hp:200|max:200|walls:0/0|owner:1|melee_adjacent:0|melee_within_2:0|supply:2/6|
```

An independent re-derivation of the same six hexes (`.tools/probes/verify-supply-river.lua`, which
does not use the adapter's code) agrees exactly:

```
HEX|55,43|cut-by-zoc:UNIT_HEAVY_CHARIOT@55,42
HEX|56,42|cut-by-zoc:UNIT_HEAVY_CHARIOT@55,42
HEX|56,44|OPEN
HEX|57,42|OPEN
HEX|57,43|OPEN
HEX|57,44|OPEN
SUPPLY|2/6
```

So the count is right, the ZOC rule is right (the Chariot at (55,42) is *beside* the two cut hexes
rather than on them), and the city was healing off the four open hexes. This is the lever the
SIEGE PROGRESS block tells the agent to pull.

## 6. The river `-5`: not observable at T113, and a false alarm of my own making

**Retraction first.** An early probe of mine reported `river:true` for sixteen adjacent pairs,
including one sixteen tiles away, and I read the estimate's missing `river -5` as a bug. The probe
was wrong, not the adapter: `local cross, err = pcall(...)` captures pcall's *status* in `cross`,
so `tostring(cross)` printed `true` for every call that did not error. With the second return value
read instead, every one of the sixteen pairs at T113 crosses no river - and the estimate's own
`Modifiers:` line was correct.

No river-crossing melee pair exists on that board, so the modifier itself is still unverified live.
What *is* now checked is the branch: `river-crossing-truth.lua` asks the plot's own edge flags and
the crossing call three times each - stable `false`, both directions, and `(54,40)` carries its
river on the **NW** edge, whose neighbour is not `(53,40)`.

## 7. The engine's own combat preview, and the flanking bug it found

`CombatManager` is available in the InGame state with the functions the game's unit panel itself
uses (`Base/Assets/UI/Panels/UnitPanel.lua:3352`):

```
CMFN|CanAttackTarget,GenerateCombatResults,GetBestDefender,GetBestInterceptor,IsAttackChangeWarState,SimulateAttackInto,SimulateAttackVersus,SimulatePriorityAttackInto
```

`CombatManager.SimulateAttackVersus(attackerComponentID, defenderComponentID, eCombatType)` returns
the engine's combat solution, indexed by `CombatResultParameters`. For our Heavy Chariot (id
1310724) in Moscow against the Russian Warrior at (53,40) it says:

```
RES|ATTACKER.COMBAT_STRENGTH=28        RES|ATTACKER.STRENGTH_MODIFIER=0
RES|ATTACKER.PREVIEW_TEXT_MODIFIER.1=因难度设置而+2 [ICON_Strength] 战斗力。
RES|ATTACKER.PREVIEW_TEXT_ASSIST.1=+4夹击加成
RES|ATTACKER.PREVIEW_TEXT_HEALTH.1=[COLOR_RED]-6[ENDCOLOR] 受损单位
RES|DEFENDER.COMBAT_STRENGTH=20        RES|DEFENDER.STRENGTH_MODIFIER=-5
RES|DEFENDER.PREVIEW_TEXT_TERRAIN.1=[COLOR_RED]-2不利地形[ENDCOLOR]
```

The engine flanks with **+4** (two neighbours). Our estimate said `flank +6`: the flanking loop
walked a 3x3 box, and two of those eight plots are two tiles away in a hex grid, so a third unit at
distance two was counted. The support loop had the same defect. Both now filter on
`Map.GetPlotDistance(...) == 1`, and the same estimate now reads `flank +4` - matching the engine.

This is the engine oracle the adapter was missing. It also shows what the estimate still does *not*
model: the engine applies a difficulty modifier (+2 here), a damaged-unit penalty (-6 on the
attacker), and defender-side terrain (`-2`) folded into `DEFENDER.STRENGTH_MODIFIER=-5`. Our
attacker CS after the fix is 32 where the engine's effective value is 28, and our defender CS is 20
where the engine has 15 - so the estimate is still optimistic, and `FINAL_DAMAGE_TO` (77 / 79 in
this dump) still needs decoding before it becomes a regression check.

## 8. Corps and Armies: the API is reachable where we need it

```
CMD|FORM_CORPS=487801373          CMD|FORM_ARMY=-1373423663
CMD|ENTER_FORMATION=-913294208    CMD|EXIT_FORMATION=-50443187
UNITMANAGER|table                 UNITCOMMANDTYPES|table
CAN|UNIT_ARCHER|FORM_CORPS=487801373|false
```

`UnitCommandTypes.FORM_CORPS` / `FORM_ARMY` resolve in the **InGame** state, and so does
`UnitManager.CanStartCommand(unit, commandType, false)` - which is the gate a `form_formation` tool
should use. Every unit answers `false` at T113, as it must: Nationalism is not researched and no
two same-type units are stacked. Note `Players[me]:GetCivics()` is **nil** in InGame, so civic
state must be read in GameCore; the command gate is the better check anyway.

## How to test these changes

Two ways in. **Launch the game yourself** (desktop or Steam) and the sandbox is not involved at
all: the game writes its own profile with your own rights, and every command below runs under the
default confined mode. Only a *launched-from-here* game needs `danger-full-access` (see §1).

FireTuner serves exactly one client, so nothing else may hold 4318 while these run - stop the agent
session (or its MCP server) first.

### The loyalty reading (both fixes)

```powershell
.venv\Scripts\python.exe .tools\verify-live.py --no-load --get-cities   # the MCP tool's own line
.venv\Scripts\python.exe .tools\verify-live.py --no-load --loyalty      # the scan + LOYALTY WARNING
```

Look for the difference between these two lines - the same city, one turn after it was retaken:

```
before:  莫斯科 ... (+15.0/turn, flips in 4)          # a city four turns from a full pool, called a revolt
after:   莫斯科 ... (gaining +15.0/turn, full in 4)   # and the advice string is readable Chinese
```

The advice text is the encoding fix; the `gaining ... full in` is the outcome fix. A city that is
really draining reads `losing -7.8/turn, revolts in 4 -> 自由城市`.

To see the bug itself rather than the fix, check out the commit before it and run the same
command - the tree is committed, so this is a clean A/B:

```powershell
git switch --detach db17838^
.venv\Scripts\python.exe .tools\live-capture-test.py --loyalty
git switch -
```

### The encoding fix, independent of our code

`.tools/probes/loyalty-encoding.lua` computes both sanitisers itself, so it demonstrates the byte
loss whatever the checkout:

```powershell
.venv\Scripts\python.exe .tools\live-lua.py --lua-file .tools\probes\loyalty-encoding.lua
```

`high:366,346,366` is the raw string, the `%c` version and the TAB/LF/CR version: twenty high
bytes eaten by `%c`, none by the replacement. `.tools/probes/loyalty-enum.lua` prints the enum
(`STABLE=0`, `LOSING_LOYALTY=1`, `GAINING_LOYALTY=2`) and the next owner the game names.

### The coroutine warning

```powershell
.venv\Scripts\python.exe .tools\verify-live.py --no-load --loyalty 2>&1 | Select-String never
```

Nothing should match. The guard has a test that fails on the old code:
`pytest tests/test_menu_navigation.py -q -k orphan`.

### Through the agent instead of the scripts

The MCP server imports the Lua builders at call time, so a running server serves the *old* code
until it is restarted. Start a fresh session (or restart the MCP) before judging a fix this way;
otherwise the new rules read as `un-evaluable`. Then `get_cities` shows the loyalty line and
`end_turn` carries the `LOYALTY WARNING`.

## What is still not verified live

- **The capture move itself.** `supply:C/T` is done (§5), but ordering a melee unit onto a 0 HP
  city tile (`CAPTURE_MOVE` -> `CITY TAKEN`) still needs a board with a city at 0 HP and a melee
  unit adjacent, and it is the one check that **orders a unit**. To close it:
  `.tools\verify-live.py --no-load --raw-capture` to confirm the city is at 0 HP with
  `melee_adjacent >= 1`, then `--capture` (which moves the unit) and re-scan.
- **The river `-5` branch.** No river-crossing pair existed at T113 or T121 (§6). To close it: a
  board where `.tools\probes\river-pairs.lua` prints `river:true` and `legal:true`, then
  `.tools\verify-live.py --no-load --estimate <unit_id> <x> <y>` and read `Modifiers:` for
  `river -5` (the estimate orders nothing).
- **The estimate against the engine's numbers.** `CombatManager.SimulateAttackVersus` is the oracle
  (§7) and the flanking count has been reconciled with it; the difficulty, damaged-unit and
  defender-terrain modifiers, and the meaning of `FINAL_DAMAGE_TO`, are not yet modelled or decoded.
- **Corps/Armies end to end.** The API and the command gate are reachable in InGame (§8), but
  forming one needs Nationalism or Mobilization plus two same-type units, which no save here has.
- **Corps/Armies.** `UnitCommandTypes.FORM_CORPS` / `FORM_ARMY` still have no tool.
