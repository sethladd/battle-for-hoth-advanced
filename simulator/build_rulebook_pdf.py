"""Generate the print-ready Battle of Hoth: Advanced rulebook PDF.
Content is sourced from the canonical markdown/design; this just formats it nicely.
Run from the simulator/ directory."""
import hoth_cards as HC
from hoth_engine import UNIT_TYPES, LEADER_DEF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, NextPageTemplate,
                                Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether, HRFlowable, Flowable)

OUT = '../docs/Battle_of_Hoth_Advanced_Rulebook.pdf'

# ---- theme ----
NAVY   = colors.HexColor('#0c2233')
ICE    = colors.HexColor('#bfe6f5')
STEEL  = colors.HexColor('#3a5a78')
REBEL  = colors.HexColor('#b3322c')
EMPIRE = colors.HexColor('#274a72')
GOLD   = colors.HexColor('#c8a046')
LIGHT  = colors.HexColor('#eef4f8')
INK    = colors.HexColor('#16242f')

ss = getSampleStyleSheet()
def style(name, **kw):
    base = kw.pop('parent', ss['Normal'])
    return ParagraphStyle(name, parent=base, **kw)

H1   = style('H1', fontName='Helvetica-Bold', fontSize=20, textColor=NAVY, spaceBefore=6, spaceAfter=8, leading=23)
H2   = style('H2', fontName='Helvetica-Bold', fontSize=14, textColor=STEEL, spaceBefore=12, spaceAfter=4, leading=17)
BODY = style('Body', fontSize=10.2, leading=14.5, textColor=INK, spaceAfter=6, alignment=TA_LEFT)
BULL = style('Bull', parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=3)
SMALL= style('Small', fontSize=8.5, leading=11, textColor=colors.HexColor('#5b6b78'))
CARDNAME = style('CardName', fontName='Helvetica-Bold', fontSize=9.5, textColor=colors.white, leading=11)
CARDMETA = style('CardMeta', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.white, leading=9)
CARDBODY = style('CardBody', fontSize=8.4, leading=10.6, textColor=INK)
STATLBL = style('StatLbl', fontName='Helvetica-Bold', fontSize=9, textColor=NAVY)
TITLE = style('Title', fontName='Helvetica-Bold', fontSize=34, textColor=colors.white, alignment=TA_CENTER, leading=38)
SUBT  = style('Subt', fontName='Helvetica', fontSize=14, textColor=ICE, alignment=TA_CENTER, leading=18)

def rule(color=GOLD, w=1.2):
    return HRFlowable(width='100%', thickness=w, color=color, spaceBefore=2, spaceAfter=8)

def P(t, s=BODY): return Paragraph(t, s)
def B(t): return Paragraph('• ' + t, BULL)

# ---- card descriptions (mirror the canonical compendium) ----
# Card rules text is read from the single canonical source (docs/Advanced_Deck_Compendium.md);
# nothing is hard-coded here. See CLAUDE.md "golden rule".
import card_text
CARD_TEXT = card_text.parse()

def card_desc(c):
    return card_text.to_reportlab(CARD_TEXT.get(c['name'], ''))

FACTION_COLOR = {'section': STEEL, 'rebel': REBEL, 'empire': EMPIRE, 'leader_r': GOLD, 'leader_e': GOLD}

def card_tile(name, count, type_label, desc, header_color, width):
    head = Table([[Paragraph(name, CARDNAME),
                   Paragraph(('×%d' % count) if count else '', CardName_right)]],
                 colWidths=[width*0.72, width*0.28])
    head.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), header_color),
                              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                              ('LEFTPADDING', (0, 0), (0, 0), 6), ('RIGHTPADDING', (-1, 0), (-1, 0), 6),
                              ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    meta = Table([[Paragraph(type_label, CardMetaDark)]], colWidths=[width])
    meta.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), LIGHT),
                              ('LEFTPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 1),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
    body = Table([[Paragraph(desc, CARDBODY)]], colWidths=[width])
    body.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                              ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                              ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    tile = Table([[head], [meta], [body]], colWidths=[width])
    tile.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, header_color),
                              ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                              ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    return tile

CardName_right = style('CNR', parent=CARDNAME, alignment=2)
CardMetaDark = style('CMD', fontName='Helvetica-Oblique', fontSize=7.5, textColor=STEEL)

def card_grid(cards, header_color, cols=2):
    W = (6.9*inch - (cols-1)*0.18*inch) / cols
    tiles = [card_tile(c['name'], c.get('count', 1),
                       ('Reaction' if c.get('ctype') == 'reaction' else 'Command card'),
                       card_desc(c), header_color, W) for c in cards]
    rows = []
    for i in range(0, len(tiles), cols):
        row = tiles[i:i+cols] + [''] * (cols - len(tiles[i:i+cols]))
        rows.append(row)
    g = Table(rows, colWidths=[W + 0.18*inch]*cols if False else [W]*cols, hAlign='LEFT')
    g.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
                           ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
    return g

# ---- 59mm x 91mm print-and-play cards ----
CW, CH = 59*mm, 91*mm
PP_NAME = style('PPName', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, leading=11.5)
PP_TYPE = style('PPType', fontName='Helvetica-Oblique', fontSize=7.5, textColor=STEEL, leading=9)
PP_BODY = style('PPBody', fontSize=9, leading=11.5, textColor=INK)
PP_FOOT = style('PPFoot', fontName='Helvetica-Bold', fontSize=6.5, textColor=colors.white, leading=8)

def card59(c, color, footer):
    name = c['name']
    o = c.get('order', {})
    if c.get('ctype') == 'reaction':
        tline = 'Reaction card'
    elif o.get('mode') == 'fixed_section':
        tline = 'Section card · %s sector' % o['zone']
    else:
        tline = 'Command card'
    nm = name
    Hh, Ht, Hf = 30, 14, 13
    Hb = CH - Hh - Ht - Hf
    t = Table([[Paragraph(nm, PP_NAME)],
               [Paragraph(tline, PP_TYPE)],
               [Paragraph(card_desc(c), PP_BODY)],
               [Paragraph(footer, PP_FOOT)]],
              colWidths=[CW], rowHeights=[Hh, Ht, Hb, Hf])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), color), ('BACKGROUND', (0, 1), (0, 1), LIGHT),
        ('BACKGROUND', (0, 3), (0, 3), color),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'), ('VALIGN', (0, 1), (0, 1), 'MIDDLE'),
        ('VALIGN', (0, 2), (0, 2), 'TOP'), ('VALIGN', (0, 3), (0, 3), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 2), (0, 2), 7), ('TOPPADDING', (0, 0), (0, 1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 0.8, INK)]))   # the card border = the cut line
    return t

def pp_sheet(card_specs, cols=3):
    """Lay cards out at exact 59x91mm, `cols` per row; Platypus paginates the rows."""
    tiles = [card59(c, col, foot) for (c, col, foot) in card_specs]
    rows = []
    for i in range(0, len(tiles), cols):
        chunk = tiles[i:i+cols]
        rows.append(chunk + [''] * (cols - len(chunk)))
    g = Table(rows, colWidths=[CW]*cols, hAlign='CENTER')
    g.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                           ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    return g

# ---------------------------------------------------------------- story
story = []

# ---- title page (banner) ----
banner = Table([[Paragraph('BATTLE OF HOTH', TITLE)],
                [Paragraph('ADVANCED', style('A', parent=TITLE, fontSize=22, textColor=GOLD))],
                [Spacer(1, 8)],
                [Paragraph('An expert variant &amp; expansion — new command deck, '
                           'on-board leaders, and units', SUBT)]],
               colWidths=[6.9*inch])
banner.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY),
                            ('TOPPADDING', (0, 0), (-1, 0), 46), ('BOTTOMPADDING', (0, -1), (-1, -1), 46),
                            ('LEFTPADDING', (0, 0), (-1, -1), 20), ('RIGHTPADDING', (0, 0), (-1, -1), 20)]))
story += [Spacer(1, 1.1*inch), banner, Spacer(1, 0.4*inch)]
story += [P('<b>For experienced players of the base game.</b> This variant keeps the same board, '
            'dice, command-card economy, and victory medals — and layers expert decision-making on '
            'top: reaction cards played on the opponent’s turn, combo and escalation cards, '
            'characters who fight on the board, and two new units.', style('intro', parent=BODY, fontSize=11, leading=16, alignment=TA_CENTER))]
story += [Spacer(1, 0.3*inch),
          P('Unofficial fan content. Original rules &amp; design © their authors (CC BY 4.0); '
            'built on <i>Star Wars: Battle of Hoth</i> © &amp; ™ Lucasfilm Ltd. / Days of Wonder.', SMALL)]
story += [PageBreak()]

# ---- 1. What's new ----
story += [P('1 · What’s New', H1), rule()]
story += [P('The Advanced variant adds four things, all expressed in the base game’s own terms:', BODY)]
for t in ['<b>A redesigned command deck</b> (~24 cards/side) — see §5.',
          '<b>On-board leaders</b> — six characters who ride with a unit, inspire those around '
          'them, and can be hunted down (§4).',
          '<b>Two new units</b> — the Rebel Tauntaun Scout and the Imperial AT-ST (§3).',
          '<b>Destroyable structures</b> — shield generators and the ion cannon become objectives '
          'you can blast apart in the scenarios that feature them.']:
    story += [B(t)]
story += [P('Everything else — setup, movement, line of sight, terrain, attacking, retreats, and '
            'winning by victory medals — works exactly as in the base rulebook.', BODY)]

story += [P('Core new mechanics', H2)]
story += [B('<b>Sector-locked orders (kept from the base game).</b> Most ordering cards name a '
            'sector (Probe / Raid / Assault — Left, Center, or Right) and you may act only there. '
            'If you have no units in that sector, the card is wasted. Only two cards per side let '
            'you choose freely (Coordinated Command, Grand Offensive). This preserves the game’s '
            'central "you can’t always act where you want" tension.'),
          B('<b>Reaction cards.</b> Held in hand and played on the <i>opponent’s</i> turn when '
            'their trigger occurs (e.g. Ambush, Evasive Maneuvers, Suppressing Fire). They are not '
            'played on your own turn.'),
          B('<b>Escalation cards.</b> Their strength scales with the score — Desperate Valor arms '
            'the Rebels as they fall behind; Crush Them sharpens the Empire as it pulls ahead.'),
          B('<b>Unit-type fallback.</b> If a card that orders a specific unit type finds none of '
            'that type, instead order 1 unit of your choice (with no bonus).')]
story += [PageBreak()]

# ---- 2. How to adopt ----
story += [P('2 · How to Adopt This Variant', H1), rule()]
story += [P('This variant is built on a copy of the base game — you don’t replace it, you '
            'extend it. Here is the checklist to get an Advanced game to the table.', BODY)]

story += [P('1. Start with the base game', H2)]
story += [P('Use your <b>Battle of Hoth</b> board, miniatures, terrain hexes, symbol dice, and '
            'victory medals, and pick a battle from the scenario book. Set up the scenario exactly '
            'as printed — its hand size, first player, and victory conditions are unchanged.', BODY)]

story += [P('2. Build the Advanced command decks (the one thing you must make)', H2)]
story += [P('The Advanced deck <b>replaces the base command deck</b>. Choose any one of:', BODY)]
for t in ['<b>Print &amp; cut</b> the card tiles in §5 onto cardstock at 100% scale, or',
          '<b>Sleeve</b> the printed tiles in front of any same-size cards, or',
          '<b>Hand-write</b> the cards onto blank/index cards from the text in §5.']:
    story += [B(t)]
story += [P('Each side needs its <b>23-card base deck</b> (13 section + 10 tactic). Keep the two '
            'decks separate — the Rebel and Imperial tactic cards differ. Shuffle each and draw to '
            'the scenario’s hand size.', BODY)]

story += [P('3. (Optional) Add leaders', H2)]
for t in ['Each player picks <b>one</b> leader from their faction (choices are open) and shuffles '
          'that leader’s <b>3 cards</b> into their deck.',
          'Mark the leader’s <b>escort unit</b> with a distinctive token — a coin, a colored ring, '
          'or a spare figure — so both players can see which unit carries the leader.',
          'Honor the <b>escort lock</b>: a leader may be fielded only if its escort type is in the '
          'scenario (Luke→Snowspeeder, Han→Tauntaun, Leia→Echo trooper, Vader→Snowtrooper, '
          'Veers→AT-AT). <b>Piett</b> needs no figure — he is off-board.']:
    story += [B(t)]

story += [P('4. Proxy the new units (when a scenario uses them)', H2)]
story += [P('There are no Tauntaun or AT-ST miniatures in the base box — use any stand-in figures '
            'or tokens (Tauntaun Scout = a 2-figure cavalry unit; AT-ST = a 2-figure walker). The '
            'standard booklet scenarios don’t require them, so add them to your own scenarios or '
            'substitute them in for variety.', BODY)]

story += [P('5. Structures', H2)]
story += [P('For scenarios that feature a shield generator or ion cannon, use the base game’s '
            'structure pieces as <b>destroyable objectives</b>: a unit may attack one by normal '
            'rules, and a single <b>Blast</b> destroys it. Note which structures are objectives '
            'before you start.', BODY)]

story += [P('Recommended first game', H2)]
story += [P('Play <b>Scenario 1 (Imperial Scout Mission)</b> with the Advanced decks and <i>no</i> '
            'leaders to learn the new cards. Then add one leader each and try a scenario with '
            'vehicles (e.g. Snowspeeder Counter-Attack) to see leaders, auras, and the new units in '
            'action.', BODY)]
story += [P('<b>Printing tip:</b> print §5 at 100% (turn off "fit to page"), on cardstock or in '
            'sleeves; the tiles are laid out two per row for easy cutting.', SMALL)]
story += [PageBreak()]

# ---- 3. New Units ----
story += [P('3 · New Units', H1), rule()]
story += [P('Two units fill the gaps between the existing light and heavy pieces. Proxy with any '
            'suitable figures — there are no tauntaun or AT-ST minis in the base box.', BODY)]

def stat_block(title, color, lines, flavor):
    head = Table([[Paragraph(title, style('UN', fontName='Helvetica-Bold', fontSize=12, textColor=colors.white))]],
                 colWidths=[6.9*inch])
    head.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), color),
                              ('LEFTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 4),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    rows = [[Paragraph('<b>%s</b>' % k, CARDBODY), Paragraph(v, CARDBODY)] for k, v in lines]
    tbl = Table(rows, colWidths=[1.5*inch, 5.4*inch])
    tbl.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                             ('LINEBELOW', (0, 0), (-1, -2), 0.4, colors.HexColor('#cdd8e0')),
                             ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                             ('LEFTPADDING', (0, 0), (-1, -1), 8)]))
    return KeepTogether([head, tbl, Spacer(1, 3), P('<i>%s</i>' % flavor, SMALL), Spacer(1, 14)])

story += [stat_block('Tauntaun Scout — Rebel light cavalry', REBEL, [
    ('Figures', '2 (mounted riders)'),
    ('Hit on', 'Infantry symbol or Blast'),
    ('Move', '0–3 hexes; may still attack after moving up to 2'),
    ('Attack', '3 dice in close combat; 1 die at range 2'),
    ('Special', 'All-terrain (ignores the first "must stop" each turn); after attacking it may '
                'move 1 hex (hit-and-run). Eliminating it grants a victory medal.')],
    'Fast skirmishers that harry the flanks and vanish — the mount for Han Solo in the leader rules.')]
story += [stat_block('AT-ST — Imperial scout walker (medium armor)', EMPIRE, [
    ('Figures', '2 (one walker that soaks two hits)'),
    ('Hit on', 'Vehicle symbol or Blast'),
    ('Move', '0–2 hexes; may still attack after moving'),
    ('Attack', '3 / 3 / 2 dice at range 1 / 2 / 3'),
    ('Special', 'May climb onto ridges (the AT-AT cannot); no AT-AT confirmation rule and it '
                'retreats normally, so it is far easier to kill than an AT-AT. Grants a medal.')],
    'A nimble walker that takes ground and contests objectives — General Veers’ lighter companion.')]

# roster table
story += [P('Full unit roster', H2)]
roster = [['Unit', 'Side', 'Figs', 'Move', 'Attack', 'Hit on', 'Notes']]
rows = [
 ('Echo Base Trooper', 'Rebel', '3', '1 / 2', '3 / 2 / 1', 'inf, blast', 'baseline infantry'),
 ('Tauntaun Scout', 'Rebel', '2', '3', '3 / 1', 'inf, blast', 'cavalry; hit-and-run'),
 ('Snowspeeder', 'Rebel', '3', '3', '4 / 2', 'veh, blast', 'flying; crosses crevasses'),
 ('Rebel Artillery', 'Rebel', '1', '0', '1 / 3 / 3', 'blast', 'no move; no medal'),
 ('Snowtrooper', 'Empire', '4', '1 / 2', '3 / 2 / 1', 'inf, blast', 'baseline infantry'),
 ('Probe Droid', 'Empire', '2', '2', '2 / 1', 'blast', 'recon; no medal'),
 ('AT-ST', 'Empire', '2', '2', '3 / 3 / 2', 'veh, blast', 'medium walker; climbs ridges'),
 ('AT-AT', 'Empire', '1', '1', '3 / 3 / 3', 'veh, blast', 'confirmation kill; ignores retreats'),
]
for r in rows:
    roster.append(list(r))
rt = Table(roster, colWidths=[1.45*inch, .65*inch, .4*inch, .55*inch, .85*inch, .8*inch, 1.7*inch])
rt.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 8.2),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#c2cfd8')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('LEFTPADDING', (0, 0), (-1, -1), 5)]))
story += [rt, PageBreak()]

# ---- 4. Leaders ----
story += [P('4 · Advanced Leaders', H1), rule()]
story += [P('In the base game a leader is just three command cards. Here each leader is also a '
            '<b>character figure on the board</b> that rides with a unit (its <i>escort</i>), '
            'strengthens it, projects an aura to nearby friendlies, and can be hunted down.', BODY)]
for t in ['<b>Open selection.</b> Each player picks one leader from their faction; choices are open.',
          '<b>Escort lock.</b> A leader can be fielded only if a unit of its escort type is in the '
          'scenario; otherwise that leader sits out entirely. Piett is the exception — off-board, '
          'always available.',
          '<b>Deploy</b> the figure with one of your escort-type units after forces are placed.',
          '<b>Transfer.</b> When you order the escort you may instead move the leader 1 hex to join '
          'another friendly unit.',
          '<b>Capture (Bonus Medals).</b> If the escort is destroyed, the leader escapes to an '
          'adjacent friendly unit; if isolated, the opponent scores the leader’s Bonus Medal.']:
    story += [B(t)]
story += [Spacer(1, 4)]

LEAD = [
 ('Luke Skywalker', 'rebel', 'Rogue Leader — pilots a Snowspeeder',
  'Escort rolls +1 die and may reroll one die (the Force); ignores 1 Retreat against it. '
  'Aura (1 hex): friendly units may ignore 1 Retreat. Bonus Medal 2.',
  ['Force Push', 'Trust Your Feelings', 'Heroic Resolve']),
 ('Han Solo', 'rebel', 'On a Tauntaun Scout',
  'Escort rolls +1 die and may reroll one die. Aura (1 hex): friendly units +1 movement. '
  'Bonus Medal 1.',
  ['Never Tell Me the Odds', 'Surprise Attack', 'Covering Fire']),
 ('Leia Organa', 'rebel', 'Command squad (4-figure Echo Base unit)',
  'Her squad rolls +1 die and, if it does not attack, returns 1 figure (rally). Bonus Medal 2.',
  ['Coordinated Defense', 'New Hope', 'Deploy the Fleet']),
 ('Darth Vader', 'empire', 'Sith Lord — on foot with a Snowtrooper unit',
  '+2 dice in close combat; his attacks treat Retreats as hits and ignore the target’s terrain '
  'cover. Aura — Fear (1 hex): adjacent enemies roll 1 fewer die. Survives his escort’s death as '
  'a lone figure (worth 2 if killed).',
  ['Force Choke', 'Lack of Faith', 'Power of the Dark Side']),
 ('General Veers', 'empire', 'Commands an AT-AT ("Blizzard 1")',
  'His walker rolls +1 die; all friendly vehicles roll +1 die in close combat. Bonus Medal 1.',
  ['Concentrate All Fire', 'Maximum Firepower', 'Break Their Lines']),
 ('Admiral Piett', 'empire', 'Off-board — Fleet Command (no figure)',
  'You hold +1 command card; once a game, call his orbital bombardment. No aura, cannot be '
  'captured. Bonus Medal 0.',
  ['Orbital Bombardment', 'Tactical Redeployment', 'Special Orders']),
]
for name, side, escort, passive, cards in LEAD:
    col = REBEL if side == 'rebel' else EMPIRE
    head = Table([[Paragraph(name, style('LN', fontName='Helvetica-Bold', fontSize=12, textColor=colors.white)),
                   Paragraph(escort, style('LE', fontName='Helvetica-Oblique', fontSize=9, textColor=ICE, alignment=2))]],
                 colWidths=[2.6*inch, 4.3*inch])
    head.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), col), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                              ('LEFTPADDING', (0, 0), (0, 0), 8), ('RIGHTPADDING', (-1, 0), (-1, 0), 8),
                              ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    bodyt = Table([[Paragraph('<b>On the board.</b> ' + passive, CARDBODY)],
                  [Paragraph('<b>Cards.</b> ' + ', '.join(cards) + '.', CARDBODY)]],
                  colWidths=[6.9*inch])
    bodyt.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                               ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                               ('BOX', (0, 0), (-1, -1), 0.6, col)]))
    story += [KeepTogether([head, bodyt, Spacer(1, 9)])]
story += [PageBreak()]

# ---- 5. The Command Deck (print & play, 59x91mm) ----
story += [NextPageTemplate('cards'), PageBreak()]
story += [P('5 · The Advanced Command Deck — Print &amp; Play', H1), rule()]
story += [P('The cards below are sized to a standard <b>59 × 91 mm</b> playing-card and laid out '
            'three per row. Print at <b>100% scale</b> (turn off "fit to page") on cardstock and '
            'cut along the card borders; sleeve them if you like.', BODY)]
for t in ['<b>Every copy is included.</b> Each card appears exactly as many times as its deck '
          'needs (e.g. Speeder Strike appears twice) — just print a deck’s pages and cut, no '
          'photocopying.',
          'The <b>Rebel</b> and <b>Empire</b> decks each include their own copy of the 13 section '
          'cards (identical between sides); the footer names which deck each card belongs to.',
          '<b>Colour code:</b> slate = section cards · red = Rebel · blue = Empire · leader cards '
          'name their leader in the footer.']:
    story += [B(t)]
story += [Spacer(1, 6)]

def expand(cards):
    out = []
    for c in cards:
        out += [c] * c.get('count', 1)
    return out

RLN = {'Luke': 'LUKE SKYWALKER', 'Han': 'HAN SOLO', 'Leia': 'LEIA ORGANA'}
ELN = {'Vader': 'DARTH VADER', 'Veers': 'GENERAL VEERS', 'Piett': 'ADMIRAL PIETT'}
rebel_deck = ([(c, STEEL, 'SECTION · REBEL DECK') for c in expand(HC.section_cards())]
              + [(c, REBEL, 'REBEL ALLIANCE · TACTIC') for c in expand(HC.rebel_tactics())])
empire_deck = ([(c, STEEL, 'SECTION · IMPERIAL DECK') for c in expand(HC.section_cards())]
               + [(c, EMPIRE, 'GALACTIC EMPIRE · TACTIC') for c in expand(HC.imperial_tactics())])
leaders = []
for L in ['Luke', 'Han', 'Leia']:
    for c in HC.leader_cards(L):
        leaders.append((dict(c, count=1), REBEL, 'REBEL LEADER · ' + RLN[L]))
for L in ['Vader', 'Veers', 'Piett']:
    for c in HC.leader_cards(L):
        leaders.append((dict(c, count=1), EMPIRE, 'IMPERIAL LEADER · ' + ELN[L]))

story += [P('Rebel Alliance deck — print these %d cards' % len(rebel_deck), H2)]
story += [pp_sheet(rebel_deck, cols=3)]
story += [P('Galactic Empire deck — print these %d cards' % len(empire_deck), H2)]
story += [pp_sheet(empire_deck, cols=3)]
story += [P('Leader cards — add a leader’s 3 cards to your deck if you field that leader', H2)]
story += [pp_sheet(leaders, cols=3)]

# ---- 6. Quick reference ----
story += [NextPageTemplate('normal'), PageBreak()]
story += [P('6 · Quick Reference', H1), rule()]
story += [P('Attack dice (6 faces)', H2)]
for t in ['<b>Infantry</b> symbol — a hit on an infantry target.',
          '<b>Vehicle</b> symbol — a hit on a vehicle target.',
          '<b>Blast</b> — a hit on <i>any</i> target (and the only thing that hits special units '
          'and destroys structures).',
          '<b>Retreat</b> — the target retreats 1 hex (no figure lost unless it cannot retreat).',
          '<b>Miss</b> (×2 faces) — no effect.']:
    story += [B(t)]
story += [P('Turn sequence', H2)]
for t in ['Play one command card.', 'Order the units it allows.', 'Move ordered units.',
          'Attack with ordered units.', 'Resolve any reactions, then draw a card.']:
    story += [B(t)]
story += [P('Winning', H2)]
story += [P('Score victory medals by eliminating enemy units (and via each scenario’s special '
            'objectives — exits, held hexes, captured leaders, destroyed structures). First to the '
            'scenario’s medal target, or a sudden-death condition, wins.', BODY)]
story += [Spacer(1, 10), rule(GOLD),
          P('Canonical rules text lives in the project’s markdown documents; this PDF is a '
            'formatted, print-ready edition. Unofficial fan variant.', SMALL)]

# ---- build: two page templates (normal rules, wide card sheets) ----
PW, PH = letter
def footer(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setStrokeColor(GOLD); canvas.setLineWidth(0.6)
    canvas.line(0.9*inch, 0.6*inch, PW - 0.9*inch, 0.6*inch)
    canvas.setFont('Helvetica', 8); canvas.setFillColor(STEEL)
    canvas.drawString(0.9*inch, 0.42*inch, 'Battle of Hoth — Advanced')
    canvas.drawRightString(PW - 0.9*inch, 0.42*inch, 'Page %d' % doc.page)
    canvas.restoreState()

normal_frame = Frame(0.9*inch, 0.85*inch, PW - 1.8*inch, PH - 1.55*inch, id='normal')
cards_frame = Frame(0.45*inch, 0.7*inch, PW - 0.9*inch, PH - 1.4*inch, id='cards')
doc = BaseDocTemplate(OUT, pagesize=letter,
                      title='Battle of Hoth — Advanced Rulebook', author='Battle of Hoth Advanced')
doc.addPageTemplates([
    PageTemplate(id='normal', frames=[normal_frame], onPage=footer),
    PageTemplate(id='cards', frames=[cards_frame], onPage=footer),
])
doc.build(story)
print('wrote', OUT)
