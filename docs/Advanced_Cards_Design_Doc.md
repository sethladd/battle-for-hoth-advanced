# Advanced Cards — Design Doc (Stage 2 proposal)

**Status:** Draft · slate selected (5/faction) · **pipeline validated** with 2 cards now live in the deck (see end)
**Purpose:** Capture 10 candidate new command cards per faction, their themes, and how each
maps to the simulator, so we can choose a balanced subset to actually build. This is a
*precursor* to development — nothing here is implemented yet.

> **Pipeline note (see [CLAUDE.md](../CLAUDE.md) golden rule).** When a card here is approved,
> it becomes real markdown-first: add its line to `Advanced_Deck_Compendium.md`, then the
> structure to `simulator/hoth_cards.py`, then the mechanic to `hoth_sim.py`/`hoth_engine.py`,
> then regenerate + validate. This doc is the spec we promote *from*, not a generated artifact.

## Design goals

1. **Theme first.** Every card should evoke a specific beat of the Battle of Hoth — the
   evacuation, the trench line, the walker assault, the ion cannon, the probe droids.
2. **Faction identity, sharpened.** The new cards should deepen each side's existing role
   rather than blur it:
   - **Rebel Alliance** — *information, mobility, evasion, and stalling for the evacuation.*
     They survive and delay; they win by not losing.
   - **Galactic Empire** — *fear, suppression, relentless armor, and closing the noose.*
     They press, break morale, and deny escape.
3. **Engine-translatable.** Prefer effects that reuse existing building blocks; introduce a new
   mechanic only when it unlocks several cards and a genuinely new feel.
4. **Balance-aware.** New cards must survive the fair-mirror harness (~50/50) before shipping;
   intel and disable effects are powerful and will need conservative first numbers.

## What already exists (so we don't repeat ourselves)

Current Rebel tactics: Speeder Strike, Trench Fighting, Artillery Barrage, Focus Fire,
Desperate Valor, Forward Command, Regroup, Evasive Maneuvers, Ambush.
Current Imperial tactics: Armored Advance, Trooper Assault, Concentrated Fire, Hold the Line,
Probe Recon, Crush Them, Suppressing Fire, Imperial Ambush.
Plus 18 leader cards and the 13 shared section cards. The ideas below are deliberately distinct
from all of these.

## New mechanic families this proposal introduces

These are the only genuinely new systems required; each is shared by multiple cards, so
greenlighting the *family* is the real decision. Implementation pointers are best-guesses for
where the code would live.

| Family | What it does | Cards using it | Likely implementation |
|---|---|---|---|
| **Intel** | Look at the opponent's hand (peek only — no forced discard) plus a minor own-deck rider | Sliced Transmissions (R), Probe Droid Network (E) | New hand/deck access in `hoth_sim.py`; AI must value & respond to known info |
| **Disable / Suppress** | Reduce an enemy unit's *next* activation (no act, or −dice) | Ion Cannon Salvo (R), Terror of the Walkers (E) | Per-unit status flag on `Unit`; checked in `plan_unit_action` / `_do_attack` |
| **Protective zone / weather** | Round-long modifier on a region or all attacks | Shields Holding (R), Blizzard Cover (R) | Round-scoped state on `Game`; checked in `resolve_attack` |
| **Sacrifice-for-buff** | Spend your own figure for a turn-wide bonus | You Have Failed Me (E) | Eliminate a friendly figure, set a turn buff |
| **Exit-lock / blockade** | Deny enemy board-exit and exit-medals for a round | Tighten the Blockade (E) | Toggle on existing `exits`/`exit_medal` handling |
| **Conditional / positional bonus** | Bonus only vs. a target type or near a structure | Tow Cable Run (R), Defend the Generators (R) | Extend `est_attack_value` + `_do_attack` with a target/position predicate |
| **Triggered rally / morale** | Destroying a target fires a follow-on effect for nearby friendlies | Tow Cable Run (R); generalizable to "any walker falls" | Hook the kill path in `_eliminate`; queue a morale move + dice buff for units within range |

The remaining ~11 cards are **"easy"** — they compose bonus keys already implemented
(`dice`, `close_dice`, `move`, `after_move`, `attack_twice`, `ignore_terrain`, `reinforce`,
`no_move`, `draw`, `retreat_as_hit`, `full_move_attack`, `no_enemy_reactions`, `multi_target`,
escalation, and the existing leader retreat-ignore).

---

## Rebel Alliance — 10 candidates

| # | Card | Theme | Effect (draft) | Mechanic |
|---|------|-------|----------------|----------|
| R1 | **Sliced Transmissions** | Echo Base slices the Imperial command net | Look at the opponent's hand (peek only — nothing is discarded), then draw 1 command card. | new: intel (peek) |
| R2 | **Ion Cannon Salvo** | The v-150 Planet Defender fires | Choose any one enemy unit anywhere on the board; it cannot move or attack on its next activation. | new: disable |
| R3 | **Tow Cable Run** | Rogue Squadron's harpoon-and-tow trick — *and the trench line surging forward when the first walker falls* | Order up to 2 Snowspeeders; their attacks vs. *vehicles* roll +2 dice and ignore the target's armor. **If a vehicle is destroyed this way, every friendly infantry unit within 2 hexes immediately advances 1 hex toward the enemy and rolls +1 die this turn** (the line rallies). | new: conditional-vs-vehicle + triggered rally |
| R4 | **Shields Holding** *(reaction)* | The deflector shield absorbs the barrage | Until your next turn, your units in your home rows cannot be hit by ranged/orbital attacks — only by adjacent close combat. | new: protective zone |
| R5 | **Tauntaun Recon** | Outriders brave the cold | Order up to 2 light/Tauntaun units; each gains +2 movement; look at the top 2 cards of your deck and keep 1. | easy-ish: scout/move/draw + scry |
| R6 | **Strategic Withdrawal** | "Begin the evacuation." | Order up to 3 units; each moves its full distance toward your home edge, not counted as a forced retreat. | easy: move + safe-retreat flag |
| R7 | **Rogue Leader's Gambit** | Wedge lines up the shot | Order 1 Snowspeeder; it attacks twice this turn; each hit vs. a vehicle that forces a retreat counts as an extra hit. | easy: attack_twice + conditional |
| R8 | **Blizzard Cover** | A whiteout rolls in | This round, *all* ranged attacks (both sides) roll 1 fewer die. Favors the dug-in defender. | new: round-long global modifier |
| R9 | **Defend the Generators** | The line holds at the power core | Units adjacent to a friendly structure roll +2 attack dice this turn. | new-ish: positional |
| R10 | **Rally to the Princess** | Leia steadies the line | Order up to 2 units adjacent to your leader; each returns 1 lost figure and rolls +1 die. | easy: reinforce + leader synergy |

## Galactic Empire — 10 candidates

| # | Card | Theme | Effect (draft) | Mechanic |
|---|------|-------|----------------|----------|
| E1 | **Probe Droid Network** | The Empire's eyes everywhere | Look at the opponent's hand (peek only — nothing is discarded), then look at the top 2 cards of your deck and keep 1. | new: intel (peek) |
| E2 | **You Have Failed Me** | Command by terror | Eliminate one figure from one of your *own* units; every unit you order this turn rolls +1 die. | new: sacrifice-for-buff |
| E3 | **Walkers Inbound** | Blizzard Force closes in | Order *all* vehicles in one section; each gains +1 movement, ignores terrain, and rolls +1 close-combat die. | easy: combine move/ignore_terrain/close_dice |
| E4 | **Imperial Discipline** | They do not break | Units you order this turn ignore retreat results and roll +1 die. | easy: retreat-ignore exists |
| E5 | **Cold Assault** | Snowtroopers surge across open ice | Order up to 4 snowtroopers; each gains +1 movement and may move its full distance and still attack. | easy: full_move_attack + move + filter |
| E6 | **Terror of the Walkers** | An AT-AT's shadow scatters the line | When a vehicle you order hits, the target retreats 1 extra hex and is suppressed (−1 die on its next activation). | new: suppression |
| E7 | **No Disturbance** | Vader's grip silences the field | Order up to 2 units; the enemy may play no reactions this turn, and retreat results count as hits. | easy: no_enemy_reactions + retreat_as_hit |
| E8 | **Death Squadron Salvo** | Concentrated fire from above | Roll 2 dice against each of up to 2 enemy units in one section, ignoring cover. (Distinct from Piett's board-wide Orbital Bombardment.) | easy: multi_target |
| E9 | **Tighten the Blockade** | Cut off the escape | This round the enemy cannot exit the board or score exit-medals; your units gain +1 movement toward the enemy edge. | new: exit-lock |
| E10 | **Endless Ranks** | The Empire's weight tells | While you lead on medals, return 1 lost figure to each of up to 2 vehicle units. | easy: reinforce + snowball escalation |

---

## Mechanics borrowed from the Commands & Colors system

Battle of Hoth is built on the Richard Borg *Commands & Colors* engine (the same lineage as
Memoir '44, C&C: Ancients, C&C: Napoleonics, and BattleLore). Studying the wider family surfaces
a key insight: in those games **"advanced" depth comes from two layers** — the command-card deck
*and* a set of combat/unit rules (battle back, evade, momentum, squares). Our variant so far lives
almost entirely in the deck. Several of the strongest ideas below are therefore best adopted as
*optional advanced combat rules* that the deck can then reference, not as cards alone.

| Mechanic | Source game | What it does | Hoth fit | Already have? | Best route |
|---|---|---|---|---|---|
| **Battle Back** | C&C: Ancients / Napoleonics | A defender that survives close combat immediately strikes back at the attacker | Trench defenders return fire; a walker shrugs off a hit and fires back | No | Combat rule, or card ("Return Fire" / "Defiant Stand") |
| **Momentum / Breakthrough** | C&C: Ancients | After forcing a retreat, advance into the vacated hex and make a *bonus* attack (cavalry may advance +1 hex first) | Walker breakthrough; Snowspeeder pursuit | Partial — `after_move`, `full_move_attack`, Break Their Lines | Vehicle combat rule, or card |
| **Evade** | C&C: Ancients (light units) | A fast unit retreats *before* the hit lands, denying the attacker (and denying momentum advance) | Speeders / Tauntauns dodging | Partial — Evasive Maneuvers (Snowspeeder reaction) | Extend to a Tauntaun unit trait |
| **Support / Steadfast** | C&C: Ancients | Supported or leader-attached units ignore a retreat flag | A cohesive line holds its ground | Partial — `retreat_ignore` (leaders only) | Rule: a unit with 2+ adjacent friendlies ignores 1 retreat |
| **Combined Arms** | Memoir '44 / Napoleonics | An artillery / different-type adjacent unit adds dice to another unit's attack | E-web + infantry; walker + snowtroopers firing together | No (Focus Fire is same-target, not mixed-type) | Card "Combined Arms", or rule |
| **Dig In / Entrench** | Memoir '44 | A unit fortifies for a lasting defensive die and cannot move | Digging into the ice trench line | Partial — Hold the Line (one turn only) | Card that places a *persistent* cover marker |
| **Counter-Attack** | Memoir '44 | Play a copy of the opponent's last-played command card | Imperial adaptive command / "Anticipate Their Move" | No | Meta card |
| **First Strike / Defensive Fire** | Napoleonics (square) / Memoir overrun | A defending unit fires first as the enemy closes | Echo Base e-web emplacements | Partial — Ambush (close combat on adjacency) | Card, or emplacement unit trait |
| **Brace / Form Square** | C&C: Napoleonics | Infantry brace against a fast attacker: reduced damage, defender fires first | Infantry bracing against a walker or speeder charge | No | Reaction card "Brace for Impact" |
| **Resolve / Lore tokens** | BattleLore / C&C: Medieval | Bank a currency earned from dice symbols, spend it on powerful triggered effects | "Resolve" (Rebel) vs. "Initiative" (Imperial) as faction meta-resources | No | **Ambitious meta-layer — Stage 3 candidate, not this round** |

**Recommendation.** The five highest-value, theme-rich, engine-feasible additions are
**Battle Back, Combined Arms, Support/Steadfast, Dig In, and Counter-Attack**. **Momentum** and
**Evade** are best treated as upgrades to mechanics we already approximate (breakthrough movement
and the Snowspeeder evade reaction). **Resolve/Lore tokens** is the single biggest idea — it would
give the variant a genuinely new strategic layer — but it is a Stage 3-sized commitment and should
be scoped separately rather than folded into the card round above.

**Design caution — cards vs. rules.** Adopting these as always-on *advanced combat rules*
changes the baseline for the entire deck, so the fair-mirror balance must be re-established from
scratch before any new card is tuned on top. Adopting them as *cards* is safer and more modular
(each is just another tactic to value), at the cost of them appearing only when drawn. Battle Back
and Support are the two that feel most like they "want" to be rules; the rest work cleanly as cards.

Sources: [C&C: Ancients living rules (GMT)](https://www.gmtgames.com/living_rules/CC_Rules_2009.pdf),
[Momentum Advance FAQ](https://www.commandsandcolors.net/ancients/the-game/main/faqs/momentum-advance.html),
[Close Combat / Battle Back](https://www.commandsandcolors.net/ancients/the-game/main/11-close-combat.html),
[Memoir '44 rulebook](https://cdn.1j1ju.com/medias/5b/6d/be-memoir-44-rulebook.pdf),
[Memoir '44 command-card catalog](https://memoir44fans.com/t/command-card-catalog/36),
[BattleLore lore cards](https://www.commandsandcolors.net/battlelore/index.php?option=com_content&view=article&id=16:lore-cards&catid=18&Itemid=212),
[C&C: Napoleonics living rules (GMT)](https://www.gmtgames.com/living_rules/CCN-RULES-2012.pdf).

## Stage 2b — system-derived card directions

Concrete card drafts that turn the borrowed *Commands & Colors* mechanics above into playable
Hoth cards. These are **possible directions**, not commitments. A design observation drives the
grouping: some borrowed mechanics are inherently *symmetric* (both armies do them in the source
games), so they fit best as shared cards — like the Probe/Raid/Assault section backbone — while
others carry obvious faction flavor.

Each is tagged with the borrowed mechanic and a feasibility note. Most need **new engine work**
(several are reactions and several introduce a persistent marker or a kill/defense hook), so they
are heavier than the "easy" Stage 2 cards.

### Symmetric system cards (offer to both sides, flavored per faction)

| # | Card (Rebel name / Imperial name) | Mechanic | Effect (draft) | Feasibility |
|---|---|---|---|---|
| SY1 | **Defiant Stand** / **Unyielding Armor** | Battle Back | *(reaction)* When one of your units is attacked in close combat and survives, it immediately battles back — roll its close-combat dice against the attacker. | new: battle-back hook in `resolve_attack` |
| SY2 | **Stand Together** / **Disciplined Ranks** | Support / Steadfast | Order up to 3 units. This turn, each ignores retreat results while it has a friendly unit adjacent (the line holds). | new: support test; `retreat_ignore` exists for leaders to build on |
| SY3 | **Dig Into the Ice** / **Establish a Firebase** | Dig In | Order up to 2 units; each may not move and places a **persistent cover marker** on its hex that grants cover until the unit leaves. | new: lasting terrain marker on `Game` |
| SY4 | **Improvise** / **Anticipate Their Move** | Counter-Attack | Play a copy of the last command card your opponent played, resolving its effect for your units. | new: track opponent's last card; replay its resolution |
| SY5 | **E-Web Overwatch** / **Imperial Overwatch** | First Strike / Defensive Fire | *(reaction)* When an enemy unit moves adjacent to your infantry, that unit fires first — one attack — before the enemy may act. | new: on-approach defensive-fire trigger (distinct from Ambush's end-of-move close combat) |

### Rebel-flavored system cards

| # | Card | Theme | Effect (draft) | Mechanic |
|---|------|-------|----------------|----------|
| RS1 | **Crossfire** | E-web, infantry, and speeders converge on one target | Order 1 unit to attack; each friendly unit of a *different type* adjacent to the same target adds +1 die. | new: combined arms (mixed-type) |
| RS2 | **Strafing Pursuit** | A Snowspeeder rides the enemy down | Order 1 Snowspeeder; if its attack forces a retreat, it advances into the vacated hex and immediately attacks again. | new-ish: momentum advance (builds on `after_move`) |
| RS3 | **Tauntaun Evade** | Outriders break away from the line of fire | *(reaction)* When an enemy attacks your Tauntaun (or other light unit), it may retreat up to 2 hexes before the attack resolves, avoiding it. | extends evade beyond the Snowspeeder reaction |
| RS4 | **Brace for Impact** | Infantry set themselves against a charging walker | *(reaction)* When a vehicle attacks your infantry, the unit braces: the attack rolls 2 fewer dice and your unit does not retreat. | new: brace / form-square |

### Imperial-flavored system cards

| # | Card | Theme | Effect (draft) | Mechanic |
|---|------|-------|----------------|----------|
| ES1 | **Concentrated Assault** | A walker and its escort focus fire | Order 1 vehicle to attack; each snowtrooper unit adjacent to the same target adds +1 die. | new: combined arms (mixed-type) |
| ES2 | **Walker Breakthrough** | An AT-AT overruns the broken line | Order 1 AT-AT; if its attack forces a retreat, it advances into the vacated hex and attacks again (overrun). | new-ish: momentum advance |
| ES3 | **Relentless Pursuit** | AT-STs chase down the routed | Order up to 2 AT-STs; each that forces a retreat may advance 1 hex and make a second attack. | new-ish: momentum advance |

### Optional Stage 3 hook — the Resolve / Initiative meta-layer

If the **Resolve / Lore-token** family (see the borrowed-mechanics table) is ever pursued, the
cleanest on-ramp is a single pair of cards that *generate* the resource, plus a few that *spend*
it — e.g. **Rally Cry** (Rebel) / **By My Command** (Imperial): "bank 1 Resolve token; you may
spend 2 Resolve at any time to add 1 die to an attack or cancel 1 retreat." This keeps the new
currency contained to an opt-in mini-suite rather than rewriting the base deck.

## Proposed build slate (5 per faction)

Per the decisions above: expand each tactic deck by **5 cards**, chosen to maximize faction
identity while spreading across mechanic families and difficulty. **Dig In (SY3)** is the shared
symmetric card, so it counts toward both sides and is built once. That makes **9 unique new
cards** total (4 Rebel-only + 4 Imperial-only + 1 shared), taking each tactic deck from 10 → 15.

### Rebel Alliance — *information, mobility, the iconic walker-kill, the trench*

| Card | Source idea | Why it's in | Mechanic |
|---|---|---|---|
| **Tow Cable Run** | R3 | The signature Hoth moment — speeders fell a walker and the line surges forward | conditional-vs-vehicle + triggered rally |
| **Sliced Transmissions** | R1 | The faction's intel/evasion identity, peek-only | intel (peek) |
| **Tauntaun Recon** | R5 | Mobility + card selection; easy, low-risk | scout/move/draw + scry |
| **Brace for Impact** | RS4 | Infantry holding against a walker charge — defensive depth the deck lacks | brace / form-square (reaction) |
| **Dig Into the Ice** | SY3 (shared) | The Echo Base trench, made persistent | dig in (persistent cover) |

### Galactic Empire — *fear, the overrun, the closing noose, the firebase*

| Card | Source idea | Why it's in | Mechanic |
|---|---|---|---|
| **You Have Failed Me** | E2 | Command-by-terror; the most distinctly Imperial card in the pool | sacrifice-for-buff |
| **Probe Droid Network** | E1 | The faction's intel identity, peek-only | intel (peek) |
| **Walker Breakthrough** | ES2 | The AT-AT overrun — armor's signature tempo play | momentum advance |
| **Tighten the Blockade** | E9 | "Cut off the escape" — denies the Rebel evacuation win | exit-lock |
| **Establish a Firebase** | SY3 (shared) | The Imperial face of Dig In; anchors the walker advance | dig in (persistent cover) |

**Deliberately deferred** (strong, but heavier or riskier than a first batch warrants): Ion Cannon
Salvo (disable), Shields Holding & Blizzard Cover (zone/weather), Terror of the Walkers
(suppression), the Battle Back / Support / Counter-Attack / Overwatch system suite, and the entire
Resolve-token Stage 3 layer. They stay in the pools above for a later round.

### Suggested build order (lowest-risk first)

1. **Tauntaun Recon** — pure composition of existing keys; proves the expanded-deck balance harness.
2. **Dig In (shared)** — first persistent-marker mechanic; test on both decks at once.
3. **Sliced Transmissions / Probe Droid Network** — intel scaffolding (peek + rider).
4. **Tow Cable Run** — conditional bonus + the triggered-rally kill hook.
5. **Brace for Impact** — first new reaction; requires AI reaction-valuation work.
6. **Walker Breakthrough**, **Tighten the Blockade**, **You Have Failed Me** — the Imperial
   mechanics (momentum, exit-lock, sacrifice), each balance-tested before the next.

After each card: update `Advanced_Deck_Compendium.md` → `hoth_cards.py` → mechanic → regenerate →
`build_compendium.py` sync check → fair-mirror on the **expanded** deck → 17-scenario sweep.

## Balance & risk notes

- **Intel (R1/E1) is scoped to peek-only** (signed off — no forced discard), which removes the
  worst swing. The residual risk is that the heuristic AI can't yet *act* on a revealed hand, so
  in a first build the peek is mostly flavor and the rider (draw / scry) carries the card's value.
  Revisit a stronger intel effect only once the AI can plan against known cards.
- **Disable/suppress (R2, E6)** are strong tempo plays; cap them to a single target and a single
  activation, and watch for degenerate lock loops against slow vehicles.
- **Shields Holding (R4)** must not make a turtling Rebel un-winnable on defensive scenarios —
  test specifically on the base-defense maps (e.g., the shield-generator scenarios).
- **You Have Failed Me (E2)** is thematically perfect but the AI valuation is tricky (it must
  weigh a self-loss against a board-wide buff); needs explicit `est_attack_value` handling.
- **Triggered rally (R3)** is the movie's emotional pivot — the trench line surging when the
  first walker falls. Watch for a swingy combo (speeders + a packed infantry line = a free
  multi-unit advance and a board-wide dice spike); cap the radius (2 hexes) and the advance
  (1 hex) tightly, and only trigger on a *vehicle* kill so it can't chain off trooper kills.
  If it tests well, consider a standalone version that fires when **any** AT-AT is destroyed
  (by any means), making walker-hunting a whole-deck Rebel theme.
- **System-derived cards (Stage 2b) are reaction- and hook-heavy.** Battle Back (SY1), the
  evade/brace reactions (RS3, RS4), and Overwatch (SY5) all fire on the *opponent's* turn, which
  the current AI handles only for the existing reaction set — it must be taught to value holding
  and triggering each new one, or it will under- or over-play them and skew the harness. Momentum
  cards (RS2, ES2, ES3) can chain; cap the bonus attack to one extra to avoid runaway turns.
- **Symmetric cards reset the mirror cleanly.** Because SY1–SY5 are offered to both sides, they
  are the safest borrowed mechanics to test first — a fair mirror with both decks holding them
  should stay ~50/50 by construction, isolating whether the *mechanic* (not the matchup) is sound.
- **Sector tension preserved.** None of these convert the Probe/Raid/Assault backbone to
  "choose anywhere"; they're tactic cards layered on top, per the design constraint in CLAUDE.md.
- Every approved card re-runs the fair-mirror (~50/50 target) and the 17-scenario regression
  sweep before it's considered done.

## Recommended phasing

1. **Phase A — easy wins (no new engine code):** R5, R6, R7, R10, E3, E4, E5, E7, E8, E10.
   Pure compositions of existing keys; implement, then balance-test as a batch.
2. **Phase B — one new family at a time, each fully tested before the next:**
   1. Conditional/positional + triggered rally (R3, R9) — R3's rally trigger is a small,
      self-contained hook on the kill path; a good first new mechanic to prove the pattern.
   2. Disable/suppress (R2, E6).
   3. Exit-lock (E9) and sacrifice-buff (E2).
   4. Protective zone / weather (R4, R8).
   5. **Intel (R1, E1) last** — biggest AI and balance unknowns.
3. **Stage 2b — system-derived cards** can interleave with Phase B, but lead with the
   *symmetric* suite (SY1–SY5) since a both-sides mirror isolates the mechanic from the matchup.
   Combined arms (RS1, ES1) and momentum (RS2, ES2, ES3) follow; the evade/brace reactions
   (RS3, RS4) come once the AI reliably values the existing reaction cards.
3. After each phase, regenerate the compendium/PDF/replay and confirm `build_compendium.py`
   reports in sync.

## Decisions (signed off)

1. **Deck size — expand, don't replace.** New cards are *added* to each side's tactic deck
   rather than swapping out existing ones. Target **4–5 new cards per faction**. Note: this
   raises each tactic deck from 10 to ~14–15 cards, which dilutes draw odds and shifts the
   balance baseline — so the fair-mirror must be re-run on the *expanded* deck, not the old one.
2. **How many to ship — 4–5 per faction.** See the proposed slate below.
3. **Intel scope — peek-only.** No forced discard; R1/E1 reworded above to peek + a minor rider.
4. **New units as prerequisites — allowed.** Cards may require Snowspeeders, Tauntauns,
   snowtroopers, or vehicles; the unit-type **fallback clause** already covers scenarios that
   lack the unit (order 1 unit of choice, no bonus), consistent with the rest of the deck.

## Pipeline validation (completed)

The full markdown-first pipeline was exercised end-to-end with two real cards to prove it works,
**including the balance gate and the loop-back-to-development step**:

- **Cards added:** **Tauntaun Recon** (Rebel — order up to 2 units, +1 move, draw 1) and
  **Cold Assault** (Imperial — section, order snowtroopers, +1 move, full-move-attack). Both use
  only existing bonus keys, so no new engine code was needed. Each tactic deck went 10 → 11.
- **Order followed:** canonical markdown (`Advanced_Deck_Compendium.md`) → `hoth_cards.py`
  definitions → `build_compendium.py` sync check (`✓ 50 cards`) → balance sim → regenerate
  PDF + replay → 17-scenario regression sweep (34 runs, all clean).
- **Balance gate + loop:** a deck-isolation fair mirror (identical forces, symmetric medals/hand,
  alternating first; ~±2.5pt noise floor at N=800 because the AI's jitter is unseeded).
  - *First draft* (Cold Assault orders **3** infantry): base 67.9% → with-cards 63.5% Rebel,
    a **−4.4pt** skew toward the Empire → flagged **off**.
  - *Tuned* (Cold Assault trimmed to **2** infantry): base ≈67% → with-cards ≈67% Rebel,
    **Δ ≈ 0** across two reps → **balanced**, gate passed.
- **Harness:** `outputs/fair_mirror.py` (monkeypatches `standard_setup` to a symmetric force;
  `base` mode strips the two test cards to measure the pre-change baseline).

Both cards are currently **live in the advanced deck**. Note Tauntaun Recon is part of the
selected slate; Cold Assault was chosen here as a low-risk Imperial test card (it sits in the
Stage 2 pool as E5, not the final 5-card Imperial slate) — easy to revert or swap for a slate
card. If they stay, `docs/Balance_Report.md` should be refreshed to reflect the 11-card decks.
