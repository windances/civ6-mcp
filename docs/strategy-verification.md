# Verifying the strategy documents: manual first, game data where the manual is silent

The three strategy files (`docs/production-speed.md`, `docs/production-strategy.md`,
`docs/china-production-by-victory.md`) were audited claim by claim. The rule applied is the one
`AGENTS.md` states: **the manual is the first authority, and where it is silent the installed game
files are** - never memory, and never the repo's own doctrine treated as fact. Four verdicts:

- **MANUAL** - the manual states it, with a line number in `.tools/manuals/manual.clean.txt`.
- **DATA** - the manual is silent; the installed game files state it.
- **CORRECTED** - the claim was wrong or incomplete, and the fix is in section 3.
- **DOCTRINE** - no source states it; it is the repo's own strategy and is only as good as the ledger.

## 1. What the manual does verify

| claim | the manual's own words (abbreviated) | line |
|---|---|---|
| a tech boost is 50% of the cost, a civic boost 50% | "a technology boost (50% of the needed research towards a technology)"; "free civic boosts (50% of the needed culture towards a civic)" | `1157`, `1173` |
| **boosts do not stack** | "you cannot get one boost on a tech from a Great Scientist for 50% its cost and then boost it with its normally" | `2063` |
| production comes from worked tiles | "Their citizens **work** the land, harvesting food, wealth, **production**"; tiles within three tiles of the city, one city per tile | `1401` |
| unimproved terrain and resources yield production | "how much food, gold, or **productivity** a nearby city can acquire from an **unimproved** tile"; resources "are the source of food, **Production**, or gold" | `463`, `459` |
| assignment and focus decide which tiles | automatic assignment "seeks to provide a balanced amount"; you may demand "**on production** or gold instead" | `1403`, `1495-1497` |
| a specialist gives up its tile | "whatever they were producing will be **lost**" | `1447` |
| an unemployed citizen yields 1 gold | "still provide 1 gold ... but consume as much food" | `1451-1453` |
| the amenity bands (base numbers) | content = no modifier; happy +5% yield / +10% growth; ecstatic +10% / +20%; negative below; unrest stops growth | `1255` |
| war weariness and a deficit cost amenities | war weariness "applied to every city you own as a negative Amenity, lowering your city growth and productivity"; "-1 amenity per 10 Gold below zero" | `2155`, `2139` |
| purchase constructs immediately | "it will be **immediately constructed** in the city" | `2111` |
| Campus and Holy Site want mountains | "Campuses and Holy Sites alike receive special yield boosts from placement near Mountains" | `1337` |
| religion is founded early and capped | "A maximum of 7 religions can ever be created in any game. Try to get one early"; religious units "may be purchased through your city with Faith" | `1887` |
| late starts have no Great Prophets | "no longer available when starting the game in the Industrial Era or later" | `2049` |
| theological combat exists | "Apostles may initiate Theological Combat against enemy Missionaries or Apostles" | `1891-1893` |
| what the score counts | "the Score each civ receives for **tiles, number of cities, and population**"; a wonder scores for **whoever holds its city**; the game ends in 2050 and the surviving civ's score decides; an eliminated civ scores zero | `2401`, `2405`, `2391`, `2395` |
| contamination blocks production | "**Production cannot be applied** ... Tiles that are contaminated **cannot be worked**" | `2497` |
| wonder effects are documented per wonder | e.g. the Great Library "will award +2 Science per turn, and you receive free boosts to all Ancient and Classical era technologies" | `1573` |

## 2. Where the manual is silent and the data decides

| claim | evidence |
|---|---|
| **Dynastic Cycle**: 60% boosts, and a completed wonder grants a Eureka **and** an Inspiration "if available" | `Base\Assets\Text\en_US\Civilizations_Text.xml:296` (verbatim), with the four modifiers at `Civilizations.xml:269-289` |
| **Great Wall**: built by Builders, **in a line on the frontier**, +4 defence / +2 fortification, +1 gold per adjacent segment (Masonry), +1 culture (Castles), tourism from Flight | `Improvements.xml:56,384,385,373,300` |
| a **domestic trade route** gives its destination +1 production and +1 food **per qualifying district**; +3 gold as an international destination | `Districts.xml`, the `District_TradeRouteYields` rows (City Center: production 1 / food 1 as domestic destination, gold 3 international) |
| GS **adds** Industrial Zone adjacency rows rather than replacing the base set | `DLC\Expansion2\Data\Expansion2_Districts.xml` inserts new `YieldChangeId`s (`Minel_HalfProduction`, `LumberMill_HalfProduction`, `Aqueduct_Production`, `Bath_Production`, `Canal_Production`, `Dam_Production`, `Strategic_Production`) alongside the base rows in `Districts.xml` |
| power plants give **+1 production per citizen**, require a **Factory**, and are mutually exclusive per city | `Expansion2_Buildings.xml`, `<Building_CitizenYieldChanges>` (`:409,412`), `<BuildingPrereqs>` (`:441`), `<MutuallyExclusiveBuildings>` |
| **Ruhr Valley**: +20% production in its city and +1 per Mine and Quarry; requires a Factory | `Buildings.xml:1768` (`RUHR_VALLEY_PRODUCTION_MODIFIER`), `:1572` (`RUHRVALLEY_ADDPRODUCTIONYIELD`), `:232` |
| **gold purchase is 2x the production cost** | `GlobalParameters.xml:334` (`GOLD_PURCHASE_MULTIPLIER = 2`), `:465` |
| Missionary, Apostle, Inquisitor, Guru, Warrior Monk and Naturalist are **faith-purchase only** | `Units.xml:754-758,770` (`MustPurchase="true"`) |
| a theological-combat victory projects **250** pressure; adjacent-city spread distance **10** | `GlobalParameters.xml:483` (`RELIGION_SPREAD_COMBAT_VICTORY`), `:477` |
| the power penalty and what it removes | `Expansion2_GlobalParameters.xml:224` (`-50`), `Expansion2_Buildings.xml` (`Building_YieldChangesBonusWithPower`) |
| chops are fixed integers with no scaling | `Features.xml:186-189`, and the audit's negative result across XML, SQL and Lua |

## 3. Corrected or qualified in this pass

1. **Dynastic Cycle's grant is conditional, and boosts do not stack.** The ability text says "if
   available" (`Civilizations_Text.xml:296`) and the manual says boosts cannot stack (`manual:2063`).
   So a wonder completed after an era's techs and civics are already boosted returns **nothing** - the
   docs had this as an unconditional double-dip. Applied to `china-production-by-victory.md`; it is also
   why 028's `done when:` insists the granted boost be *written down* rather than assumed.
2. **The Great Wall is a chain, not a scatter.** The docs implied walls give gold/culture/defence
   wherever they stand; the data requires **a line along the frontier** and pays **per adjacent
   segment**, which changes the value of the wall plan considerably.
3. **The religion deadline has a manual number.** The docs repeated the preset's "roughly half the
   major civilisations"; the manual's authority is **"a maximum of 7 religions"** plus "try to get one
   early" (`manual:1887`) and the Industrial-start cutoff (`manual:2049`). The preset's phrasing is now
   labelled doctrine.
4. **"Apostles may be built" is manual looseness.** `manual:1891` says Apostles "may be **built** in any
   city with a Temple"; the data marks them **faith-purchase only** (`Units.xml:754-758`). The data
   wins, and the conflict is recorded here rather than smoothed over.
5. **"Gold purchase is 2x" is a data value.** The manual says only that gold buys units and buildings
   (`manual:2111`); the 2x multiplier is `GOLD_PURCHASE_MULTIPLIER` (`GlobalParameters.xml:334`).
6. **The 60% has no numeric row anywhere.** The four Dynastic Cycle modifiers are
   `MODIFIER_PLAYER_ADJUST_CIVIC_BOOST`, `..._TECHNOLOGY_BOOST`,
   `..._ADJUST_FREE_CIVIC_BOOST_WONDER_ERA` and `..._ADJUST_FREE_TECH_BOOST_WONDER_ERA`
   (`Civilizations.xml:269-289`) - engine-implemented, so 60% exists in the ability text only. A reader
   should not expect to find it in a data file.
7. **Score gained two facts the docs lacked**: a wonder's score travels with **the city that holds it**
   (`manual:2405`), and an **eliminated civ scores zero** (`manual:2395`) - both sharpen the score
   fallback's two hard rules.

## 4. Doctrine, not verifiable, and labelled as such

These are decisions from the repo's own strategy files. No manual or data file states them; they are
hypotheses this match's ledger supports or refutes, and they should be read that way:

- the assault **establishment counts** (siege 2, melee 2, ranged 4, cavalry 1) and "one garrison per
  city plus one mobile unit" - `prompts/tactics/01-unit-production.md`;
- **one war city** and "every other city builds its next district" - `directive.md:317-331`;
- "**finish the opening** before converting to war" - `domination/directive.md:3-7`;
- the **+10 gold/turn floor** with the army counted, and negative GNP as an over-built army -
  `directive.md:374,301-305`;
- the **4-6 city** ceiling and the Ancestral Hall step - `expansion/directive.md`, `directive.md:271`;
- "the pool fills at roughly half the major civilisations" - `religion/directive.md:3-5`.

## 5. What this pass did not verify

- The **exact adjacency total** of a mature Industrial Zone: the row set supports "several points
  before doubling", but no single data value states "8-12", so `docs/production-strategy.md`'s figure
  is an **estimate from the rows**, not a reading.
- The **per-line citations for policies, governors, wonders and Great People** come from the earlier
  data audit, not from a re-read in this pass; the headline numbers in this file (power plants, Ruhr
  Valley, trade routes, purchase multiplier, religious units, theology pressure, Great Wall) were each
  re-read directly.
- The **R&F-only governor promotions** (Liang's Infrastructure and Amusement) are unreachable under
  this install per the audit, and reachability was not re-tested.
- Whether the live **SQLite database** resolves the Ethiopia-pack envoy rows over the base/R&F ones -
  load order decides, and only the running game can settle it.

**Verdict**: the three strategy documents stand. One claim was materially incomplete (the wonder-grant
condition), one was vague in a way that changes a decision (the Great Wall's placement), one repeated a
preset's number as if it were the game's (the religion deadline), and one manual sentence is loose
enough to mislead (Apostles "built"). All four are now recorded, and the first two are fixed in
`docs/china-production-by-victory.md`.
