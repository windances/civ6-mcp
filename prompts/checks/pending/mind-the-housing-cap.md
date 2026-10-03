# `mind-the-housing-cap` - staged: needs a server started after `_city_health_metrics`

```yaml
id: mind-the-housing-cap
when: metric(cities_housing_capped) >= 1
require: metric(cities_housing_capped) <= 0
message: A city is at or over its housing cap (`housing - pop <= 1`) and nothing is being built to lift it. This is a hard stop, not a warning: a capped city's growth stops for dozens of turns, and growth is also the district plan (`districts <= floor(pop / 3)`), so a stalled city is a district slot nobody can ever use. Fix the cap in that city this turn - an Aqueduct is the cheapest large lift and the district advisor ranks the tiles for it, then Granary, Water Mill, farms, or a domestic trade route (a domestic route pays Food and Production to its destination). Read `housing_slack` for the worst city and `get_cities` for which one it is. Measured T291: Changsha at housing 11 against pop 12 with 210 turns to the next population, and the queue was empty.
```

**Why it exists.** The reference already calls `housing - pop <= 1` a hard stop, and nothing
measured it: the empire warnings cover `food_surplus < 0` and slow growth, but a city can sit at
`housing - pop == 0` with a positive food surplus and never be mentioned.

**What is already in place** (so promoting this is a file move, nothing else):

- `CityInfo.housing`, `.population`, `.food_surplus` and `.turns_to_grow` all ride in on the
  existing city scan, so no new Lua and no extra round trip;
- `end_turn._city_health_metrics` computes `housing_slack` (the worst city's `housing - pop`, so
  the report names a number to close) and `cities_housing_capped`;
- both names are in `end_turn._CONTACT_METRIC_KEYS`, so a stored-row pass reads 0 rather than
  `un-evaluable`.

**Why it is still staged.** The metric tuple is read at *import* time, exactly as
`answer-the-missionary` explains: a server process started before this commit still answers the
history recomputation with `un-evaluable`, which reads as a permanent streak and shifts the verdict.

**Cut it in** with the two-file move `pending/README.md` describes, in a session whose server
started after the commit that added `_city_health_metrics`: copy this block into `../turn-checks.md`,
delete this file, and flip the staged assertion in `tests/test_city_cap_rules.py` to live.
