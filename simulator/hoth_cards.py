"""
Battle of Hoth -- ADVANCED DECK definitions.

Each card is a dict. The engine/AI interpret these fields:

  name, count, ctype: 'section'|'tactic'|'reaction'|'leader'
  order: dict {mode, n, filter}
     mode: 'section'      choose 1 best section, order up to n there
           'each_section' order up to n in EACH of the 3 sections
           'each_flank'   order up to n in EACH flank (no center)
           'flank'        choose 1 best flank, order up to n
           'anywhere'     order up to n anywhere
     n: int  OR  'all'    ('all' = every eligible unit in the chosen scope)
     filter: None | 'infantry' | 'vehicle' | 'special'
  bonus: dict, any of:
     dice            +X attack dice (all ranges)
     close_dice      +X dice in close combat only
     move            +X movement
     after_move      X  hit-and-run: ordered unit may move X after attacking
     attack_twice    True  ordered unit attacks twice
     ignore_terrain  True  ignore terrain attack restrictions/penalties
     focus           'simple' (+1/extra attacker same target) | 'escalate' (2nd +1, 3rd +2)
     reroll          True  reroll missed attack dice
     reroll_one      True  reroll one die (Force)
     escalation      ('comeback', cap) +1/medal lost ; ('snowball', cap) +1/weak enemy
     reinforce       X  ordered non-attacking units regain X figs
     no_move         True  ordered units may not move (defensive)
     draw            X  draw X extra cards
     scout           True grants +1 die vs targets seen by your special units
     retreat_as_hit  True retreats also count as hits this attack
     multi_target    (dice, n) roll `dice` vs each of up to n enemies
  reaction (for ctype 'reaction'): 'ambush' | 'evade' | 'cover'
  leader: leader name (for ctype 'leader')
"""

# --------------------------------------------------------------------------
# Shared SECTION backbone (identical structure both sides)
# --------------------------------------------------------------------------
def section_cards():
    """Sector-LOCKED backbone (like the basic deck's Attack Left/Center/Right): the card
    you draw dictates which sector you may act in -- you do not choose. Two rare flexible
    cards (Coordinated Command, Grand Offensive) are the exceptions."""
    out = []
    for z in ('left', 'center', 'right'):
        out.append(dict(name=f'Probe {z.title()}', count=1, ctype='section',
                        order=dict(mode='fixed_section', zone=z, n=1, filter=None)))
    for z in ('left', 'center', 'right'):
        out.append(dict(name=f'Raid {z.title()}', count=1, ctype='section',
                        order=dict(mode='fixed_section', zone=z, n=2, filter=None)))
    for z in ('left', 'center', 'right'):
        out.append(dict(name=f'Assault {z.title()}', count=1, ctype='section',
                        order=dict(mode='fixed_section', zone=z, n=3, filter=None)))
    out.append(dict(name='Recon in Force', count=1, ctype='section',
                    order=dict(mode='each_section', n=1, filter=None)))
    out.append(dict(name='Pincer Movement', count=1, ctype='section',
                    order=dict(mode='each_flank', n=2, filter=None)))
    out.append(dict(name='Coordinated Command', count=1, ctype='section',
                    order=dict(mode='anywhere', n=4, filter=None)))
    out.append(dict(name='Grand Offensive', count=1, ctype='section',
                    order=dict(mode='flank', n='all', filter=None), bonus=dict(move=1)))
    return out

# --------------------------------------------------------------------------
# REBEL tactics (mobility, focus fire, resilience, comeback)
# --------------------------------------------------------------------------
def rebel_tactics():
    return [
        dict(name='Speeder Strike',     count=2, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter='vehicle'),
             bonus=dict(after_move=1)),
        dict(name='Trench Fighting',    count=1, ctype='tactic',
             order=dict(mode='section', n=3, filter='infantry'),
             bonus=dict(ignore_terrain=True, dice=1)),
        dict(name='Artillery Barrage',  count=1, ctype='tactic',
             order=dict(mode='anywhere', n=1, filter='special'),
             bonus=dict(attack_twice=True)),
        dict(name='Focus Fire',         count=1, ctype='tactic',
             order=dict(mode='section', n=3, filter=None),
             bonus=dict(focus='simple')),
        dict(name='Desperate Valor',    count=1, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter=None),
             bonus=dict(escalation=('comeback', 3))),
        dict(name='Forward Command',    count=1, ctype='tactic',
             order=dict(mode='anywhere', n=1, filter=None),
             bonus=dict(draw=2)),
        dict(name='Regroup',            count=1, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter=None),
             bonus=dict(reinforce=1, no_move=False)),
        dict(name='Evasive Maneuvers',  count=1, ctype='reaction', reaction='evade'),
        dict(name='Ambush',             count=1, ctype='reaction', reaction='ambush'),
        dict(name='Tauntaun Recon',     count=1, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter=None),
             bonus=dict(move=1, draw=1)),
    ]

# --------------------------------------------------------------------------
# IMPERIAL tactics (armor, suppression, snowball)
# --------------------------------------------------------------------------
def imperial_tactics():
    return [
        dict(name='Armored Advance',    count=2, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter='vehicle'),
             bonus=dict(move=1, close_dice=1)),
        dict(name='Trooper Assault',    count=1, ctype='tactic',
             order=dict(mode='section', n=3, filter='infantry'),
             bonus=dict(dice=1)),
        dict(name='Concentrated Fire',  count=1, ctype='tactic',
             order=dict(mode='section', n=3, filter=None),
             bonus=dict(focus='escalate')),
        dict(name='Hold the Line',      count=1, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter=None),
             bonus=dict(close_dice=1, no_move=True)),
        dict(name='Probe Recon',        count=1, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter='special'),
             bonus=dict(move=1, scout=True)),
        dict(name='Crush Them',         count=1, ctype='tactic',
             order=dict(mode='anywhere', n=2, filter=None),
             bonus=dict(escalation=('snowball', 3))),
        dict(name='Forward Command',    count=1, ctype='tactic',
             order=dict(mode='anywhere', n=1, filter=None),
             bonus=dict(draw=2)),
        dict(name='Suppressing Fire',   count=1, ctype='reaction', reaction='cover'),
        dict(name='Imperial Ambush',    count=1, ctype='reaction', reaction='ambush'),
        dict(name='Cold Assault',       count=1, ctype='tactic',
             order=dict(mode='section', n=2, filter='infantry'),
             bonus=dict(move=1, full_move_attack=True)),
    ]

# --------------------------------------------------------------------------
# Leaders: passive trait + 3 cards each
# --------------------------------------------------------------------------
LEADER_PASSIVES = {
    # rebel
    'Leia':  'command_network',   # first ordered unit each turn gets +1 die
    'Luke':  'the_force',         # once/turn reroll one attack die (engine: reroll_one on best attack)
    'Han':   'scoundrels_luck',   # reaction cards: +1 die on the reacting attack
    # empire
    'Vader': 'fear',              # forced retreats push 1 extra hex
    'Veers': 'armored_spearhead', # vehicles +1 close-combat die
    'Piett': 'fleet_command',     # +1 card in hand (economy)
}

def leader_cards(name):
    L = {
        'Leia': [
            dict(name='Coordinated Defense', count=1, ctype='leader', leader='Leia',
                 order=dict(mode='anywhere', n=3, filter=None), bonus=dict(reinforce=1)),
            dict(name='New Hope',            count=1, ctype='leader', leader='Leia',
                 order=dict(mode='anywhere', n=4, filter=None), bonus=dict(dice=1)),
            dict(name='Deploy the Fleet',    count=1, ctype='leader', leader='Leia',
                 order=dict(mode='anywhere', n=1, filter=None), bonus=dict(draw=3)),
        ],
        'Luke': [
            dict(name='Force Push',          count=1, ctype='leader', leader='Luke',
                 order=dict(mode='anywhere', n=1, filter=None), bonus=dict(retreat_as_hit=True)),
            dict(name='Trust Your Feelings', count=1, ctype='leader', leader='Luke',
                 order=dict(mode='anywhere', n=2, filter=None), bonus=dict(dice=1, reroll=True)),
            dict(name='Heroic Resolve',      count=1, ctype='leader', leader='Luke',
                 order=dict(mode='anywhere', n=1, filter=None), bonus=dict(attack_twice=True)),
        ],
        'Han': [
            dict(name='Never Tell Me the Odds', count=1, ctype='leader', leader='Han',
                 order=dict(mode='anywhere', n=2, filter=None), bonus=dict(move=2)),
            dict(name='Surprise Attack',     count=1, ctype='leader', leader='Han',
                 order=dict(mode='anywhere', n=1, filter=None), bonus=dict(dice=1, full_move_attack=True)),
            dict(name='Covering Fire',       count=1, ctype='leader', leader='Han',
                 order=dict(mode='anywhere', n=3, filter=None), bonus=dict(focus='simple')),
        ],
        'Vader': [
            dict(name='Force Choke',         count=1, ctype='leader', leader='Vader',
                 order=dict(mode='anywhere', n=1, filter=None), bonus=dict(retreat_as_hit=True, dice=1)),
            dict(name='Lack of Faith',       count=1, ctype='leader', leader='Vader',
                 order=dict(mode='anywhere', n=2, filter=None), bonus=dict(dice=1, no_enemy_reactions=True)),
            dict(name='Power of the Dark Side', count=1, ctype='leader', leader='Vader',
                 order=dict(mode='anywhere', n=1, filter=None), bonus=dict(attack_twice=True, dice=1)),
        ],
        'Veers': [
            dict(name='Concentrate All Fire', count=1, ctype='leader', leader='Veers',
                 order=dict(mode='anywhere', n=1, filter='vehicle'), bonus=dict(attack_twice=True)),
            dict(name='Maximum Firepower',   count=1, ctype='leader', leader='Veers',
                 order=dict(mode='anywhere', n=2, filter='vehicle'), bonus=dict(dice=1, move=1)),
            dict(name='Break Their Lines',   count=1, ctype='leader', leader='Veers',
                 order=dict(mode='anywhere', n=3, filter=None), bonus=dict(after_move=1)),
        ],
        'Piett': [
            dict(name='Orbital Bombardment', count=1, ctype='leader', leader='Piett',
                 order=dict(mode='none'), bonus=dict(multi_target=(2, 3))),
            dict(name='Tactical Redeployment', count=1, ctype='leader', leader='Piett',
                 order=dict(mode='anywhere', n=4, filter=None), bonus=dict(move=1)),
            dict(name='Special Orders',      count=1, ctype='leader', leader='Piett',
                 order=dict(mode='anywhere', n=1, filter=None), bonus=dict(draw=2)),
        ],
    }
    return L[name]


def build_deck(side, leader=None):
    cards = []
    base = section_cards() + (rebel_tactics() if side == 'rebel' else imperial_tactics())
    for c in base:
        cards.extend([dict(c) for _ in range(c['count'])])
    if leader:
        for c in leader_cards(leader):
            cards.extend([dict(c) for _ in range(c['count'])])
    return cards


# Basic deck (approximation of the published 16 standard cards) for comparison.
# Also sector-LOCKED, matching the real Attack/Raid/Recon Left/Center/Right cards.
def build_basic_deck(side, leader=None):
    base = []
    for z in ('left', 'center', 'right'):
        base.append(dict(name=f'Recon {z.title()}', count=1, ctype='section',
                         order=dict(mode='fixed_section', zone=z, n=1, filter=None)))
    for z in ('left', 'center', 'right'):
        base.append(dict(name=f'Raid {z.title()}', count=1, ctype='section',
                         order=dict(mode='fixed_section', zone=z, n=2, filter=None)))
    for z in ('left', 'center', 'right'):
        base.append(dict(name=f'Assault {z.title()}', count=1, ctype='section',
                         order=dict(mode='fixed_section', zone=z, n='all', filter=None)))
    base += [
        dict(name='Recon in Force', count=1, ctype='section', order=dict(mode='each_section', n=1, filter=None)),
        dict(name='Pincer', count=1, ctype='section', order=dict(mode='each_flank', n=2, filter=None)),
        dict(name='Direct From HQ', count=1, ctype='tactic', order=dict(mode='anywhere', n=3, filter=None)),
        dict(name='Trooper Assault', count=1, ctype='tactic', order=dict(mode='section', n='all', filter='infantry'), bonus=dict(dice=1)),
        dict(name='Vehicle Tactic', count=1, ctype='tactic', order=dict(mode='anywhere', n=2, filter='vehicle'), bonus=dict(after_move=1)),
        dict(name='Artillery/Precision', count=1, ctype='tactic', order=dict(mode='anywhere', n=1, filter=None), bonus=dict(dice=1)),
    ]
    cards = []
    for c in base:
        cards.extend([dict(c) for _ in range(c['count'])])
    return cards
