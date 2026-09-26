# cut-the-supply — staged, cut into `turn-checks.md` when the MCP server next starts

**Why this is staged.** The rule file is re-read every turn, but the *metric set* lives in the
running MCP server's memory: `turn_checks.evaluate` raises on an unknown metric, so a live rule
naming `enemy_supply_uncut_with_idle` reports itself `un-evaluable` every turn and cannot be fixed
until that process restarts (the same reason `answer-the-camp` ships here). The metric is already
computed by `end_turn._capture_metrics` — this file moves into `prompts/checks/turn-checks.md`
the next time the server starts.

- id: cut-the-supply
  require: when an enemy city is under siege and its adjacent hexes are not covered, the units
           within three tiles that still have movement spend it on those hexes — the city heals
           about twenty points a turn while any adjacent hex is outside our zone of control
           (`manual:1066-1085`, HEALING DAMAGE TO CITIES), so cutting the last open hex is worth
           more than any amount of extra fire.
  metric: enemy_supply_uncut_with_idle == 0
  why: measured over the T139–T159 Russian war. 沃罗涅什 read `supply line 3/6 cut` and 喀山 read
       `1/6` for their whole sieges; both pools came back to full and both cities rebuilt their
       walls while our Catapults "fortified in place because the corridor is jammed" (T155,
       verbatim). 圣彼得堡 took six turns of fire for the same reason — the heal was never cut,
       only out-damaged, and the train could not out-damage it from one firing tile.
  fix: order the surplus units — the ones with movement and nothing to shoot at — onto or beside
       the open hexes, taking the far side of the ring rather than queueing in the corridor; a
       unit that walks there is out of the firing line that turn, which is the trade this rule
       asks you to make explicitly (and to record in the diary if you decline it).
