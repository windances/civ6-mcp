# `repair-the-pillaged-district` - staged: needs a server started after `_city_health_metrics`

```yaml
id: repair-the-pillaged-district
when: metric(cities_pillaged) >= 1
require: metric(pillaged_districts) + metric(pillaged_buildings) <= 0
message: A district or a building is standing pillaged and nothing has been queued to repair it. Pillaged is not cosmetic - a pillaged Industrial Zone, Workshop, Factory or Power Plant is a power and production penalty across the whole empire, not one city's problem, and every turn it stands is a turn the empire produces less than it should. Queue the repair in that city's production **before** anything new (`set_city_production` with the `REPAIRS:` entry from `get_city_production`; a pillaged *building* is repaired from the build queue, a pillaged *improvement* needs a builder's `repair`). Measured T291: Xi'an - 16 pop, the science city and the empire's largest single source of research - sat on a pillaged Industrial Zone with a pillaged Workshop, Factory and Coal Power Plant while the power-shortage warning fired four times and the queue held a project.
```

**Why it exists.** The directive's Development section orders the four city checks (housing, food,
amenities, pillaged districts) before any production choice, and until now a rule could name `pop`
and `cities` and nothing else about a city at all. `unpowered_cities` could see the *symptom* of
the T291 waste - the power shortage - and nothing could see the cause.

**What is already in place** (so promoting this is a file move, nothing else):

- `CityInfo` has carried `pillaged_districts` and `pillaged_buildings` since the city scan gained
  them, so the data needed no new Lua and no extra round trip;
- `end_turn._city_health_metrics` reads them off the same `_last_snapshot` `_garrison_metrics`
  uses and computes `pillaged_districts`, `pillaged_buildings` and `cities_pillaged`;
- all three names are in `end_turn._CONTACT_METRIC_KEYS`, so a stored-row pass reads 0 rather than
  `un-evaluable`.

**Why it is still staged.** The metric tuple is read at *import* time, exactly as
`answer-the-missionary` explains: a server process started before this commit still answers the
history recomputation with `un-evaluable`, which reads as a permanent streak and shifts the verdict.

**Cut it in** with the two-file move `pending/README.md` describes, in a session whose server
started after the commit that added `_city_health_metrics`: copy this block into `../turn-checks.md`,
delete this file, and flip the staged assertion in `tests/test_city_cap_rules.py` to live.
