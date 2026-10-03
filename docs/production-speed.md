# What decides how fast a city builds something

Two authorities answer this, and they answer different halves of it. The **manual** explains the
mechanic a player manipulates (whose citizens work what, what happiness does to yields, what gold
buys). The **game's own data files** decide every number the manual never prints - policy cards,
governors, city-state bonuses, power, loyalty, the scaling of district costs. Where the two disagree,
**the data files win**: this install is Gathering Storm, and GS rewrites the happiness table
(`DLC\Expansion2\Data\Expansion2_Buildings.xml:463-515`), so the manual's +5%/+10% for happy and
ecstatic cities is not the number the game uses.

Paths below are relative to the game root
(`D:\SteamLibrary\steamapps\common\Sid Meier's Civilization VI`); `manual:NNN` is a line in the
extracted manual, `.tools/manuals/manual.clean.txt` (its text extraction lost some characters, so only
intact sentences are quoted).

## 1. The arithmetic

A city accumulates production toward one item at a time:

- a unit has "a certain **Production Cost** which determines how many units of Production a city must
  expend to produce the unit" (`manual:679`) - plus a technology, and for some units a resource;
- the production menu shows "**the number of turns required to complete construction**"
  (`manual:1295-1297`).

So **turns to complete = (cost - already accumulated) / production per turn**. Leftover production
rolls into the next item, and **gold or faith purchase constructs the item immediately**
(`manual:2111`, `manual:1275`, `manual:1279`). Everything below moves one of those terms or bypasses the
quotient.

Two honest caveats about the quotient itself: **no data file defines overflow** - there is no
`PRODUCTION_OVERFLOW`/carry-over row in any `GlobalParameters` file, and no minimum-turns row either
(the only `*_MIN_TURNS` rows are the 10-turn diplomacy ones); both are engine-side. And **the cost term
is not a constant**: district costs are the one item class whose price grows with your progress
(section 3).

## 2. What the manual states outright

| factor | what the manual says | source |
|---|---|---|
| worked tiles | "Their citizens **work** the land, harvesting food, wealth, **production**, and science from the tiles"; a tile must be within three tiles of the city and inside your borders, and only one city can work it | `manual:1401` |
| terrain, resources, improvements | "City Yield: ... how much food, gold, or **productivity** a nearby city can acquire from an **unimproved** tile"; resources "are the source of food, **Production**, or gold"; a Lumber Mill "provide[s] extra Production" | `manual:463`, `459`, `1783` |
| which tiles are worked | automatic assignment "seeks to provide a balanced amount of food, production, and wealth"; you may instead demand "**on production** or gold", through the Manage Citizens lens or the city-yield bar's radial focus buttons | `manual:1403`, `1495-1497`, `1283-1287` |
| specialists cost you | a citizen moved off a tile into a district means "whatever they were producing will be **lost**" | `manual:1447` |
| unemployed citizens | neither on a tile nor a specialist: "still provide **1 gold** ... but consume as much food" - no production | `manual:1451-1453` |
| **amenities (happiness)** | content = no modifier; happy = +5% yields, +10% growth; ecstatic = +10% yields, +20% growth; too few = negative modifiers; unrest stops growth and spawns partisans. **Superseded by GS - see section 6** | `manual:1255` |
| amenity sources | luxuries (up to 4 amenities each, era-dependent reach), Arena/Zoo/Stadium, some wonders, beliefs, policies | `manual:1257`, `2145` |
| negative amenities | **war weariness** (worse in later eras; losing units compounds it) and a negative treasury: "a penalty to your Amenities per every 10 Gold you drop below 0", plus disbanding units | `manual:2155`, `2139` |
| purchase instead of production | gold buys units and buildings outright; certain beliefs allow faith purchases | `manual:2111`, `1279`, `1299` |
| contamination | "**Production cannot be applied** to anything in tiles containing contamination ... Tiles that are contaminated **cannot be worked**" | `manual:2497` |
| settlers | require a city of size 2+, and cost that city one population | `manual:1541` |

The manual never names a policy card, governor, city-state bonus, belief, wonder, power, loyalty or
the district cost scaling; it describes Trade Routes as a gold mechanic only (`manual:2091-2093`). All
of that is section 3 onward.

## 3. Production cost - the term that moves on its own

**District costs scale with progress.** Districts carry `CostProgressionModel` /
`CostProgressionParam1` (`Base\Assets\Gameplay\Data\Districts.xml:44-63`):

| model | districts | source |
|---|---|---|
| `COST_PROGRESSION_NUM_UNDER_AVG_PLUS_TECH`, param **40** (base cost 54) | Holy Site, Campus, Encampment, Harbor, Aerodrome, Commercial Hub, Entertainment Complex, Theater Square, Industrial Zone | `Districts.xml:44-52` |
| same model, param 40, base 27 | Acropolis, Hansa, Lavra, Street Carnival, Royal Navy Dockyard; Ikanda, Seowon, Cothon, Suguba | `Districts.xml:57-63`; `DLC\Expansion1\Data\Expansion1_Districts_Major.xml:9,10`; `DLC\Expansion2\Data\Expansion2_Districts_Major.xml:12,13` |
| param **25** (base 30) | Government Plaza; Diplomatic Quarter | `DLC\Expansion1\Data\Expansion1_Districts.xml:19`; `DLC\Ethiopia\Data\Ethiopia_Districts.xml:7` |
| `COST_PROGRESSION_GAME_PROGRESS`, param 1000 | Neighborhood (54), Aqueduct (36), Bath (18), Mbanza (27), Canal and Dam (81) | `Districts.xml:53,54,58,61`; `DLC\Expansion2\Data\Expansion2_Districts.xml:15,16` |
| none | City Center (54), Spaceport (1800) | `Districts.xml:43,55` |

The scaling maths is engine-side; the token and its parameter are what the data states. **No building
or wonder carries a cost-progression column** in any of the five buildings files - so a district built
late costs far more than the same district built early, and nothing else does.

Other cost-side rules:

- **Occupation**: production **-50%** in an occupied city (`Yields.xml:65-70`; gold -50%, science/
  culture/faith -75%, food 0) and growth is zero (`GlobalParameters.xml:84`); occupation is not
  permanent (`:136`). R&F and GS add loyalty pressure instead
  (`DLC\Expansion1\Data\Expansion1_GlobalParameters.xml:80,82`).
- **Game speed scales every cost**: Marathon 300 / Epic 150 / Standard 100 / Quick 67 / Online 50
  (`Base\Assets\Gameplay\Data\GameSpeeds.xml:22,31,40,49,58`).
- **Repairing a pillaged building costs 25% of its original production** (`GlobalParameters.xml:420`),
  and the repair is itself a production item.
- **A resource floor can forbid the item outright**: 2 of the strategic resource to produce it
  anywhere, 1 if you have the right district (`GlobalParameters.xml:551,553`).
- **Upgrades**: `UPGRADE_NET_PRODUCTION_PERCENT_COST` is 75 in the base data, overridden to **100** by
  GS (`GlobalParameters.xml:615`; `DLC\Expansion2\Data\Expansion2_GlobalParameters.xml:288`).
- **Corps and Armies** cost 1.5x and 2.0x the unit (`GlobalParameters.xml:601,603`).

## 4. Production yield, flat - where the hammers actually come from

| source | value | file:line |
|---|---|---|
| city centre tile | production floor **1** (`YIELD_PRODUCTION_CITY_TERRAIN_REPLACE`) | `GlobalParameters.xml:663` |
| terrain | Plains +1, Plains Hills +2, other Hills +1 | `Terrains.xml:64-69` |
| features | Forest +1; Reef +1 (R&F) | `Features.xml:157`; `DLC\Expansion1\Data\Expansion1_Features.xml:13` |
| improvements | Mine +1, Quarry +1, Pasture +1, Lumber Mill +1, Oil Well +2, Offshore Oil Rig +2 | `Improvements.xml:312,314,318,324,325,326` |
| improvement tech upgrades | Mine +1 Apprenticeship, +1 Industrialization; Lumber Mill +1 Steel, +1 adjacent to a River; Camp +1 Mercantilism; Pasture +1 Robotics; Quarry +1 Rocketry (GS adds Gunpowder, Smart Materials, Cybernetics, Predictive Systems rows) | `Improvements.xml:352-360,453-456,565-573`; `DLC\Expansion2\Data\Expansion2_Improvements.xml:270-287` |
| resources on the tile | Oil +3, Coal +2, Uranium +2, Stone/Gypsum/Ivory/Whales/Deer/Horses/Niter +1 | `Resources.xml:385-431` |
| buildings (GS values) | Workshop 3, Factory 3, Electronics Factory 3, Power Plant 4 (+3 science), Armory 3, Military Academy 4, Airport 4 | `DLC\Expansion2\Data\Expansion2_Buildings.xml:319,325,330,334,340,346,358,389` |
| **power adds yield** | `Building_YieldChangesBonusWithPower`: Factory +3, Electronics Factory +5, Airport +2 - exactly what an unpowered city loses | `Expansion2_Buildings.xml:394-404` |
| power plants | Coal Power Plant **+1 per citizen**; Fossil Fuel and ordinary Power Plant likewise | `Expansion2_Buildings.xml:409,412,417` |
| specialist (Industrial Zone) | +2 production per specialist | `Districts.xml:192` |
| Industrial Zone adjacency | +1 per adjacent Mine, +1 per Quarry, +1 per 2 adjacent districts; GS adds +1 per 2 Mines, +1 per 2 Lumber Mills, +2 Aqueduct/Bath/Canal/Dam, +1 strategic resource | `Districts.xml:232-234,90-92`; `DLC\Expansion2\Data\Expansion2_Districts.xml:83-89,63-69` |
| domestic trade route **destination** | +1 production per City Center, Encampment, Harbor, Commercial Hub, Industrial Zone, Hansa or Dockyard in the destination | `Districts.xml:159-180`; `DLC\Expansion1\Data\Expansion1_Districts.xml:62` |
| beliefs (GS) | Lady of the Reeds and Marshes +2 Marsh/Oasis/Desert Floodplains; God of the Sea +1 Fishing Boats; God of Craftsmen +1 production and +1 faith from improved strategic resources; Goddess of the Hunt +1 Camps | `Expansion2_Beliefs.xml:495-503,665-677,655-662` |
| governments | Autocracy +1 to **all** yields in cities with the Palace and each government building; Communism (GS) **+0.6 production per citizen** in cities with a Governor | `Expansion1_Governments.xml:121-138,312-327`; `:189-191,341-347` |
| governors | Magnus/Industrialist +2 per Coal, Oil or Nuclear Power Plant; Magnus/Vertical Integration - the city receives the regional effect of **all** nearby Industrial Zone buildings, not just the first | `Expansion1_Governors.xml:655-664,990-1030`; `:671-672,1038-1040` |
| wonders | Ruhr Valley +1 per Mine and Quarry in the city; Chichen Itza +1 per Rainforest tile; Petra +1 per non-floodplain Desert tile; St. Basil's +1 per Tundra; Etemenanki, Huey Teocalli and Machu Picchu variants | `Buildings.xml:851-853,836-838,846-848,1445-1452`; `DLC\Expansion1\Data\Expansion1_Buildings_Major.xml:612-624` |
| Great People | James Watt: Factories +2 production, permanent and empire-wide; Nikola Tesla: the district's regional buildings +2 | `GreatPeople_Engineers.xml:318-328,149`; `:343-348,167` |
| city-state suzerain | Auckland +1 shallow water (+1 more from the Industrial era); Johannesburg +1 per improved resource type (+2 after Industrialization); Singapore +2 per foreign civ with a trade route | `DLC\VikingsLandmarks\Data\VikingsLandmarks_CityStates.xml:234-253`; `DLC\Babylon\Data\Babylon_Leaders.xml:256-280`; `DLC\GranColombia_Maya\Data\GranColombia_Maya_Leaders.xml:467-476` |

## 5. Production yield, percentage - the multipliers

Every modifier whose target is a class of unit/building/district/project is a **percentage on the
production needed**; the `Amount` is the number.

**Policy cards** (`Base\Assets\Gameplay\Data\Policies.xml`): Agoge +50% Ancient/Classical melee,
anti-cavalry and ranged (`:1264-1354`); Maneuver +50% the same-era cavalry (`:2713-2767`); Feudal
Contract, Chivalry, Grande Armée, Military First and Lightning Warfare +50% for their era or class;
Corvée +15% Ancient/Classical wonders (`:1588-1603`); Gothic Architecture +15% Ancient-to-Renaissance
wonders (`:1988-2003`); Skyscrapers +15% all wonders (`:3680-3695`); **Craftsmen and Five-Year Plan
+100% Industrial Zone adjacency** (`:1613`, `:1961`; R&F's Collectivism
`Expansion1_Policies.xml:1353`); Ilkum +30% Builders (`:2236`); Colonization +50% Settlers (`:1573`);
Limes +100% Walls/Castle/Star Fort (`:2576-2596`); Veterancy +30% Encampment and, under GS, Harbor
(`:4052-4062`; `Expansion2_Policies.xml:1249,1259`); Maritime Industries +100% early naval
(`:2785-2875`); Integrated Space Cell +15% Space Race projects (`:2256`); **Urban Planning +1 flat
production in all cities** (`:4042`). R&F/GS additions worth knowing: Robber Barons (Dark Age) **+25%
in cities with a Factory** (`Expansion1_Policies.xml:1293-1298`); Colonial Taxes +10% in cities off
your capital's continent (`:562`); Automated Workforce +20% all city projects
(`Expansion2_Policies.xml:993`); Flower Power **-100% production of every unit except Rock Bands**
(`:958`).

**Governments - plenary bonuses**: Autocracy +10% wonders (`Expansion1_Governments.xml:230-236`);
Merchant Republic +15% districts (`:280-286`); Fascism +50% units (`:290-296`); Corporate
Libertarianism - a Commercial Hub and an Encampment each give +10% (`Expansion2_Governments.xml:363-379`);
Synthetic Technocracy +30% city projects (`:424`); Democracy - a trade route to an Ally or Suzerain
gives **+4 production to both cities** (`:177-202,273-339`).

**Governor promotions**: Liang/Zoning Commissioner **+20% districts** (`Expansion1_Governors.xml:1065`);
Pingala/Space Initiative +30% space projects (`:1180`); Victor/Arms Race Proponent +30% nuclear
projects (`:1145-1175`); Ibrahim/Pasha +20% military units (`Expansion2_Governors.xml:107`). Liang's
R&F-only Infrastructure and Amusement promotions are **not reachable under GS** - the R&F file that
defines them does not load.

**Beliefs**: God of the Forge +25% Ancient/Classical units (`Beliefs.xml:1096-1108`); City Patron
Goddess +25% districts in a city with no specialty district (`:1690-1693`); Monument to the Gods +15%
early wonders (`:876-893`); **Work Ethic under GS mirrors the Holy Site's Faith adjacency as
production** (`Expansion2_Beliefs.xml:831-839`; the base "+1% per citizen" version is deleted by
`Expansion2_RemoveData.xml:651`).

**City-state envoy bonuses are the Ethiopia pack's version** - that pack deletes and replaces the base
and R&F rows (`DLC\Ethiopia\Data\Ethiopia_RemoveData.xml:17-25,40-48`): **Industrial** 1 envoy +1
production toward wonders, buildings and districts in the Capital and in cities with a Workshop, 3
envoys +2 (with a Factory or Consulate, +4 with both), 6 envoys +3 (Chancery or Power Plant, +6 with
both) (`Ethiopia_Buildings.xml:1519-1626`); **Militaristic** the same ladder for **units**, keyed on
Barracks/Stable, Armory and Military Academy (`:1453-1505`). **Suzerain**: Brussels **+15% wonders**
(`Leaders.xml:4685-4690`), Hong Kong +20% city projects (`:4835-4840`), Mexico City +3 tiles of
regional range (`Expansion2_Leaders.xml:1146`) - Toronto no longer exists under GS.

**Wonders**: **Ruhr Valley +20% production in its own city** (`Buildings.xml:1005-1012`);
Amundsen-Scott +10% all cities, +20% with 5 Snow/Snow-Hills tiles
(`Expansion1_Buildings_Major.xml:376-399`); Kilwa Kisiwani +15% units and/or buildings-and-districts
per matching suzerainty (`:482-550`); Casa de Contratación +15% in off-continent cities with a Governor
(`:427-434`); Statue of Zeus +50% anti-cavalry
(`DLC\Byzantium_Gaul\Data\Byzantium_Gaul_Buildings.xml:79-93`). **Venetian Arsenal has no production
modifier** - it grants a second naval unit (`Buildings.xml:1667-1678`).

**Dedications** (Golden Age; the table is `Expansion1_Moments.xml`, not `Eras.xml`): To Arms! +15%
military units (`:964-966`); Heartbeat of Steam +10% Industrial-and-later wonders **and** the Campus's
Science adjacency mirrored as production (`:899-932`). The other dedications have no production effect.

**Great People**: Goddard +20% space projects; von Braun and Kwolek +100% space projects; Nimitz +20%
naval raiders; Eisenhower +5% units as a retirement. **World Congress**: Mercenary Companies +/-100%
and -50% to the cost of producing or buying military units; Public Works Program +/-100% a project;
Urban Development Treaty +100% buildings; the International Space Station emergency +40%/+20% space.

**Civ traits**: Aztec +100% Builders (`Civilizations.xml:800-807`); France +20% Medieval-Industrial
wonders (`:1827-1844`); Spain +25% districts off the capital's continent (`:1687-1689`) and +2
production on intercontinental trade routes (`:1657-1684`); Scotland +5% production in Happy cities and
+10% in Ecstatic (`Expansion1_Civilizations_Major.xml:18,100,141`).

## 6. Conditions that reduce production

| condition | value | source |
|---|---|---|
| **amenities (GS table)** | Revolt **-40%**, Unrest **-30%**, Unhappy **-20%**, Displeased **-10%**, Content 0, Happy **+10%**, Ecstatic **+20%** - applied to all **non-food** yields, production included; the bands shift to Content 0-2 amenities, Happy 3-4, Ecstatic 5+ | `DLC\Expansion2\Data\Expansion2_Buildings.xml:463-515` |
| amenities (base/R&F, for reference) | Revolt -60, Unrest -30, Unhappy -10, Displeased -5, Content 0, Happy +5, Ecstatic +10 | `Base\Assets\Gameplay\Data\Happinesses.xml:17-23` |
| amenity plumbing | 1 amenity per 2 population; GS removes the free amenity; luxuries fade by era | `GlobalParameters.xml:104,72`; `Expansion2_GlobalParameters.xml:46`; `:360,362` |
| **loyalty** | city yields **-100%** at loyalty 0-25, **-50%** at 26-50, **-25%** at 51-75, none at 76-100 | `DLC\Expansion1\Data\Expansion1_LoyaltyLevels.xml:14-17` |
| **power shortage (GS)** | `POWER_MAX_PRODUCTION_MODIFIER_PENALTY = -50`: "Buildings which require Power provide less than half of their normal yield when the city is Unpowered" - the missing half is the `Building_YieldChangesBonusWithPower` row (Factory +3, Electronics Factory +5, Airport +2) | `Expansion2_GlobalParameters.xml:224`; `Expansion2_Civilopedia_Text.xml:153`; `Expansion2_Buildings.xml:394-404` |
| **occupied city** | production **-50%**, growth 0 (section 3) | `Yields.xml:65-70`; `GlobalParameters.xml:84` |
| **war weariness** | 400 points per amenity lost, at most 3 amenities lost in a city at war, +2 per combat in foreign lands, +3 per unit killed, +10 per WMD; decays 50/turn at war, 200 at peace, 2000 on peace | `GlobalParameters.xml:617-637` |
| negative treasury | -1 amenity per 10 gold below zero | `GlobalParameters.xml:324,328` |
| **pillaged** | the object is disabled, so its yield simply stops; a pillaged building blocks its district and a pillaged district blocks building there; repair costs 25% of the original production | `GlobalParameters.xml:420`; `Civilopedia_Concepts_Text.xml:432`; `InGameText.xml:1589-1590` |
| contamination | the tile cannot be worked and no production can be applied in it | `Civilopedia_Concepts_Text.xml:1074` |

**Not production effects, despite the folklore**: **starvation** (it removes population and, in R&F/GS,
4 loyalty per turn - `Expansion2_GlobalParameters.xml:168`), **housing** (growth only), and the
"ProductionModifier" column names people look for in the loyalty table - the real columns there are
`YieldChange` / `GrowthChange` / `IdentityChange`.

## 7. One-time production

| mechanism | value | source |
|---|---|---|
| chop Woods | **+20 production** | `Features.xml:186` |
| harvest Rainforest | **+10 production and +10 food** | `Features.xml:187,188` |
| remove Marsh | +20 food, **no production** | `Features.xml:189` |
| harvest Deer or Stone | **+20 production** each - the only two resource harvests that give production | `Resources.xml:372,376` |
| removability gate | Forests need Mining, Rainforest Bronze Working, Marsh Irrigation | `Features.xml:31,32,34` |
| Magnus/Groundbreaker | **+50%** to plot harvests and feature removals in that city | `Expansion1_Governors.xml:635-636,955` |
| World Congress Deforestation Treaty | can ban chopping, or convert it to Gold (which adds no production) | `Expansion2_Congress.xml:230-234,468-481` |
| Great Engineers | Isidore 215, **Brunelleschi 315**, Eiffel 480, Korolev 1500 (space), Sagan 3000 (space) - `KeepOverflow=false`, so the excess is discarded | `GreatPeople_Engineers.xml:240-303,378-384`; `GreatPeople_Scientists.xml:712-718` |
| Military Engineer charges | 20% of the district's cost per charge (Canal, Dam, Aqueduct, Bath), 20% for a Flood Barrier | `Expansion2_Districts.xml:96-99`; `Expansion2_Buildings.xml:461` |
| **Royal Society** (`BUILDING_GOV_SCIENCE`) | Builders may spend charges to add production to a district **project** - the ability this repo's adapter exposes as `UNITCOMMAND_PROJECT_PRODUCTION` (`src/civ_mcp/lua/units.py:2083`) | `Expansion1_Buildings.xml:317,621` |
| free buildings (not production points) | James of St. George builds Walls and Castle, Watt Factory and Workshop, Newton Library and University, Hypatia Library, Medici Market and Bank, Nelson Lighthouse and Shipyard | `GreatPeople_Engineers.xml:95-143`; `GreatPeople_Scientists.xml:196-208`; `GreatPeople_Merchants.xml:152-158` |

**The folklore that chops scale with era is not in this install.** There is no era, tech-count,
civic-count or population scaling of chop or harvest output in any XML, SQL or Lua: the values are the
fixed integers 20 / 10 / 20, and the only harvest parameters are
`HARVEST_IMPROVED_DEGRADATION = 50` and `HARVEST_PILLAGED_DEGRADATION = 30`
(`GlobalParameters.xml:344,346`), whose semantics no shipped file documents.

## 8. Buying it instead

- **Gold price = 2x the production cost**: `GOLD_PURCHASE_MULTIPLIER = 2` (`GlobalParameters.xml:334`)
  and `GOLD_EQUIVALENT_OTHER_YIELDS = 2` (`:320`), combined in the Civilopedia's own arithmetic
  `purchase_cost = cost * GOLD_PURCHASE_MULTIPLIER * GOLD_EQUIVALENT_OTHER_YIELDS`
  (`Base\Assets\UI\Civilopedia\CivilopediaPage_Building.lua:278`).
- **Districts are not purchasable by default**; Liang enables gold purchase of districts
  (`Expansion1_Governors.xml:795`) and Moksha/Cardinal enables faith purchase of them (`:615`;
  `Expansion2_Modifiers.xml:348-350`).
- Discounts that matter: Holy Order -30% Missionaries and Apostles (`Beliefs.xml:1611,1626`); Valletta
  suzerain -50% Walls/Castle/Star Fort (`Leaders.xml:5158-5188`); Mali Suguba -20% units, buildings
  **and districts** (`Expansion2_Districts.xml:185-197`); Monumentality (Golden Age) -30% Builders and
  Settlers (`Expansion1_Moments.xml:944-962`); Theocracy -15% faith purchases (`Governments.xml:463,468`).
- A purchase is **blocked by the same resource floor** as production (2 anywhere, 1 with the district)
  - `GlobalParameters.xml:555,557`.

## 9. What the data does not say

Recorded so the next reader does not mistake absence for a fact:

- **No overflow and no minimum turns to build** in any data file - both engine-side.
- **No chop scaling** (section 7), and the two `HARVEST_*_DEGRADATION` parameters are undocumented.
- **No starvation or housing production effect**; occupation's magnitude is only in the yield table.
- **No gameplay Lua ships at `Base\Assets\Gameplay\Lua`** - that path does not exist; all 646 `.lua`
  files are UI scripts, and no Lua computes purchase cost, production cost, chops or the power penalty
  (those are engine APIs).
- **Text/data mismatches**, reported rather than normalised: the World Congress Global Energy Treaty
  says "50% discount" while its data `Amount` is 100; the R&F Civilopedia puts the -50% loyalty band
  "below 25" while the table puts it at 26-50; Ibn Khaldun's English summary says "+40%" while the data
  is a flat +2/+4; the Ethiopia-pack city-state text mentions wonders while its file contains no wonder
  modifier.
- Whether the Ethiopia-pack envoy rows or the base/R&F rows win for a given ruleset depends on load
  order; the decisive check is the live database, not the shipped XML.

## 10. Measured in this match

- **A +1 production policy is worth exactly 1**: `城市规划` (Urban Planning) was slotted at T16 and the
  city's production read 8 -> 9 (diary T16).
- **The base is citizens on tiles and it can be near zero**: 北京 stood at **production 1** on T41 and
  its Monument needed **34 turns**, against 6 turns for the same building in 西安 - `manual:1401-1403`
  is the whole explanation.
- **A pillaged district blocks its buildings**: at T281 沃罗涅什's order was refused with
  `CANNOT_START|Prerequisite district is pillaged: DISTRICT_CAMPUS`.
- **An unpowered building pays and delivers nothing**: 西安's Factory completed at T228 and the city
  reported `城市供电不足`; section 6 puts the number on it (-50% of a power building's yield, i.e. the
  missing `Building_YieldChangesBonusWithPower` row).
- **A captured city starts from nothing**: 哈勒姆 on the turn it fell had production 1 and both Monument
  and Granary pillaged (`docs/task-history.md`, 022 outcome).
- **What this agent can read**: `get_cities` prints the current item's **"(N turns)"**
  (`src/civ_mcp/narrate.py:355-356`), the city's production per turn is `GetYield(1)`
  (`src/civ_mcp/lua/cities.py:359`), and `amenities`/`amenities_needed`
  (`src/civ_mcp/lua/overview.py:1417`) plus the pillaged district and building lists are what section 6
  needs to be checked each turn.

## 11. The order that actually works

1. **Base first** - citizens onto production tiles (mines, quarries, strategic resources, lumber mills,
   and the city centre's floor of 1), and repair or replace pillaged improvements and districts
   (section 4; `manual:1401-1403`).
2. **Fix the multiplier's precondition** - amenities. A city below Content multiplies its production by
   less than 1 (section 6), and war weariness and a negative treasury are the two self-inflicted
   sources (`manual:2155`, `2139`).
3. **Then the percentage and flat bonuses** (sections 4-5), which scale the base from step 1. This is
   also why the **+100% Industrial Zone adjacency cards (Craftsmen, Five-Year Plan) are worth more the
   better the adjacency is**, and why a Factory is worth building for its powered yield rather than its
   base 3.
4. **Bypass or burst when the item matters more than the tempo**: gold or faith purchase (section 8),
   one-time production from chops, Great Engineer charges or Military Engineer charges (section 7), and
   overflow carried from a cheap item into an expensive one.
5. **Remember the district clock**: a district's price grows with your tech progress (section 3), so the
   same Campus costs more at T200 than at T50 - locking the placement in early is cheaper than waiting
   for the perfect tile.

## 12. The factors, in the order they cost you production

Sections 1-9 are the arithmetic and section 6 is the manual's account of the conditions. This is the
operational list: what to check, how to check it, and what to do about it.

**Measure first, and measure all of them.** `.tools/production-audit.py` reads every city, ranks them
by the production each one is currently losing, and prints the per-city evidence for every factor
below. Two rules learned the hard way:

- **Never carry a city name, a coordinate or a unit id forward** from a previous turn, a previous
  session or a note. A rollback or a new game renames every city and renumbers every unit, so a plan
  that carries a name is a plan for a board that no longer exists. Name the city from the read in
  front of you. `.tools/_game.py` resolves the run; `.tools/advance-turns.py --march` selects a unit
  by what it *is* (`BOMBARD:28,14`) rather than by an id.
- **A factor you did not measure is a factor you will report as fine.** An audit that examined the
  one city it had already noticed reported "two cities unpowered"; the empire-wide read said nine,
  and only one of the nine was unpowered for the reason the audit had found.

### The six factors, and what each one actually costs

**1. An empty queue.** The city produces nothing at all this turn. This is the largest single loss
available and the only one that is free to fix. It blocks `end_turn` as well, so it costs a round
trip whether or not you notice it.

  *Do:* fill it the same turn it is noticed, with the item that answers the city's highest-ranked
  factor. `.tools/production-audit.py --apply` does exactly that; `.tools/production-recovery.py
  --fill` does it without the factor ranking.

**2. A pillaged district.** An Industrial Zone down takes the production district *and* the power it
was supplying, and - measured - **a pillaged building's repair is not even offered until its
district is repaired**. So the order inside a city is forced by the game, not chosen by you.

  *Do:* repair the district first, then its buildings, before anything new is built in that city. The
  repair entry carries the tile; the fresh-build entry under the same name does not, which is why a
  name-only lookup picks the wrong one about half the time.

**3. A pillaged production building.** Workshop, Factory, Coal/Oil/Nuclear Power Plant, Shipyard,
Seaport, Stock Exchange, and the Encampment line. A down building yields nothing.

  *Do:* repair it before anything new. `.tools/production-audit.py --apply` ranks repairs ahead of
  every other item.

**4. Unpowered.** A building that needs power yields nothing while it is unpowered, so this is the
Research Lab, the Factory and the Stock Exchange silently switched off. Three channels, from
`City:GetPower()` as the game's own panel reads it (`CityPanelPower.lua:42-54`):

    currentPower = freePower + temporaryPower
    requiredPower == 0                -> no power needed
    not IsFullyPowered()              -> unpowered
    IsFullyPoweredByActiveProject()   -> powered by a project

  `free` is renewable sources and dams; `temporary` is a fuel-burning plant, **and a plant's output
  reaches neighbouring cities through `temporary` too**. The trap is the **third** channel: power
  from a project appears in neither number, so a city can read `required > 0, free == 0,
  temporary == 0` and still answer powered. **`IsFullyPowered()` is a statement about this turn and
  never about durable supply** - test `free + temporary > 0` instead.

  The reach is **not** the six tiles the power lens suggests. Measured in one match: a city four
  tiles from the empire's only plant drew from it, and one five tiles away did not. Measure the reach
  per match - build one plant, then read `temporary` in the cities around it - rather than planning a
  cluster on a radius.

  `City:GetPowerAdvice()` is **boilerplate**: the same paragraph for every city, including the
  powered ones. It is not a diagnosis.

  *Do:* repair a pillaged plant; otherwise build one, and place the next from what the read says.

**5. Amenities.** `amenities - amenities_needed < 0` applies a percentage penalty to **every** yield
in the city, so it is a production loss like any other. A duplicate luxury gives no amenities, so
surplus copies are worth trading.

  *Do:* a new luxury type, an Entertainment Complex, or a policy card.

**6. Housing and food.** `housing - pop <= 1` stops growth, and `food_surplus <= 0` does the same one
step earlier. Neither costs production today; both cost it later, because **growth is the district
plan**: `districts <= floor(pop / 3)`, with the Government Plaza and Aqueduct exempt.

  *Do:* Granary, Water Mill, farms, a domestic trade route, an Aqueduct (exempt from the cap), a
  Neighbourhood. This is the one factor that is genuinely **deferred**.

### Two more that are not "conditions" but cost the same

**A free district slot** is a multiplier nobody took. `districts <= floor(pop / 3)` says how many the
city may have; a slot under that is production, science or gold left on the table.

**An unimproved or pillaged tile** is a yield that is simply absent. Builders are the cheapest
multiplier in the game, and a Builder standing on a pillaged tile should repair it rather than start
something new - the tile is already ours and already improved.

**An idle trade route** is free yields uncollected. A domestic route pays Food and Production to its
destination, which is a growth fix and a production fix in one.

### The order of work

1. **An empty queue** - same turn, always.
2. **Repair, district before its buildings**, before anything new in that city.
3. **Power** - repair a plant, or build one, and confirm the reach by reading `temporary` around it.
4. **Amenities**, if any city is negative.
5. **Housing and food** - Aqueduct first where the cap is binding, because it is exempt from the
   district rule and lifts the cap further than a building does.
6. **Fill a free district slot.**
7. **Builders for unimproved and pillaged tiles**, and **traders for idle routes.**

### When to replace a queue instead of waiting for it

Replacing a build throws its accumulated hammers away, so it is only worth it for a factor that is
switching yields off **right now** - **unpowered** or **pillaged** - and only while more than about
three turns remain on the current item. Housing and food are deferred, and a Campus or a Research Lab
is a yield in its own right: measured, an early version of the rule ranked housing above everything
but pillage and replaced, in one call, a 3-turn Research Lab and a 3-turn Campus with Granaries and
Sewers. That is a science loss bought with nothing. `.tools/production-audit.py --redirect` now
applies the narrow rule.

One caveat worth knowing: a **placed** district keeps its accumulated production, so putting a
district back after a bad switch resumes at the same turn count. Losing the hammers and keeping them
are different failures, and only the first is permanent.
