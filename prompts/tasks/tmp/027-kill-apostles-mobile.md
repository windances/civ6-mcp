# TEMP TASK 027 - the apostles: kill the Dutch ones with our fastest units

added:     2026-09-28 (human instruction: 新任务：用机动性高的部队消灭使徒)
expires:   turn 265 - 20 turn(s) from T245, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **荷兰's own row in the turn's per-player snapshot no longer lists `APOSTLE` (that field is
           `unit_composition`, and `count == 0` is the reading), and the diary names, for each
           apostle destroyed, the turn it died, the tile it stood on and the unit that took it** -
           the Dutch row read `APOSTLE: 2` on the turn this file was added, so zero means both of
           those are gone; if the count reaches zero with fewer than two kills recorded here,
           somebody else destroyed them and the diary says so instead of counting them as ours.
           **Hard stop at turn 265**, retired either way; a third apostle bought with faith after
           that is the next window's business, not this file's.
overrides: **the directive's `Foreign missionaries` section, for 荷兰's apostles only.** That section holds that
           a religious unit is an opportunistic target - "Treat that as opportunistic: one unit, no
           chase, one tile of movement at most. A missionary is never worth pulling a unit off the
           front - and the sweep that finds them is task 014's job, not the army's" - and the
           human's instruction reverses exactly that for the apostles of the civilization we are at
           war with: they are the target, the mounted units are the hunters, and the sweep is this
           file's work. It also outranks any reading of that section that would have us ignore a
           Dutch apostle standing next to one of our units. **It does not override**: 023 (the Dutch
           campaign), which keeps the siege train, the ranged line, the Bombards, the assault
           timetable and the gold - this file lends only the mounted units it names and returns
           them; `hold-what-you-take` and `one-garrison-per-city` (哈勒姆's garrison is not spent on
           the hunt while that city still needs it); `use-your-attacks` and `finish-the-wounded`;
           the directive's ban on `propose_peace` and its refusal of every peace offer; and the
           directive's rule that **no war is declared over a religious unit** - 腓尼基's apostle and
           印度's missionaries are at peace with us and stay untouched. **It does not authorize buying
           a religious unit** (a missionary bought in a Chinese city carries a foreign faith, and
           the directive forbids it), and it does not authorize an assault of its own: an apostle
           inside a Dutch city we have not taken is answered by 023 taking the city.
scope:     The religious units of civilizations we are at war with - 荷兰's apostles and missionaries, and only
           those; the mounted units lent to the hunt (the `UNIT_CAVALRY`, the `UNIT_CUIRASSIER`, and
           any `UNIT_KNIGHT` or `UNIT_HORSEMAN` still alive); their movement inside and outside our
           territory; the `get_map_area` and `get_religion_spread` reads that find the targets; and
           the diary lines that record each sweep and each kill. Not the Dutch cities and not their
           capture (023's), not the siege train or the ranged line (023's), not the navy (026's),
           not the two scouts (025's), not a war declaration, not a peace, and not a religious unit
           belonging to a civilization we are not at war with.

## The instruction, and who it is about

「新任务：用机动性高的部队消灭使徒」 - kill the apostles with high-mobility units.

On this board there is exactly **one** civilization whose apostles we may lawfully touch: **荷兰**, the
only player we are at war with. Two other players own religious units and are **not** at war with us -
 **腓尼基** (one apostle, two gurus, one warrior monk, religion 犹太教) and **印度** (three missionaries,
religion 印度教) - and at peace a religious unit cannot be touched at all: `condemn` answers
`ERR:REQUIRES_WAR`, `attack` answers `ERR:NOT_AT_WAR`, and a city strike answers `NO_ENEMY`. **The hunt is
the Dutch war's business.** No war is declared over a missionary, and this file does not ask for one.

## Why this instruction, measured

荷兰's own row of the per-turn snapshot (`unit_composition` and `religion_cities`, read from the diary)
over the last eighteen turns of this branch:

| turn | Dutch apostles | Dutch cities | cities following their religion | their military |
|---|---|---|---|---|
| 230 | 4 | 7 | 13 | 120 |
| 232 | 5 | 7 | 13 | 124 |
| 241 | 1 | 5 | 15 | 70 |
| 244 | 2 | 3 | 15 | 22 |
| 248 | 2 | 2 | 15 | 48 |

Their army is gone - **military 120 -> 22** across the turns we took four of their cities - and the
apostles are still here, and their religion is still spreading: **13 cities at T230, 15 at T244** while
they themselves hold three cities, so most of that number belongs to somebody else, ours among them.
An apostle costs them faith (they hold about 145 with +28 a turn), no rule in this repository can see
one, and killing their army did not stop the conversion. That is the measured case for hunting it
deliberately instead of treating it as the directive's "opportunistic, one tile of movement at most"
case.

**The two that exist right now are not a stale reading.** Three turns after this file was written the
Dutch row still read `APOSTLE: 2` - the same two, while their cities went 3 -> 2 and their military
went 22 -> 48 - so the finish line is still false, the sweep still has a target, and the two apostles
have outlived five of their cities. They are not standing in the open waiting to be found: they are
either inside the two cities that are left or walking between them, and both of those cities are in
our fog at this writing.

The only sighting on record: at T220 a Dutch apostle stood **on a Dutch city tile** with one of our
mounted units one tile away (the run log of the session that played it, tile line
`**[荷兰 APOSTLE]**`). **They shelter inside their own cities**, which is why finding one is a sweep and
not a look at the threat list.

**And this is where the two have been working.** `get_religion_spread` at T246 puts 新教 (the Dutch
faith) in the majority in **eight of our own cities** - 阿姆斯特丹 (8 followers), 乌得勒支 (5),
布鲁塞尔 (5), 成都 (5), 哈勒姆 (4), 赫利奥波利斯 (4), 塞纳 (3), 奈梅亨 (2) - while the Dutch
themselves are listed with a single city, 埃因霍温 (7). Most of those eight are the cities we have
just taken from them, so the apostles are not wandering our interior: they follow the army. That
list is the sweep's target list, and it is one call away.

## Two facts no tool puts in front of you

- **A religious unit is invisible to every metric.** It is `FORMATION_CLASS_RELIGIOUS` with
  `Combat = 0`, so `get_units` (its "Nearby threats" block lists combat units), no `end_turn` block and
  no rule in `prompts/checks/turn-checks.md` will ever mention one. **The only detector is the tile's
  unit list in `get_map_area`**, which prints owner and type - `**荷兰 APOSTLE**`.
- **The count is visible even though the tile is not.** The turn's per-player snapshot carries
  `unit_composition`, and 荷兰's row read `APOSTLE: 2` on the turn this file was added. So the sweep is
  not blind: the snapshot says whether any exist, the map read says where, and the difference between
  the two is what this file is for.

## Gate 0 - sweep first, and write down the answer

One sweep per turn, and the whole sweep is a handful of calls, not one call per tile:

1. `get_religion_spread` once - it names which cities follow 新教 (Protestantism). Those tiles are where
   an apostle stands or is heading, and it is the cheapest way to point the sweep.
2. `get_map_area` at radius 2-3 around each Dutch city we can see, and around any of our cities the
   religion read shows as converted. **Read the tile lines, not the threats block.**
3. Write the result down as `owner | type | tile` for every religious unit found - and write the sweep
   into the diary even when the answer is "none found". A sweep with no record is a sweep nobody can
   check.

The tiles to read first are the ones this branch has already shown an apostle on, plus the Dutch core;
the coordinates belong in this match's diary and in the task's own runs, not in this file's headers.

## Execution - an apostle dies the turn it is found

- **`condemn` first.** It is the game's own `UNITCOMMAND_CONDEMN_HERETIC`, a command rather than an
  attack: one **adjacent** military unit, no charge, no combat, and the reply names the candidates
  before it fires. It does not require the apostle to be in the open, so a Dutch apostle sitting on a
  Dutch city tile is still a legal condemn from an adjacent tile - the one case the T220 sighting
  measured.
- **`attack` is the fallback**, and it works for the same reason the condemn does: the target has
  `Combat = 0`, so any attacker destroys it. Prefer the unit that is already adjacent and has movement
  to spare. Do not spend a siege unit on it - a Bombard cannot attack units at all
  (`ERR:SIEGE_CANNOT_ATTACK_UNITS`).
- **Never leave it alive at the end of the turn.** A religious unit that survives keeps converting on
  its own turn, and `use-your-attacks` already fails a turn that ends with a legal attack unused - an
  adjacent apostle is exactly such an attack. If the only unit in reach cannot finish it this turn, say
  so in the diary and record the tile, so the next turn starts from the same tile instead of a new
  search.
- **Do not walk into the Dutch city's reach to do it.** Under 023's standard the target is worth one
  tile of movement and nothing more: if the shot means standing where the Dutch city and their
  remaining units can answer, the shot waits for the escort - and the unit that would die is a mounted
  unit the campaign needs.

## Who hunts, and what does not leave the front

- The lent units are **the mounted line only**: the `UNIT_CAVALRY` (moves 7, CS 62 at the last read),
  the `UNIT_CUIRASSIER` (moves 4, CS 64), and any `UNIT_KNIGHT` or `UNIT_HORSEMAN` still alive. They are
  the only units in the empire that can cross the Dutch lane and still act on the far side, which is
  what 「机动性高」 buys.
- **The `UNIT_CUIRASSIER` is 哈勒姆's garrison at the last read.** `hold-what-you-take` fails while a city
  below 50 loyalty has neither a governor on its tile nor a unit on it, and 哈勒姆 was taken within the
  two turns before this file was added, with its governor still in transit. So the Cuirassier leaves
  only once that city passes the rule without it, and **until then the Cavalry is the hunter**; the
  diary names the unit that took each apostle, so the ledger shows whether the garrison ever moved.
- Nothing else is lent: **no Bombard, no Field Cannon, no Line Infantry, no siege unit, no navy.** The
  Dutch campaign's train stays where it is, and this file's whole cost is the movement of two mounted
  units between assaults.

## What this file is not

- **Not a war.** 腓尼基's apostle and 印度's missionaries are at peace with us and stay untouched,
  however tempting their tiles look.
- **Not a purchase.** China has no religion of its own, and a missionary bought in a Chinese city
  carries the majority faith of that city - a foreign one. Faith is banked (it read 3273 with +99 a
  turn at the last snapshot), and it is not spent on religious units.
- **Not a substitute for the campaign.** An apostle inside a Dutch city we have not taken is best
  answered by taking the city, which is 023's business; this file does not order an assault of its own,
  and an apostle that shelters behind walls we have not broken is a report, not a detour.

## Report

Every turn: the sweep's result - the tiles read, and every religious unit found as
`owner | type | tile`, or "none found" - and each kill as `turn | tile | unit | condemn or attack`. At
the end, whether the file is retired on its finish line or on its hard stop: the apostles accounted for
one by one, 荷兰's `unit_composition` before and after, the movement the hunt actually cost, and which
unit spent it.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "the apostles: kill the Dutch ones with our fastest units" --slug kill-apostles-mobile --instruction @.tmp\kill-apostles-instruction.txt --why "hunt the apostles of the civilization we are at war with using our fastest units, on the human's instruction: their army is gone and their apostles are still spreading their faith" --done-when @.tmp\kill-apostles-done.txt --overrides @.tmp\kill-apostles-overrides.txt --scope @.tmp\kill-apostles-scope.txt --body-file .tmp\kill-apostles-body.md --cn @.tmp\kill-apostles-cn.md --turns 20 --no-commit
     at: 2026-09-28T22:20:31+08:00
     chinese backup: prompts/tasks/cn/027-kill-apostles-mobile.cn.md
-->
