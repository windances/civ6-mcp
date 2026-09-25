# 3. Under attack / 部队被攻击时，对敌人行动策略

Read whenever one of our units lost HP during the AI turn (`damaged_this_turn >= 1`), or when an
enemy attacked a city or a civilian.

## The answer is never a trade

A unit that is hit and ignored is hit again next turn, and the attacker chooses the moment. The
response is a three-step procedure, and the turn result already carries the first step's data in
its `BATTLE ASSESSMENT` block.

## 1. Assess

- Which of our units were hit, for how much, and where they now stand.
- Who did it: type, class, combat strength, HP, distance (`BATTLE ASSESSMENT` lists every enemy
  within three tiles with all of that).
- What is **killable this turn** - the block names the ones at low HP with our units in range.
- What the hit unit's escape routes are: terrain defence, a city, a river line, or nothing.
- Whether the attack is part of a bigger move (several enemies converging, a stack forming, a
  second city's units appearing).

## 2. Mass

Bring the units standing nearby into contact - **two or three attackers on one target kills it
this turn; one attacker trades**. `mass-on-contact` fails while an enemy is in contact and only
one of our units is within two tiles, whether or not we attacked. Do not feed units in one at a
time: that is how a Battering Ram and a Warrior were lost in consecutive turns at T109-T111.

## 3. Annihilate

Concentrate every attacker on the same target so it reaches 0 HP this turn. **What a survivor heals
depends on where it stands, and the manual gives the numbers** (`HEALING DAMAGE`, p.89): a unit
heals **20 HP per turn in a city, 15 in friendly territory, 10 in neutral, 5 in enemy territory** —
and naval units heal only in friendly territory, at 2. So:

- an enemy **inside a city** is the one that must not be left alive: it heals 20 and comes back at
  full strength (`finish-the-wounded`);
- an enemy in the **field** heals 5-10, which makes "leave it for next turn" less catastrophic
  than the city case - but it still gets to attack first, so the decision is about tempo, not HP;
- **our own damaged units should rotate back across the border.** Healing at 5-10 in enemy
  territory versus 15 at home is a three-fold difference: a unit that is too hurt to attack is
  usually better off walking one or two tiles back into our territory, healing at 15, and
  returning, than sitting in place at 5. A city of ours heals 20 (and a unit inside it heals 20),
  which is the fastest repair there is - and the reason not to drain the front into those
  garrisons is `one-garrison-per-city`.

Then stay concentrated and finish the rest of the group before returning to the original
objective - a beaten field force is the only thing that makes the next city cheap.

## The cases that need a different answer

- **A civilian was hit or is threatened.** Civilians cannot fight: move it out, or put a unit on
  it. Do not trade a unit for a builder, and do not leave the builder where it was.
- **The attacker is stronger than anything we can mass this turn.** Refuse the battle: withdraw
  the hit unit to a city, hills or forest, keep the stack together, and counterattack when the
  numbers exist. Record that withdrawal as the decision - the rule fires on the fact that a unit
  was hit, and a stated withdrawal is the accepted answer.
  - **Withdraw the shooters, not the screen.** A disengagement that pulls the *whole* line back
    empties the front, and the enemy walks into it: live T114, the stack was pulled north out of a
    Battlecry Swordsman's reach, the melee came with it, and a Russian Horseman was standing on
    Moscow's doorstep the next turn grinding a city that had no walls. Pull back the siege and the
    ranged, and leave the melee holding the ring tiles between the enemy and the city - a screen
    that does not fight is still doing its job when it is the thing the enemy has to attack first.
- **We are mid-assembly when it happens.** A hit taken on the march is a different problem from a
  hit taken at the wall: the army is strung out, the tail is the siege train, and the answer that
  matters is whether the wounded unit can still reach its ring tile and whether the contact has
  invalidated the rally point. Run `tactics/04-staging-out-of-range.md` **step 5** first, then this
  file's mass-and-annihilate. The measured shape of it: T103 Russia declared on the assembly, the
  next three turns went on clearing the field in contact (T104–T106), and the first volley on the
  city waited until T107.
- **We are mid-assault when it happens.** Decide explicitly: finish the city (if the walls are
  down and a melee unit can walk in this turn) or break off the assault and deal with the field
  force first. What is never acceptable is leaving the siege train between the two.
- **A city was attacked.** Garrison it (one unit), repair the walls if they are down, and clear
  the attacker with the field army - a city under siege is not a reason to drain the front.

## Prohibitions

- Do not leave the hit unit standing where it was hit.
- Do not answer with one unit when more are within reach of the attacker.
- Do not chase the attacker into fog.
- Do not buy peace to make it stop: the directive forbids peace, and a war that is stopped
  halfway is pure cost.
- Do not convert the response into a march on a different objective - the attacker first, or an
  explicit decision to disengage.

## What to report

The hit units and the damage taken; the attacker and its class/strength/HP; the killable target
and the units assigned to it (named, with tiles); the units that should move up to screen or
close; and, if the answer is to withdraw rather than fight, where to and why. Flag any unit that
is isolated - no friendly unit within two tiles - as the first thing to fix.
