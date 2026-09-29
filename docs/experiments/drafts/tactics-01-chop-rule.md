# Staged doctrine edit for A5 - landed 2026-09-30, after A4's window closed

**Landed.** The rule below is now in `prompts/tactics/01-unit-production.md`, inserted as the
sub-paragraph of item 3 in `## Production order`. It was held until **A4's** window closed, not A3's as
this file first said: the reasoning is the same either way - the file is read by the advisors of whichever
session is *running*, so adding a chop rule while one plays introduces an uncontrolled behaviour into that
attempt's own window, the same argument the retro records for `turn-checks.md`. A4's task retired itself at
**T66** and its record was closed, which is the boundary this waited for; A5 is the attempt the rule exists
for, and it could not be published before the rule was in the doctrine.

**Why staged and not applied at the time.** `prompts/tactics/01-unit-production.md` is read by the
advisors of the *running* session. Adding a chop rule while an attempt plays would introduce an
uncontrolled behaviour into that attempt's own window - the same reasoning the retro already records for
`turn-checks.md` ("editing `turn-checks.md` mid-attempt would stop the rule firing and erase the
measurement it was producing").

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
