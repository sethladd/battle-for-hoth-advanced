"""Auto-generate annotations for scenarios 5-17 (positions+side reliable, types via
icon templates, crystal terrain as generic rocks). Merge with the hand-verified 1-4."""
import json, importlib, detect_maps
importlib.reload(detect_maps)
import detect_maps as D

truth = json.load(open('../data/hoth_scenario_positions.json'))
full = {'_note': 'Scenarios 1-4 hand-verified by user; 5-17 auto-detected '
                 '(unit positions/sides reliable; types via template match; '
                 'terrain crystal hexes marked as generic rocks, approximate).'}
for k in ['1', '2', '3', '4']:
    full[k] = {kk: truth[k][kk] for kk in ('units', 'terrain', 'markers')}

for n in range(5, 18):
    img = D.board_rgb(n)
    units, terrain = [], []
    for c in range(10):
        for r in range(7):
            if not D.valid(c, r):
                continue
            x, y = [int(v) for v in D.ctr(c, r)]
            sr, ub, dk, wh = D.classify_hex(img, x, y)
            if sr > 0.09 and wh > 0.10:
                units.append(dict(kind=D.classify_type(img, x, y, 'rebel'), side='rebel', col=c, row=r))
            elif ub > 0.10 and wh > 0.12:
                units.append(dict(kind=D.classify_type(img, x, y, 'empire'), side='empire', col=c, row=r))
            elif dk > 0.25:
                terrain.append(dict(type='rocks', col=c, row=r))
    full[str(n)] = dict(units=units, terrain=terrain, markers=[])
    rc = sum(1 for u in units if u['side'] == 'rebel')
    ec = len(units) - rc
    print(f"scn {n:2}: rebel {rc}, empire {ec}, terrain {len(terrain)}")

json.dump(full, open('../data/hoth_scenario_positions_full.json', 'w'), indent=1)
print('wrote hoth_scenario_positions_full.json')
