# CLAUDE.md — maintainer guide

Guidance for making changes to this project (especially **cards**) and flowing them through
the production pipeline.

## ☆ The golden rule: information flows in ONE direction

```
   canonical Markdown (docs/)  →  Python (simulator/)  →  generated artifacts (PDF · HTML · JSON)
```

1. **Markdown in `docs/` is the single source of truth** for all rules, card text, and
   leader/unit/scenario descriptions. **Author every rules or text change there first.**
2. **Then apply it to the Python** in `simulator/` — implement the *mechanics* of the change
   (`hoth_cards.py`, `hoth_engine.py`, `hoth_sim.py`, `hoth_scenarios.py`) and update any card
   text the build scripts emit so they match the docs.
3. **Then regenerate the artifacts** with the build scripts — the PDF, the web tools, and the
   position JSON. **Never hand-edit a generated artifact**; it will be overwritten.

Never push information backwards (don't edit the PDF or a generated file and back-port it).
This keeps the pipeline sane and predictable.

**Canonical (edit by hand) vs generated (never edit):**

| Canonical source | Generated artifact (do not edit) |
|---|---|
| `docs/Advanced_Leaders.md`, `docs/Advanced_Units.md`, `docs/Balance_Report.md`, `README.md` | `docs/Battle_of_Hoth_Advanced_Rulebook.pdf` (← `build_rulebook_pdf.py`) |
| `docs/Advanced_Deck_Compendium.md` (canonical **card rules text**, hand-edited) | `tools/*.html` (← `build_replay.py`, `build_annotator.py`) |
| `simulator/hoth_cards.py` (card structure/counts), `hoth_engine.py`, `hoth_scenarios.py` (mechanics) | `data/hoth_scenario_positions_full.json` (← `generate_annotations.py`) |

> **Card text is now single-sourced.** Every card's human-readable description lives ONLY in
> `docs/Advanced_Deck_Compendium.md`. `simulator/card_text.py` parses that file, and both the
> PDF (`build_rulebook_pdf.py`) and the replay viewer (`build_replay.py`) read their text from
> it — nothing hard-codes card text. `build_compendium.py` no longer generates the markdown; it
> now **validates** that the markdown and `hoth_cards.py` agree (every card has a description,
> counts match, no stale lines). Run it after any card change.

## Where things live

| Concern | File |
|---|---|
| Card definitions (names, counts, type, order, bonus) | `simulator/hoth_cards.py` |
| Card *mechanics* (how a bonus/order actually resolves) | `simulator/hoth_sim.py`, `simulator/hoth_engine.py` |
| Units, terrain, dice, leaders, structures | `simulator/hoth_engine.py` |
| Scenarios + special rules | `simulator/hoth_scenarios.py` |
| Card *rules text* (human descriptions) | `docs/Advanced_Deck_Compendium.md` (canonical) → parsed by `simulator/card_text.py` |
| Generated docs / PDF / tools / data | `docs/` (incl. the rulebook PDF), `tools/`, `data/` |

All Python scripts run **from the `simulator/` directory** (paths are relative: `source/…`,
`../docs/…`, `../tools/…`, `../data/…`).

## Card text: one canonical source

A card's human-readable rules text is **not** stored in `hoth_cards.py` and is **not**
duplicated across build scripts. It lives in exactly one place:

- **`docs/Advanced_Deck_Compendium.md`** — the canonical, hand-edited card text. Each card is
  one bullet: `- **Name** ×N *(reaction)* — description.` (counts and the `(reaction)` tag are
  optional). Include any unit-type fallback clause directly in the description here.

`simulator/card_text.py` parses this file (`parse()` → `{name: markdown}`, plus `to_reportlab()`
and `to_plain()` converters). Consumers read from it:

- `build_rulebook_pdf.py` → `card_desc()` pulls text via `card_text` (ReportLab markup).
- `build_replay.py` → builds `CARD_TEXT` via `card_text` (plain text; adds `[Leader]` prefixes).
- `build_compendium.py` → **validates** markdown vs. `hoth_cards.py` (does not generate).

To change a card's wording, edit the one markdown line and regenerate. Card *structure*
(name, count, order, bonus) still lives in `hoth_cards.py`; keep the name and `×N` in the
markdown matching it, then run `python3 build_compendium.py` to confirm they agree.

## Recipe: change an existing card  (follow the golden-rule order)

1. **Markdown first.** Edit the card's canonical text/intent in
   `docs/Advanced_Deck_Compendium.md` (and `docs/Advanced_Leaders.md` if it's a leader card).
2. **Then the Python.** Edit the definition in `simulator/hoth_cards.py` (count, `order`,
   `bonus`). Make sure the mechanic is supported: the `order.mode` and every `bonus` key must
   be handled in the simulator (see "Supported keys" below). A *new* bonus key must be
   implemented in `hoth_sim.py` — usually `_do_attack` (combat), `execute_card`/
   `plan_unit_action` (ordering/movement) — and added to `est_attack_value` so the AI values it.
   (No text tables to mirror — the description is read from the markdown you edited in step 1.)
3. **Then regenerate artifacts** (see Pipeline) — PDF and replay (they re-read the markdown).
4. **Validate** (see Validation) — run `build_compendium.py` (markdown ↔ definitions check) and
   re-check balance if you changed power level.

## Recipe: add a new card

1. Add its description line to `docs/Advanced_Deck_Compendium.md` (the canonical text).
2. Append it to the right list in `hoth_cards.py` (`section_cards`, `rebel_tactics`,
   `imperial_tactics`, or `leader_cards`). Set `name`, `count`, `ctype`, `order`, `bonus`
   (name + `×count` must match the markdown line).
3. Implement any new `bonus`/`order` behavior in `hoth_sim.py`/`hoth_engine.py` + valuation.
4. Run `build_compendium.py` (sync check), regenerate, then validate. Re-run the fair-mirror
   balance — a new card can shift it.

## Supported building blocks (no new code needed)

- **`order.mode`**: `fixed_section` (+`zone`: left/center/right), `section`, `flank`,
  `each_section`, `each_flank`, `anywhere`, `none`. **`order.n`**: int or `'all'`.
  **`order.filter`**: `infantry` / `vehicle` / `special` (with the rulebook fallback:
  no eligible units → order 1 unit of choice, no bonus).
- **`bonus` keys already implemented:** `dice`, `close_dice`, `move`, `after_move`,
  `attack_twice`, `ignore_terrain`, `focus` (`'simple'`/`'escalate'`), `escalation`
  (`('comeback'|'snowball', cap)`), `reinforce`, `no_move`, `draw`, `reroll`,
  `retreat_as_hit`, `scout`, `full_move_attack`, `no_enemy_reactions`, `multi_target`
  (`(dice, n_targets)`).
- **Reactions:** set `ctype='reaction'` and `reaction` = `'ambush'`/`'evade'`/`'cover'`
  (handled in `_do_attack` and `try_ambush`).

## Recipe: add a unit or leader

- **Unit:** add to `UNIT_TYPES` in `hoth_engine.py`; add a brush to `build_annotator.py`
  (`PALETTE`); add letter/colour to `build_replay.py` (`UK`/`COL`); add to the rulebook
  roster + `docs/Advanced_Units.md`.
- **Leader:** add to `LEADER_DEF` in `hoth_engine.py` (escort, combat, aura, bonus_medal);
  add its 3 cards in `hoth_cards.py` `leader_cards`; add a `leader_<name>` brush in
  `build_annotator.py`; describe it in `docs/Advanced_Leaders.md` + the rulebook `LEAD` list.
  Leader combat/aura is single-sourced in `LEADER_DEF` — do **not** re-add it as a passive.

## Pipeline — regenerate artifacts

From `simulator/`:

```bash
python3 build_compendium.py      # VALIDATES ../docs/Advanced_Deck_Compendium.md vs hoth_cards.py (no output file)
python3 build_rulebook_pdf.py    # -> ../docs/Battle_of_Hoth_Advanced_Rulebook.pdf (incl. 59x91mm cards)
python3 build_replay.py 1 7 Leia Vader   # -> ../tools/hoth_game_replay.html (scenario seed [leaders])
python3 build_annotator.py       # -> ../tools/hoth_map_annotator.html  (only if units/geometry changed)
```

Data (only when re-reading the scenario maps): `python3 generate_annotations.py` rebuilds
`../data/hoth_scenario_positions_full.json` (uses `detect_maps.py`; scenarios 1–4 stay
hand-verified). Requires `pdfplumber`, `numpy`, `opencv-python`.

## Validation

```bash
python3 hoth_sim.py 200          # quick win-rate sanity (alternating first player)
```

- **Card text sync:** `python3 build_compendium.py` must print `✓ compendium in sync` — it
  exits non-zero if the markdown and `hoth_cards.py` disagree (missing/stale/count drift).
- **Deck balance:** run a fair-mirror (identical forces, both decks) and aim for ~50/50; a
  card change that pushes it past ~55% means re-tune. See `docs/Balance_Report.md` for the
  harness pattern and target numbers.
- **HTML tools:** after regenerating, extract the `<script>` and run `node --check` on it.
- **No regressions:** loop all 17 scenarios (`hoth_scenarios.SCENARIOS`) through
  `play_game(scenario=..., annot=data[str(n)])` for both `basic=True/False` and confirm none
  raise.

## Conventions & notes

- Board coordinates are engine-space: **row 0 = Rebel baseline (bottom), row 6 = Empire (top)**;
  brick layout (odd rows have 9 hexes, even rows 10); pointy-top "odd-r" adjacency. The
  annotator/maps use image rows (row 0 = top); the loader converts via `6 - row`.
- AI policy is `AI_MODE` (default `'base'` greedy — validated strongest); a lookahead `'smart'`
  mode exists for analysis but is not stronger.
- Keep the **sector-locked** ordering tension: don't convert the Probe/Raid/Assault backbone
  to "choose anywhere," and keep section-restriction symmetric across factions.
- Licensing: code is BSD-3 (`LICENSE`); original content is CC BY 4.0 (`LICENSE-CONTENT.md`);
  `simulator/source/` publisher materials are neither.
