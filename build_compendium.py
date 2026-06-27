"""Generate the Advanced Deck card compendium (markdown) from the live card definitions."""
import importlib, hoth_cards
importlib.reload(hoth_cards)
import hoth_cards as HC

OUT = '/sessions/gracious-admiring-mccarthy/mnt/BattleForHothAdvanced/Advanced_Deck_Compendium.md'

def sector_text(c):
    o = c.get('order', {})
    if o.get('mode') == 'fixed_section':
        n = 'ALL' if o['n'] == 'all' else o['n']
        return (f"Order {n} unit{'' if n==1 else 's'} in the **{o['zone']}** sector "
                "(locked to this sector — you cannot choose another).")
    return None

TEXT = {
 'Recon in Force': 'Order 1 unit in EACH section (left, center, and right).',
 'Pincer Movement': 'Order 2 units in EACH flank (left and right; the center is skipped).',
 'Coordinated Command': 'Order up to 4 units anywhere on the battlefield.',
 'Grand Offensive': 'Choose a flank. Order ALL of your units there; each ordered unit gains +1 movement this turn.',
 'Speeder Strike': 'Order up to 2 Snowspeeder units. After it attacks, each may move 1 hex (hit-and-run).',
 'Trench Fighting': 'Choose a section. Order up to 3 infantry units there. They roll +1 attack die and ignore terrain attack penalties this turn.',
 'Artillery Barrage': 'Order 1 Rebel Artillery unit. It attacks twice this turn.',
 'Focus Fire': 'Choose a section. Order up to 3 units there. For each unit after the first that attacks the SAME target, that attack rolls +1 die.',
 'Desperate Valor': 'Order up to 2 units. Each rolls +1 attack die for every victory medal the enemy has scored (max +3).',
 'Forward Command': 'Order 1 unit. Then draw 2 extra command cards.',
 'Regroup': 'Order up to 2 units. Each ordered unit that does NOT attack returns 1 lost figure to full-strength cap.',
 'Evasive Maneuvers': 'REACTION (play on the enemy turn). When an enemy declares an attack on your Snowspeeder, it may first move 1 hex; recompute the attack.',
 'Ambush': 'REACTION. When an enemy unit ends its move adjacent to one of your units, that unit immediately makes a close-combat attack.',
 'Armored Advance': 'Order up to 2 AT-AT units. Each gains +1 movement and +1 die in close combat.',
 'Trooper Assault': 'Choose a section. Order up to 3 snowtrooper units there. Each rolls +1 attack die.',
 'Concentrated Fire': 'Choose a section. Order up to 3 units there. The 2nd unit to attack a given target rolls +1 die; the 3rd rolls +2 dice.',
 'Hold the Line': 'Order up to 2 units anywhere. They may not move, but each rolls +1 die in close combat (defensive firing line).',
 'Probe Recon': 'Order up to 2 Probe Droid units. Each gains +1 movement; your units roll +1 die against any enemy a droid can see.',
 'Crush Them': 'Order up to 2 units anywhere. Each rolls +1 die for every enemy unit currently below half strength (max +3).',
 'Suppressing Fire': 'REACTION. When an enemy attacks one of your infantry units in cover, the attacker rolls 1 fewer die.',
 'Imperial Ambush': 'REACTION. When an enemy unit ends its move adjacent to one of your units, that unit immediately makes a close-combat attack.',
}
LEADER_TEXT = {
 'Coordinated Defense': 'Order up to 3 units. Each ordered unit that does not attack returns 1 lost figure.',
 'New Hope': 'Order up to 4 units. Each rolls +1 attack die.',
 'Deploy the Fleet': 'Order 1 unit. Draw 3 extra command cards.',
 'Force Push': 'Order 1 unit. On its attack, Retreat results also count as hits.',
 'Trust Your Feelings': 'Order up to 2 units. Each rolls +1 die and may reroll its missed dice once.',
 'Heroic Resolve': 'Order 1 unit. It attacks twice this turn.',
 'Never Tell Me the Odds': 'Order 2 units in two different sections. Each gains +2 movement.',
 'Surprise Attack': 'Order 1 unit. It may move its full distance and still attack, rolling +1 die.',
 'Covering Fire': 'Order up to 3 units. Focus fire: +1 die for each unit after the first to attack the same target.',
 'Force Choke': 'Order 1 unit. It rolls +1 die and Retreat results also count as hits.',
 'Lack of Faith': 'Order up to 2 units. Each rolls +1 die; the enemy may not play reaction cards this turn.',
 'Power of the Dark Side': 'Order 1 unit. It attacks twice, each attack rolling +1 die.',
 'Concentrate All Fire': 'Order 1 AT-AT unit. It attacks twice this turn.',
 'Maximum Firepower': 'Order up to 2 vehicle units. Each rolls +1 die and gains +1 movement.',
 'Break Their Lines': 'Order up to 3 units. After attacking, each may move 1 hex (breakthrough).',
 'Orbital Bombardment': 'Do not order units. Roll 2 dice against EACH of up to 3 enemy units; blasts (and matching symbols) hit, ignoring cover and line of sight.',
 'Tactical Redeployment': 'Order up to 4 units. Each gains +1 movement.',
 'Special Orders': 'Order 1 unit. Draw 2 extra command cards.',
}
PASSIVE = {
 'Leia': "Command Network — the first unit you order each turn rolls +1 attack die.",
 'Luke': "The Force — once per turn you may reroll one of your attack dice.",
 'Han': "Scoundrel's Luck — you hold +1 command card, and your reaction cards' attacks roll +1 die.",
 'Vader': "Fear — when one of your attacks forces a retreat, the target retreats 1 extra hex.",
 'Veers': "Armored Spearhead — your vehicle units roll +1 die in close combat.",
 'Piett': "Fleet Command — you hold +1 command card (superior battle coordination).",
}

def rows(cards):
    seen = {}
    for c in cards:
        seen.setdefault(c['name'], {'count': 0, 'c': c})
        seen[c['name']]['count'] += c['count'] if False else 0
    # build_deck already expands; here we use the *definition* lists (count field present)
    out = []
    for c in cards:
        out.append((c['name'], c['count'], c.get('ctype', '')))
    return out

def fmt(cards, text):
    lines = []
    for c in cards:
        nm = c['name']; cnt = c['count']; rt = c.get('ctype', '')
        tag = ' *(reaction)*' if rt == 'reaction' else ''
        desc = text.get(nm) or sector_text(c) or ''
        lines.append(f"- **{nm}** ×{cnt}{tag} — {desc}")
    return '\n'.join(lines)

md = []
md.append("# Battle of Hoth — Advanced Deck Compendium\n")
md.append("An alternate command deck for expert play. Each side runs a **23-card base deck** "
          "(13 section + 10 tactic cards); adding a leader shuffles in that leader's 3 cards and "
          "applies a passive trait, for a **26-card deck**.\n")
md.append("**New mechanics:** *Reaction* cards are held and played on the opponent's turn when their "
          "trigger occurs. *Escalation* cards (Desperate Valor, Crush Them) scale with the game state. "
          "Unit-type cards use the rulebook fallback: if you command none of the listed unit type, "
          "instead order 1 unit of your choice with no bonus.\n")

md.append("## Section cards (both sides — 13 cards)\n")
md.append("The ordering backbone, identical for both sides. The nine **Probe / Raid / Assault** cards "
          "are *sector-locked* — the card names a sector (left, center, or right) and you may only act "
          "there, exactly like the basic game's Attack Left/Center/Right. If you have no units in that "
          "sector, the card is wasted. Only **Coordinated Command** and **Grand Offensive** let you "
          "pick where to act, and they are rare.\n")
md.append(fmt(HC.section_cards(), TEXT) + "\n")

md.append("## Rebel Alliance — Tactic cards (10 cards)\n")
md.append("*Theme: mobility, concentrated fire, resilience, and a comeback when behind.*\n")
md.append(fmt(HC.rebel_tactics(), TEXT) + "\n")

md.append("## Galactic Empire — Tactic cards (10 cards)\n")
md.append("*Theme: armored aggression, suppression, and snowballing a winning position.*\n")
md.append(fmt(HC.imperial_tactics(), TEXT) + "\n")

md.append("## Leader cards & passive traits\n")
md.append("Each player may choose one leader; shuffle in its 3 cards and apply its passive for the whole game.\n")
order = ['Leia', 'Luke', 'Han', 'Vader', 'Veers', 'Piett']
labels = {'Leia': 'Leia Organa (Rebel)', 'Luke': 'Luke Skywalker (Rebel)', 'Han': 'Han Solo (Rebel)',
          'Vader': 'Darth Vader (Empire)', 'Veers': 'General Veers (Empire)', 'Piett': 'Admiral Piett (Empire)'}
for L in order:
    md.append(f"### {labels[L]}\n")
    md.append(f"*Passive — {PASSIVE[L]}*\n")
    for c in HC.leader_cards(L):
        md.append(f"- **{c['name']}** — {LEADER_TEXT.get(c['name'], '')}")
    md.append("")

with open(OUT, 'w') as f:
    f.write('\n'.join(md))
import os
print('wrote', OUT, round(os.path.getsize(OUT)/1024, 1), 'KB')
