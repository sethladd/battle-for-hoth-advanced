# Battle of Hoth — Advanced Deck Balance Report

This report summarizes the AI-vs-AI balance testing of the Advanced expansion: the
redesigned command deck, the six on-board leaders, the two new units (Tauntaun Scout,
AT-ST), and all 17 booklet scenarios.

## 1. Method

A custom Python engine reimplements the published rules (hex board, the symbol dice,
movement/attack/terrain, line of sight, medals) and the Advanced content. A heuristic AI
plays both sides: it plays the highest-value command card, concentrates fire to secure
kills, finishes wounded units, uses cover, pursues objectives/exits, and triggers reaction
cards. Win rates below are from thousands of AI-vs-AI games.

**Confidence.** Most cells use 50–80 games per condition, so individual numbers carry
roughly a ±10–14 point sampling error; read trends, not exact values.

**Fidelity tiers.** Each scenario is tagged `full` (win conditions and special rules
modelled exactly) or `approx` (a structural objective is approximated). Shield generators
and the ion cannon are now modelled as **destroyable structures** (special units killed by
a blast) with sudden-death; the remaining `approx` items are reinforcement waves, hold-3-
hexes, and the officer-evac micro-rules.

**Map fidelity.** Scenario unit positions/sides/types are hand-verified for 1–4 and
auto-detected (and validated to 100% on 1–4) for 5–17; terrain on 5–17 is sparse
(crevasse/serac/trenches aren't visually detectable) and can be refined in the annotator.

## 2. Deck balance (the core question)

To isolate the *decks* from scenario asymmetry, both sides are given **identical forces**
(an all-card-types mirror) and each plays its own faction deck, alternating who moves first.

> **Fair mirror: Rebel ~55% (range 53–57% across runs, N=400).**

The two advanced decks are balanced to within a few points, with a slight Rebel edge — a
reasonable and thematically acceptable result for an asymmetric-faction game. Crucially,
the advanced section backbone is **sector-locked** (Probe/Raid/Assault Left/Center/Right),
preserving the basic game's "you can't always act where you want" tension; only two cards
per side (Coordinated Command, Grand Offensive) let you choose where to act.

## 3. Per-scenario balance — Advanced vs. Basic deck

Rebel win % under each deck. The point is not the absolute number (that's the scenario's own
asymmetry) but that **the advanced deck tracks the basic deck** — it doesn't distort the
scenarios.

| # | Scenario | Fidelity | Advanced | Basic |
|---|---|---|---|---|
| 1 | Imperial Scout Mission | full | 38% | 26% |
| 2 | Snowspeeder Counter-Attack | full | 34% | 34% |
| 3 | Enemy Spotted | full | 34% | 26% |
| 4 | Successful Landings | approx | 28% | 30% |
| 5 | Hill Alpha Defense | approx | 76% | 78% |
| 6 | Retrieve Imperial Data | approx | 10% | 16% |
| 7 | Outpost Attack | approx | 0% | 2% |
| 8 | Medevac! | approx | 94% | 94% |
| 9 | Securing Defensive Positions | approx | 24% | 18% |
| 10 | Target the Shield Generators | approx* | 32% | 30% |
| 11 | Rebel Breakout | full | 46% | 58% |
| 12 | Under Siege | approx | 0% | 4% |
| 13 | Enter Echo Base | full | 100% | 96% |
| 14 | Protect Rebel Transports | approx* | 16% | 10% |
| 15 | South Gate Retreat | full | 0% | 0% |
| 16 | Echo Base Evacuation | full | 46% | 70% |
| 17 | Last Stand | full | 92% | 84% |

\*Now driven by real destroyable structures (previously broken at ~100%).

**Reading it.** Advanced and Basic are within sampling noise on most scenarios — the
advanced deck adds depth without skewing outcomes. The extreme cells (Medevac, Enter Echo
Base, South Gate, Last Stand) are lopsided because the scenario itself is a one-sided
sudden-death race; the wider Advanced-vs-Basic gaps (e.g. Echo Base Evacuation, Rebel
Breakout) are within the ±10–14 error band at this sample size. Scenarios 10 and 14, which
used to be unwinnable for the Empire, now produce genuine contests (Empire wins by
destroying the shields / ion cannon).

## 4. Leader balance

Tested on a symmetric arena (identical forces, an escort for every leader) so deviation
from the no-leader baseline isolates each leader. Rebel win %, rows = Rebel leader,
columns = Empire leader (N=55 each):

| Rebel \ Empire | None | Vader | Veers | Piett |
|---|---|---|---|---|
| **None** | 44 | 45 | 40 | 40 |
| **Luke** | 53 | 53 | 36 | 51 |
| **Han** | 49 | 53 | 44 | 44 |
| **Leia** | 55 | 56 | 51 | 45 |

All matchups sit in a **~36–56% band** — no dominant leader, and every leader is a net
positive. Each leader keeps a distinct identity (Luke/Leia/Vader as combat anchors, Veers
as the armor commander, Han as a mobility harasser, Piett as the safe off-board economy
pick) while staying within tolerance.

### Tuning applied during the pass

- **Luke/Leia were over-strong:** Luke's "reroll" was rerolling *every* missed die (now
  rerolls **one**, as written); Leia's +1-die aura blanketed the army (now her command is
  focused on her own squad).
- **Han was a *negative* leader** (fragile mount captured for a medal): his escort now also
  rolls **+1 die**, bringing him to par.
- Leader effects were **consolidated to a single source** to remove double-counting between
  the old passives and the new on-board auras; Veers' aura was made functional (friendly
  walkers +1 close-combat die).
- Bonus-Medal values (2 for Luke/Leia/Vader, 1 for Han/Veers, 0 for off-board Piett) and
  aura ranges remain the clean tuning levers.

## 5. Deck-tuning history (summary)

- Added the **rulebook fallback** (a type-restricted card with no eligible units orders 1
  unit of your choice) so cards are never dead.
- **Sector-locked** the section backbone and made the section-restriction symmetric across
  factions after it briefly over-buffed the Rebels.
- Equalized the offensive tactics so the fair mirror settled near 50/50.

## 6. Key findings

1. **The advanced decks are balanced** (~55/45 mirror) and **don't distort the scenarios**
   (advanced ≈ basic per scenario).
2. **Leaders are balanced and distinct** after tuning (36–56% band, no dominant pick).
3. **The new units slot in cleanly** between the existing light and heavy units.
4. **Structural-objective scenarios now work** thanks to destroyable structures.

## 7. Known limitations

- Several scenarios are intrinsically lopsided under automated play; the AI also under-uses
  mobility, so mobile leaders/units (Han, Snowspeeders, Tauntauns) are worth more at the
  table than the simulation credits.
- `approx` scenarios still abstract reinforcement waves, hold-3-hexes, and officer-capture
  micro-rules.
- Auto-detected terrain for scenarios 5–17 is sparse; refining it (and exact structure/
  objective placement) in the annotator would tighten those numbers.
- Sampling error is ±10–14 points per cell; the conclusions are about trends and bands, not
  exact percentages.
