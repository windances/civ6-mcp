# `attacks-that-land-nothing` - staged: needs a server started after the row-context tuple gained it

```yaml
id: attacks-that-land-nothing
level: error
when: metric(attacks_landed_nothing) >= 1
require: metric(attacks_landed_nothing) == 0
message: A melee land unit attacked an enemy at sea, which the rules refuse - a melee unit cannot attack a unit at sea (manual:723, MELEE UNITS - "They cannot attack enemies at sea"). The engine does not refuse the order: it acknowledges it as OK:MELEE_ATTACK and the target's HP never moves, while the attack spent the move that would have carried the unit out of the water. Measured on this branch, T222-T237: seven melee attacks on Dutch Caravels with the target's HP identical every time, and two of our units sunk. Attack a hull only with a ranged or a naval unit; move a melee unit out of the water rather than swinging from it.
```

**Why it exists.** A melee **land** unit cannot attack a unit **at sea** (`manual:723`, MELEE UNITS:
"They cannot attack enemies at sea"). The engine does not refuse the order: it acknowledges it as
`OK:MELEE_ATTACK`, the tool printed a damage estimate (`Est damage to defender: ~151`), and the target's
HP never moved. Measured on this branch, T222-T237: **seven melee attacks on Dutch Caravels, the
target's HP identical every single time** (`enemy HP:57 -> 57/100`; the Dutch hulls read 57 and 100 for
seventeen consecutive turns while the diary recorded "four Caravels destroyed"), and **two of our units
sunk** - a Cavalry at (74,27) on T226 and a Field Cannon at (74,29) on T233 - because each attack spent
the move that would have carried them out of the water. The same anomaly had already been written into
three retired task files (018 at T216, 019 and 021 at T225).

**What is already in place** (so promoting this is a file move, nothing else):

- the Lua refuses the order (`ERR:MELEE_CANNOT_ATTACK_AT_SEA`, with the manual citation) - measured live
  in the session that started at 20:28, which got the refusal twice at T225/T226 and produced **zero**
  `MELEE_ATTACK` lines;
- the estimate answers `REFUSED BY THE RULES` instead of printing a number for it;
- `GameState.note_attack_result()` counts it into `attacks_landed_nothing` and puts
  `!!! ATTACK LANDED NOTHING ...` in the reply;
- `end_turn`'s live metric block exposes it, and `_CONTACT_METRIC_KEYS` includes it so a **stored-row**
  context reads 0 rather than `un-evaluable`.

**Why it is still staged.** That last item is read at *import* time: a server whose process predates the
tuple change still answers a row-based pass - the history recomputation and the TURN START briefing -
with `un-evaluable`, which reads as a permanent streak. It was promoted on 2026-09-28 and taken back out
the same hour for exactly that reason.

**Cut it in** with the two-file move `pending/README.md` describes, in a session whose server started
after the commit that added `attacks_landed_nothing` to `end_turn._CONTACT_METRIC_KEYS`: copy this rule
block into `../turn-checks.md`, delete this file, and flip `tests/test_attack_domain.py`'s assertion from
staged to live. On a corrected server the metric reads 0, so the rule is a **regression lock**: it fires
the first turn the refusal is removed or bypassed.
