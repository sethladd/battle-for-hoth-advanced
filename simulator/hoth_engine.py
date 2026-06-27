"""
Battle of Hoth -- Advanced Deck balance simulator: CORE ENGINE.

Implements an abstracted-but-faithful model of the published rules
(Richard Borg / Days of Wonder hex-and-card system) so that the ADVANCED
card deck can be stress-tested for balance via AI vs AI play.

Coordinate system
-----------------
Board is 10 columns (q = 0..9) x 7 rows (r = 0..6), flat-top hexes,
"odd-q" vertical offset layout. Offset coords are canonical; cube coords
are used for distance and neighbours.

Documented modelling assumptions (see balance report):
  * Attack die has 6 faces: Infantry, Infantry, Vehicle, Blast, Retreat, Miss
    => P(inf)=2/6, P(veh)=1/6, P(blast)=1/6, P(retreat)=1/6, P(miss)=1/6.
    A target is "hit" by faces matching its type, plus every Blast.
  * Unit attack profiles (dice by hex distance) and movement match the
    rulebook unit recap; AT-AT / artillery long-range values are inferred
    (the printed dice diagrams are images) and are flagged in the report.
  * Line of sight uses a hex-supercover test with the rulebook's terrain
    blocking rules (ridges/rocks/buildings/seracs/structures), approximated.
"""

import random
import math
from dataclasses import dataclass, field

BOARD_W = 10
BOARD_H = 7

def valid_hex(col, row):
    """Brick layout: even rows have 10 hexes (cols 0-9); odd (inset) rows have 9 (cols 0-8)."""
    if not (0 <= row < BOARD_H and 0 <= col):
        return False
    return col < (BOARD_W - 1 if row % 2 else BOARD_W)

# ---------------------------------------------------------------------------
# Hex geometry (odd-q offset <-> cube)
# ---------------------------------------------------------------------------

def offset_to_cube(col, row):
    # "odd-r" pointy-top: odd ROWS are shifted right by half a hex
    x = col - (row - (row & 1)) // 2
    z = row
    y = -x - z
    return (x, y, z)

def cube_distance(a, b):
    ax, ay, az = a
    bx, by, bz = b
    return (abs(ax - bx) + abs(ay - by) + abs(az - bz)) // 2

def hex_distance(p, q):
    return cube_distance(offset_to_cube(*p), offset_to_cube(*q))

# "odd-r" pointy-top neighbour directions (odd rows shifted right)
_ODDR_DIRS = {
    0: [(+1, 0), (0, -1), (-1, -1), (-1, 0), (-1, +1), (0, +1)],   # even row
    1: [(+1, 0), (+1, -1), (0, -1), (-1, 0), (0, +1), (+1, +1)],   # odd row
}

def neighbors(col, row):
    parity = row & 1
    out = []
    for dc, dr in _ODDR_DIRS[parity]:
        nc, nr = col + dc, row + dr
        if valid_hex(nc, nr):
            out.append((nc, nr))
    return out

def all_hexes():
    return [(c, r) for c in range(BOARD_W) for r in range(BOARD_H) if valid_hex(c, r)]

def section_of(col):
    """Return set of sections a column belongs to. left=0, center=1, right=2.
    Overlap columns belong to two sections (red dotted lines cut hexes)."""
    s = set()
    if col <= 3:
        s.add('left')
    if 3 <= col <= 6:
        s.add('center')
    if col >= 6:
        s.add('right')
    return s

def flank_of(col):
    s = set()
    if col <= 3:
        s.add('left')
    if col >= 6:
        s.add('right')
    return s

# ---------------------------------------------------------------------------
# Terrain
# ---------------------------------------------------------------------------
# terrain types: 'open','ridge','rocks','buildings','trenches','crevasse',
#                'serac','structure'
BLOCK_LOS = {'ridge', 'rocks', 'buildings', 'serac', 'structure'}
STOP_ON_ENTER = {'rocks', 'buildings'}
NO_ATTACK_AFTER_ENTER = {'rocks', 'buildings'}

def impassable_for(terr, unit):
    if terr == 'serac' or terr == 'structure':
        return True
    if terr == 'crevasse':
        return not unit.flying
    if terr == 'ridge':
        return unit.kind == 'AT-AT'
    return False

# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

@dataclass
class UnitType:
    kind: str
    category: str          # 'infantry','vehicle','special'
    full: int              # miniatures at full strength
    move: int              # max move hexes
    move_attack: int       # max move hexes that still allows an attack
    attack: dict           # {distance: dice}
    flying: bool = False
    ignore_retreat: bool = False
    no_terrain_protection: bool = False
    grants_medal: bool = True
    confirmation: bool = False   # AT-AT special death rule
    ignore_terrain_stop: bool = False   # cavalry: not forced to stop on rough terrain
    after_attack_move: int = 0          # inherent hit-and-run / overrun distance
    is_structure: bool = False          # shield generator / ion cannon (destroyed on a blast)

# Inferred / rulebook-derived stat block (see report for sourcing)
UNIT_TYPES = {
    'echo':      UnitType('echo', 'infantry', 3, 2, 1, {1: 3, 2: 2, 3: 1}),
    'snowtroop': UnitType('snowtroop', 'infantry', 4, 2, 1, {1: 3, 2: 2, 3: 1}),
    'speeder':   UnitType('speeder', 'vehicle', 3, 3, 3, {1: 4, 2: 2}, flying=True),
    'atat':      UnitType('atat', 'vehicle', 1, 1, 1, {1: 3, 2: 3, 3: 3},
                          ignore_retreat=True, no_terrain_protection=True, confirmation=True),
    'artillery': UnitType('artillery', 'special', 1, 0, 0, {1: 1, 2: 3, 3: 3},
                          ignore_retreat=True, grants_medal=False),
    'droid':     UnitType('droid', 'special', 2, 2, 2, {1: 2, 2: 1},
                          grants_medal=False),
    # --- Advanced expansion units ---
    # Tauntaun Scout (Rebel light cavalry): fast, close-combat, hit-and-run.
    # Inspired by C&C/Memoir cavalry: high move, strong melee, takes ground after combat.
    'tauntaun':  UnitType('tauntaun', 'infantry', 2, 3, 2, {1: 3, 2: 1},
                          ignore_terrain_stop=True, after_attack_move=1),
    # AT-ST scout walker (Imperial medium armor): between the Snowspeeder and the AT-AT.
    # Inspired by the Memoir '44 tank (3/3/3, mobile) but lighter to fit Hoth's scale.
    'atst':      UnitType('atst', 'vehicle', 2, 2, 2, {1: 3, 2: 3, 3: 2}),
    # lone Darth Vader figure (after his escort is destroyed but he survives)
    'vader':     UnitType('vader', 'infantry', 1, 1, 1, {1: 3, 2: 1}),
    # structures: special, immobile, no attack, hit only on a blast (1 hit destroys them)
    'shieldgen': UnitType('shieldgen', 'special', 1, 0, 0, {}, grants_medal=False,
                          is_structure=True, ignore_retreat=True, no_terrain_protection=True),
    'ioncannon': UnitType('ioncannon', 'special', 1, 0, 0, {}, grants_medal=False,
                          is_structure=True, ignore_retreat=True, no_terrain_protection=True),
}

# --- Advanced Leader definitions (on-board characters) ---
# escort: eligible escort unit kind.  combat: bonus applied to the escort's attacks.
# aura: {range, type, amount} applied to nearby friendly units (or 'fear' to enemies).
# bonus_medal: medals the opponent scores if the leader is captured/killed.
LEADER_DEF = {
    'Luke':  dict(side='rebel', escort='speeder', combat=dict(dice=1, reroll=True),
                  ignore_retreat_self=1, aura=dict(range=1, type='ignore_retreat'),
                  bonus_medal=2),
    'Han':   dict(side='rebel', escort='tauntaun', combat=dict(dice=1, reroll=True),
                  aura=dict(range=1, type='move', amount=1), bonus_medal=1),
    'Leia':  dict(side='rebel', escort='echo', combat=dict(dice=1), extra_fig=1, rally=True,
                  aura=dict(range=1, type='none'), bonus_medal=2),
    'Vader': dict(side='empire', escort='snowtroop',
                  combat=dict(close_dice=2, retreat_as_hit=True, ignore_terrain=True),
                  aura=dict(range=1, type='fear'), bonus_medal=2, immortal=True),
    'Veers': dict(side='empire', escort='atat', combat=dict(dice=1),
                  aura=dict(range=99, type='vehicle_close'), bonus_medal=1),
    'Piett': dict(side='empire', offboard=True, bonus_medal=0),
}

@dataclass
class Unit:
    utype: UnitType
    side: str            # 'rebel' or 'empire'
    pos: tuple
    figs: int
    badge: str = None    # special-forces badge: 'assault','eweb','scout','elite', etc.
    eweb_inplace: bool = True
    uid: int = 0
    leader: str = None   # name of the leader character riding with this unit

    @property
    def kind(self):
        return self.utype.kind
    @property
    def category(self):
        return self.utype.category
    @property
    def flying(self):
        return self.utype.flying
    @property
    def alive(self):
        return self.figs > 0

# ---------------------------------------------------------------------------
# Dice
# ---------------------------------------------------------------------------
FACES = ['inf', 'inf', 'veh', 'blast', 'retreat', 'miss']

def roll(n, rng):
    return [rng.choice(FACES) for _ in range(max(0, n))]

def count_hits(faces, target_category):
    """Hits against a unit of target_category (infantry/vehicle/special)."""
    hits = 0
    retreats = 0
    for f in faces:
        if f == 'blast':
            hits += 1
        elif f == 'inf' and target_category == 'infantry':
            hits += 1
        elif f == 'veh' and target_category == 'vehicle':
            hits += 1
        elif f == 'retreat':
            retreats += 1
    return hits, retreats

# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------

class Game:
    def __init__(self, terrain, units, first='rebel', medals_to_win=6, rng=None):
        self.terrain = terrain                 # {(c,r): terrtype}
        self.units = [u for u in units]
        for i, u in enumerate(self.units):
            u.uid = i
        self.first = first
        self.turn_side = first
        self.medals = {'rebel': 0, 'empire': 0}
        if isinstance(medals_to_win, dict):
            self.medals_to_win = medals_to_win
        else:
            self.medals_to_win = {'rebel': medals_to_win, 'empire': medals_to_win}
        self.rng = rng or random.Random()
        self.turn_count = 0
        self.log = []
        self.recording = False   # when True, append human-readable events to self.log
        self._log_mark = 0
        self.cur_turn = 0
        self.cur_side = '-'
        self.cur_card = ''
        self.cur_hands = {}
        # --- scenario special-rule hooks (set by the Scenario loader) ---
        self.droid_medal_to_rebel = 0
        self.droid_medal_to_empire = 0
        self.kill_bonus = {}                 # per-(kind, by_side) medal override
        self.no_kill_medal = set()           # sides that score no medals from kills
        self.sudden_death_checks = []        # callables game-> winner/None
        self.objectives = []                 # hold-hex objectives
        self.ion = None                      # ion-cannon charge
        self.exits = {'rebel': 0, 'empire': 0}
        self.exit_medal = {}

    def snapshot(self):
        return [dict(kind=u.kind, side=u.side, col=u.pos[0], row=u.pos[1], figs=u.figs,
                     leader=u.leader)
                for u in self.units if u.alive]

    def emit_substep(self, phase):
        """Record a sub-frame (Move / Fire / Retreat) for the replay viewer."""
        if not self.recording or not hasattr(self, 'frames'):
            return
        new = self.log[self._log_mark:]
        self._log_mark = len(self.log)
        self.frames.append(dict(turn=self.cur_turn, side=self.cur_side, card=self.cur_card,
                                phase=phase, events=list(new), units=self.snapshot(),
                                medals=dict(self.medals), hands=self.cur_hands))

    def process_objectives(self, side):
        """Called at the start of each turn: resolve hold-hex medals (contestable
        by both sides) and ion-cannon charge for `side`."""
        for ob in self.objectives:
            owner = ob['side']
            holder = self.unit_at(ob['hex'])
            holds = holder is not None and holder.side == owner
            if ob['mode'] == 'perm':
                if holds and not ob.get('claimed'):
                    ob['claimed'] = True
                    self.medals[owner] += ob['value']
            else:  # temp: medal is held only while occupied by the owner
                if holds and not ob.get('held'):
                    ob['held'] = True
                    self.medals[owner] += ob['value']
                elif not holds and ob.get('held'):
                    ob['held'] = False
                    self.medals[owner] = max(0, self.medals[owner] - ob['value'])
        if self.ion and self.ion['side'] == side:
            self.ion['charge'] += 1
            if self.ion['charge'] >= self.ion['cap']:
                self.ion['charge'] -= self.ion['cap']
                self.medals[side] += 1

    # -- queries --
    def terr(self, pos):
        return self.terrain.get(pos, 'open')

    def unit_at(self, pos):
        for u in self.units:
            if u.alive and u.pos == pos:
                return u
        return None

    def side_units(self, side):
        return [u for u in self.units if u.alive and u.side == side]

    def enemies_of(self, side):
        other = 'empire' if side == 'rebel' else 'rebel'
        return self.side_units(other)

    def baseline_row(self, side):
        # rebels baseline at row 0, empire at row BOARD_H-1 (arbitrary, consistent)
        return 0 if side == 'rebel' else BOARD_H - 1

    def winner(self):
        for chk in self.sudden_death_checks:
            w = chk(self)
            if w:
                return w
        if self.medals['rebel'] >= self.medals_to_win['rebel']:
            return 'rebel'
        if self.medals['empire'] >= self.medals_to_win['empire']:
            return 'empire'
        return None

    # -- movement --
    def reachable_extra(self, unit, extra):
        return self.reachable(unit, extra_move=extra)

    def reachable(self, unit, extra_move=0):
        """BFS reachable hexes -> dict pos: (steps, can_attack_after)."""
        start = unit.pos
        maxmove = unit.utype.move + (extra_move if unit.utype.move > 0 else 0)
        if maxmove == 0:
            return {start: (0, True)}
        # eweb 'in place' acts as standard infantry when moving; fine.
        occupied = {u.pos for u in self.units if u.alive and u.uid != unit.uid}
        result = {start: (0, True)}
        frontier = [(start, 0, False)]  # pos, steps, stopped
        while frontier:
            pos, steps, stopped = frontier.pop()
            if stopped or steps >= maxmove:
                continue
            for nb in neighbors(*pos):
                terr = self.terr(nb)
                if impassable_for(terr, unit):
                    continue
                if nb in occupied:
                    continue
                nsteps = steps + 1
                stop_here = (terr in STOP_ON_ENTER) and not unit.utype.ignore_terrain_stop
                can_attack = nsteps <= unit.utype.move_attack and terr not in NO_ATTACK_AFTER_ENTER
                prev = result.get(nb)
                if prev is None or nsteps < prev[0]:
                    result[nb] = (nsteps, can_attack)
                    frontier.append((nb, nsteps, stop_here))
        return result

    # -- line of sight (approximate hex supercover) --
    def has_los(self, a, b):
        if a == b:
            return True
        ca = offset_to_cube(*a)
        cb = offset_to_cube(*b)
        N = cube_distance(ca, cb)
        if N == 0:
            return True
        between = set()
        for i in range(1, N):
            t = i / N
            x = ca[0] + (cb[0] - ca[0]) * t
            y = ca[1] + (cb[1] - ca[1]) * t
            z = ca[2] + (cb[2] - ca[2]) * t
            # round cube
            rx, ry, rz = round(x), round(y), round(z)
            dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
            if dx > dy and dx > dz:
                rx = -ry - rz
            elif dy > dz:
                ry = -rx - rz
            else:
                rz = -rx - ry
            between.add((rx, ry, rz))
        a_ridge = self.terr(a) == 'ridge'
        b_ridge = self.terr(b) == 'ridge'
        for cube in between:
            pos = self._cube_to_offset(cube)
            if pos is None:
                continue
            terr = self.terr(pos)
            # ridges block unless both endpoints on ridge
            if terr == 'ridge':
                if not (a_ridge and b_ridge):
                    return False
            elif terr in ('rocks', 'buildings', 'serac', 'structure'):
                return False
            # blocking units
            u = self.unit_at(pos)
            if u is not None:
                return False
        return True

    @staticmethod
    def _cube_to_offset(cube):
        x, y, z = cube
        row = z
        col = x + (z - (z & 1)) // 2
        if valid_hex(col, row):
            return (col, row)
        return None

    # -- attack --
    def attack_dice(self, attacker, target, extra_dice=0, ignore_terrain=False,
                    close_only_bonus=0):
        dist = hex_distance(attacker.pos, target.pos)
        prof = attacker.utype.attack
        if dist not in prof:
            return None  # out of range
        dice = prof[dist]
        dice += extra_dice
        if dist == 1:
            dice += close_only_bonus
        if not ignore_terrain:
            tterr = self.terr(target.pos)
            if not attacker.utype.no_terrain_protection:
                # protection of target's terrain (attacker is the one reducing)
                if tterr == 'rocks':
                    dice -= 2 if attacker.category == 'vehicle' else 1
                elif tterr == 'buildings':
                    dice -= 2 if attacker.category == 'vehicle' else 1
                elif tterr == 'trenches' and target.category == 'infantry':
                    dice -= 1
                elif tterr == 'ridge' and self.terr(attacker.pos) != 'ridge':
                    dice -= 1
            # attacker terrain penalty
            aterr = self.terr(attacker.pos)
            if aterr == 'buildings' and attacker.category == 'vehicle':
                dice -= 2
        return max(0, dice)

    def resolve_attack(self, attacker, target, extra_dice=0, ignore_terrain=False,
                       close_only_bonus=0, reroll_misses=False, retreat_as_hit=False,
                       reroll_one=False):
        n = self.attack_dice(attacker, target, extra_dice, ignore_terrain, close_only_bonus)
        if n is None:
            return False
        faces = roll(n, self.rng)
        if reroll_misses:                       # reroll ALL misses (a one-shot card)
            faces = [f if f != 'miss' else self.rng.choice(FACES) for f in faces]
        elif reroll_one:                        # reroll a single die (the Force, passive)
            for i, f in enumerate(faces):
                if f == 'miss':
                    faces[i] = self.rng.choice(FACES)
                    break
        hits, retreats = count_hits(faces, target.category)
        if retreat_as_hit and retreats:     # Force Push / Vader: retreats become hits
            hits += retreats
            retreats = 0
        if self.recording:
            self.log.append({'type': 'attack', 'from': list(attacker.pos), 'to': list(target.pos),
                             'atk_kind': attacker.kind, 'tgt_kind': target.kind,
                             'dice': n, 'faces': faces, 'hits': hits, 'retreats': retreats})

        # E-Web in place reroll handled by reroll_misses flag at call site.

        # AT-AT confirmation: hits on an AT-AT are re-rolled; a blast eliminates it
        if target.utype.confirmation and hits > 0:
            confirm = roll(hits, self.rng)
            if 'blast' in confirm:
                self._eliminate(attacker.side, target)
                self.emit_substep('Fire')
                return True
            else:
                # AT-AT has 1 fig; non-confirmed hits do nothing
                hits = 0

        if hits > 0:
            removed = min(hits, target.figs)
            target.figs -= removed
            if target.figs <= 0:
                self._eliminate(attacker.side, target)
                self.emit_substep('Fire')
                return True

        self.emit_substep('Fire')
        # retreats (leaders may let the target ignore some)
        if retreats > 0 and not target.utype.ignore_retreat and target.alive:
            retreats = max(0, retreats - self.retreat_ignore(target))
        if retreats > 0 and not target.utype.ignore_retreat and target.alive:
            self._apply_retreat(attacker.side, target, retreats)
            self.emit_substep('Retreat')
        return True

    def _apply_retreat(self, attacker_side, target, n):
        toward = self.baseline_row(target.side)
        step = -1 if toward < target.pos[1] else 1
        for _ in range(n):
            if not target.alive:
                break
            options = []
            for nb in neighbors(*target.pos):
                # must move toward baseline (row closer to baseline)
                if (toward - target.pos[1]) * (nb[1] - target.pos[1]) <= 0:
                    continue
                terr = self.terr(nb)
                if impassable_for(terr, target):
                    continue
                if self.unit_at(nb) is not None:
                    continue
                options.append(nb)
            if not options:
                # cannot retreat: 1 casualty
                target.figs -= 1
                if target.figs <= 0:
                    self._eliminate(attacker_side, target)
                    break
            else:
                # pick hex closest to baseline
                options.sort(key=lambda p: abs(p[1] - toward))
                frm = target.pos
                target.pos = options[0]
                if self.recording:
                    self.log.append({'type': 'retreat', 'kind': target.kind,
                                     'frm': list(frm), 'to': list(target.pos)})

    def medal_value(self, unit, by_side):
        # explicit per-(kind, side) override wins first (e.g. droid=2, atat=2)
        if (unit.kind, by_side) in self.kill_bonus:
            return self.kill_bonus[(unit.kind, by_side)]
        # back-compat for droid alias
        if unit.kind == 'droid':
            v = self.droid_medal_to_rebel if by_side == 'rebel' else self.droid_medal_to_empire
            if v:
                return v
        if by_side in self.no_kill_medal:
            return 0
        return 1 if unit.utype.grants_medal else 0

    def retreat_ignore(self, target):
        """How many retreats `target` may ignore thanks to a leader (self or aura)."""
        ig = 0
        if target.leader:
            ig += LEADER_DEF[target.leader].get('ignore_retreat_self', 0)
        for u in self.units:
            if u.alive and u.side == target.side and u.leader:
                a = LEADER_DEF[u.leader].get('aura', {})
                if a.get('type') == 'ignore_retreat' and u.uid != target.uid:
                    if hex_distance(u.pos, target.pos) <= a['range']:
                        ig += 1
                        break
        return ig

    def _eliminate(self, by_side, unit):
        unit.figs = 0
        mv = self.medal_value(unit, by_side)
        self.medals[by_side] += mv
        if self.recording:
            self.log.append({'type': 'eliminate', 'pos': list(unit.pos),
                             'kind': unit.kind, 'side': unit.side, 'by': by_side, 'medal': mv})
        if unit.leader:
            self._handle_leader_loss(by_side, unit)

    def _handle_leader_loss(self, by_side, unit):
        name = unit.leader
        unit.leader = None
        ldef = LEADER_DEF[name]
        # try to escape to an adjacent friendly unit
        for nb in neighbors(*unit.pos):
            f = self.unit_at(nb)
            if f and f.alive and f.side == unit.side and not f.leader:
                f.leader = name
                if self.recording:
                    self.log.append({'type': 'leader_escape', 'name': name, 'to': list(f.pos)})
                return
        if ldef.get('immortal'):           # Vader survives as a lone Sith figure
            lone = Unit(UNIT_TYPES['vader'], unit.side, unit.pos, 1)
            lone.uid = len(self.units)
            self.units.append(lone)
            self.kill_bonus[('vader', by_side)] = ldef['bonus_medal']
            if self.recording:
                self.log.append({'type': 'leader_survive', 'name': name, 'pos': list(unit.pos)})
            return
        # captured / killed -> opponent scores the bonus medal
        self.medals[by_side] += ldef['bonus_medal']
        if self.recording:
            self.log.append({'type': 'leader_captured', 'name': name, 'by': by_side,
                             'medal': ldef['bonus_medal']})
