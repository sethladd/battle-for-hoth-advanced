# Battle of Hoth — Advanced

A fan-made expert expansion and toolkit for *Star Wars: Battle of Hoth* (Days of Wonder).
It adds a deeper command deck, on-board leaders, two new units, and a full game simulator
used to balance everything across all 17 booklet scenarios.

## ▶ Start here

**If you just want to play, read [`Battle_of_Hoth_Advanced_Rulebook.pdf`](docs/Battle_of_Hoth_Advanced_Rulebook.pdf).**
It's a single, polished, print-ready document with everything a player needs: what's new,
**how to adopt the variant**, the new units and leaders, the entire deck as **print-and-play
59 × 91 mm cards** (just print and cut), and a quick reference. Most people need nothing else.

Everything else in this repo — the markdown sources in `docs/`, the simulator, and the web
tools — is for tinkering, balancing, and regenerating that PDF, and is entirely optional.

## What's here

- **An Advanced command deck** (~24 cards/side) that keeps the basic game's sector-locked
  ordering tension but adds reactions, combos, escalation cards, and richer tactics.
- **On-board leaders** — six characters (Luke, Han, Leia, Vader, Veers, Piett) that ride
  with a unit, project auras, and can be hunted for bonus medals.
- **Two new units** — the Rebel **Tauntaun Scout** (cavalry) and the Imperial **AT-ST**
  (scout walker).
- **A Python simulator** (AI vs AI) with all units, terrain, scenarios, leaders, and
  destroyable structures, used to verify balance.
- **Two web tools** — a scenario **map annotator** and a **game replay viewer**.

## Quick start

- **Play the variant:** read / print [`Battle_of_Hoth_Advanced_Rulebook.pdf`](docs/Battle_of_Hoth_Advanced_Rulebook.pdf) (see "Start here" above) — that's all most players need.
- **Canonical rules sources** (what the PDF is generated from) live in [`docs/`](docs/).
  - [`Advanced_Deck_Compendium.md`](docs/Advanced_Deck_Compendium.md) — every card.
  - [`Advanced_Leaders.md`](docs/Advanced_Leaders.md) — the on-board leader system.
  - [`Advanced_Units.md`](docs/Advanced_Units.md) — the Tauntaun Scout and AT-ST.
  - [`Balance_Report.md`](docs/Balance_Report.md) — simulation results and tuning.
- **Watch a game:** open [`tools/hoth_game_replay.html`](tools/hoth_game_replay.html) in a
  browser. Play/step through a simulated battle (moves, dice, hits, retreats, KOs, cards,
  and each player's hand).
- **Annotate scenarios:** open [`tools/hoth_map_annotator.html`](tools/hoth_map_annotator.html).
  Calibrate once (4 clicks), then place units/terrain/objectives/leaders on any scenario
  map and Export the positions.

## Using the tools

### Game replay viewer (`tools/hoth_game_replay.html`)

Double-click to open it in a browser — it already contains one recorded game.

- **Controls:** `▶ Play` auto-advances; `◀ Prev` / `Next ▶` step one sub-step at a time; the
  slider scrubs; the speed slider sets the pace.
- **Each turn is broken into sub-steps** — **Move → Fire → Retreat** — shown as a colored
  phase pill, so you can follow one action at a time.
- **On the board:** units show a type letter (T=trooper, S=speeder, Tn=tauntaun, A=artillery,
  W=AT-AT, St=AT-ST, D=droid) and figure count; red = Rebel, blue = Empire. A unit carrying a
  leader has a gold ring and ★name. Actions are signaled in place: green move arrows, a red
  **−N HIT** burst, a gray **MISS** ring, a gold **KO** burst, and red **RETREAT** arrows.
- **Side panel:** the card played (with a description of what it does), the turn's event log
  with the actual dice faces, and the running medal totals.
- **Both hands** are shown at the bottom; the active player's chosen card is highlighted in
  gold (hover any card for its effect).
- **Watch a different battle:** `cd simulator && python3 build_replay.py <scenario> <seed>
  [rebelLeader] [empireLeader]`, then reopen the file. Example: `build_replay.py 3 12 Han Veers`.

### Scenario map annotator (`tools/hoth_map_annotator.html`)

Used to mark exact unit/terrain/objective positions on the real scenario maps.

1. **Calibrate once.** Click **🎯 Calibrate grid** and click the 4 prompted hex centers
   (top-left, top-right, bottom-left, then the inset second-row hex). This aligns the
   clickable hex grid to the printed map; it's saved and applies to all scenarios.
2. **Pick a scenario** from the dropdown.
3. **Pick a brush** (units, terrain, objectives/exits/structures, or ★ leaders) and **click a
   hex** to place it. Units, terrain, and markers are separate layers, so a trooper in a
   trench is two clicks on the same hex; click the same brush on a hex again to clear it.
   Row 0 is the top (Empire) edge — just click what you see; orientation is handled.
4. **Export ALL** downloads the positions as JSON (and copies them to the clipboard). Drop
   that file into `data/` (or paste it back) to use it in the simulator.
5. **Resume/refine:** paste a previous export into the box and click **Load** — e.g. load
   `data/hoth_scenario_positions_full.json` to review and fix the auto-detected maps (5–17).

## Directory layout

```
.
├── README.md                  ← you are here
├── LICENSE
├── docs/                      ← start here
│   ├── Battle_of_Hoth_Advanced_Rulebook.pdf   ← the player-facing, print-ready rulebook
│   ├── Advanced_Deck_Compendium.md
│   ├── Advanced_Leaders.md
│   ├── Advanced_Units.md
│   └── Balance_Report.md
├── tools/                     ← open in a browser (self-contained)
│   ├── hoth_map_annotator.html
│   └── hoth_game_replay.html
├── data/                      ← scenario unit/terrain positions (JSON)
│   ├── hoth_scenario_positions.json       (scenarios 1–4, hand-verified)
│   └── hoth_scenario_positions_full.json  (all 17; 5–17 auto-detected)
└── simulator/                 ← the Python engine + build scripts
    ├── hoth_engine.py          board, units, dice, movement, attack, leaders, structures
    ├── hoth_sim.py             AI, turn loop, card execution, game runner
    ├── hoth_cards.py           the Advanced (and Basic) command decks
    ├── hoth_scenarios.py       all 17 scenarios + special-rule loader
    ├── card_text.py            parses canonical card text from the compendium markdown
    ├── build_compendium.py     validates docs/Advanced_Deck_Compendium.md vs the card defs
    ├── build_replay.py         regenerates tools/hoth_game_replay.html
    ├── build_annotator.py      regenerates tools/hoth_map_annotator.html
    ├── detect_maps.py          auto-detects unit/terrain positions from the maps
    ├── generate_annotations.py builds data/hoth_scenario_positions_full.json
    └── source/                 original DoW rulebook, scenario book, card list
```

## Running the simulator

All scripts run from the `simulator/` directory (paths are relative):

```bash
cd simulator

# quick balance check (alternating first player)
python3 hoth_sim.py 200

# watch a specific scenario/seed, optionally with leaders
python3 build_replay.py 1 7 Leia Vader     # scenario 1, seed 7, Leia vs Vader
#   then open ../tools/hoth_game_replay.html

# check the card compendium is in sync with the definitions, and regenerate the annotator
python3 build_compendium.py     # validates docs/Advanced_Deck_Compendium.md (no output file)
python3 build_annotator.py
```

Programmatic use:

```python
import hoth_sim as S, hoth_scenarios as HS, json
data = json.load(open('../data/hoth_scenario_positions_full.json'))
result = S.play_game(scenario=HS.SCENARIOS[3], annot=data['3'],
                     rebel_leader='Luke', emp_leader='Vader')
print(result['winner'], result['medals'])
```

The core simulator needs only the Python 3 standard library; the map/replay **build**
scripts additionally need `pdfplumber`, `numpy`, and `opencv-python`.

## Why the deck is "advanced"

The basic game's 16-card deck is almost entirely about **where** you may act: nine of its
cards are sector-locked orders (Assault/Raid/Recon Left, Center, Right), plus a couple of
multi-sector cards and a handful of simple one-shot tactics. A turn is mostly "this card lets
me order N units in this sector — go." That tension is great, but the *decisions inside a
turn* are shallow, and there's essentially no play on the opponent's turn.

The advanced deck keeps that sector-locked backbone intact (so the core "you can't always act
where you want" pressure survives) and layers expert-level decision-making on top:

| | Basic deck | Advanced deck |
|---|---|---|
| Sector-locked ordering | Yes (the whole point) | **Yes — preserved** (9 Probe/Raid/Assault L/C/R) |
| Play on the opponent's turn | None | **Reaction cards** (Ambush, Evasive Maneuvers, Suppressing Fire) |
| Rewarding focused attacks | Incidental | **Combo cards** (Focus Fire, Concentrated Fire) that pay off concentration |
| Comeback / snowball tension | None | **Escalation cards** (Desperate Valor scales as you fall behind; Crush Them as you pull ahead) |
| Card economy | Fixed draw | **Draw/sustain cards** (Forward Command, Regroup) — manage your hand |
| Heroes | 3 cards shuffled in | **On-board leaders** — auras, transfer, and capture risk (a whole subsystem) |
| Roster | Stock units | **+ Tauntaun Scout and AT-ST** filling the cavalry / medium-walker niches |

What actually makes it "advanced":

- **Decision density.** Every turn you weigh combos (will a second attacker finish that
  unit?), reactions (do I hold Ambush or spend it?), escalation timing, and card economy —
  not just which sector to push.
- **Two-sided play.** Reaction cards mean your turn is never fully safe and the deck rewards
  reading the opponent, not just optimizing your own moves.
- **State-dependent cards.** Escalation cards make the *score* part of your hand — falling
  behind arms the Rebels, pulling ahead sharpens the Empire — which keeps games swingy and
  tense to the end.
- **Positional commitment.** Leaders turn one unit into a powerful, mobile threat that must
  be screened and protected, adding a layer of maneuver and risk absent from the base game.
- **Faction identity.** Basic decks are near-mirror images; the advanced Rebel and Imperial
  tactic suites diverge (mobility/resilience/comeback vs. armor/suppression/snowball) so the
  two sides *feel* different to pilot.

It is deliberately a bit longer and heavier — aimed at players who already know the base game
and want more rope. See [`docs/Advanced_Deck_Compendium.md`](docs/Advanced_Deck_Compendium.md)
for the full card list.

## Design diary

**Goals.**
- *Add real strategic depth for expert/older players* — more meaningful decisions per turn
  (combos, reactions, escalation, leader positioning) without bloating playtime much.
- *Stay true to the Richard Borg command system* — same hexes, symbol dice, command-card
  economy, and victory medals; everything new is expressed in those existing terms.
- *Reward planning over luck* — give players levers (focus fire, cover, leader auras,
  hit-and-run) that let skill shift outcomes.
- *Keep both factions viable but distinct* — Rebels mobile/resilient/comeback-oriented,
  Empire armored/aggressive/snowballing.
- *Be verifiable* — design only what could be simulated and balance-checked, not just
  asserted.

**Constraints (deliberate boundaries).**
- *Preserve the sector-lock tension.* The single most important rule we protected: most
  cards still dictate **which** sector you may act in (Probe/Raid/Assault Left/Center/Right).
  An early draft let tactics fire anywhere and quietly gutted the game's core "you can't
  always act where you want" pressure — so we reverted to sector-locked section cards with
  only two flexible cards per side.
- *Work within the box.* New content reuses existing components and conventions; the only
  genuinely new pieces are the Tauntaun Scout and AT-ST (proxy figures), each slotted to
  fill an empty niche (light cavalry; medium walker) rather than power-creep.
- *Asymmetry is the scenario's job.* Many scenarios are intentionally lopsided (it's the
  Empire steamrolling Hoth); the **decks and leaders** are balanced against each other, and
  per-scenario fairness is tuned via victory targets, not by flattening the factions.
- *Leaders must be a risk, not just a buff.* A leader makes a unit dangerous but becomes a
  high-value target — capture grants bonus medals — so fielding one is a real gamble.

**What the simulation taught us (and changed).**
- Greedy, focused AI play is already strong; hand-tuned lookahead didn't beat it, which kept
  the AI simple and the design honest.
- The first leader pass was wildly unbalanced (Leia/Luke dominant, Han actively *harmful*);
  reading "reroll one die" literally, localizing Leia's aura, and buffing Han brought all
  six into a tight band.
- Structural-objective scenarios (shield generators, ion cannon) were unwinnable until those
  objects were modeled as destroyable structures — a reminder that abstractions hide
  imbalance.
- The AI under-uses mobility, so we credit mobile units/leaders (Tauntauns, Snowspeeders,
  Han) more than the raw win rates suggest.

## Status & caveats

The advanced decks are balanced (~55/45 in a fair mirror) and don't distort the scenarios;
leaders are balanced and distinct after tuning. Some scenarios are intrinsically lopsided
under automated play, a few structural objectives are approximated, and auto-detected
terrain for scenarios 5–17 is sparse — see [`docs/Balance_Report.md`](docs/Balance_Report.md)
for the full picture and the per-scenario numbers.

## License

This project is **dual-licensed**, and one part is not ours to license at all:

- **Code — BSD 3-Clause.** Everything in `simulator/` (the engine, AI, scenario logic, and
  build scripts) and the JavaScript/HTML of the tools in `tools/` is licensed under the
  [BSD 3-Clause License](LICENSE).
- **Original written & design content — CC BY 4.0.** The original creative work in this
  project — the rules and design documents in `docs/` (the Advanced Deck Compendium, Advanced
  Leaders, Advanced Units, and Balance Report), this README, and the new card/leader/unit
  designs themselves — is licensed under
  [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-CONTENT.md). You may
  share and adapt it with attribution.
- **Not licensed by us:** the publisher materials in `simulator/source/` (the rulebook,
  scenario book, and card list PDFs/ODT) and the underlying *Star Wars* / *Battle of Hoth*
  intellectual property remain © & ™ their respective owners (see Attribution). Our CC BY
  license covers only our original additions, not the game it builds upon.

## Attribution

Built on *Star Wars: Battle of Hoth* by Richard Borg and Adrien Martinot, © & ™ Lucasfilm
Ltd., published by Days of Wonder. The PDFs and card list in `simulator/source/` are the
publisher's materials, included as design references. Unofficial fan project — not
affiliated with or endorsed by Days of Wonder, Asmodee, or Lucasfilm.
