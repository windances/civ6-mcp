# `answer-the-missionary` - staged: needs a server started after the scan gained `RELIGIOUS|` rows

```yaml
id: answer-the-missionary
when: metric(religious_at_war_within_2) >= 1
require: metric(attacks_this_turn) >= 1
message: A religious unit of a civ we are at war with is within two tiles of one of our units and nothing attacked this turn. While at war an adjacent military unit can destroy it with `unit_action(action="condemn")` - one command, no charges, one tile of movement at most - or with a normal attack, and killing it is worth more than the faith it would otherwise spread. Treat it as opportunistic: never pull a unit off the front for it, and a missionary more than one tile away is not worth the chase. At peace nothing can touch it at all (`attack` answers `ERR:NOT_AT_WAR`, `condemn` answers `ERR:REQUIRES_WAR`), so this rule is war-time only, like the other answer rules.
```

**Why it exists.** Religious units were invisible to every metric in the toolkit, and the predicate the
documentation carried for months was wrong: there is **no `FORMATION_CLASS_RELIGIOUS`** in the game's
data. A Missionary is `FORMATION_CLASS_CIVILIAN` with `ReligiousStrength="100"` and no `PromotionClass`
at all (`Base/Assets/Gameplay/Data/Units.xml`, `UNIT_MISSIONARY`); Apostle 350, Inquisitor 200, Guru 200.
The threat scan filtered on `Combat > 0 or RangedCombat > 0`, so a missionary was dropped before any
metric could see it, and the only detector was the tile list in `get_map_area`. Measured consequence:
the whole missionary campaign in this match was tracked by temporary task files (008, 014, 027), never
by a rule - and when those tasks retired, nothing was watching.

**What is already in place** (so promoting this is a file move, nothing else):

- `build_threat_scan_query` prints `RELIGIOUS|pid|owner|type|x,y|hp|rstr:N|dist:N|udist:N|atwar:0/1|uid:N`
  for every visible unit with `ReligiousStrength > 0`, without touching the `THREAT|` rows the contact
  metrics are built from;
- `parse_religious_sightings` reads those rows into `ReligiousSighting` (`killable` is "at war and
  adjacent");
- `end_turn` computes `religious_within_3` and `religious_at_war_within_2`, prints a
  `FOREIGN RELIGIOUS UNITS` block naming each one with the doctrine for its case, and both metrics are
  in `_CONTACT_METRIC_KEYS` so a stored-row pass reads 0 rather than `un-evaluable`.

**Why it is still staged.** That last item is read at *import* time: a server whose process predates the
tuple change still answers a row-based pass - the history recomputation and the TURN START briefing -
with `un-evaluable`, which reads as a permanent streak and shifts the verdict.

**Cut it in** with the two-file move `pending/README.md` describes, in a session whose server started
after the commit that added the two metrics to `end_turn._CONTACT_METRIC_KEYS`: copy this rule block into
`../turn-checks.md` (dropping the `level:` line, as every live rule does), delete this file, and flip
`tests/test_religious_units.py`'s staged assertion to live. The peacetime case gets **no rule** on
purpose: the doctrine is to leave the unit alone and watch `get_religion_spread`, and a rule that cannot
be satisfied is worse than none. The block is what makes that case visible.
