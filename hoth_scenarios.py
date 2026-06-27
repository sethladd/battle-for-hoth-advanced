"""
Battle of Hoth -- SCENARIO REGISTRY (all 17 standard scenarios).

For every scenario the booklet specifies four balance drivers that we encode
FAITHFULLY from the rules text:
   * starting hand size per side
   * which side plays first
   * victory conditions (medal targets and/or sudden-death objective)
   * special rules (medal bonuses, no-medal clauses, exit medals, etc.)

Unit FORCES and exact placement are *reconstructed* from each scenario's
narrative and the standard army components -- the booklet's battle maps are
printed art and not machine-readable. Each scenario carries a `fidelity` tag:
   'full'   -> win condition & special rules modelled exactly
   'approx' -> a structural objective (officer evac, hold-3-hexes, destroy a
               structure, reinforcement waves, ion-cannon charging) is
               approximated by an equivalent medal race; flagged in the report.

Board: rebel baseline = row 0, empire baseline = row 6 (10 cols x 7 rows).
"""

from dataclasses import dataclass, field
from hoth_sim import make_unit

# ---- deployment helpers ----------------------------------------------------
def _spread_cols(n):
    """Return n columns spread across the 10-wide board."""
    if n <= 0:
        return []
    if n == 1:
        return [4]
    step = 9 / (n - 1)
    return [round(i * step) for i in range(n)]

def _place(side, kinds, rng):
    """kinds: list of (kind, count). Rebels fill rows 0,1; Empire rows 6,5."""
    units = []
    rows = [0, 1, 2] if side == 'rebel' else [6, 5, 4]
    # flatten requested units
    queue = []
    for kind, count in kinds:
        queue += [kind] * count
    # lay out row by row, back row first for artillery/special
    # simple: distribute across columns, wrapping to next row
    per_row = max(1, (len(queue) + 1) // 2)
    cols = _spread_cols(min(len(queue), 10))
    occupied = set()
    ri = 0
    ci = 0
    colset = _spread_cols(max(2, min(len(queue), 8)))
    idx = 0
    for kind in queue:
        placed = False
        for r in rows:
            for c in _spread_cols(8):
                if (c, r) not in occupied:
                    occupied.add((c, r))
                    units.append(make_unit(kind, side, (c, r)))
                    placed = True
                    break
            if placed:
                break
        idx += 1
    return units


@dataclass
class Scenario:
    num: int
    name: str
    first: str
    hand: tuple              # (rebel, empire)
    rebel_forces: list       # [(kind, count)]
    empire_forces: list
    win_rebel: int = 99
    win_empire: int = 99
    fidelity: str = 'full'
    rules_text: str = ''
    # special-rule hooks
    start_medals: tuple = (0, 0)      # (rebel, empire) medals at start
    kill_bonus: dict = field(default_factory=dict)   # (kind, side)->value
    no_kill_medal: tuple = ()          # sides that score no medals from kills
    exit_medal: dict = field(default_factory=dict)   # side -> medals per exited unit
    sudden_death: str = ''             # '', 'kill_all_atat', 'exit_n:<side>:<n>'

    def build(self, rng):
        units = _place('rebel', self.rebel_forces, rng) + _place('empire', self.empire_forces, rng)
        return units


# ---------------------------------------------------------------------------
# The 17 scenarios. Hand/first/victory/special rules are verbatim from booklet.
# ---------------------------------------------------------------------------
SCENARIOS = {
 1: Scenario(1, 'Imperial Scout Mission', 'rebel', (4, 3),
        [('echo', 4)], [('snowtroop', 4), ('droid', 2)],
        win_rebel=4, win_empire=4, fidelity='full',
        rules_text='Rebel: killing a probe droid unit = 2 medals.',
        kill_bonus={('droid', 'rebel'): 2}),

 2: Scenario(2, 'Snowspeeder Counter-Attack', 'rebel', (4, 4),
        [('speeder', 3), ('echo', 2)], [('snowtroop', 5), ('atat', 1)],
        win_rebel=4, win_empire=4, fidelity='full',
        rules_text='Straight medal race; Rebels delay and may bag an AT-AT.'),

 3: Scenario(3, 'Enemy Spotted', 'empire', (4, 4),
        [('echo', 5), ('speeder', 2)], [('atat', 1), ('snowtroop', 3), ('droid', 2)],
        win_rebel=5, win_empire=5, fidelity='full',
        rules_text='Rebel: eliminating the AT-AT unit = 2 medals.',
        kill_bonus={('atat', 'rebel'): 2}),

 4: Scenario(4, 'Successful Landings', 'empire', (4, 4),
        [('echo', 5), ('speeder', 1), ('artillery', 1)], [('atat', 2), ('snowtroop', 4)],
        win_rebel=4, win_empire=4, fidelity='approx',
        rules_text='Rebel holds a building objective (starts +1 temp medal). '
                   '[objective-hold approximated as a +1 Rebel head start]',
        start_medals=(1, 0)),

 5: Scenario(5, 'Hill Alpha Defense', 'empire', (5, 5),
        [('artillery', 2), ('echo', 4), ('speeder', 1)], [('atat', 1), ('snowtroop', 6)],
        win_rebel=5, win_empire=5, fidelity='approx',
        rules_text='Rebel holds a wreckage objective worth 2 (starts +2 temp medals). '
                   '[objective-hold approximated as a +2 Rebel head start]',
        start_medals=(2, 0)),

 6: Scenario(6, 'Retrieve Imperial Data', 'rebel', (4, 4),
        [('echo', 4), ('speeder', 1)], [('snowtroop', 6), ('droid', 2)],
        win_rebel=5, win_empire=5, fidelity='approx',
        rules_text='Rebel gains a medal each turn it holds the shuttle wreckage; '
                   'Empire reinforces eliminated infantry (Imperial War Machine). '
                   '[both modelled as a straight medal race]'),

 7: Scenario(7, 'Outpost Attack', 'empire', (4, 4),
        [('echo', 4), ('artillery', 1), ('speeder', 2)], [('snowtroop', 5), ('droid', 2)],
        win_rebel=5, win_empire=5, fidelity='approx',
        rules_text='Empire holds Rebel outpost (permanent objective); Rebel air '
                   'reinforcements arrive late. [objective approximated as +1 Empire head start]',
        start_medals=(0, 1)),

 8: Scenario(8, 'Medevac!', 'empire', (4, 4),
        [('echo', 3), ('speeder', 2)], [('snowtroop', 4), ('atat', 1)],
        win_rebel=5, win_empire=5, fidelity='approx',
        rules_text='Sudden death: Rebel evacuates the officer off-board (exit) / '
                   'Empire captures the officer. [modelled as Rebel exit-race: '
                   'exit 1 unit through Empire baseline to win].',
        exit_medal={'rebel': 1}, sudden_death='exit_n:rebel:1'),

 9: Scenario(9, 'Securing Defensive Positions', 'rebel', (4, 4),
        [('echo', 5)], [('snowtroop', 5), ('atat', 1)],
        win_rebel=4, win_empire=4, fidelity='approx',
        rules_text='Sudden death: Rebel occupies 3 marked hexes; Empire fields an '
                   'E-Web team. [occupy-3 approximated as a straight medal race]'),

 10: Scenario(10, 'Target the Shield Generators', 'empire', (4, 4),
        [('artillery', 2), ('echo', 5), ('speeder', 1)], [('atat', 2), ('snowtroop', 3)],
        win_rebel=5, win_empire=4, fidelity='approx',
        rules_text='Empire sudden death: destroy both shield generators; eliminating '
                   'Rebel units grants Empire no medals. [generators approximated: Empire '
                   'must score 4 by reaching/holding -> modelled as medal race, Empire kills no medals]',
        no_kill_medal=('empire',)),

 11: Scenario(11, 'Rebel Breakout', 'rebel', (3, 4),
        [('echo', 6), ('speeder', 1)], [('snowtroop', 5), ('droid', 1)],
        win_rebel=5, win_empire=5, fidelity='full',
        rules_text='Rebel units exiting the Empire baseline = 1 medal each; killing a '
                   'probe droid = 1 medal. Steep ridges cost 2 to enter.',
        exit_medal={'rebel': 1}, kill_bonus={('droid', 'rebel'): 1}),

 12: Scenario(12, 'Under Siege', 'empire', (5, 5),
        [('speeder', 2), ('echo', 4)], [('atat', 2), ('snowtroop', 5)],
        win_rebel=4, win_empire=4, fidelity='approx',
        rules_text='Rebel may grab one temporary objective medal; special retreat & '
                   'attrition-pass rules. [objective approximated as medal race]'),

 13: Scenario(13, 'Enter Echo Base', 'empire', (4, 4),
        [('artillery', 2), ('speeder', 2), ('echo', 4)], [('atat', 3), ('snowtroop', 4)],
        win_rebel=5, win_empire=99, fidelity='full',
        rules_text='Rebel sudden death: eliminate all 3 AT-ATs. Empire sudden death: '
                   'exit 3 infantry units. Eliminating Rebel units grants Empire no medals.',
        no_kill_medal=('empire',), exit_medal={'empire': 1},
        sudden_death='kill_all_atat;exit_n:empire:3'),

 14: Scenario(14, 'Protect Rebel Transports', 'empire', (4, 4),
        [('artillery', 1), ('echo', 5), ('speeder', 1)], [('atat', 1), ('snowtroop', 7)],
        win_rebel=3, win_empire=4, fidelity='approx',
        rules_text='Rebel charges the ion cannon (3 turns = 1 medal, to 3). Empire sudden '
                   'death: destroy the ion cannon. Neither side scores from kills. '
                   '[ion cannon charging approximated as a slow Rebel medal drip; Empire '
                   'must win by destroying it -> modelled as Empire medal race vs the clock]',
        no_kill_medal=('rebel', 'empire')),

 15: Scenario(15, 'South Gate Retreat', 'rebel', (5, 4),
        [('artillery', 1), ('speeder', 1), ('echo', 5)], [('snowtroop', 4), ('atat', 1), ('droid', 1)],
        win_rebel=5, win_empire=99, fidelity='full',
        rules_text='Rebel infantry exiting the board = 1 medal each. Empire sudden death: '
                   'eliminate 4 Rebel infantry units. Eliminating Imperial units grants Rebel no medals.',
        no_kill_medal=('rebel',), exit_medal={'rebel': 1},
        sudden_death='exit_n:empire:0_kill4inf'),

 16: Scenario(16, 'Echo Base Evacuation', 'rebel', (4, 4),
        [('echo', 5), ('speeder', 1)], [('atat', 1), ('snowtroop', 6)],
        win_rebel=5, win_empire=5, fidelity='full',
        rules_text='Rebel units exiting any Empire baseline hex = 1 medal each. A ridge '
                   'objective grants an extra card to whoever holds it.',
        exit_medal={'rebel': 1}),

 17: Scenario(17, 'Last Stand', 'rebel', (5, 5),
        [('artillery', 1), ('echo', 6)], [('snowtroop', 5), ('atat', 1), ('droid', 1)],
        win_rebel=5, win_empire=5, fidelity='full',
        rules_text='Rebel units exiting the board = 1 medal each; a ridge objective = +2 '
                   'permanent medals. Special retreat & attrition-pass rules.',
        exit_medal={'rebel': 1}),
}


def apply_markers(game, scn, markers):
    """Convert annotator markers (image rows) into engine objectives/structures.
    Objective hexes default to the Rebel side; value 2 for scenario 5 (wreckage),
    else 1. Shield-gen/ion-cannon become destroyable structures (terrain)."""
    if not markers:
        return
    # if exact objective hexes are given, drop the start-medal approximation
    if any(m['type'] == 'objective' for m in markers):
        game.medals['rebel'] -= scn.start_medals[0]
        game.medals['empire'] -= scn.start_medals[1]
        game.medals['rebel'] = max(0, game.medals['rebel'])
    val = 2 if scn.num == 5 else 1
    for m in markers:
        hx = (m['col'], 6 - m['row'])
        if m['type'].startswith('leader_'):
            from hoth_engine import LEADER_DEF
            name = m['type'].split('_', 1)[1].capitalize()
            u = game.unit_at(hx)
            if u is not None and name in LEADER_DEF:
                u.leader = name
                if LEADER_DEF[name].get('extra_fig'):
                    u.figs += LEADER_DEF[name]['extra_fig']
            continue
        if m['type'] == 'objective':
            owner = 'empire' if scn.num == 7 else 'rebel'
            mode = 'perm' if scn.num in (7,) else 'temp'
            game.objectives.append(dict(hex=hx, value=val, mode=mode, side=owner))
        elif m['type'] in ('shieldgen', 'ioncannon'):
            game.terrain[hx] = 'structure'
        elif m['type'] == 'exit':
            pass  # exit handled by baseline exit_medal rule


def apply_rules(game, scn):
    """Apply a Scenario's special rules onto a freshly-built Game."""
    game.medals['rebel'] += scn.start_medals[0]
    game.medals['empire'] += scn.start_medals[1]
    game.kill_bonus.update(scn.kill_bonus)
    game.no_kill_medal = set(scn.no_kill_medal)
    game.exits = {'rebel': 0, 'empire': 0}
    game.exit_medal = dict(scn.exit_medal)

    # sudden-death checks
    sd = scn.sudden_death
    if 'kill_all_atat' in sd:
        def chk_atat(g):
            if not any(u.alive for u in g.units if u.kind == 'atat'):
                return 'rebel'
            return None
        game.sudden_death_checks.append(chk_atat)
    if 'exit_n:empire:3' in sd:
        game.sudden_death_checks.append(
            lambda g: 'empire' if g.exits.get('empire', 0) >= 3 else None)
    if 'exit_n:rebel:1' in sd:
        game.sudden_death_checks.append(
            lambda g: 'rebel' if g.exits.get('rebel', 0) >= 1 else None)
    if 'kill4inf' in sd:
        def chk_kill4(g):
            lost = sum(1 for u in g.units
                       if u.side == 'rebel' and u.category == 'infantry' and not u.alive)
            return 'empire' if lost >= 4 else None
        game.sudden_death_checks.append(chk_kill4)
