"""Auto-detect unit positions (by colour) and crystal terrain (by texture) from the
scenario maps, mapping each to its nearest hex. Best-effort; validated vs the hand-
annotated scenarios 1-4."""
import pdfplumber, numpy as np, cv2, json

PDF = 'source/DOWSWB0101_EN_BATTLEOFHOTH_SCENARIO_WEB.pdf'
pdf = pdfplumber.open(PDF)
R = 150; PADX, CW, CH = 44, 500, 364
# grid fitted to the detected rebel icon blobs in Scenario 1 (ground truth)
GEO = dict(x0=122, dx=91, y0=201, dy=77, off=45)
COG = np.asarray(pdf.pages[1].crop((117, 104, 139, 126)).to_image(resolution=300).original.convert('L'))

def find_cog(idx):
    reg = np.asarray(pdf.pages[idx].crop((15, 95, 220, 155)).to_image(resolution=300).original.convert('L'))
    r = cv2.matchTemplate(reg, COG, cv2.TM_CCOEFF_NORMED); _, _, _, loc = cv2.minMaxLoc(r)
    return 15 + (loc[0]+COG.shape[1]/2)/(300/72), 95 + (loc[1]+COG.shape[0]/2)/(300/72)

def valid(c, r): return 0 <= c < (9 if r % 2 else 10) and 0 <= r < 7
def ctr(c, r): return (GEO['x0']+GEO['dx']*c+(GEO['off'] if r % 2 else 0), GEO['y0']+GEO['dy']*r)

def board_rgb(idx):
    cx, cy = find_cog(idx)
    crop = (cx-PADX, cy-47, cx-PADX+CW, cy-47+CH)
    return np.asarray(pdf.pages[idx].crop(crop).to_image(resolution=R).original.convert('RGB')).astype(int)

def classify_hex(img, x, y, rad=18):
    H, W, _ = img.shape
    x0, x1 = max(0, x-rad), min(W, x+rad); y0, y1 = max(0, y-rad), min(H, y+rad)
    patch = img[y0:y1, x0:x1].reshape(-1, 3)
    if len(patch) == 0:
        return 0, 0, 0
    Rr, Gg, Bb = patch[:, 0], patch[:, 1], patch[:, 2]
    satred = np.mean((Rr > 150) & (Gg < 90) & (Bb < 90))        # red unit badge
    unitblue = np.mean((Bb > 160) & (Rr < 110) & (Gg > 90) & (Gg < 170))  # blue figure
    dark = np.mean(Rr + Gg + Bb < 300)
    white = np.mean((Rr > 205) & (Gg > 210) & (Bb > 215))       # the unit icon's white box
    return satred, unitblue, dark, white

def detect(idx):
    img = board_rgb(idx)
    units, terrain = [], []
    for c in range(10):
        for r in range(7):
            if not valid(c, r):
                continue
            x, y = [int(v) for v in ctr(c, r)]
            satred, unitblue, dark, white = classify_hex(img, x, y)
            if satred > 0.09 and white > 0.10:
                units.append(dict(side='rebel', col=c, row=r))
            elif unitblue > 0.10 and white > 0.12:
                units.append(dict(side='empire', col=c, row=r))
            elif dark > 0.28:
                terrain.append(dict(type='rocks', col=c, row=r))
    return units, terrain

def crop_patch(img, x, y, s=19):
    H, W, _ = img.shape
    sub = img[max(0, y-s):min(H, y+s), max(0, x-s):min(W, x+s)].astype('uint8')
    g = cv2.cvtColor(sub, cv2.COLOR_RGB2GRAY)
    return cv2.resize(g, (24, 24)).astype(float)

_TEMPLATES = None
def build_templates():
    global _TEMPLATES
    if _TEMPLATES is not None:
        return _TEMPLATES
    truth = json.load(open('hoth_scenario_positions.json'))
    _TEMPLATES = {}
    for k in ['1', '2', '3', '4']:
        img = board_rgb(int(k))
        for u in truth[k]['units']:
            x, y = [int(v) for v in ctr(u['col'], u['row'])]
            _TEMPLATES.setdefault(u['kind'], []).append(crop_patch(img, x, y))
    return _TEMPLATES

SIDE_KINDS = {'rebel': ['echo', 'speeder', 'artillery', 'tauntaun'],
              'empire': ['snowtroop', 'atat', 'droid', 'eweb', 'atst']}
def classify_type(img, x, y, side):
    tpl = build_templates()
    patch = crop_patch(img, x, y)
    best, bd = None, 1e18
    for kind in SIDE_KINDS[side]:
        for t in tpl.get(kind, []):
            d = float(np.mean((patch - t) ** 2))
            if d < bd:
                bd, best = d, kind
    return best or ('echo' if side == 'rebel' else 'snowtroop')

if __name__ == '__main__':
    truth = json.load(open('hoth_scenario_positions.json'))
    for k in ['1', '2', '3', '4']:
        u, t = detect(int(k))
        du = {(x['col'], x['row'], x['side']) for x in u}
        tu = {(x['col'], x['row'], x['side']) for x in truth[k]['units']}
        print(f"scn {k}: detected {len(u)} units (truth {len(tu)}); "
              f"match {len(du & tu)}, missed {len(tu-du)}, extra {len(du-tu)}; "
              f"terrain det {len(t)} (truth {len(truth[k]['terrain'])})")
