# `attacks-that-land-nothing` - staged: needs a server that computes `attacks_landed_nothing`

```yaml
id: attacks-that-land-nothing
level: error
require: metric(attacks_landed_nothing) == 0
once: false
```

**Why it exists.** A melee **land** unit cannot attack a unit **at sea** (`manual:723`, MELEE UNITS:
"They cannot attack enemies at sea"). The engine does not refuse the order: it acknowledges it as
`OK:MELEE_ATTACK`, the tool prints a damage estimate (`Est damage to defender: ~151`), and the target's
HP never moves. Measured on this branch, T222-T237: **seven melee attacks on Dutch Caravels, the
target's HP identical every single time** (`enemy HP:57 -> 57/100`, and the Dutch hulls read 57 and 100
for seventeen consecutive turns while the diary recorded "four Caravels destroyed"), and **two of our
units sunk** - a Cavalry at (74,27) on T226 and a Field Cannon at (74,29) on T233 - because each attack
consumed the movement that would have carried them out of the water. The same anomaly had already been
written into three retired task files (018 at T216, 019 and 021 at T225) and never became a rule.

**The metric.** `attacks_landed_nothing` counts, per turn, attacks whose result line starts
`MELEE_ATTACK` while the combat estimate says the target's domain is `DOMAIN_SEA`:
`GameState.note_attack_result()` increments it and `end_turn` exposes it beside `attacks_this_turn`.
It is computed by `src/civ_mcp/game_state.py` and read at `end_turn.py`'s metric block.

**What has to ship first.** The Lua refusal is already in `lua/units.py`
(`ERR:MELEE_CANNOT_ATTACK_AT_SEA`, with the manual citation), so on a corrected server this metric
should read **0 on every turn** - the rule is a **regression lock**, not a warning: it fires the first
turn the refusal is removed, bypassed, or re-introduced by a new attack path. That is why it is worth
cutting in even though the number is expected to be zero.

**Cut it in** in the same commit as a server build that computes the metric (the counter is read in
`end_turn`'s check context, so any session started after that commit qualifies). The message should
carry the manual citation and the way out - fire with a ranged unit from two tiles away
(`manual:725`: ranged units always use ranged combat, even adjacent), or use a naval unit of our own -
and the refusal message itself is the first line of defence.
