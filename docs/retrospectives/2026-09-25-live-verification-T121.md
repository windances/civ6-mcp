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

## What is still not verified live

- **`supply:C/T` and the capture move.** T121 has no enemy city both visible and at war (the
  capture scan returned `0 enemy cit(ies) in sight`, the two visible cities are city-states), so
  the per-city supply arithmetic and `CAPTURE_MOVE` could not be exercised. The query itself ran
  without error in the InGame context, which is all that proves.
- **The river `-5`.** No attack across a river existed to measure; the change is a constant with a
  unit test and an unverified live reading.
- **Corps/Armies.** `UnitCommandTypes.FORM_CORPS` / `FORM_ARMY` still have no probe and no tool.

## Reproduce

```powershell
.venv\Scripts\python.exe .tools\verify-live.py                      # load the newest save, then read-only
.venv\Scripts\python.exe .tools\verify-live.py --no-load --cities --loyalty
.venv\Scripts\python.exe .tools\live-lua.py --lua-file .tools\probes\loyalty-encoding.lua
```

The game must be launched with `danger-full-access` (see §1); everything after that needs no wider
mode than the default.
