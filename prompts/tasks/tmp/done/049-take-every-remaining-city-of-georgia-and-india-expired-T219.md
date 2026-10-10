# TEMP TASK 049 - Take every remaining city of Georgia and India

added:     2026-10-07 (human instruction: 继续攻占所有城市（人类指令 2026-10-07）。不求和、不停战，格鲁吉亚与印度的每一座城都要拿下；无墙的 先用现有军团吃，400
           墙的等满编炮兵。)
expires:   turn 420 - 35 turn(s) from T385, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 cities owned by Georgia and count == 0 owned by India, as read by get_diplomacy (or the
           domination victory the game reports itself); the two held 10 and 8 at T385
overrides: the compounding default and the corps production limit: up to eight cities may stay on unit
           production until both rings are taken, and the faith balance may be spent on units or
           Great People
scope:     the conquest of every city Georgia and India own, on both fronts; nothing else changes

## The order

Take every remaining city of Georgia and of India. Peace is never proposed and every offer is refused
(the directive), so this ends when the map does: `get_diplomacy` showing both at 0 cities, or the
domination victory the game reports itself.

## Where it stands at T385

50 cities against Georgia's 10 and India's 8 (down from 10 each at T370) - two fronts, both armies
shattered (Georgia 231 -> 144 military, India 260 -> 84), ours over 2000. Gold is 1472 at
-18/turn and faith 12577 unspent.

Two targets are in reach of the western group right now and they are the cheapest cities on the map:

- **Chennai (10,32), India**: 20/200 HP and **walls 0**, with a Destroyer within two tiles - one
  melee attack takes the city. Attack, then resolve the capture with `city_action(city_id, "keep")`
  or the turn will not advance. A Destroyer is a melee naval unit and does take coastal cities.
- **Nazca (21,36), city-state**: 200/200 with walls ground from 294 to 209. No melee unit is within
  two tiles, so the ring has to be closed before the walls finish falling - park a Modern Armor or
  a Mechanized Infantry adjacent while the guns work.

## How to take the rest, in order

1. **Wall-less cities first** (India's are mostly `walls none`): a 3-gun corps plus two melee units
   takes one in two or three turns. `get_target_report(x, y)` prints the pool, the walls and the
   garrison in one call.
2. **Georgia's 400-wall ring last, with the full train**: bombard with the 3-gun standard until
   `SIEGE PROGRESS` shows the walls gone, keep the melee adjacent so the city falls the same turn
   the pool empties, and remember a melee unit must be next to the city to take it - ranged units
   cannot capture.
3. **Never open an assault that cannot win** (`prompts/tactics/07-pre-war-analysis.md`), and never
   leave a captured city unresolved: the capture prompt blocks the turn until `city_action` answers.
4. **Keep the train fed**: the war economy is authorised for up to eight cities; the rest compound.
   Every city taken fixes the gold rate, which is what pays for the next corps.
5. **Spend the faith**: 12577 is worth 4 land units if the Grand Master's Chapel is built, or Great
   People otherwise. Unspent faith is the only idle resource left in the empire.
6. **Missionaries and Apostles at war are destroyed** (`condemn`), as always.

## Done when

`get_diplomacy` reports Georgia and India at 0 cities (or the game reports a domination victory).
Retire this file that turn and record in the diary how many turns each civ's ring took.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Take every remaining city of Georgia and India" --instruction @.tmp/task049-instruction.txt --done-when "count == 0 cities owned by Georgia and count == 0 owned by India, as read by get_diplomacy (or the domination victory the game reports itself); the two held 10 and 8 at T385" --overrides "the compounding default and the corps production limit: up to eight cities may stay on unit production until both rings are taken, and the faith balance may be spent on units or Great People" --scope "the conquest of every city Georgia and India own, on both fronts; nothing else changes" --why "take every remaining enemy city" --turns 35 --body @.tmp/task049-body.txt --cn @.tmp/task049-cn.txt
     at: 2026-10-07T23:41:07+08:00
     chinese backup: prompts/tasks/cn/049-take-every-remaining-city-of-georgia-and-india.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 049 --expired --turn 385 --note "the game reported GAME OVER - VICTORY (Culture) at T385 and its engine refuses to advance the turn, so the conquest cannot continue: Georgia still held 8 cities and India 8. Retired because the match is over, not because the goal was met."
     at: 2026-10-07T23:45:20+08:00
     status: expired at T385
     chinese backup: prompts/tasks/cn/049-take-every-remaining-city-of-georgia-and-india.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 049 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:29+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/049-take-every-remaining-city-of-georgia-and-india.cn.md
-->
