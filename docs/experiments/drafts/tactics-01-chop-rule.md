# Staged doctrine edit for A5 - apply only after A3's window closes

**Why staged and not applied now.** `prompts/tactics/01-unit-production.md` is read by the
advisors of the *running* session (A3). Adding a chop rule while A3 plays would introduce an
uncontrolled behaviour into A3's own window - the same reasoning the retro already records for
`turn-checks.md` ("editing `turn-checks.md` mid-attempt would stop the rule firing and erase the
measurement it was producing"). A3's variable is the target's defences; its opening is already
one confound (task 034's pinned opening was broken at T15), and it does not need a second.

Apply this in the commit that retires task 034, before A5 is published.

## The edit

In `prompts/tactics/01-unit-production.md`, section `## Production order`, after item 2
("Then the screens") and before item 3 ("Then the economy buildings"), insert the chop rule as a
sub-paragraph of item 3:

> **One exception, and it is a timing one: while the train is the bottleneck, a feature removal
> (chop or harvest) in a city that is building a unit goes into that unit.** A chop is production
> the city already owns, it arrives in one turn, and the buildings it would otherwise fund are
> worth less than a Catapult that exists five turns earlier. **Governor Magnus in the
> war-production city is what makes this worth doing**: his base ability Groundbreaker
> (`GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER`, `BaseAbility="true"`, +50% to plot
> harvests and feature removals in his city) is held from the moment he is appointed there - it is
> not a promotion to spend, and `promote_governor` on it answers `ERR:ALREADY_PROMOTED`. The
> effect is only banked when the feature actually disappears, and a tile outside the city's owned
> ring is refused, so the record names the city and the tile for every chop. Attempt **A5** is
> this exception measured against the economy it defers.

## Provenance of the Groundbreaker sentence

Checked in the game's own files, not from memory (this is where the claim comes from):
`DLC/Expansion1/Data/Expansion1_Governors.xml:40,151` -
`GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER`, `Level="0"`, `BaseAbility="true"`,
"+50% yields from plot harvests and feature removals in city". A5's own brief therefore records
the appointment turn, the assignment turn and the turn `established=1` reads, and treats the
ability's absence from the `GOV_PROMO` list as the evidence it is in force.

After the edit: `python scripts/fix-text-encoding.py` (the file carries a BOM), then
`python .tools/kb.py index` (the knowledge index is derived and goes stale).
