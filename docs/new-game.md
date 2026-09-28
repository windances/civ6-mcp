---
title: Starting a new game — the first three decisions
---

Moved out of `AGENTS.md` on 2026-09-27, when that file was cut back to the running-game loop.
Nothing was reworded: this is the section as it stood. **A new game is the only time it
applies** - once the loop is running, the turn procedure and the strategy directive own these
decisions.

## Game Start

Before your first turn:
1. Read your civ's unique abilities, units, and buildings — what is this civ designed to do?
2. Identify the tech/civic that unlocks your unique unit; plan a research path to reach it.
3. Form a working hypothesis for a victory path. Hold it loosely — geography and rivals will clarify things through the Classical era.

Early choices compound. Each decision shapes what's available 20, 40, 60 turns later. A scout reveals the map early; a defensive unit lets your settlers move safely; more cities mean more districts which mean more everything. Religious civs often benefit from Holy Site infrastructure before the Great Prophet pool fills. What you don't build early, you pay for later.

## Power, planned at the start (Gathering Storm)

Power is the one late-game bill that is decided early: a city is either fully powered or its
power-load buildings — Research Lab 3, Stock Exchange 3, Broadcast Center 3, Factory 2, Stadium 2 and
the rest — run at **less than half** their normal yield (`POWER_MAX_PRODUCTION_MODIFIER_PENALTY = -50`,
`Expansion2_GlobalParameters.xml:224`), and by the time a Campus city is unpowered the fix is a district
and a building you did not queue.

Two consequences for a plan made on turn one:

- **An Industrial Zone is placed for its 6-tile ring, not for itself.** Coal, oil and nuclear power
  plants are mutually exclusive in a city, require a **Factory**, and each serves the cities **within
  six tiles** — so the clusters to plan are the rings, and a wide empire needs several plants plus
  free sources for whatever no ring reaches.
- **Fuel is an army decision as much as a city one.** A plant burns 1 coal or oil for **4 power** (1
  uranium for 16), so a plan that spends oil on power is spending the oil its tanks and artillery
  upgrade on. Coal is the fuel to burn; the free sources are a Hydroelectric Dam **+6**, Geothermal
  **+4** and Solar/Wind **+2** each, which cost production and builder charges instead of a resource.

The full table, the four deciding rules and the report line are in
`prompts/tactics/08-war-and-the-home-front.md`, under **Power — the bill the compounding cities run
up**; `get_cities` prints each city's `Power available/required` and marks an unpowered one.

