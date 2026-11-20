# The MKK charts of the budget and stats slides as inline SVG (no JS, works offline), from
# src/mkk_finances.json and src/mkk_stats.json. build.py puts them in place of <!-- chart:NAME -->.
import json
from html import escape
from pathlib import Path

SRC = Path(__file__).resolve().parent

COSTS = [('xcontest', 'XContest', '#4472c4'), ('kupak', 'Díjak (kupák, érmek, utalványok)', '#ed7d31')]
# before 2022 only the SIRESZ total is known ('siresz'), a plain lighter green
INCOME = [
    ('siresz', 'SIRESZ', '#a9d18e'),
    ('siresz_cel', 'SIRESZ önkéntes támogatás', '#70ad47'),
    ('hffa', 'HFFA önkéntes támogatás', '#5b9bd5'),
    ('sarkany', 'Sárkányrepülésért Alapítvány', '#ffc000'),
    ('siresz_alt', 'SIRESZ Sportalap', '#3f7a2a'),
]
# segments not certain yet ('unsure' in mkk_finances.json): drawn with a red frame, as the red frames of the slides
UNSURE_NOTE = 'piros keret: nem biztos'
RED = '#e01b1b'


def charts():
    # placeholder name -> SVG
    years = finances()
    return {
        # same height and legend space: the years of the two charts side by side line up
        'costs': hbar('Költségek (eFt)', years, COSTS, 840, 940, totals=True, legend_rows=3),
        'income': hbar('Bevételek (eFt)', years, INCOME, 840, 940, totals=True, legend_rows=3),
        'stats': stats_chart(),
    }


def finances():
    # [(year, {key: Ft, 'unsure': set}), ...]; siresz_alt derived where marked
    data = json.loads((SRC / 'mkk_finances.json').read_text())['years']
    out = []
    for y, d in sorted(data.items()):
        v = {k: d[k] for k in ('xcontest', 'kupak', 'siresz', 'siresz_cel', 'siresz_alt', 'hffa', 'sarkany') if k in d}
        if 'siresz_alt' in d.get('derived', []):
            v['siresz_alt'] = v['xcontest'] + v['kupak'] - sum(v.get(k, 0) for k in ('siresz_cel', 'hffa', 'sarkany'))
        v['unsure'] = set(d.get('unsure', []))
        out.append((int(y), v))
    return out


def hbar(title, rows, series, w, h, totals=False, legend_rows=1):
    # stacked horizontal bars, one row per year, values in thousand Ft
    left, right, top = 78, 70 if totals else 24, 92
    rows_used, legend = legend_svg(series + ([(None, UNSURE_NOTE, None)] if any(v['unsure'] & {k for k, _, _ in series} for _, v in rows) else []), w)
    bottom = h - 16 - 30 * max(rows_used, legend_rows)
    xmax, step = 1400, 200
    sx = (w - left - right) / xmax
    band = (bottom - top) / len(rows)
    bar = min(band * 0.68, 46)
    out = [svg_open(w, h, title), text(w / 2, 36, title, 30, weight=700)]
    for t in range(0, xmax + 1, step):
        x = left + t * sx
        out.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{bottom}" class="grid"/>')
        out.append(text(x, top - 18, fmt(t), 19, cls='tick'))
    for i, (y, v) in enumerate(rows):
        cy = top + band * (i + 0.5)
        out.append(text(left - 14, cy + 7, str(y), 21 if band > 26 else 19, anchor='end', weight=600 if y == rows[-1][0] else 500))
        x = left
        for key, _, color in series:
            val = v.get(key, 0) / 1000
            if val <= 0:
                continue
            frame = f' stroke="{RED}" stroke-width="4"' if key in v['unsure'] else ''
            out.append(f'<rect x="{x:.1f}" y="{cy - bar / 2:.1f}" width="{val * sx:.1f}" height="{bar:.1f}" fill="{color}"{frame}/>')
            x += val * sx
        if totals:
            out.append(text(x + 10, cy + 7, fmt(round(sum(v.get(k, 0) for k, _, _ in series) / 1000)), 21, anchor='start', weight=600))
    out.append(f'<g transform="translate(0 {bottom + 22})">{legend}</g>')
    out.append('</svg>')
    return '\n'.join(out)


def stats_chart():
    data = json.loads((SRC / 'mkk_stats.json').read_text())
    series = data['series']
    # wide for the full-width chart of the stats slide (about 1740 x 720 px on the slide)
    w, h = 1740, 720
    left, right, top = 80, 96, 34
    order = ['pilota', 'tavrepulo', 'repulesek', 'tav', 'legtersertes', 'ko100']  # klub: in the data, not drawn
    legend_rows, legend = legend_svg([(k, series[k]['label'], series[k]['color']) for k in order], w, line=True, size=25)
    bottom = h - 62 - 36 * legend_rows
    years = list(range(2007, 2027))
    sx = (w - left - right) / (len(years) - 1)
    scales = {'left': (600, 100), 'right': (12000, 2000)}
    out = [svg_open(w, h, 'MKK számokban, 2007–2026')]
    for i in range(7):
        y = bottom - i * (bottom - top) / 6
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - right}" y2="{y:.1f}" class="grid"/>')
        out.append(text(left - 14, y + 8, fmt(i * 100), 24, anchor='end', cls='tick'))
        out.append(text(w - right + 14, y + 8, fmt(i * 2000), 24, anchor='start', cls='tick'))
    for i, yr in enumerate(years):
        last = yr == years[-1]
        out.append(text(left + i * sx, bottom + 36, str(yr), 26 if last else 23, weight=700 if last else 500, cls='' if last else 'tick'))
    for key in reversed(order):
        s = series[key]
        ymax = scales[s['axis']][0]
        pts = [(left + i * sx, bottom - s['values'][str(yr)] / ymax * (bottom - top)) if str(yr) in s['values'] else None for i, yr in enumerate(years)]
        runs, cur = [], []
        for p in pts:
            if p:
                cur.append(p)
            elif cur:
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        for run in runs:
            d = ' '.join(f'{x:.1f},{y:.1f}' for x, y in run)
            out.append(f'<polyline points="{d}" fill="none" stroke="{s["color"]}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>')
        if pts[-1]:
            x, y = pts[-1]
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{s["color"]}" stroke="#fff" stroke-width="2.5"/>')
    out.append(f'<g transform="translate(0 {bottom + 80})">{legend}</g>')
    out.append('</svg>')
    return '\n'.join(out)


def legend_svg(items, w, line=False, size=20):
    # centered legend rows; items: (key, label, color); color None: the red frame sample
    widths = [34 + len(label) * size * 0.56 + 30 for _, label, _ in items]
    rows, cur, cur_w = [], [], 0
    for item, iw in zip(items, widths):
        if cur and cur_w + iw > w - 40:
            rows.append((cur, cur_w))
            cur, cur_w = [], 0
        cur.append((item, iw))
        cur_w += iw
    rows.append((cur, cur_w))
    out = []
    for r, (row, row_w) in enumerate(rows):
        x = (w - row_w) / 2
        y = r * (size + 11)
        for (key, label, color), iw in row:
            if line:
                out.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + 24:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')
            else:
                style = f'fill="{color}"' if color else f'fill="none" stroke="{RED}" stroke-width="4"'
                out.append(f'<rect x="{x:.1f}" y="{y - 9:.1f}" width="20" height="18" {style}/>')
            out.append(text(x + 32, y + 7, label, size, anchor='start'))
            x += iw
    return len(rows), ''.join(out)


def svg_open(w, h, label):
    return f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'


def text(x, y, s, size, anchor='middle', weight=500, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"{c}>{escape(s)}</text>'


def fmt(n):
    # Hungarian thousands separator: a space (thin no-break space)
    return f'{n:,}'.replace(',', '\u202f')
