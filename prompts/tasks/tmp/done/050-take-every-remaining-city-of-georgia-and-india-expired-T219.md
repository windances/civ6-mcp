# TEMP TASK 050 - Take every remaining city of Georgia and India

added:     2026-10-07 (human instruction: 继续攻占所有城市。（2026-10-07，新任务；上一局 T385 已报文化胜利，本任务从游戏恢复可推进的那一刻开始执行。）)
expires:   turn 420 - 35 turn(s) from T385, the turn the match stands on (read from the save); a hard stop,
           retired either way on that turn
done when: count == 0 cities owned by Georgia and count == 0 owned by India, as read by get_diplomacy (or the
           domination victory the game reports itself); they held 10 and 8 at T385
overrides: the compounding default: up to eight cities may stay on unit production while both rings are taken,
           and the faith balance may be spent on units or Great People
scope:     the conquest of every city Georgia and India own, on both fronts, once the match is playable again;
           nothing else changes

## Read this first: the state it starts from

The match reported `GAME OVER - VICTORY (Culture)` at T385, and the session that was playing found the
engine would not advance a turn afterwards. So step 0 is not a game action: **the victory screen has
to be cleared** before anything below can happen - in the game UI that is the "one more turn" button
on the victory screen (`dismiss_popup` may clear it; if it answers `No popups to dismiss` while the
turn still will not advance, read the screen with `.tools/whats-on-screen.py` and ask the human to
click it). `get_game_overview`'s `GAME OVER` line disappears once the match is playable again, and
that line is the test for "step 0 is done".

A task published after a victory cannot be executed in that position - that is the lesson the last
one recorded (T385, task 049). This file exists so the order survives the pause, not because it is
playable yet.

## The order

Take every remaining city of Georgia and of India. Peace is never proposed and every offer is refused
(the directive), so this ends when the map does.

## Where it stood when the match ended

50 cities of ours against Georgia's 10 and India's 8 (both were 10 at T370). Both enemy armies were
shattered - Georgia 231 -> 144 military, India 260 -> 84 - against ours over 2000. Gold ~1470 at
-18/turn (the rate improves with every city taken) and faith ~12500 unspent, which is four land units
if the Grand Master's Chapel is built.

Two targets were one move from falling:

- **Chennai (10,32), India**: 20/200 HP and **walls 0**, with a Destroyer within two tiles - one
  melee attack takes the city, and a Destroyer is a melee naval unit so it can hold a coastal one.
  A capture is unresolved until `city_action(city_id, "keep")` answers, and that blocks the turn.
- **Nazca (21,36), city-state**: walls ground from 294 to 209 with no melee unit within two tiles -
  park a Modern Armor or Mechanized Infantry adjacent while the guns finish the wall.

## How to take the rest

1. **Wall-less cities first** - most of India's are `walls none`, and a three-gun corps plus two melee
   units takes one in two or three turns. `get_target_report(x, y)` prints the pool, the walls and
   the garrison in one call.
2. **Georgia's 400-wall ring last, with the full train**: bombard to zero walls, keep the melee
   adjacent, and remember **only a melee unit can capture** a city - ranged units cannot.
3. **Never open an assault that cannot win** (`prompts/tactics/07-pre-war-analysis.md`), and never
   leave a capture unresolved.
4. **Keep the train fed while the front is hot** (up to eight cities on unit production; the rest
   compound), because every city taken is what pays for the next corps.
5. **Missionaries and Apostles at war are destroyed** (`condemn`), as always. No rams, no siege
   towers, ever.

## Done when

`count == 0` cities owned by Georgia and `count == 0` owned by India, as read by `get_diplomacy` - or
the domination victory the game reports itself. Retire this file that turn and record in the diary
how many turns each ring took, and whether the victory screen pause cost anything.

<!-- published by scripts/temp-task.py
     command: python scripts/temp-task.py --root . add --title "Take every remaining city of Georgia and India" --instruction @.tmp/task050-instruction.txt --done-when "count == 0 cities owned by Georgia and count == 0 owned by India, as read by get_diplomacy (or the domination victory the game reports itself); they held 10 and 8 at T385" --overrides "the compounding default: up to eight cities may stay on unit production while both rings are taken, and the faith balance may be spent on units or Great People" --scope "the conquest of every city Georgia and India own, on both fronts, once the match is playable again; nothing else changes" --why "take every remaining enemy city" --turns 35 --body @.tmp/task050-body.txt --cn @.tmp/task050-cn.txt
     at: 2026-10-07T23:56:49+08:00
     chinese backup: prompts/tasks/cn/050-take-every-remaining-city-of-georgia-and-india.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 050 --expired --turn 420 --note "Conquest incomplete: Georgia held 3 cities (Telavi 28,39; Batumi 25,33; Omalo 25,45) and India 2 (Agra 10,38; Ahmadabad 3,41) when the hard stop arrived; the order continues under the standing no-peace conquest directive."
     at: 2026-10-08T18:47:10+08:00
     status: expired at T420
     chinese backup: prompts/tasks/cn/050-take-every-remaining-city-of-georgia-and-india.cn.md
-->

<!-- retired by scripts/temp-task.py
     command: python scripts/temp-task.py retire 050 --expired --turn 219 --no-gate --no-commit --note "cleared in bulk on the human's instruction after the rollback; new tasks will be published for T219"
     at: 2026-10-10T13:05:30+08:00
     status: expired at T219
     chinese backup: prompts/tasks/cn/050-take-every-remaining-city-of-georgia-and-india.cn.md
-->
