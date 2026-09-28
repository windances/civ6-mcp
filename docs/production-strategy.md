# The production-development strategy for the 028 window (T288-T317)

`028-development-science-wonders.md` is in force until **T317** and its `done when:` is the objective:
the **Spaceport standing in 西安**, the **first space project under way** with its remaining turns in
the diary, **at least one wonder completed inside the window** with the Eureka and Inspiration it
granted written down, **every missing Research Lab and University finished**, and the ledger - no war
started by us. So "production" here is not a general goal: it is **one city's hammers** (the Spaceport
and then four projects) plus **science per turn** (the techs that unlock them). Everything below is
ranked by measured size, and every number comes from `docs/production-speed.md`, which cites the game's
own data files.

Read first: `get_cities` (西安's production, its districts, the amenity column), `get_trade_routes` +
`get_trade_destinations`, `get_policies`, `get_great_people`, `get_city_states`, `get_wonder_advisor`.
Nothing below should be executed from assumption.

## 1. The biggest lever is free: re-target the domestic trade routes

A domestic route gives its **destination** +1 production **per qualifying district** in that city -
City Center, Encampment, Harbor, Commercial Hub, Industrial Zone, Hansa, Royal Navy Dockyard
(`District_TradeRouteYields`, `Base\Assets\Gameplay\Data\Districts.xml:159-180`). The match has **12
routes, 8 of them domestic**. If the space factory holds five of those district types, packing all
eight domestic routes into it is **+40 production per turn in one city** - more than any building in
the game, for the price of eight `teleport`/`trade_route` orders. Read the current destinations first;
routes pointing anywhere else are production left on the table.

Two follow-ons: domestic routes also carry **food** (more citizens on production tiles), and every
Market/Lighthouse adds capacity - the next capacity point is another route to the same city.

## 2. The ranked levers at the space factory

| # | lever | measured value |
|---|---|---|
| 1 | **Coal or Fossil Fuel Power Plant** | **+1 production per citizen** (`Expansion2_Buildings.xml:409,412`) - a pop-15 city gets +15. The largest flat building in the game |
| 2 | **Power the city** | an unpowered city loses the power-only rows - Factory **+3**, Electronics Factory **+5**, Airport **+2** (`Expansion2_Buildings.xml:394-404`) - under a **-50%** cap (`Expansion2_GlobalParameters.xml:224`). 煤 70 in stock, so this is a queue question, not a resource one |
| 3 | **Industrial Zone adjacency, doubled** | +1 per adjacent Mine and Quarry, +1 per 2 districts, +1 per 2 Mines, +1 per 2 Lumber Mills, **+2 Aqueduct/Bath/Canal/Dam**, +1 strategic resource (`Districts.xml:232-234`; `Expansion2_Districts.xml:83-89`). **Five-Year Plan (+100%) is already slotted**; Craftsmen is the same +100% (`Policies.xml:1613,1961`) - check whether a slot allows both |
| 4 | **Industrial Zone specialists** | **+2 production each** (`Districts.xml:192`) - a better use of a citizen than a 1-production tile |
| 5 | **Magnus: Industrialist +2 per power plant, and Vertical Integration** | Vertical Integration makes the city receive **every** nearby Industrial Zone regional building, not just the first (`Expansion1_Governors.xml:671-672,1038-1040`). Magnus is in 底比斯 - moving him costs the re-establishment turns, so compare against the gain |
| 6 | **Governors: Liang for the district, Pingala for the projects** | Liang/Zoning Commissioner **+20% districts** (`Expansion1_Governors.xml:1065`); Pingala/Space Initiative **+30% space projects** (`:1180`). Pingala is already in the city; the Spaceport is a *district*, so Liang's +20% applies while it builds and Pingala's +30% applies to the four projects after it |
| 7 | **Ruhr Valley, if it is still unbuilt** | **+20% production in its own city and +1 per Mine and Quarry there** (`Buildings.xml:1005-1012,851-853,1445-1452`) - the production wonder, and it belongs in the space factory. Kilwa Kisiwani (+15%, +15% more empire-wide at ≥2 suzerainties of a type) and Amundsen-Scott (+10% all cities) are the runners-up |
| 8 | **Great People as free production** | **Carl Sagan 3000** and **Korolev 1500** toward space-race projects; Eiffel 480, Brunelleschi 315 (wonders only, and **`KeepOverflow=false`** - the excess is discarded) (`GreatPeople_Scientists.xml:712-718`; `GreatPeople_Engineers.xml:297-303,378-384`). **Faith is 2502 and banked** - `get_great_people`, then `patronize_great_person`. This is the cheapest way to buy a project |
| 9 | **Royal Society, if we have it** (`BUILDING_GOV_SCIENCE`) | builders spend charges to add production to a district **project** (`Expansion1_Buildings.xml:317,621`); the adapter exposes it as `UNITCOMMAND_PROJECT_PRODUCTION` (`src/civ_mcp/lua/units.py:2083`). With 19+ builders this is a burst |
| 10 | **Amenities: the empire-wide multiplier** | GS **Happy +10%**, **Ecstatic +20%** on all non-food yields, and -10/-20/-30/-40% below Content (`Expansion2_Buildings.xml:463-515`). Moving 27 cities from Content to Happy is +10% production *and* science on everything, and it costs Zoos, Arenas and luxuries rather than hammers |
| 11 | **District costs rise with tech progress** | `COST_PROGRESSION_NUM_UNDER_AVG_PLUS_TECH`, param 40 (`Districts.xml:44-52`). Any district we already know we want (Neighborhoods, more Industrial Zones, a Water Park) is **cheaper queued now** than in twenty turns; no building or wonder has this clock |

## 3. What not to spend production on (measured, not opinion)

- **Chops into the Spaceport.** Woods +20, Rainforest +10, Marsh 20 food and no production
  (`Features.xml:186-189`), with **no scaling** anywhere in the data. A chop is ~1% of an 1800-cost
  Spaceport. Chops are for early items, and only worth it with **Magnus/Groundbreaker +50%**
  (`Expansion1_Governors.xml:635-636`).
- **Units.** 028 caps the window at development; the directive calls a large army pure cost
  (`directive.md:301-305`). Military is 1255 and gold/turn has fallen to about +29.6 - the directive's
  floor is **+10 with the army counted** (`directive.md:374`). Check the maintenance line before any
  new unit, and remember **no war inside this window**.
- **Expansion.** 27 cities against the directive's four-to-six (`directive.md:271`), and 028 caps it.
  No Settlers.
- **Districts in low-production cities for their own sake.** A district in a 5-hammer city is a
  40-turn item; the compounding rule is growth first, then the Campus line
  (`directive.md:289-292`), and that line is nearly closed - finish the **Research Labs and
  Universities** and stop.
- **Non-production policies when a production card fits.** Read `get_policies`: Five-Year Plan and
  Craftsmen are +100% Industrial Zone adjacency, and each of those adjacency points is worth more than
  a flat +1. The military cards (Praetorium, Conscription) earn their slots only while a war is live.

## 4. The plan, by phase

| phase | turns | work |
|---|---|---|
| **Measure and re-route** | T288-T290 | `get_trade_routes` + `get_trade_destinations`; move every domestic route to the space factory; `get_cities` for its production, power state and amenity band; `get_great_people` for a space-project Great Person and patronize with the 2502 faith if one is there |
| **Power and the wonder line** | T288-T295 | a Coal/Fossil Fuel Plant wherever a Factory sits unpowered (the `城市供电不足` notices); Oxford University continues (the window's wonder; China gets a Eureka **and** an Inspiration from it - `directive.md:306-309`); Ruhr Valley decision via `get_wonder_advisor`; **Research Labs and Universities finished** |
| **The Spaceport** | ~T288-T305 | it read **19 turns** at T286; Liang into the city while it builds (+20% districts), Pingala back for the projects (+30%) |
| **First project** | T305-T317 | the Earth Satellite (**900**) starts the turn the Spaceport lands - 028's `done when:` - and the ledger records its remaining turns. This is the phase where **Eiffel/Sagan/Korolev charges and the Royal Society builders** are spent, because a project takes them and a district does not |

## 5. The three numbers to re-read every five turns

1. **The space factory's production per turn** - it alone sets the space chain's finish date. If it is
   not rising, the trade routes are still pointed somewhere else.
2. **Domestic routes into that city × the qualifying districts it has** - the free production from
   section 1, and the first thing to check when the Spaceport's turn count stalls.
3. **How many cities sit below Content** - each band is -10%, -20%, -30% or -40% on all non-food
   yields, empire-wide (`Expansion2_Buildings.xml:463-515`), and it is the only multiplier in this list
   that is bought with food and luxuries rather than production.

## Sources

- `docs/production-speed.md` - the full factor list with `path:line` citations into the installed game
  data, plus what the data does **not** say (no overflow parameter, no chop scaling, no starvation or
  housing production effect).
- `prompts/tasks/tmp/028-development-science-wonders.md` - the objective this plan serves, and the
  window's own finish line.
- `prompts/strategies/china-conquest/directive.md` - the compounding rules, the army budget and the
  "for China a wonder is a research building" ability.
