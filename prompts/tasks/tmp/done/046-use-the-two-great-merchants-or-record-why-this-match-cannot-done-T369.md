# TEMP TASK 046 - Use the two Great Merchants, or record why this match cannot

added:     2026-10-04 (human instruction: 大科学家，大商人由agent负责)
expires:   turn 372 - 30 turn(s) from T352, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 of our UNIT_GREAT_MERCHANT units still hold an unspent charge (`charges:1` in the
           `get_units` read), and the turn that retires this file records in the diary which lever
           was tried and what the game answered. Both merchants held their charge when the file was
           published, and `skip` cannot satisfy this line - only activating them, or deleting them
           with that reason written down, changes the count.
overrides: nothing. The standing directive's "no peace, ever" and its "a city-state is not a conquest target"
           both stand: this file does not authorize a war on, or the capture of, a city-state to
           reach an activation tile. It also does not outrank the space race, the war front, or the
           directive's spending rules - the two merchants are an errand, not a plan.
scope:     this match only, and only the Great Merchants we already own: the passage question (can a city-state
           be traded Open Borders at all), the activation if it can, and the record if it cannot. It
           authorizes `propose_trade` in test mode with any city-state, and one `unit_action` per
           merchant - `trade_route`-style errands are not in scope.

## Why this is a file and not a check rule

`units(GREAT_MERCHANT) == 0` is mechanically checkable, and that is exactly the problem: **deleting
the merchant satisfies it**, which is not the thing wanted. No metric expresses "the question was
asked and answered", so a goal here would reward the wrong action, and it could be cleared without
anyone learning whether the two were usable at all.

The Great Scientist we own does have a goal rule (`use-the-great-scientist`) because for her the same
metric is honest: her requirement is a city holding an Artifact, which is something we can build
towards. These two are different - their requirement is a tile owned by a city-state, and whether we
can reach it is the open question.

## Steps

1. `get_units`: name every Great Merchant of ours still holding `charges:1`, with its tile. At T352
   there are two - (68,15) and (53,26) - and both still hold their single charge.
2. `get_city_states`: every city-state, and which of them we are suzerain of.
3. Ask each city-state for passage with `propose_trade(player_id, mode="test")` and write down what
   the game answers. Record it as **the game's answer**, which is not the same thing as our own
   diagnostic: the sentence a refused move prints - "need suzerainty or Open Borders" - is written by
   `src/civ_mcp/lua/units.py:350` for any refused move into a non-major owner's territory, and it has
   already misled once. A2/A3 spent six turns re-declaring a war on the strength of it, and
   `AGENTS.md` records the measured fact it contradicts: a city-state refused our scout while
   `get_city_states` named us its Suzerain with five envoys, so **suzerainty alone is not passage**.
4. If passage is granted anywhere, walk the merchant to a tile the activation validator lists (the
   `CANNOT_ACTIVATE ... Valid tiles:` reply names them) and activate it there; the charge is spent
   and the merchant is gone.
5. If no city-state grants it, put the answers in the diary in one line - which were asked, what each
   answered - conclude that both merchants are unusable for this match, and `skip` them for good.
   `delete` only with that line as the reason: deleting a Great Person to clear a line is the failure
   this file exists to avoid.
6. Do not declare war on a city-state, capture one, or break "no peace, ever" to reach the tile.
   `overrides: nothing` means exactly that.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Use the two Great Merchants, or record why this match cannot" --instruction @.tmp/m-instruction.txt --done-when @.tmp/m-done-when.txt --overrides @.tmp/m-overrides.txt --scope @.tmp/m-scope.txt --body @.tmp/m-body.md --cn @.tmp/m-body.cn.md --why "use the two Great Merchants we already own, or record why this match cannot" --expires-turn 372
     at: 2026-10-04T20:07:36+08:00
     chinese backup: prompts/tasks/cn/046-use-the-two-great-merchants-or-record-why-this-match-cannot.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 046 --done --turn 369
     at: 2026-10-07T00:27:04+08:00
     status: done at T369
     chinese backup: prompts/tasks/cn/046-use-the-two-great-merchants-or-record-why-this-match-cannot.cn.md
-->
