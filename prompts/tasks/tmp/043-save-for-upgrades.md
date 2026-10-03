# TEMP TASK 043 - Save gold to upgrade the front line

added:     2026-10-04 (human instruction: 除修复电力和提高宜居度的开销外，攒钱升级前线部队)
expires:   turn 341 - 30 turn(s) from T311, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 units within 3 tiles of an enemy city or a visible enemy unit of the civ we are at war
           with have `can_upgrade` true with an `upgrade_cost` the treasury covers, as read by
           `get_units`.
overrides: The directive's own spending lines while the front is a tier behind: the rule that gold above about
           300 is wasted unless saved for a named purchase, and the rule that a builder is the
           cheapest multiplier. Both are suspended until this task retires - and this task is itself
           the named purchase. It does not outrank the war front, the target order, or a production
           order.
scope:     Gold spending. It authorises holding the treasury and spending it on exactly two things: a repair
           that restores power or an amenity fix, and `upgrade_unit` for a unit within three tiles
           of the enemy we are at war with. It authorises nothing else with gold.

## Why

The directive says two things that this task deliberately suspends: that gold above about 300 which
is not being saved for a named purchase on a named turn is wasted, and that a builder is the cheapest
multiplier in the game. Both are usually true. They are suspended because **a front-line unit that is
a tier behind loses fights it would have won**, and no amount of later gold buys back the turns that
cost.

So the treasury has one purpose until the front is upgraded. Power repairs and amenity fixes are the
only things that may be bought ahead of it.

## What may be spent, in this order

1. **A repair that restores power, or an amenity fix**, when a city is actually losing production or
   yields to it. These are production, and production is what buys the army - so they are not
   competing with this task, they are feeding it.
2. **Upgrading a front-line unit**, whenever a read of `get_units` shows `can_upgrade` and the
   treasury covers `upgrade_cost`.

That is the whole rule. A builder, a settler, a wonder, a tile purchase, a great person, or a
building bought for its own sake all wait.

## Who counts as the front

A unit within **three tiles of an enemy city or of a visible enemy unit**, for the civ we are at war
with. Read it - `get_units` gives the positions and `target_report(x, y)` gives the city - never
carry a unit id or a coordinate in from a note. A garrison in the interior is not the front, and
upgrading it is not this task.

## What the upgrade is worth, and when to skip it

- **The chain matters.** The siege line is the wall-breaker (`Engineering` -> Catapult,
  `Military Engineering` -> Trebuchet, `Niter` -> Bombard), and a ranged unit's upgrade changes what
  it can do to a city at all. Upgrade in the order the front needs, not the order the units appear.
- **Do not buy an upgrade you are about to lose.** A unit at 0 movement in a losing position, or one
  the next turn will disband, is not worth the gold.
- **Do not spend the treasury to zero.** Keep enough for one replacement. The point is a front that
  can absorb a loss, and a treasury at zero with one new unit on the map is not that.

## The one thing to watch

The **upgrade discount card**. If a policy slot holds one, upgrading while it is slotted is
cheaper; if the card is available and not slotted, say so in the diary, because the saving is worth
a turn of waiting.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py add --title "Save gold to upgrade the front line" --instruction 除修复电力和提高宜居度的开销外，攒钱升级前线部队 --slug save-for-upgrades --scope @.tmp/task-upgrades-scope.txt --done-when @.tmp/task-upgrades-done.txt --overrides @.tmp/task-upgrades-overrides.txt --why "hold the treasury for front-line upgrades ahead of every other purchase" --body-file .tmp/task-upgrades-body.md --cn @.tmp/task-upgrades-cn.md --turns 30 --no-commit
     at: 2026-10-04T05:55:56+08:00
     chinese backup: prompts/tasks/cn/043-save-for-upgrades.cn.md
-->
