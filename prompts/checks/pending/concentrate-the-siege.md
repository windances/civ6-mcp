# `concentrate-the-siege` - staged: needs a server started after the metric shipped

```yaml
id: concentrate-the-siege
level: error
when: metric(siege_firing_alone) >= 1
require: metric(siege_firing_alone) == 0
```

**Why it exists.** The directive counts **units**; what takes a city is **shots**, and until now
nothing in the rule file could tell the two apart - `siege-train` counts how many Catapults we own and
`SIEGE FIRE: n/m` prints how many can reach the target, but no rule read that second number.

**Measured in A6, which is the case this rule is for.** A6 arrived with a **complete** establishment
(`siege 2, melee 2, anticav 1, ranged 4, cavalry 1, recon 1`) and a Catapult **bought with gold**, and
its target finished the window at **`200/200` - not one point of net damage** - because the log reads
**`SIEGE FIRE: 1/2`**: one gun in range, and the supply line never passed `2/6 cut`. A siege unit does
**45-52** against a city where an Archer does 9-11 into a CS 35 garrison, and a city heals about
**twenty a turn** while any adjacent hex is outside our zone of control - so **two guns out-damage the
heal and one does not**, which is `tactics/07`'s gate 1 ("net fire > 0, computed against the garrison")
and `tactics/06`'s concentration in the one form the board can be asked for. The same gap was written
into `end_turn`'s own comment at the `SIEGE FIRE` line: *"the '3 Catapults' the directive counts is a
count of units, not of shots, and nothing said so."*

**What is already in place** (so promoting this is a file move, nothing else):

- `end_turn._siege_metrics` computes `siege_firing_alone` from the same posture list that prints
  `SIEGE FIRE: n/m`. It is **1** exactly when a train is deployed (`siege_units >= 1`) and only one of
  its guns is inside range 2 (`siege_in_city_range == 1`), and **0** while the train is still marching
  in (nothing in range), when two or more guns are in position, and when we own no siege units at all -
  so it cannot fire during staging or in a war we have not brought a train to;
- the metric is in `end_turn._CONTACT_METRIC_KEYS`, so a **stored diary row reads 0** rather than
  `un-evaluable`;
- `tests/test_war_footing.py::TestSiegePosture` pins all four states - one gun in range, two in range,
  three units with one shot, and a train still staging - and pins that the key is in the tuple above.

**Why it is still staged.** The metric is new, and `_CONTACT_METRIC_KEYS` is read at **import** time: a
server whose process started before this commit answers a row-based pass - the history recomputation and
the TURN START briefing - with `un-evaluable`, which reads as a permanent streak and shifts the verdict.
That is the trap that took `attacks-that-land-nothing` and `power-the-cities` in and out of the live file
on 2026-09-28.

**It is also deliberately not cut in while an attempt is being measured.** `rules_red` is one of the
experiment's own metrics (`scripts/experiment-report.py` counts the red rule-turns per attempt), so a
rule added inside an attempt's window changes what that count means for the attempt it is added to. A
rule that only *adds* a failure mode does not disturb the rules already firing, which is why this is a
timing rule and not a correctness one - but the count is the count.

**Cut it in** with the two-file move `pending/README.md` describes, in a session whose server started
after the commit that added `siege_firing_alone` to `end_turn._CONTACT_METRIC_KEYS`: copy the rule block
above into `../turn-checks.md`, delete this file, and flip `tests/test_war_footing.py`'s staged
assertion to live. On that server the metric reads the real count, so the rule fires the first turn a
train is deployed with a single gun in range - which is the state A6 sat in for its whole window.
