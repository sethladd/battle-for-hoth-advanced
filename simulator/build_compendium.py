"""Validate the canonical card compendium against the live card definitions.

Per the golden rule (CLAUDE.md), docs/Advanced_Deck_Compendium.md is the SINGLE canonical
source for card rules text — it is hand-edited, not generated. This script no longer writes
that file; instead it checks that the markdown and simulator/hoth_cards.py agree:

  * every card defined in hoth_cards.py has a description line in the compendium
  * no stale compendium card lines refer to cards that no longer exist
  * the ×N counts in the markdown match each card's `count`

Run it after editing either the markdown or the card definitions; a non-zero exit means the
two have drifted. The PDF (build_rulebook_pdf.py) and replay (build_replay.py) both read
their card text from the same markdown via card_text.py.
"""
import re
import sys
import importlib
import hoth_cards
importlib.reload(hoth_cards)
import hoth_cards as HC
import card_text

CANON = card_text.CANON
LEADERS = ['Luke', 'Han', 'Leia', 'Vader', 'Veers', 'Piett']

def defined_cards():
    """{name: count} for every card in the advanced variant."""
    cards = (HC.section_cards() + HC.rebel_tactics() + HC.imperial_tactics()
             + sum((HC.leader_cards(L) for L in LEADERS), []))
    return {c['name']: c['count'] for c in cards}

# {name: count} as written in the canonical markdown (count defaults to 1 when no ×N given).
_COUNT = re.compile(r'^- \*\*(.+?)\*\*(?:\s*×(\d+))?', )
def markdown_counts(path=CANON):
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = _COUNT.match(line.rstrip('\n'))
            if m and card_text._LINE.match(line.rstrip('\n')):
                out[m.group(1).strip()] = int(m.group(2)) if m.group(2) else 1
    return out

def main():
    defined = defined_cards()
    md_text = card_text.parse()
    md_counts = markdown_counts()
    problems = []

    for name, cnt in defined.items():
        if name not in md_text:
            problems.append(f"MISSING in markdown: '{name}' is defined in hoth_cards.py "
                            f"but has no description line in the compendium.")
        elif md_counts.get(name) != cnt:
            problems.append(f"COUNT mismatch for '{name}': hoth_cards.py says ×{cnt}, "
                            f"compendium says ×{md_counts.get(name)}.")

    for name in md_text:
        if name not in defined:
            problems.append(f"STALE in markdown: '{name}' has a description but is not a "
                            f"card in hoth_cards.py.")

    if problems:
        print(f"✗ {len(problems)} problem(s) — markdown and card definitions have drifted:\n")
        for p in problems:
            print("  - " + p)
        print(f"\nFix {CANON} (canonical) or hoth_cards.py so they agree.")
        sys.exit(1)

    print(f"✓ compendium in sync: {len(defined)} cards, all descriptions present and counts match.")

if __name__ == '__main__':
    main()
