# Battle of Hoth — Advanced

A fan-made expert expansion and toolkit for *Star Wars: Battle of Hoth* (Days of Wonder).
It adds a deeper command deck, on-board leaders, two new units, and a full game simulator
used to balance everything across all 17 booklet scenarios.

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

- **Read the rules:** open the files in [`docs/`](docs/).
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

## Directory layout

```
.
├── README.md                  ← you are here
├── LICENSE
├── docs/                      ← rules & report (start here)
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
    ├── build_compendium.py     regenerates docs/Advanced_Deck_Compendium.md
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

# regenerate the card compendium and the annotator
python3 build_compendium.py
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

## Status & caveats

The advanced decks are balanced (~55/45 in a fair mirror) and don't distort the scenarios;
leaders are balanced and distinct after tuning. Some scenarios are intrinsically lopsided
under automated play, a few structural objectives are approximated, and auto-detected
terrain for scenarios 5–17 is sparse — see [`docs/Balance_Report.md`](docs/Balance_Report.md)
for the full picture and the per-scenario numbers.

## Attribution

Built on *Star Wars: Battle of Hoth* by Richard Borg and Adrien Martinot, © & ™ Lucasfilm
Ltd., published by Days of Wonder. The PDFs and card list in `simulator/source/` are the
publisher's materials, included as design references. Unofficial fan project — not
affiliated with or endorsed by Days of Wonder, Asmodee, or Lucasfilm.
