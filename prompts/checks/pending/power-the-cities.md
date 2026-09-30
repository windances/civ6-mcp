# `power-the-cities` - staged: needs a server started after the row-context tuple gained the metric

```yaml
id: power-the-cities
level: error
when: metric(unpowered_cities) >= 1
require: metric(unpowered_cities) == 0
message: A city is not fully powered, so every building that needs power runs at reduced strength - Research Lab, Stock Exchange, Broadcast Center and Film Studio need 3 power each, Factory and Stadium 2, Food Market and Shopping Mall 1. Power comes from a Coal or Oil Power Plant (1 resource into 4 Power) or a Nuclear Power Plant (1 Uranium into 16), and each plant serves every city within 6 tiles that needs power, so this is a coverage question and not a per-city one. The free sources are the Hydroelectric Dam (+6), the Geothermal Plant (+4) and the Solar, Wind and Offshore Wind Farms (+2 each). Build or buy a plant that covers the city, or trade for the resource it burns.
```

**Why it exists.** Power is the one city fact that decided whether a building was working and that
nothing in this toolkit could see: it lives on the city banner (`LOC_CITY_BANNER_UNPOWERED_CITY`) and in
the city panel, and no MCP tool, no turn block and no rule mentioned it. What it costs when it is
missing is measured in the game's own data (`DLC/Expansion2/Data/Expansion2_Buildings.xml`,
`Building_RequiredPower`): **Research Lab 3, Stock Exchange 3, Broadcast Center 3, Film Studio 3,
Factory 2, Stadium 2, Aquatics Center 2, Food Market 1, Shopping Mall 1, Airport 1** - and an unpowered
city runs every one of them at reduced strength. A city is either fully powered or it is not; there is no
partial state to average.

The sources, from the same data and its text (`Expansion2_Buildings_Text.xml`,
`Expansion2_Improvements.xml`, `LOC_PEDIA_CONCEPTS_PAGE_POWER_*`): a **Coal Power Plant converts 1 Coal
into 4 Power**, an **Oil Power Plant 1 Oil into 4**, a **Nuclear Power Plant 1 Uranium into 16** - and
each plant serves every city **within 6 tiles** that needs power, which makes plants a coverage question
rather than a per-city one. The free sources are `MODIFIER_SINGLE_CITY_ADJUST_FREE_POWER`:
**Hydroelectric Dam +6**, **Geothermal Plant +4**, **Solar Farm, Wind Farm and Offshore Wind Farm +2
each**, and the Merchant governor's `RENEWABLE_ENERGY` promotion adds **+2** to each of those in its city.

**What is already in place** (so promoting this is a file move, nothing else):

- `build_cities_query` reads `City:GetPower()` - `GetRequiredPower()`, `GetFreePower()`,
  `GetTemporaryPower()`, `IsFullyPowered()`, `GetPowerAdvice()` - the same table the game's own
  `CityPanelPower.lua` reads, and `CityInfo` carries it (`power_required`, `power_free`,
  `power_temporary`, `power_fully_powered`, `power_advice`) with `unpowered` / `power_available` /
  `power_reported` as the readings;
- `narrate_cities` prints `Power available/required` on the city line and a `!! UNPOWERED` line with the
  game's own advice when it is short;
- the loyalty scan carries it too (`CITY_LOYALTY|...|power_req:N|power_free:N|power_temp:N|powered:yes`),
  so `unpowered_cities` costs **no extra round trip** - `_loyalty_metrics` counts it from the rows it
  already has, and `unpowered_power_gap` is the worst city's shortfall in power;
- the per-turn diary row carries `power_required`, `power_available` and `powered`, so the history of a
  city's power is readable after the fact;
- `end_turn`'s live metric block exposes both metrics, and `_CONTACT_METRIC_KEYS` includes them so a
  **stored-row** context reads 0 rather than `un-evaluable`.

**Why it is still staged.** That last item is read at *import* time. A server whose process started
before the tuple change still answers a row-based pass - the history recomputation and the TURN START
briefing - with `un-evaluable`, which reads as a permanent streak and shifts the verdict. The same trap
took `attacks-that-land-nothing` in and out of the live file on 2026-09-28.

**Cut it in** with the two-file move `pending/README.md` describes, in a session whose server started
after the commit that added `unpowered_cities` to `end_turn._CONTACT_METRIC_KEYS`: copy this rule block
into `../turn-checks.md`, delete this file, and flip `tests/test_city_power.py`'s assertion from staged
to live. On a corrected server the metric reads the real count, so the rule is the thing that stops an
unpowered city from sitting unnoticed for fifty turns of a science push - which is exactly what the
development task (028) is doing when the load goes up.
