# Battle of Hoth — Advanced

A fan-made expansion and toolkit for the *Star Wars: Battle of Hoth* board game by Days of Wonder. This project includes an alternative expert-level command deck, advanced unit and leader rules, scenario tooling, and a game engine for simulation and replay.

## Contents

### Rules & Reference
- `DOWSWB0101_EN_BATTLEOFHOTH_RULES_20250121_LD.pdf` — Official rulebook
- `DOWSWB0101_EN_BATTLEOFHOTH_SCENARIO_WEB.pdf` — Official scenario book
- `STAR_WARS_BATTLE_OF_HOTH_Cards.odt` — Full card compendium for the base game (all 60 cards)

### Advanced Rules
- `Advanced_Deck_Compendium.md` — Alternate 23-card expert deck with new mechanics (Reaction cards, Escalation cards, sector-locked section cards)
- `Advanced_Leaders.md` — Expanded leader rules and passive traits
- `Advanced_Units.md` — Advanced unit rules

### Tooling
- `hoth_engine.py` — Core game engine
- `hoth_sim.py` — Game simulation / AI
- `hoth_scenarios.py` — Scenario definitions
- `hoth_scenario_positions.json` — Scenario starting positions
- `hoth_cards.py` — Card data
- `build_compendium.py` — Builds the deck compendium document
- `build_annotator.py` — Builds the map annotator tool
- `build_replay.py` — Builds the game replay viewer

### Interactive HTML Tools
- `hoth_map_annotator.html` — Visual map editor for annotating scenarios
- `hoth_game_replay.html` — Step-through replay viewer for recorded games

## Getting Started

Open the HTML tools directly in a browser — no server required. For the Python tooling, run any of the `build_*.py` scripts with Python 3.

```bash
python3 build_compendium.py
python3 build_annotator.py
python3 build_replay.py
```

## License

See [LICENSE](LICENSE). Fan content only — *Star Wars* and *Battle of Hoth* are trademarks of their respective owners. This project is not affiliated with or endorsed by Lucasfilm, Asmodee, or Days of Wonder.
