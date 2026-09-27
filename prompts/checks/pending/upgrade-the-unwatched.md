# upgrade-the-unwatched - STAGED, do not cut in until a server computes the metric

Written 2026-09-27 (T218). Staged rather than live because `prompts/checks/turn-checks.md` is
re-read every turn by the *running* process, whose metric set is in memory: a rule naming
`uncovered_upgrades_available` before a server computes it reports `un-evaluable` every turn and
nobody can satisfy it. The code that computes it ships in the commit that adds this file; the rule
moves up to `../turn-checks.md` once a session running that code has started.

**Metric it needs:** `uncovered_upgrades_available`, `min_uncovered_upgrade_cost` - computed by
`end_turn._uncovered_upgrade_metrics` from the unit list (`can_upgrade` / `upgrade_cost`), counting
only the classes `match-their-melee` and `upgrade-the-siege` do **not** watch (ranged, cavalry,
anti-cavalry; recon excluded on purpose).

**Why it exists - measured T204-T215.** The treasury went 621 -> 768 while `UPGRADE AVAILABLE`
offered a Knight -> Cuirassier at 230g and two Crossbowman -> Field Cannon at 310g each, and no rule
in the file watched those classes at all: `match-their-melee` watches melee, `upgrade-the-siege`
watches siege. At T216-T217 two of them were finally bought, at the **doubled** price created when
the free policy window of T201 traded `POLICY_PROFESSIONAL_ARMY` ("50% discount on all unit
upgrades") for `POLICY_MEDINA_QUARTER` - 540g paid where 270g would have done.

The proposed rule, in the shape `turn-checks.md` uses:

```
<!-- check
id: upgrade-the-unwatched
when: metric(at_war) >= 1 and metric(uncovered_upgrades_available) >= 1 and metric(gold) >= metric(min_uncovered_upgrade_cost) * 2
require: metric(uncovered_upgrades_available) <= 0
level: warn
message: An affordable upgrade for a ranged, cavalry or anti-cavalry unit is waiting while the war is on, and the treasury can pay for it twice over. This class has no other rule watching it - `match-their-melee` covers melee and `upgrade-the-siege` covers siege - so nothing else will say it. Measured T204-T215: 621 -> 768 gold sat while a Knight -> Cuirassier (230g) and two Crossbowman -> Field Cannon (310g each) went unbought for twelve turns, and at T216-T217 two of them were bought at double price because the T201 policy window had traded Professional Army (50% off all upgrades) for housing. Upgrade the cheapest one, or say in the diary why the gold is being kept.
-->
```

Notes for whoever cuts it in:

- The gate is `gold >= min_uncovered_upgrade_cost * 2` and not merely `gold >= cost`, so a treasury
  that can barely afford one upgrade is not nagged; the rule is about gold that is *sitting*.
- `require: ... <= 0` makes it a standing rule with the same escape hatch as `upgrade-the-siege`
  ("or say in the diary why"), because some offers are genuinely poor value - a Spearman -> Pikeman
  at 380g for a city garrison was judged exactly that at T209.
- If the two existing rules are ever generalised into one army-wide upgrade rule, this file should
  be deleted rather than cut in, so the same fact is not reported twice.
- The policy half of the same lesson is handled in code: `GameState.set_policies` now warns when a
  change drops `POLICY_PROFESSIONAL_ARMY` while upgrades are waiting, because that swap doubles
  every pending price (measured: 115 -> 230, 155 -> 310, 190 -> 380).
