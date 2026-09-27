# TEMP TASK 022 - take Haarlem: locate the Dutch city, analyse it, stage and concentrate fire

added: 2026-09-28 (human instruction: 增加任务：占领哈勒姆)
expires: turn 288 - 31 turn(s) from T257, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: **Haarlem is ours** - the tile at its own (x,y) reads `[CITY_CENTER]` owned by 中国 with one of our
           units standing on it (`hold-what-you-take`), Haarlem appears in `get_cities`, and the
           Netherlands' city count in `get_diplomacy` has fallen by one. If Haarlem turns out to be
           the Dutch original capital, the proof is `get_victory_progress`'s DOMINATION block: it
           reads `荷兰: holds own capital` before and does not after. The diary carries the ledger -
           the four numbers re-read at war and which of them came from a probe attack, the staging
           table with its overrides, the shots per turn and the tile each shot came from, the cost
           paid, and the hold plan. Retire it as `022-take-haarlem-done-T<n>.md` the turn the city
           is ours, or as `-expired-T<n>.md` at the hard stop with where the force stood and what
           blocked it.
overrides: **the human's instruction is the reason of record for this one city.** 占领哈勒姆 was given at T254,
           while the standing plan was the science line and 021's Sumer expedition; this file puts
           Haarlem ahead of that plan **for the force and the queues named below only**, and the
           diary records the instruction as the reason rather than inventing a strategic one - the
           same treatment 016 gave 埃里温 and 020 gave 布鲁塞尔. **021 keeps its expedition**: the units
           already at sea on the west lane (Bombards #4128794, #5636108, #4325376, #4980745, Field
           Cannons #6291469, #4784149, Line Infantry #4456464, #5111819, Pike&Shot #6815776,
           Cuirassier #6029340, Cavalry #5177368, 圣女贞德) and 021's Frigate are **not** recalled,
           diverted or re-tasked; this file's force is the home slice, at most **four new builds**,
           and gold. **No new war is declared**: the Netherlands is already at war (diplomatic state
           6), so an attack needs no declaration and no waiting turn - the combat engine is already
           synced - and Sumer stays 021's business and neutral here. Gold purchases are authorized
           for the units this file names (the treasury read 699 at +89/turn at T254), and any city's
           queue except 西安's may be used. **It does not override**: `one-garrison-per-city`,
           `use-your-attacks`, the eastern-shore defence of 塞纳 and 亚历山大, 西安's Rocketry-and-Spaceport
           line, 021's scope and its own T270 deadline, the housing and Sewer line, or the
           directive's ban on `propose_peace` - the Dutch war still has no exit but the capture of
           its cities.
scope: Haarlem, its ring, the Dutch units defending it, the route to it, and the force this file names. Not
           the Netherlands' other six cities - each of those is its own decision under the directive
           - not Sumer or anything on 021's west lane, not a city-state, not a barbarian camp, and
           not a third front opened by this file.

.tmp/022-body.md
