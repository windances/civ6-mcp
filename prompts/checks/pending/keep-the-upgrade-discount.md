# keep-the-upgrade-discount - STAGED, do not cut in until a server computes the metric

Written 2026-09-28 (T227). Staged rather than live because `prompts/checks/turn-checks.md` is re-read
every turn by the *running* process, whose metric set lives in memory: a rule naming
`upgrades_gated_by_discount` before a server computes it reports `un-evaluable` every turn and nobody
can satisfy it. The code that computes it ships in the commit that adds this file; the rule moves up
to `../turn-checks.md` once a session running that code has started.

**Metric it needs:** `upgrades_gated_by_discount` - computed by `end_turn._gated_by_discount` from the
unit list plus the agent diary row's `gold` and `policies`, counting only the offers whose *halved*
price the treasury could afford and whose quoted price it cannot, and only while
`POLICY_PROFESSIONAL_ARMY` is not slotted.

**Why it exists - measured T201-T217.** The free policy window at T201 traded
`POLICY_PROFESSIONAL_ARMY` ("50% discount on all unit upgrades") for `POLICY_MEDINA_QUARTER`, to clear
a housing hard stop in 西安 - a defensible trade that nothing ever asked to be re-examined. Every
pending price doubled with it (115 -> 230, 155 -> 310, 190 -> 380), and `UPGRADE AVAILABLE` lists only
what the treasury can already pay, so the doubling did not make the offers loud: it made them
**silent**. Over T204-T215 the treasury went 621 -> 768 while a Knight -> Cuirassier (230g) and two
Crossbowman -> Field Cannon (310g each) sat unbought, and T216-T217 bought two of them at 540g where
270g would have done. At T224 the last Crossbowman went the same way (283.9 -> 2.1 gold).

`GameState.set_policies` already warns at the moment the card is *dropped* (`NOTE:UPGRADE_DISCOUNT_LOST`).
Nothing covered the state: the card is absent and an upgrade sits one policy change away from being
affordable. `end_turn._upgrade_event` now says so in the `UPGRADE AVAILABLE` block for exactly this
case - the channel the agent reads every turn - and this rule is the enforced half.

The proposed rule, in the shape `turn-checks.md` uses:

```
<!-- check
id: keep-the-upgrade-discount
when: metric(upgrades_gated_by_discount) >= 1
require: metric(upgrades_gated_by_discount) <= 0
message: An upgrade is affordable at the discount price and not at the price the treasury is quoted, because POLICY_PROFESSIONAL_ARMY ('50% discount on all unit upgrades') is not in the government - every offer has cost double since the T201 free window traded it for housing (measured 115 -> 230, 155 -> 310, 190 -> 380, and 540g paid at T216-T217 where 270g would have done). Put the card back at the next free policy change, or say in the diary which policy is worth more than halving every upgrade.
-->
```

Notes for whoever cuts it in:

- The gate needs the diary row to carry both `gold` and `policies`; a row without `policies` yields an
  empty list and the rule stays quiet rather than guessing (the field is in every agent row).
- It is deliberately narrow: it fires only in the *silent* case - the quoted price is unaffordable
  while the halved one is (`gold >= cost // 2 and gold < cost`), so the offer is not listed anywhere
  and the missing card is the whole reason. When an offer *is* affordable the `UPGRADE AVAILABLE`
  block already names its price and the class rules nag about buying it. A treasury that cannot
  afford the upgrade either way is a gold problem, which `carrying-capacity` and the empire warnings
  already report.
- If `upgrade_unit` ever stops being the only gold sink this card discounts, the metric - not the rule
  - is where that changes.
