"""
Battle of Hoth -- Advanced Deck balance simulator: AI + turn engine + runner.

Heuristic AI plays both sides. Greedy value model:
  value(action) = expected miniatures removed + MEDAL_W * P(kill)
Units order to maximise summed value; otherwise advance toward the enemy,
preferring cover. Reaction cards (ambush/evade/cover) fire on the opponent's
turn when their trigger conditions are met and the holding side benefits.
"""

import random
from hoth_engine import (Game, Unit, UNIT_TYPES, hex_distance, neighbors,
                         section_of, flank_of, FACES, roll, count_hits, BOARD_W, BOARD_H)

MEDAL_W = 4.5          # weight of scoring a medal vs a plain casualty
ADVANCE_W = 0.35       # value of closing distance when no attack available
RISK_W = 0.12          # how strongly to avoid exposing units to lethal return fire

# per-die hit probability by target category
PHIT = {'infantry': 3/6, 'vehicle': 2/6, 'special': 1/6}
PRET = 1/6

# Per-side AI policy. 'base' = refined greedy (validated strongest in A/B testing);
# 'smart' = experimental lookahead/minimax (kept for analysis, not stronger here).
AI_MODE = {'rebel': 'base', 'empire': 'base'}
BASE_JITTER = 0.10     # randomness in card choice; lower = more consistently optimal


def leader_attack_mods(game, attacker):
    """Combat bonuses on `attacker` from its own leader, friendly auras, and enemy Fear."""
    from hoth_engine import LEADER_DEF
    m = dict(dice=0, close_dice=0, reroll_one=False, retreat_as_hit=False, ignore_terrain=False)
    if attacker.leader:
        cb = LEADER_DEF[attacker.leader].get('combat', {})
        m['dice'] += cb.get('dice', 0); m['close_dice'] += cb.get('close_dice', 0)
        m['reroll_one'] = m['reroll_one'] or cb.get('reroll', False)
        m['retreat_as_hit'] = m['retreat_as_hit'] or cb.get('retreat_as_hit', False)
        m['ignore_terrain'] = m['ignore_terrain'] or cb.get('ignore_terrain', False)
    for u in game.units:
        if not u.alive or not u.leader:
            continue
        a = LEADER_DEF[u.leader].get('aura', {})
        if u.side == attacker.side and a.get('type') == 'dice' and u.uid != attacker.uid:
            if hex_distance(u.pos, attacker.pos) <= a['range']:
                m['dice'] += a.get('amount', 0)
        if u.side != attacker.side and a.get('type') == 'fear':
            if hex_distance(u.pos, attacker.pos) <= a['range']:
                m['dice'] -= 1
    return m

def leader_move_bonus(game, unit):
    """Extra movement granted by a friendly leader's aura (e.g. Han)."""
    from hoth_engine import LEADER_DEF
    best = 0
    for u in game.units:
        if not u.alive or not u.leader or u.side != unit.side or u.uid == unit.uid:
            continue
        a = LEADER_DEF[u.leader].get('aura', {})
        if a.get('type') == 'move' and hex_distance(u.pos, unit.pos) <= a['range']:
            best = max(best, a.get('amount', 0))
    return best

def threat_at(game, unit, pos):
    """Expected hits the enemy could land on `unit` if it sits on `pos` next turn
    (any enemy that could move-and-attack into range). Used for self-preservation."""
    t = 0.0
    p = PHIT[unit.category]
    for e in game.enemies_of(unit.side):
        if not e.alive:
            continue
        rng = e.utype.move_attack + max(e.utype.attack.keys())
        if hex_distance(e.pos, pos) <= rng:
            t += max(e.utype.attack.values()) * p
    return t

def risk_penalty(game, unit, pos):
    """Cost of ending on `pos`: chance of losing miniatures (and feeding a medal)."""
    th = threat_at(game, unit, pos)
    if th <= 0:
        return 0.0
    mv = 1 if unit.utype.grants_medal else 0
    # probability the threat removes the unit's remaining figures
    p_wipe = min(1.0, th / max(1, unit.figs))
    return RISK_W * (MEDAL_W * mv + unit.figs) * p_wipe

# --------------------------------------------------------------------------
# value estimation
# --------------------------------------------------------------------------
def est_attack_value(game, attacker, target, bonus, dist_override=None,
                     focus_extra=0):
    from hoth_engine import hex_distance
    n = game.attack_dice(
        attacker, target,
        extra_dice=bonus.get('dice', 0) + focus_extra
                   + (bonus.get('close_dice', 0) if hex_distance(attacker.pos, target.pos) == 1 else 0)
                   + escalation_dice(game, attacker.side, bonus),
        ignore_terrain=bonus.get('ignore_terrain', False),
    )
    if n is None:
        return 0.0
    twice = 2 if bonus.get('attack_twice') else 1
    p = PHIT[target.category]
    if bonus.get('reroll'):
        p = p + (1 - p) * p          # one reroll of misses
    if bonus.get('retreat_as_hit'):
        p = min(1.0, p + PRET)
    exp_hits = n * p * twice
    figs_removed = min(exp_hits, target.figs)
    # medal probability
    if target.utype.confirmation:           # AT-AT
        p_any = 1 - (1 - p) ** max(1, n)
        p_kill = p_any * (1 - (5/6) ** max(1, round(n * p))) * twice
        p_kill = min(0.95, p_kill)
        medal = MEDAL_W * p_kill
        figs_removed = 0
    else:
        p_kill = 1.0 if exp_hits >= target.figs else exp_hits / max(1, target.figs)
        mv = game.medal_value(target, attacker.side)
        if mv > 0:
            medal = MEDAL_W * mv * min(1.0, p_kill)
        else:
            medal = 0.6 * min(1.0, p_kill)
    return figs_removed + medal

def escalation_dice(game, side, bonus):
    esc = bonus.get('escalation')
    if not esc:
        return 0
    kind, cap = esc
    if kind == 'comeback':
        opp = 'empire' if side == 'rebel' else 'rebel'
        return min(cap, game.medals[opp])
    if kind == 'snowball':
        opp = 'empire' if side == 'rebel' else 'rebel'
        weak = sum(1 for u in game.side_units(opp) if u.figs * 2 <= u.utype.full)
        return min(cap, weak)
    return 0

# --------------------------------------------------------------------------
# unit action planning
# --------------------------------------------------------------------------
def plan_unit_action(game, unit, bonus, hit_targets, smart=True):
    """Return dict(move_to, target, value). hit_targets: {uid: count} for focus."""
    enemies = game.enemies_of(unit.side)
    if not enemies:
        return None
    reach = game.reachable(unit)
    if bonus.get('move'):
        reach = game.reachable_extra(unit, bonus['move']) if hasattr(game, 'reachable_extra') else reach
    if bonus.get('no_move'):
        reach = {unit.pos: (0, True)}
    if bonus.get('full_move_attack'):
        # all reachable hexes can attack
        reach = {p: (s, True) for p, (s, _) in reach.items()}

    # exit-race mode: this side scores medals by exiting the enemy baseline
    exit_val = getattr(game, 'exit_medal', {}).get(unit.side, 0)
    exit_row = (BOARD_H - 1) if unit.side == 'rebel' else 0
    if exit_val:
        on_base = [p for p in reach if p[1] == exit_row]
        if on_base:
            # reaching the baseline = a guaranteed medal next step (exit)
            best_exit = max(on_base, key=lambda p: reach[p][0] == 0)
            return dict(move_to=on_base[0], target=None, value=MEDAL_W * exit_val)

    # objective-hex seeking: head for an unheld friendly objective hex
    my_obj = [ob for ob in getattr(game, 'objectives', []) if ob['side'] == unit.side]
    if my_obj:
        # nearest objective not currently held by us
        target_ob = min(my_obj, key=lambda ob: hex_distance(unit.pos, ob['hex']))
        oh = target_ob['hex']
        held = game.unit_at(oh) is not None and game.unit_at(oh).side == unit.side
        if not held and oh in reach:
            return dict(move_to=oh, target=None, value=MEDAL_W * target_ob['value'] * 0.8)
        if not held:
            bp = min(reach.keys(), key=lambda p: hex_distance(p, oh))
            if hex_distance(bp, oh) < hex_distance(unit.pos, oh):
                # still let attacks override below by recording as fallback
                pass

    best = dict(move_to=unit.pos, target=None, value=0.0)
    for pos, (steps, can_atk) in reach.items():
        # temporarily consider attacking from pos
        if can_atk and unit.utype.attack:
            saved = unit.pos
            unit.pos = pos
            for e in enemies:
                if not game.has_los(pos, e.pos):
                    continue
                focus_extra = 0
                if bonus.get('focus') == 'simple' and hit_targets.get(e.uid):
                    focus_extra = hit_targets[e.uid]
                elif bonus.get('focus') == 'escalate' and hit_targets.get(e.uid):
                    focus_extra = 1 if hit_targets[e.uid] == 1 else 2
                v = est_attack_value(game, unit, e, bonus, focus_extra=focus_extra)
                if smart:
                    v -= risk_penalty(game, unit, pos)  # prefer safe firing positions
                if v > best['value']:
                    best = dict(move_to=pos, target=e, value=v)
            unit.pos = saved
    if best['target'] is not None and not (exit_val and best['value'] < MEDAL_W):
        return best
    # exit-race: push toward the enemy baseline, favouring cover
    if exit_val:
        def exit_score(pos):
            prog = -(abs(pos[1] - exit_row))
            cover = 0.4 if game.terr(pos) in ('trenches', 'rocks', 'ridge', 'buildings') else 0
            return prog + cover
        bp = max(reach.keys(), key=exit_score)
        return dict(move_to=bp, target=None, value=ADVANCE_W if bp != unit.pos else 0.0)
    # no attack: advance toward the most VALUABLE enemy (medal-weighted), not just
    # the nearest -- this makes Rebels hunt the 2-medal probe droids.
    def enemy_priority(e):
        mv = game.medal_value(e, unit.side)
        return (1 + 1.5 * mv) - 0.12 * hex_distance(unit.pos, e.pos)
    target_enemy = max(enemies, key=enemy_priority)
    # score each reachable hex: progress toward target, cover bonus, exposure penalty
    def hex_score(pos):
        d = hex_distance(pos, target_enemy.pos)
        s = -d
        terr = game.terr(pos)
        if terr in ('trenches', 'rocks', 'ridge', 'buildings'):
            s += 0.6        # value cover
        if smart:
            s -= risk_penalty(game, unit, pos)   # threat-aware self-preservation
        else:
            exp = sum(1 for e in enemies
                      if hex_distance(pos, e.pos) <= max(e.utype.attack.keys()))
            s -= 0.4 * exp
        return s
    best_pos = max(reach.keys(), key=hex_score)
    return dict(move_to=best_pos, target=None,
                value=ADVANCE_W * 0.5 if best_pos != unit.pos else 0.0)

# --------------------------------------------------------------------------
# ordering scope
# --------------------------------------------------------------------------
def eligible_units(game, side, order):
    units = game.side_units(side)
    filt = order.get('filter')
    if filt:
        units = [u for u in units if u.category == filt]
    return units

def units_in_scope(game, side, order):
    """Return list of candidate units honoring the card's section/flank rules,
    choosing the best section/flank greedily by enemy proximity."""
    units = eligible_units(game, side, order)
    mode = order['mode']
    n = order.get('n')
    if mode == 'none':
        return []
    if mode == 'fixed_section':              # card dictates the sector (no choice)
        z = order['zone']
        us = [u for u in units if z in section_of(u.pos[0])]
        return _topn(game, us, n)
    if mode == 'anywhere':
        return _topn(game, units, n)
    if mode == 'each_section':
        out = []
        for sec in ('left', 'center', 'right'):
            us = [u for u in units if sec in section_of(u.pos[0])]
            out += _topn(game, us, n)
        return list({u.uid: u for u in out}.values())
    if mode == 'each_flank':
        out = []
        for fl in ('left', 'right'):
            us = [u for u in units if fl in flank_of(u.pos[0])]
            out += _topn(game, us, n)
        return list({u.uid: u for u in out}.values())
    if mode in ('section', 'flank'):
        zones = ('left', 'center', 'right') if mode == 'section' else ('left', 'right')
        best_zone, best_units, best_val = None, [], -1
        for z in zones:
            if mode == 'section':
                us = [u for u in units if z in section_of(u.pos[0])]
            else:
                us = [u for u in units if z in flank_of(u.pos[0])]
            sel = _topn(game, us, n)
            val = sum(_quickval(game, u) for u in sel) + 0.01 * len(sel)
            if val > best_val:
                best_zone, best_units, best_val = z, sel, val
        return best_units
    return _topn(game, units, n)

def _quickval(game, u):
    enemies = game.enemies_of(u.side)
    if not enemies:
        return 0
    d = min(hex_distance(u.pos, e.pos) for e in enemies)
    return max(0.0, 5 - d)

def _topn(game, units, n):
    if n == 'all' or n is None:
        return list(units)
    units = sorted(units, key=lambda u: _quickval(game, u), reverse=True)
    return units[:n]

# --------------------------------------------------------------------------
# executing a card
# --------------------------------------------------------------------------
def execute_card(game, side, card, states):
    bonus = card.get('bonus', {})
    order = card.get('order', {})
    passive = states[side].get('passive')

    # passive: command_network -> first unit +1 die handled below
    extra_draw = bonus.get('draw', 0)

    # Piett orbital bombardment
    if bonus.get('multi_target'):
        dice, ntar = bonus['multi_target']
        enemies = sorted(game.enemies_of(side),
                         key=lambda e: -est_attack_value_simple(e))
        for e in enemies[:ntar]:
            faces = roll(dice, game.rng)
            hits, rets = count_hits(faces, e.category)
            if e.utype.confirmation and hits > 0:
                if 'blast' in roll(hits, game.rng):
                    game._eliminate(side, e); continue
                hits = 0
            if hits:
                e.figs -= min(hits, e.figs)
                if e.figs <= 0:
                    game._eliminate(side, e)
        game.emit_substep('Fire')
        return extra_draw

    smart = AI_MODE.get(side, 'smart') == 'smart'
    ordered = units_in_scope(game, side, order)

    # rulebook fallback: a filtered card that finds no eligible units instead
    # orders 1 unit of your choice, with NO bonus.
    if order.get('filter') and not ordered:
        any_units = _topn(game, game.side_units(side), 1)
        ordered = any_units
        bonus = {}

    # reinforce (non-attacking) handled: such units regain figs and don't attack
    reinforce = bonus.get('reinforce', 0)

    # plan: first move all, then attack all (rules sequence), tracking focus
    hit_targets = {}
    plans = []
    # command_network: give first ordered unit +1 die
    first_bonus_used = False
    for u in ordered:
        ubonus = dict(bonus)
        if passive == 'command_network' and not first_bonus_used:
            ubonus['dice'] = ubonus.get('dice', 0) + 1
            first_bonus_used = True
        if passive == 'armored_spearhead' and u.category == 'vehicle':
            ubonus['close_dice'] = ubonus.get('close_dice', 0) + 1
        if u.utype.after_attack_move:   # cavalry inherent hit-and-run
            ubonus['after_move'] = max(ubonus.get('after_move', 0), u.utype.after_attack_move)
        amb = leader_move_bonus(game, u)   # Han's aura grants +movement nearby
        if amb:
            ubonus['move'] = ubonus.get('move', 0) + amb
        p = plan_unit_action(game, u, ubonus, hit_targets, smart=smart)
        plans.append((u, ubonus, p))

    # execute moves
    exit_val = getattr(game, 'exit_medal', {}).get(side, 0)
    exit_row = (BOARD_H - 1) if side == 'rebel' else 0
    for u, ubonus, p in plans:
        if p and p['move_to'] != u.pos and game.unit_at(p['move_to']) is None:
            old = u.pos
            u.pos = p['move_to']
            if game.recording:
                game.log.append({'type': 'move', 'kind': u.kind, 'side': u.side,
                                 'frm': list(old), 'to': list(u.pos)})
        # exit the board for medals (exit-race scenarios)
        if exit_val and u.pos[1] == exit_row:
            game.medals[side] += exit_val
            game.exits[side] = game.exits.get(side, 0) + 1
            u.figs = 0
            u.exited = True

    game.emit_substep('Move')

    # reinforce step (units that won't attack)
    if reinforce:
        for u, ubonus, p in plans:
            if not p or p['target'] is None:
                u.figs = min(u.utype.full, u.figs + reinforce)

    # execute attacks
    attackers = [(u, ub) for (u, ub, p) in plans if u.alive]
    if smart:
        _coordinated_attacks(game, side, attackers, hit_targets, states)
    else:
        for u, ubonus in attackers:
            if not u.alive:
                continue
            target = _best_live_target(game, u, ubonus, hit_targets, states)
            if target is None:
                continue
            _do_attack(game, u, target, ubonus, hit_targets, states)
            hit_targets[target.uid] = hit_targets.get(target.uid, 0) + 1
            if ubonus.get('after_move') and u.alive:
                _retreat_to_safety(game, u, ubonus['after_move'])
    return extra_draw


def _coordinated_attacks(game, side, attackers, hit_targets, states):
    """Greedy focus-fire: repeatedly fire the single highest-value attack available,
    recomputing against LIVE board state after each shot. Because a wounded unit's
    value rises as it nears death and a dead unit disappears, this naturally
    concentrates fire to SECURE kills (medals) and finishes the wounded without
    wasting shots on overkill."""
    pending = list(attackers)
    while pending:
        best = None  # (value, idx, target)
        for i, (u, ub) in enumerate(pending):
            if not u.alive:
                continue
            for e in game.enemies_of(side):
                if not e.alive or not game.has_los(u.pos, e.pos):
                    continue
                if game.attack_dice(u, e, ignore_terrain=ub.get('ignore_terrain', False)) is None:
                    continue
                fe = 0
                if ub.get('focus') == 'simple' and hit_targets.get(e.uid):
                    fe = hit_targets[e.uid]
                elif ub.get('focus') == 'escalate' and hit_targets.get(e.uid):
                    fe = 1 if hit_targets[e.uid] == 1 else 2
                v = est_attack_value(game, u, e, ub, focus_extra=fe)
                if best is None or v > best[0]:
                    best = (v, i, e)
        if best is None or best[0] <= 0.04:
            break
        _, idx, target = best
        u, ub = pending.pop(idx)
        _do_attack(game, u, target, ub, hit_targets, states)
        hit_targets[target.uid] = hit_targets.get(target.uid, 0) + 1
        if ub.get('after_move') and u.alive:
            _retreat_to_safety(game, u, ub['after_move'])

def est_attack_value_simple(e):
    return (MEDAL_W if e.utype.grants_medal else 0.5) + e.figs * 0.1

def _best_live_target(game, u, bonus, hit_targets, states):
    enemies = [e for e in game.enemies_of(u.side) if e.alive]
    best, bv = None, 0.0
    for e in enemies:
        if not game.has_los(u.pos, e.pos):
            continue
        focus_extra = 0
        if bonus.get('focus') == 'simple' and hit_targets.get(e.uid):
            focus_extra = hit_targets[e.uid]
        elif bonus.get('focus') == 'escalate' and hit_targets.get(e.uid):
            focus_extra = 1 if hit_targets[e.uid] == 1 else 2
        v = est_attack_value(game, u, e, bonus, focus_extra=focus_extra)
        if v > bv:
            best, bv = e, v
    return best

def _do_attack(game, attacker, target, bonus, hit_targets, states):
    defender = target.side
    dstate = states[defender]
    # ----- reaction: evade (defender moves a targeted vehicle) -----
    if (target.category == 'vehicle' and not bonus.get('no_enemy_reactions')
            and _has_reaction(dstate, 'evade')):
        cur = game.attack_dice(attacker, target,
                               extra_dice=bonus.get('dice', 0), ignore_terrain=bonus.get('ignore_terrain', False))
        # try to move target to reduce dice / break LOS
        best_pos, best_dice = target.pos, (cur if cur is not None else 0)
        for nb in neighbors(*target.pos):
            from hoth_engine import impassable_for
            if impassable_for(game.terr(nb), target) or game.unit_at(nb):
                continue
            saved = target.pos; target.pos = nb
            nd = game.attack_dice(attacker, target, extra_dice=bonus.get('dice', 0))
            los = game.has_los(attacker.pos, nb)
            target.pos = saved
            eff = 99 if (nd is None or not los) else nd
            if eff < best_dice:
                best_pos, best_dice = nb, eff
        if best_pos != target.pos and best_dice < (cur if cur is not None else 99):
            target.pos = best_pos
            _consume_reaction(dstate, 'evade')
            if not game.has_los(attacker.pos, target.pos) or \
               game.attack_dice(attacker, target) is None:
                return  # attack fizzles

    # ----- reaction: cover (defender reduces attacker dice on infantry in cover)
    cover_pen = 0
    if (target.category == 'infantry' and not bonus.get('no_enemy_reactions')
            and game.terr(target.pos) in ('trenches', 'rocks', 'buildings', 'ridge')
            and _has_reaction(dstate, 'cover')):
        cover_pen = 1
        _consume_reaction(dstate, 'cover')

    focus_extra = 0
    if bonus.get('focus') == 'simple' and hit_targets.get(target.uid):
        focus_extra = hit_targets[target.uid]
    elif bonus.get('focus') == 'escalate' and hit_targets.get(target.uid):
        focus_extra = 1 if hit_targets[target.uid] == 1 else 2

    lm = leader_attack_mods(game, attacker)   # on-board leader: escort bonus, aura, fear
    extra = (bonus.get('dice', 0) + focus_extra - cover_pen + lm['dice']
             + escalation_dice(game, attacker.side, bonus))
    close_bonus = bonus.get('close_dice', 0) + lm['close_dice']
    twice = 2 if bonus.get('attack_twice') else 1
    apass = states[attacker.side].get('passive')
    reroll_all = bonus.get('reroll', False)              # one-shot card: reroll all misses
    reroll_one = lm['reroll_one'] or apass == 'the_force'  # leader/passive: reroll one die
    ignore_terr = bonus.get('ignore_terrain', False) or lm['ignore_terrain']
    rah = bonus.get('retreat_as_hit', False) or lm['retreat_as_hit']
    for _ in range(twice):
        if not target.alive:
            break
        game.resolve_attack(attacker, target, extra_dice=extra,
                            ignore_terrain=ignore_terr,
                            close_only_bonus=close_bonus,
                            reroll_misses=reroll_all, reroll_one=reroll_one,
                            retreat_as_hit=rah)
        # Vader fear: extra retreat handled crudely as small extra push already covered

def _retreat_to_safety(game, u, dist):
    enemies = game.enemies_of(u.side)
    if not enemies:
        return
    for _ in range(dist):
        cur = min(hex_distance(u.pos, e.pos) for e in enemies)
        best = u.pos
        for nb in neighbors(*u.pos):
            from hoth_engine import impassable_for
            if impassable_for(game.terr(nb), u) or game.unit_at(nb):
                continue
            d = min(hex_distance(nb, e.pos) for e in enemies)
            if d > cur:
                best, cur = nb, d
        if best == u.pos:
            break
        u.pos = best

def _has_reaction(state, kind):
    for c in state['hand']:
        if c.get('reaction') == kind:
            return True
    return False

def _consume_reaction(state, kind):
    for i, c in enumerate(state['hand']):
        if c.get('reaction') == kind:
            state['discard'].append(state['hand'].pop(i))
            return

# --------------------------------------------------------------------------
# card selection
# --------------------------------------------------------------------------
import copy as _copy

def _clone_game(game):
    g = _copy.copy(game)
    g.units = [_copy.copy(u) for u in game.units]
    g.medals = dict(game.medals)
    g.exits = dict(getattr(game, 'exits', {}))
    g.exit_medal = dict(getattr(game, 'exit_medal', {}))
    g.objectives = [dict(o) for o in game.objectives]
    g.kill_bonus = dict(game.kill_bonus)
    g.no_kill_medal = set(game.no_kill_medal)
    g.ion = dict(game.ion) if game.ion else None
    g.terrain = dict(game.terrain)
    g.rng = random.Random(game.rng.random())   # independent dice for the rollout
    return g

def _clone_states(states):
    return {s: dict(hand=list(states[s]['hand']), discard=list(states[s]['discard']),
                    deck=states[s]['deck'], leader=states[s]['leader'],
                    passive=states[s]['passive']) for s in ('rebel', 'empire')}

def evaluate_board(game, side):
    """Static board value for `side`: progress toward victory + net surviving force."""
    opp = 'empire' if side == 'rebel' else 'rebel'
    prog = game.medals[side] / max(1, game.medals_to_win[side])
    progo = game.medals[opp] / max(1, game.medals_to_win[opp])
    s = 4 * MEDAL_W * (prog - progo) + MEDAL_W * (game.medals[side] - game.medals[opp]) * 0.4
    def figval(u):
        atk = (sum(u.utype.attack.values()) / len(u.utype.attack)) if u.utype.attack else 0
        return u.figs * (1 + 0.25 * atk) + (1.2 if u.utype.grants_medal else 0)
    for u in game.side_units(side):
        s += figval(u)
    for u in game.side_units(opp):
        s -= figval(u)
    return s

def choose_card(game, side, states):
    hand = states[side]['hand']
    playable = [c for c in hand if c.get('ctype') != 'reaction']
    if not playable:
        return None
    smart = AI_MODE.get(side, 'smart') == 'smart'
    if not smart:
        best, bv = None, -1
        for c in playable:
            v = estimate_card_value(game, side, c, states) + random.uniform(0, BASE_JITTER)
            if v > bv:
                best, bv = c, v
        return best
    opp = 'empire' if side == 'rebel' else 'rebel'
    # rank my cards by a cheap 1-ply score, keep the top few for the costlier 2-ply
    scored = []
    for c in playable:
        gc, sc = _clone_game(game), _clone_states(states)
        execute_card(gc, side, c, sc)
        scored.append((evaluate_board(gc, side), c))
    scored.sort(key=lambda t: -t[0])
    shortlist = [c for _, c in scored[:4]]

    # 2-ply minimax: for each of my candidate cards, let the opponent play their best
    # reply, then score the resulting board from my perspective. Pick the card that
    # leaves me best off AFTER the opponent's response (values defense, not just offense).
    best, bv = None, -1e18
    for c in shortlist:
        gc, sc = _clone_game(game), _clone_states(states)
        execute_card(gc, side, c, sc)
        if gc.winner() == side:
            return c
        opp_play = [oc for oc in sc[opp]['hand'] if oc.get('ctype') != 'reaction']
        worst = evaluate_board(gc, side)          # if opp has no card
        if opp_play:
            worst = 1e18
            for oc in opp_play:
                g2, s2 = _clone_game(gc), _clone_states(sc)
                execute_card(g2, opp, oc, s2)
                worst = min(worst, evaluate_board(g2, side))
        v = worst + 0.03 * c.get('bonus', {}).get('draw', 0) + random.uniform(0, 0.02)
        if v > bv:
            best, bv = c, v
    return best

def estimate_card_value(game, side, card, states):
    bonus = card.get('bonus', {})
    order = card.get('order', {})
    smart = AI_MODE.get(side, 'smart') == 'smart'
    if order.get('mode') == 'none' and bonus.get('multi_target'):
        return 2.5
    ordered = units_in_scope(game, side, order)
    if order.get('filter') and not ordered:
        ordered = _topn(game, game.side_units(side), 1)
        bonus = {}
    if not ordered:
        return 0.05
    hit_targets = {}
    total = 0.0
    acted = 0
    for u in ordered:
        p = plan_unit_action(game, u, bonus, hit_targets, smart=smart)
        if p:
            total += p['value']
            if p.get('target') is not None or p.get('move_to') != u.pos:
                acted += 1
            if p.get('target') is not None:
                hit_targets[p['target'].uid] = hit_targets.get(p['target'].uid, 0) + 1
    total += 0.15 * bonus.get('draw', 0)
    if smart:
        total += 0.22 * acted          # tempo: ordering more active units is good
    return total

# --------------------------------------------------------------------------
# ambush reaction during opponent move (checked after each enemy turn's moves)
# implemented lightweight: after opponent finishes, if any of my units is adjacent
# to an enemy and I hold ambush, free close attack.
# --------------------------------------------------------------------------
def try_ambush(game, defender, states):
    dstate = states[defender]
    if not _has_reaction(dstate, 'ambush'):
        return
    my_units = game.side_units(defender)
    best = None
    for u in my_units:
        for e in game.enemies_of(defender):
            if hex_distance(u.pos, e.pos) == 1 and game.has_los(u.pos, e.pos):
                v = est_attack_value(game, u, e, {})
                if best is None or v > best[2]:
                    best = (u, e, v)
    if best and best[2] > 0.6:
        _consume_reaction(dstate, 'ambush')
        game.resolve_attack(best[0], best[1])

# --------------------------------------------------------------------------
# full turn
# --------------------------------------------------------------------------
def draw_cards(state, n):
    for _ in range(n):
        if not state['deck']:
            state['deck'] = state['discard']
            state['discard'] = []
            random.shuffle(state['deck'])
        if state['deck']:
            state['hand'].append(state['deck'].pop())

def _snapshot(game):
    return [dict(kind=u.kind, side=u.side, col=u.pos[0], row=u.pos[1], figs=u.figs,
                 leader=u.leader)
            for u in game.units if u.alive]

def _record_frame(game, side, card_name, hands=None):
    if not getattr(game, 'recording', False):
        return
    game.frames.append(dict(turn=game.turn_count + 1, side=side, card=card_name,
                            events=list(game.log), units=_snapshot(game),
                            medals=dict(game.medals), hands=hands or {}))

def take_turn(game, side, states):
    states_other = 'empire' if side == 'rebel' else 'rebel'
    if game.recording:
        game.log = []
        game._log_mark = 0
        game.cur_turn = game.turn_count + 1
        game.cur_side = side
        def _hand(s):
            return [{'name': c.get('name', '?'), 'type': c.get('ctype', '')}
                    for c in states[s]['hand']]
        game.cur_hands = {'rebel': _hand('rebel'), 'empire': _hand('empire')}
    game.process_objectives(side)
    if game.winner():
        return
    card = choose_card(game, side, states)
    if card is None:
        if states[side]['hand']:
            states[side]['discard'].append(states[side]['hand'].pop(0))
        draw_cards(states[side], 1)
        if game.recording:
            game.cur_card = '(no playable card — discarded)'
            game.emit_substep('Pass')
        return
    if game.recording:
        game.cur_card = card.get('name', '?')
    states[side]['hand'].remove(card)
    extra_draw = execute_card(game, side, card, states)
    states[side]['discard'].append(card)
    # opponent ambush reaction in response to our moves
    try_ambush(game, states_other, states)
    draw_cards(states[side], 1 + (extra_draw or 0))

# --------------------------------------------------------------------------
# scenario / setup
# --------------------------------------------------------------------------
def make_unit(kind, side, pos, badge=None):
    ut = UNIT_TYPES[kind]
    return Unit(ut, side, pos, ut.full, badge=badge)

def attach_leaders(game, leaders):
    """Place each side's leader figure with an eligible escort unit (Piett stays off-board)."""
    from hoth_engine import LEADER_DEF
    for side, name in (leaders or {}).items():
        if not name:
            continue
        ld = LEADER_DEF.get(name)
        if not ld or ld.get('offboard'):
            continue
        cand = [u for u in game.side_units(side) if u.kind == ld['escort'] and not u.leader]
        if not cand:
            cand = [u for u in game.side_units(side) if not u.leader]
        if cand:
            cand[0].leader = name
            if ld.get('extra_fig'):
                cand[0].figs += ld['extra_fig']

def build_terrain():
    """Scenario 1 'Imperial Scout Mission' terrain: a central diagonal band of
    ice-crystal hexes (orange tiles -> rocks, green tiles -> ridges). No
    impassable terrain in this intro scenario. Rebel baseline = row 0."""
    t = {}
    for p in [(4, 3), (6, 3), (7, 2), (8, 2)]:
        t[p] = 'rocks'
    for p in [(5, 3), (4, 4), (6, 4), (7, 3)]:
        t[p] = 'ridge'
    return t

def standard_setup(rng):
    """SCENARIO 1 -- Imperial Scout Mission.
    Rebel: 4 Echo Base trooper units (deploy bottom-left/center).
    Empire: 4 Snowtrooper units + 2 Imperial probe droid units (top)."""
    units = []
    for p in [(1, 0), (2, 0), (3, 1), (4, 0)]:
        units.append(make_unit('echo', 'rebel', p))
    for p in [(1, 5), (2, 5), (5, 4), (7, 4)]:
        units.append(make_unit('snowtroop', 'empire', p))
    for p in [(3, 6), (5, 5)]:
        units.append(make_unit('droid', 'empire', p))
    return units

# --------------------------------------------------------------------------
# game runner
# --------------------------------------------------------------------------
def play_game(rebel_leader=None, emp_leader=None, basic=False,
              medals=None, first='rebel', hand_size=None, max_turns=300, seed=None,
              droid_medal=2, scenario=None, annot=None, record=False):
    """If `scenario` (a hoth_scenarios.Scenario) is given, all forces, hand sizes,
    first player, victory targets and special rules come from it. Otherwise the
    defaults model SCENARIO 1 -- Imperial Scout Mission."""
    from hoth_cards import build_deck, build_basic_deck, LEADER_PASSIVES
    rng = random.Random(seed)
    terrain = build_terrain()
    if scenario is not None:
        import hoth_scenarios as HS
        first = scenario.first
        medals = {'rebel': scenario.win_rebel, 'empire': scenario.win_empire}
        hand_size = {'rebel': scenario.hand[0], 'empire': scenario.hand[1]}
        if annot is not None:
            # exact positions from the map annotator. Convert image rows (row 0 = top
            # = Empire) to engine rows (row 0 = Rebel baseline): engine_row = 6 - row.
            units = [make_unit(u['kind'], u['side'], (u['col'], 6 - u['row']))
                     for u in annot.get('units', [])]
            terrain = {(t['col'], 6 - t['row']): t['type'] for t in annot.get('terrain', [])}
        else:
            units = scenario.build(rng)
        game = Game(terrain, units, first=first, medals_to_win=medals, rng=rng)
        HS.apply_rules(game, scenario)
        if annot is not None:
            HS.apply_markers(game, scenario, annot.get('markers', []))
    else:
        if medals is None:
            medals = {'rebel': 4, 'empire': 4}
        if hand_size is None:
            hand_size = {'rebel': 4, 'empire': 3}
        if isinstance(hand_size, int):
            hand_size = {'rebel': hand_size, 'empire': hand_size}
        units = standard_setup(rng)
        game = Game(terrain, units, first=first, medals_to_win=medals, rng=rng)
        game.droid_medal_to_rebel = droid_medal
        game.exits = {'rebel': 0, 'empire': 0}
        game.exit_medal = {}

    def mkstate(side, leader):
        deck = (build_basic_deck(side) if basic else build_deck(side, leader))
        rng.shuffle(deck)
        st = dict(deck=deck, hand=[], discard=[],
                  leader=leader,
                  passive=LEADER_PASSIVES.get(leader) if leader else None)
        return st
    states = {'rebel': mkstate('rebel', rebel_leader),
              'empire': mkstate('empire', emp_leader)}
    # place leader figures on-board (Advanced Leader rules); off-board leaders skipped
    attach_leaders(game, {'rebel': rebel_leader, 'empire': emp_leader})
    # piett +1 hand / han +1 hand
    for side in ('rebel', 'empire'):
        hs = hand_size[side]
        if states[side]['passive'] == 'fleet_command':
            hs += 1
        if states[side]['passive'] == 'scoundrels_luck':
            hs += 1
        draw_cards(states[side], hs)

    if record:
        game.recording = True
        game.frames = []
        game.frames.append(dict(turn=0, side='-', card='Initial deployment', phase='Setup',
                                events=[], units=_snapshot(game), medals=dict(game.medals),
                                hands={}))
    side = first
    while game.winner() is None and game.turn_count < max_turns:
        if not game.side_units(side):
            break
        take_turn(game, side, states)
        game.turn_count += 1
        side = 'empire' if side == 'rebel' else 'rebel'

    w = game.winner()
    if w is None:
        # decide by progress toward (possibly asymmetric) targets, then force value
        pr = game.medals['rebel'] / game.medals_to_win['rebel']
        pe = game.medals['empire'] / game.medals_to_win['empire']
        if abs(pr - pe) > 1e-9:
            w = 'rebel' if pr > pe else 'empire'
        else:
            rv = sum(u.figs for u in game.side_units('rebel'))
            ev = sum(u.figs for u in game.side_units('empire'))
            w = 'rebel' if rv >= ev else 'empire'
    droids_killed = sum(1 for u in game.units if u.kind == 'droid' and not u.alive)
    rebel_units_left = len([u for u in game.side_units('rebel')])
    out = dict(winner=w, medals=dict(game.medals), turns=game.turn_count,
               droids_killed=droids_killed, rebel_units_left=rebel_units_left)
    if record:
        out['frames'] = game.frames
        out['terrain'] = [{'col': c, 'row': r, 'type': t} for (c, r), t in terrain.items()]
        out['win_targets'] = dict(game.medals_to_win)
    return out


if __name__ == '__main__':
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    wins = {'rebel': 0, 'empire': 0}
    turns = []
    for i in range(n):
        r = play_game(seed=i, first=('rebel' if i % 2 == 0 else 'empire'))
        wins[r['winner']] += 1
        turns.append(r['turns'])
    print(f"Games: {n}")
    print(f"Rebel wins:  {wins['rebel']} ({100*wins['rebel']/n:.1f}%)")
    print(f"Empire wins: {wins['empire']} ({100*wins['empire']/n:.1f}%)")
    print(f"Avg turns: {sum(turns)/len(turns):.1f}")
