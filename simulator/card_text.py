"""Single canonical source for card rules text.

Per the golden rule (see CLAUDE.md), the human-readable card text lives ONLY in the
markdown at docs/Advanced_Deck_Compendium.md. This module parses that file so the PDF and
the replay viewer read their descriptions from it — nothing hard-codes card text anymore.
"""
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.join(HERE, '..', 'docs', 'Advanced_Deck_Compendium.md')

# matches:  - **Name** ×N *(reaction)* — description
_LINE = re.compile(r'^- \*\*(.+?)\*\*(?:\s*×\d+)?(?:\s*\*\(reaction\)\*)?\s*—\s*(.+)$')

def parse(path=CANON):
    """Return {card name: raw markdown description} from the canonical compendium."""
    out = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = _LINE.match(line.rstrip('\n'))
            if m:
                out[m.group(1).strip()] = m.group(2).strip()
    return out

def to_reportlab(s):
    """Markdown emphasis -> ReportLab inline markup."""
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<i>\1</i>', s)
    return s

def to_plain(s):
    """Strip markdown emphasis for plain-text consumers (e.g. the HTML replay)."""
    return re.sub(r'\*+', '', s)
