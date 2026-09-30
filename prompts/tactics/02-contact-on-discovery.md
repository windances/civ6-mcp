# 2. Contact on discovery / 部队发现敌人，对敌行动策略

Read whenever a visible enemy unit is within three tiles of any of our units.

## Trigger

Any enemy unit in the snapshot inside three tiles of one of our units. That includes barbarians
in peacetime: a barbarian that reaches a builder or a trade route is a lost civilian, and a
scout that walks past us reveals the whole stack.

## Assess (name these numbers before proposing anything)

For every enemy in contact, from the snapshot:

- **class** - melee, anti-cavalry, light/heavy cavalry, ranged, siege, recon, naval;
- **combat / ranged strength and HP** - is it killable this turn, or only damageable;
- **distance to our nearest unit**, and whether terrain (hills, forest, river, zone of control)
  favours it or us;
- **how many of our fighting units are already within two tiles** - `local_superiority` if the
  turn result reported it;
- **whether it is the screen of something bigger** - a lone scout is a scout; a lone scout in
  front of a stack is a spotter.

Two reading rules for the snapshot itself, both learned from live snapshots:

- **A tile listed as one of our cities may hold several of our units.** Civ VI reports the units
  inside a city at the city's own coordinates and the city centre is not bound by the field's
  one-unit-per-tile rule, so "2 Archers + 1 Warrior at (57,29)" is a garrison in Beijing, not an
  impossible stack. `get_units` marks them `[IN <city>]`; check the snapshot's city list before
  reporting a stack as a data error. A stack on a tile that is **not** a city is the real
  anomaly, and it is worth a warning because every distance-based judgement becomes suspect.
- **A barbarian-typed unit inside our own unit list** (`UNIT_BARBARIAN_HORSEMAN`) is a converted
  unit: Thirty-Six Stratagems gives China a barbarian through the game UI. It fights for us.

## Decide

1. **Killable now and worth killing → kill it this turn, with everything in range.** This is the
   default answer, and it is cheap: `finish-the-wounded` says a target at 20 HP or less is the
   one attack that is never a bad trade.
2. **Contact without local superiority → mass first.** A unit within two tiles is not enough;
   two or three attackers on one target kills it this turn, one attacker trades while the target
   heals about twenty points a turn. Pull the nearby units into contact
   (`mass-on-contact` fails while an enemy is in contact with only one of ours in range), then
   hit the same target together. **Which contacts the rule reaches** (human instruction
   2026-09-30, 突袭也算战争): a war, **and a barbarian camp within three tiles** - a raid is a fight,
   so it gets the same concentration. A wandering barbarian with no camp near, or a
   peacetime foreign unit standing in the lane, sets nothing: the rule is silent there, and the
   decision is this file's, not the rule's.
3. **No superiority available and the enemy is dangerous → do not trade.** Withdraw to rough
   terrain, a city, or out of its reach, keep the stack together, and come back with numbers.
4. **Harmless and immobile → ignore it deliberately** (a unit inside a city, a barbarian camp we
   are keeping alive for Thirty-Six Stratagems) and say so in the report, so the skipped contact
   is a decision rather than an oversight.
5. **A bypassed enemy becomes a rear threat.** If the army is marching to a city and an enemy is
   left behind it, that enemy attacks the siege train from behind while the city's ranged strike
   hits it from the front. Clear the path first, or leave a covering force and say which.

## If the contact happens while the army is still assembling

This file's five answers above are about the fight. They are not sufficient when the stack is still
forming, because there the cost of the fight is **the assembly itself**, and the questions that have
to be answered first are different ones: does the contact invalidate the rally point, can the units
already forward kill it without spending a ring tile, and does the timetable now belong to the enemy.
That procedure is `tactics/04-staging-out-of-range.md` **step 5** — read it whenever an assault is
planned and the stack is not yet formed, and report its `CONTACT` line, not just the target list.

The one sentence version, measured T103–T106: **clear the field first, then fill the pads and fire.**
The contact turn is a kill turn; the volley it costs is real (T104's contact slid Moscow's first
volley from T105 to T107), and the unit that answers it must be the screen, never the archer that is
one tile from its ring pad.

## Prefer the counter unit

The game's own `PROMOTION_CLASS_*` is the rock-paper-scissors axis:

| Our unit | Beats | Why |
|---|---|---|
| Anti-cavalry (Spearman, Pikeman) | Cavalry (Horseman, Knight, Heavy Chariot) | Cavalry reaches past the front line to the siege and ranged units; a Spearman is the cheapest answer that exists. |
| Ranged (Archer, Crossbowman) | Melee | Ranged attacks take **no retaliation**, so they grind a melee stack down without healing turns. |
| Cavalry | Ranged, siege, civilians | It reaches the targets behind the screen instead of trading with the screen. |
| Melee | Anti-cavalry | The Zweihander/melee line is the answer to anti-cavalry. |
| Siege | Cities and walls only | Nearly helpless against units - never let it be the unit holding the front tile. |

**Promotions change the table, so test before writing a unit off.** Against a melee unit with
**Battlcry** (`PROMOTION_BATTLECRY`: +7 combat strength *against melee and ranged*), our ranged
fire is penalised and our **cavalry is not** - the Swordsman that killed our ram and a Warrior at
T109 read CS 42 against Catapults but CS 35 against a chariot. One estimate settles the matchup;
do not generalise one unit's bad result into "the army cannot engage this".

**And measure the whole army, not one exchange, before deciding to mass.** Massing is the answer to
a target one or two attackers fall short of; it is not an answer to a target the entire army cannot
hurt. Measured live on a Battlecry Swordsman standing on forest (effective CS 45) at Moscow T113:
all twelve of our units together dealt **75 against its 81 HP**, each melee attacker paid 60-164
retaliation for 4-10 damage, and the two Archers nominally in range could not fire at all - one was
three tiles away and the other had line of sight blocked by a hill. Four Warriors would have died to
finish it. The honest answers in that matchup are: make the free ranged shots that cost nothing,
keep the melee **in front of** the archers so the swordsman attacks something it cannot kill in one
blow, and change the material (the Crossbowman's +15 ranged strength turns a 10-point shot into
20-25) instead of feeding units to it. `match-their-melee` asks for an attack, not a corpse; a
stated disengagement is a legitimate answer when the arithmetic says massing cannot work.

## Prohibitions

- Never attack with a single unit in range when more are within reach.
- Never spend a ranged attack on a full-health unit you cannot kill while a wounded one is in
  range.
- Never chase into fog or across a river into unknown ground without support.
- Never let a siege unit be the answer to an enemy unit: pull it back and shoot with ranged.
- Never let an available attack be discarded - every unit with moves and a legal target either
  attacks or is parked with a stated reason (`use-your-attacks`).

## What to report

The enemy in contact with its class/strength/HP/distance; the killable ones and with how many of
our units; the units that should move into contact (named, with tiles); which of our units should
not engage and where it should stand instead. Where the snapshot cannot answer a question
(terrain, fog, walls), say what is missing.
