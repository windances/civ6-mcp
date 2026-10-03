# `mind-the-amenities` - staged: needs a server started after the amenity-demand column

```yaml
id: mind-the-amenities
when: metric(cities_unhappy) >= 1
require: metric(amenities_floor) >= 0
message: A city is short of amenities (`amenities - amenities_needed < 0`), which cuts its growth and its yields and eventually spawns rebels. `amenities` alone says nothing - the demand scales with population, so -1 against a demand of 1 is a different city from -1 against a demand of 4, and the metric that matters is the difference. Fix the worst city this turn: a new luxury type (each new type is +1 amenity to four cities, so duplicates beyond the first are worth trading, not keeping), an Entertainment Complex or its buildings, or a policy card. Read `amenities_floor` for the worst gap and `metric(cities_unhappy)` for how many cities are short.
```

**Why it exists.** The reference orders `housing`, `food` and `amenities` checked every turn and the
amenity half was unmeasurable, because the city scan printed only the gross figure
(`amNeed + GetAmenities()`) and dropped `amNeed`, which the Lua had already computed for it.

**What is already in place** (so promoting this is a file move, nothing else):

- the city scan's Lua printed `amTotal = amNeed + g:GetAmenities()` and **already held `amNeed`**,
  so this needed one appended column, not a new scan: `.. "|" .. amNeed`;
- `CityInfo.amenities_needed` parses it at index 36, after the power block, so a log written
  before the column existed parses exactly as before;
- `end_turn._city_health_metrics` computes `amenities_floor` (the worst gap) and `cities_unhappy`;
- both names are in `end_turn._CONTACT_METRIC_KEYS`, so a stored-row pass reads 0 rather than
  `un-evaluable`.

**Why it is still staged.** The metric tuple is read at *import* time, exactly as
`answer-the-missionary` explains: a server process started before this commit still answers the
history recomputation with `un-evaluable`, which reads as a permanent streak and shifts the verdict.
This one is staged for a second reason too - the column only exists in a build that has the parser,
so a server started before it reports `amenities_needed == 0` for every city, which makes every city
look content and switches the rule off rather than firing it on a guess.

**Cut it in** with the two-file move `pending/README.md` describes, in a session whose server
started after the commit that added the column: copy this block into `../turn-checks.md`, delete
this file, and flip the staged assertion in `tests/test_city_cap_rules.py` to live.
