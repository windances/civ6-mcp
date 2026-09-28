# China: the optimal production strategy, per victory goal

Production is never a goal of its own - it is the means. What changes between victory types is **what
the hammers are for**, and therefore which multipliers are worth stacking and which are wasted. This
file is the per-goal answer for **China (Qin)**, whose kit bends every one of these plans:

- **Dynastic Cycle** - Eurekas and Inspirations are worth **60%** instead of 50%, and **completing ANY
  wonder grants a random Eureka *and* Inspiration** from that wonder's era (`directive.md:4-6`). The
  ability's own text (`Base\Assets\Text\en_US\Civilizations_Text.xml:296`) reads: *"Eurekas and
  Inspirations provide 60% of civics and technologies instead of 50%. When completing a wonder receive
  a random Eureka and Inspiration from the era of the wonder, **if available**."* That last clause
  matters, and the manual supplies the reason: **boosts do not stack** (`manual:2063`), and a boost is
  worth "50% of the needed research" or "50% of the needed culture" before China's +10 (`manual:1157`,
  `1173`). So the wonder's grant is **wasted when the era's techs and civics are already boosted** -
  complete wonders while the era still has unboosted items, and record whether the grant landed.
- **Great Wall** - built by **Builders, not cities** (`directive.md:14-16`), and the data adds the
  constraints: it is **built in a line along the frontier** (`BuildInLine="true"`,
  `BuildOnFrontier="true"`), it gives **+4 defence and fortification** (`DefenseModifier="4"`,
  `GrantFortification="2"`), and its yields are **per adjacent Great Wall segment** - **+1 gold** from
  Masonry and **+1 culture** from Castles (`Improvements.xml:56,384,385`) - with **tourism from Flight**
  (`:373`). It is a chain, not a scatter, and it costs builder charges rather than city production.
- **Crouching Tiger** - Medieval ranged, **Range 1**, so it must stand adjacent to its target and
  needs a melee unit holding the tile in front (`directive.md:18-21`).
- **Thirty-Six Stratagems** - the agent cannot trigger it; report convertible barbarians for the human.

Everything mechanical below is cited in `docs/production-speed.md` (the game's own data files) and used
the way `docs/production-strategy.md` ranks it. The repo's own per-goal emphases are the presets in
`prompts/strategies/`.

## The substrate every Chinese game needs, whatever the goal

1. **Citizens on tiles and improvements that exist.** The base is worked tiles (`manual:1401`); the
   cheapest multiplier in the game is a Builder, and unimproved tiles are the usual reason an empire
   stalls (`directive.md:282-288`). Gold above ~300 with unimproved tiles buys a Builder, not a bank.
2. **The district arithmetic.** `districts <= floor(pop / 3)` - check it every time a queue is chosen,
   and never leave a free slot empty, because growth *is* the district plan (`directive.md:276-281`).
3. **Amenities before they bite.** GS bands are Happy **+10%**, Ecstatic **+20%**, and -10/-20/-30/-40%
   below Content, on all non-food yields (`Expansion2_Buildings.xml:463-515`); war weariness and a
   negative treasury are the self-inflicted sources.
4. **Power from turn one.** A plant is **+1 production per citizen**, needs a **Factory**, and serves
   cities **within six tiles**; an unpowered city loses its power-only building yields under a **-50%**
   cap (`docs/new-game.md:19-40`). So Industrial Zones are placed **for their six-tile ring**, not for
   themselves, and coal is the fuel to burn (1 coal or oil = 4 power, 1 uranium = 16).
5. **One cheap wonder per era, deliberately.** For China this is a research building (above), plus era
   score, plus the effect itself.
6. **Trade routes never idle.** A domestic route gives its destination +1 production per qualifying
   district there, plus food (`Districts.xml:159-180`); the expansion preset's rule is to start a
   domestic route into the **youngest** city the turn a slot frees (`expansion/directive.md:11`).
7. **District costs rise with tech progress** (`COST_PROGRESSION_NUM_UNDER_AVG_PLUS_TECH`, param 40)
   while buildings and wonders do not - so a district you know you want is cheaper queued now.

## 1. Military - production in service of the army

**What the hammers are for**: the assault establishment, held ready *before* the war rather than built
during it. `prompts/tactics/01-unit-production.md` fixes it: **siege 2, melee 2, ranged 4, cavalry 1**,
plus one garrison per city and one mobile unit in peacetime. For China the Crouching Tiger joins the
ranged four, and each Tiger needs a melee partner in front of it.

**The one rule that beats every other optimisation**: *finish the opening first.* "An army raised on a
stalled economy loses the long war; a Settler already in the queue usually beats a Swordsman at this
stage" (`domination/directive.md:3-7`). Until five or six cities exist - or an Ancestral Hall is
already building - production belongs to expansion and the Campus line, not to units.

**Then split the cities once**: **one war city - the highest production - builds units, siege and the
Encampment**; every other city builds its next district or that district's building and nothing else
for the duration (`directive.md:317-331`). The Encampment and Barracks belong in that same
highest-production city, because **unit production time is the binding constraint** when no
resource-free army route exists (`directive.md:55-57`).

**Multipliers that matter for military production**

| lever | value |
|---|---|
| Cards by class | Agoge +50% Ancient/Classical melee, anti-cavalry and ranged; Maneuver +50% same-era cavalry; Feudal Contract / Grande Armée / Military First +50% for their eras; **Lightning Warfare +50% all cavalry**; Maritime Industries +100% early naval (`Policies.xml`) |
| Government | **Fascism plenary +50% toward units**; Autocracy's flat +1 all yields with the Palace and each government building; Ibrahim/Pasha **+20% military units** in his city |
| Wonders | **Statue of Zeus +50% anti-cavalry**; Kilwa Kisiwani +15% units per Militaristic suzerainty |
| Other | Military Alliance level 2 **+15%** while at war; World Congress Mercenary Companies **±100%/-50%** to unit production *and purchase*; Liberation War +100 for 10 turns |
| Upgrades instead of builds | an upgrade is `UPGRADE_NET_PRODUCTION_PERCENT_COST` = **100%** of the production cost under GS, and the Professional Army card halves the **gold** (`GlobalParameters.xml:615`; `Expansion2_GlobalParameters.xml:288`) - measured in this match at 310g -> **155g** for Bombard -> Artillery |

**Resources and upkeep are part of the same budget.** Mine every strategic resource inside your
borders and never plan around an import (`directive.md:52-54`); the production of a resource-requiring
unit is **blocked** below 2 of the resource (1 with the right district, `GlobalParameters.xml:551,553`).
Keep unit maintenance under roughly 30% of income and read **negative GNP as the hard signal that the
army is over-built** (`directive.md:301-305`); bank the resources and keep amenities positive, because
war weariness suppresses production exactly when it matters (`domination/directive.md:14-16`).

**What not to buy with hammers**: a second front (`domination/directive.md:9`), units above the
establishment before the first target is named, and - in this match specifically - rams and towers, a
human instruction that replaced them with Catapults/Bombards because the siege unit is what breaks
walls. Do not sack the Campus line for a bigger army: the directive's counter-example is an empire that
doubled its army and watched gold/turn fall from +17 to +0.6 for forty-five turns.

**China's edge in a war**: wonders still pay - a cheap one built *during* the war returns a Eureka and
an Inspiration; Great Wall segments along the threatened border cost builder charges rather than city
production, and give gold, culture and defence; and a converted barbarian (human-played) is a free
reinforcement that cost no production at all (`directive.md:47-48`).

## 2. Science

**What the hammers are for**: the Campus line first (`science/directive.md:3-4`) - **Library,
University, Research Lab**, adjacency from mountains, reefs and geothermal vents deciding where the
Campus goes - and then, in the last quarter of the game, the **space chain**: Spaceport 1800 and four
projects, with Industrial Zones existing for exactly that production (`science/directive.md:5-6`).

**Multipliers that matter**: the Industrial Zone line and its adjacency (mines, quarries, aqueduct,
dam, canal; GS adds lumber mills and strategic resources) doubled by Craftsmen or the Five-Year Plan
(+100% each); **power** on every Campus and Industrial Zone city, because **Research Lab needs 3
power** and an unpowered city runs its power buildings at less than half; **Pingala** in the space city
(+science, then Space Initiative **+30% space projects**); **Ruhr Valley +20%** in the city that builds
the Spaceport and **Amundsen-Scott +10% to all cities**; **Carl Sagan 3000** and **Korolev 1500**
straight into space projects; the Great Library, Oxford University and Kilwa Kisiwani for the techs and
the boosts.

**What not to build**: an army beyond one garrison per city plus one mobile unit, and wars at all -
"A stable map is worth more than any conquest" (`science/directive.md:7-8`). Science wants **four to
six tall cities**, not breadth: every extra city is another Amenities bill and another district clock
ticking.

## 3. Culture

**What the hammers are for**: the **Theater Square line** (Amphitheater, Art Museum, Archaeological
Museum, **Broadcast Center** - which needs **3 power**), the **wonders** (tourism plus, for China, a
Eureka *and* an Inspiration each), and the tile work that raises appeal (woods, rivers, National
Parks).

**Why China is unusually good at this**: the culture victory is a *tourism* race, and tourism follows
wonders, Great Works and theming - precisely the things China's ability pays her to build anyway. Every
wonder is simultaneously tourism, era score, a Eureka and an Inspiration. **Great Wall segments**
return gold *and* culture and cost no city production (`directive.md:14-16`), so surplus builder
charges convert directly into the culture line.

**Multipliers that matter**: Theater Square adjacency (**+1 per adjacent wonder, +2 per Entertainment
Complex**); policy cards and governments that lift culture and tourism rather than production, since
production's job here is only to get the buildings and wonders up; **faith** for Naturalists and Rock
Bands (`MustPurchase = TRUE`, they can only be bought - `Units.xml:754-758,770`); and the Great People
that matter are the Writers/Artists/Musicians, whose points come from the districts being built.

**What not to build**: military beyond the garrison, and low-adjacency Theater Squares for their own
sake - adjacency is fixed by the ring, so the placement decision is the whole strategy.

## 4. Religion

**What the hammers are for**: a **Holy Site in every city, then Shrine, then Temple**
(`religion/directive.md:6`), and nothing else at the start, because founding a religion is the game's
first irreversible deadline (`religion/directive.md:3-5`). The manual states the ceiling and the hurry
in its own words: **"A maximum of 7 religions can ever be created in any game. Try to get one early so
you don't miss out!"** (`manual:1887`), and **"Great Prophets are no longer available when starting the
game in the Industrial Era or later"** (`manual:2049`). The preset's "roughly half the major
civilisations" is the repo's phrasing of the same deadline, not a manual number. If China is not racing
for a Great Prophet, the directive's standing rule is the opposite: **do not build a Holy Site at all**
(`directive.md:296-300`).

**The production twist that makes religion pay for itself**: under Gathering Storm, **Work Ethic makes
the Holy Site's Faith adjacency produce Production as well** (`Expansion2_Beliefs.xml:831-839`). A Holy
Site sited for +4 or +5 Faith on mountains is therefore also +4 or +5 production, which is China's
cheapest way to turn a religious commitment into a building engine. Other production-relevant beliefs:
God of the Forge (+25% early units), City Patron Goddess (+25% districts in a city with no specialty
district), Lady of the Reeds and Marshes (+2 marsh/oasis/floodplains).

**Multipliers that matter**: faith itself (so the purchase economy can buy Missionaries and Apostles -
they cannot be produced); religious buildings; and the Apostles' theological combat, where "a kill
projects 250 pressure in a ten-tile radius, which beats passive spreading" (`religion/directive.md:8-9`).

**What not to build**: anything that competes with the Holy Site line before the religion is founded,
and a war - converting cities you are bombing is a contradiction.

## 5. Diplomacy

**What the hammers are for**: the **gold economy** and the **influence economy**, because diplomatic
victory is won at the World Congress with **20 diplomatic victory points** and neither DVP nor favor is
purchased with production. Favor accrues from **government tier (+1 base, scaling), alliances (+1/turn
per level) and suzerainties (+1/turn)** (repo reference, "Diplomatic Favor"); so production's job is
Commercial Hubs and Harbors (trade capacity and gold), the Diplomatic Quarter line where it is
available, and the **wonders and buildings whose text grants favor, envoys or DVP** - read each one's
Civilopedia text rather than assuming.

**Multipliers that matter**: nothing in the production table directly; what matters is (a) **gold per
turn**, since it buys the buildings and the Builder/Settler tempo that keep the empire's tier and
population up, and (b) **defence**, because a lost city loses its suzerainties and its votes. Keep
`gold_per_turn` at or above the directive's **+10 floor with the army counted**
(`directive.md:374`).

**What not to build**: an army (it is pure cost at peace), and wars (they destroy the alliances and
suzerainties that pay the favor).

## 6. Score (the fallback)

Score at the turn limit rewards **breadth**: cities, population, techs, civics, wonders, Great People,
Great Works and territory all feed it, and there is no single thing to rush. The manual confirms the
shape of it - the score counts "tiles, number of cities, and population" (`manual:2401`), a constructed
wonder scores for **whoever holds the city it is in** (`manual:2405`), the game simply ends in 2050 and
the surviving civ's score decides (`manual:2391`), and **an eliminated civ scores zero**
(`manual:2395`). So the optimal production strategy is the **union of the others**, with the tie broken
toward whatever compounds fastest in the current snapshot - which is exactly the expansion preset's
posture: reach four to six productive cities, keep them all growing, catch up housing, amenities and
improvements, and *then* commit (`expansion/directive.md:1-9`). The two hard rules are the ones that
keep you alive to be scored:
**never lose a city**, and **keep amenities positive**.

## 7. The comparison, on one screen

| goal | production's target | the lever that matters most | what to refuse |
|---|---|---|---|
| **Military** | the establishment (siege 2 / melee 2 / ranged 4 / cavalry 1) in **one war city** | class cards (+50/100%), Fascism +50%, Statue of Zeus, upgrades over builds | a second front, units above the establishment, a stalled opening |
| **Science** | Campus line, then the space chain | Industrial Zone adjacency + power + Pingala + Ruhr/Amundsen-Scott + Sagan/Korolev | wars, wide expansion, an army |
| **Culture** | Theater Square line + **wonders** (China's double-dip) | wonder adjacency and tourism multipliers; builder charges on Great Wall | low-adjacency districts, armies |
| **Religion** | Holy Site → Shrine → Temple **before the Prophet pool closes** | Work Ethic (faith adjacency **is** production); faith to buy Apostles | a late start, or a Holy Site at all if not racing |
| **Diplomacy** | gold and influence buildings, plus the DVP/favor wonders | gold per turn and keeping suzerainties and alliances | armies, wars |
| **Score** | everything, breadth first | the expansion posture: growth, housing, amenities, improvements | losing cities, letting amenities fall |

**The one line that is true for all six**: for China, **a wonder is a research building, and a Builder
is the cheapest multiplier in the game** - so whatever the victory, the queue that spends hammers on
improvements and on one deliberate wonder per era is never wrong, and the queue that spends them on
units before the economy is standing never pays.

## Sources

- `docs/production-speed.md` - every factor, with `path:line` citations into the installed game data.
- `docs/production-strategy.md` - the ranked levers, and the "does this hold for a new game" section.
- `prompts/tactics/01-unit-production.md` - the establishment and the production order.
- `prompts/strategies/{china-conquest,domination,science,religion,expansion}/directive.md` - the repo's
  own per-goal emphases.
- `prompts/strategies/china-conquest/directive.md` - China's kit, the compounding rules and the army
  budget.
- `prompts/strategies/README.md` - the preset roster and how a strategy reaches a running session.
