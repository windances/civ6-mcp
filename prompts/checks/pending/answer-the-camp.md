# Staged check: `answer-the-camp` — activate on the next MCP restart

This rule is **not** in `../turn-checks.md`, and that is deliberate. It reads
`metric(camps_within_3)`, a metric that did not exist before 2026-09-26; the file is re-read by
`end_turn` on **every** turn, but the *metric set* lives in the running MCP server's memory. So a rule
placed in the live file while an older server is playing would be evaluated against a metric dict that
has no such key, and `turn_checks.evaluate` raises on an unknown key - turning the rule into
`CHECK FAILED [answer-the-camp]: un-evaluable: metric('camps_within_3') is not available this turn`
**every single turn**, from a rule nobody can satisfy until that process restarts. (The evaluator also
evaluates both sides of `and` eagerly - `turn_checks.py:208-209` builds the value list before calling
`all()` - so no ordering of the gate can short-circuit around the missing key.)

Activation, in one step at the moment the MCP server is restarted (a new session, or the same task
re-run):

1. Confirm the server is new: `metric(camps_within_3)` must be in the metrics built by
   `end_turn._contact_metrics` (`src/civ_mcp/end_turn.py`), added with the camp scan
   `_camps_within_3`.
2. Cut the block below into `../turn-checks.md`, next to the other contact rules.
3. Run one turn and check that the rule appears in the contact section rather than as an
   un-evaluable failure: with a camp within three tiles of a city and a barbarian within three tiles
   of our units, it should now report `CHECK FAILED [answer-the-camp]` until something attacks.

Why the rule exists at all: a camp is not a unit, so no contact metric can see it, and the only camp
detector in the adapter is the post-move visibility probe - which announces a camp on the turn a unit
first *reveals* the tile and never again. On the T59 replay the camp beside 北京 spawned the Spearman
that forced a 160-gold Warrior purchase at T65, and nothing in the turn result had mentioned a camp.
The human's instruction is that a camp is a `prompts/tactics/07-pre-war-analysis.md` target; this rule
is what makes that mechanical rather than aspirational.

```markdown
<!-- check
id: answer-the-camp
when: metric(camps_within_3) >= 1
require: metric(attacks_this_turn) >= 1
message: A barbarian camp stands within three tiles of one of our cities and nothing attacked this turn. A camp is a tactics/07 target (human instruction 2026-09-26), and it is destroyed by force - one military unit MOVING onto its tile clears it. Run the camp gates and answer them in the diary: CAMP (x,y) terrain; GUARD (every barbarian within two tiles, class/CS/HP); FORCE (two attackers with the counter unit plus the unspent unit that walks in - barbarian Spearmen are anti-cavalry, so ranged plus melee, never cavalry into spears, never a Scout/Builder/Trader); GROUND (what the last step costs, from a tile we already hold); WORTH (gold, era score, the CIVIC_MILITARY_TRADITION inspiration, and what it has been spawning); HOLD (which city gives up its garrison); CONVERT (any barbarian next to our melee worth the human's Three-Six Stratagems play). A camp left alone keeps producing era-appropriate units beside that city - the camp beside 北京 (T83 map read: (60,29); an earlier note said (60,30)) produced the Spearman that cost 160 gold at T65 - so either this turn's attack is on its guard, or the diary says what the raid is waiting for.
-->
```
