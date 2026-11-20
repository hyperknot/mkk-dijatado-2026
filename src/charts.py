# The MKK charts of the budget and stats slides as inline SVG (no JS, works offline), from
# src/mkk_finances.json and src/mkk_stats.json. build.py puts them in place of <!-- chart:NAME -->.
import json
from html import escape
from pathlib import Path

SRC = Path(__file__).resolve().parent

COSTS = [('xcontest', 'XContest', '#4472c4'), ('kupak', 'Díjak (kupák, érmek, utalványok)', '#ed7d31')]
INCOME_DETAIL = [
    ('siresz_cel', 'SIRESZ Sportalap céltámogatás', '#70ad47'),
    ('hffa', 'HFFA', '#5b9bd5'),
    ('sarkany', 'Sárkányrepülésért Alapítvány', '#ffc000'),
    ('siresz_alt', 'SIRESZ Sportalap (általános)', '#3f7a2a'),
]
INCOME = [('siresz', 'SIRESZ', '#70ad47'), ('hffa', 'HFFA', '#5b9bd5'), ('sarkany', 'Sárkányrepülésért Alapítvány', '#ffc000')]
HATCH_NOTE = 'csíkozott: becslés'


def charts():
    # placeholder name -> SVG
    years = finances()
    detail = [(y, v) for y, v in years if y >= 2022]
    income = [(y, {**v, 'siresz': v.get('siresz', 0) + v.get('siresz_cel', 0) + v.get('siresz_alt', 0)}) for y, v in years]
    for y, v in income:
        if 'siresz_alt' in v['hatch']:
            v['hatch'] = v['hatch'] | {'siresz'}
    return {
        'income-detail': hbar('Bevételek 2022–2026 (eFt)', detail, INCOME_DETAIL, 840, 400, totals=True),
        'costs': hbar('Költségek (eFt)', years, COSTS, 840, 470),
        'income': hbar('Bevételek (eFt)', income, INCOME, 840, 470),
        'stats': stats_chart(),
    }


def finances():
    # [(year, {key: Ft, 'hatch': set}), ...]; siresz_alt derived where marked
    data = json.loads((SRC / 'mkk_finances.json').read_text())['years']
    out = []
    for y, d in sorted(data.items()):
        v = {k: d[k] for k in ('xcontest', 'kupak', 'siresz', 'siresz_cel', 'siresz_alt', 'hffa', 'sarkany') if k in d}
        if 'siresz_alt' in d.get('derived', []):
            v['siresz_alt'] = v['xcontest'] + v['kupak'] - sum(v.get(k, 0) for k in ('siresz_cel', 'hffa', 'sarkany'))
        v['hatch'] = set(d.get('hatch', []))
        out.append((int(y), v))
    return out


def hbar(title, rows, series, w, h, totals=False):
    # stacked horizontal bars, one row per year, values in thousand Ft
    left, right, top = 78, 70 if totals else 24, 92
    legend_rows, legend = legend_svg(series + ([(None, HATCH_NOTE, None)] if any(v['hatch'] for _, v in rows) else []), w)
    bottom = h - 16 - 30 * legend_rows
    xmax, step = 1400, 200
    sx = (w - left - right) / xmax
    band = (bottom - top) / len(rows)
    bar = min(band * 0.68, 46)
    out = [svg_open(w, h, title), hatch_defs(series), text(w / 2, 36, title, 30, weight=700)]
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
            fill = f'url(#hatch-{key})' if key in v['hatch'] else color
            out.append(f'<rect x="{x:.1f}" y="{cy - bar / 2:.1f}" width="{val * sx:.1f}" height="{bar:.1f}" fill="{fill}"/>')
            x += val * sx
        if totals:
            out.append(text(x + 10, cy + 7, fmt(round(sum(v.get(k, 0) for k, _, _ in series) / 1000)), 21, anchor='start', weight=600))
    out.append(f'<g transform="translate(0 {bottom + 22})">{legend}</g>')
    out.append('</svg>')
    return '\n'.join(out)


def stats_chart():
    data = json.loads((SRC / 'mkk_stats.json').read_text())
    series = data['series']
    w, h = 1000, 640
    left, right, top = 70, 86, 70
    order = ['pilota', 'tavrepulo', 'repulesek', 'tav', 'legtersertes', 'ko100', 'klub']
    legend_rows, legend = legend_svg([(k, series[k]['label'], series[k]['color']) for k in order], w, line=True)
    bottom = h - 46 - 30 * legend_rows
    years = list(range(2007, 2027))
    sx = (w - left - right) / (len(years) - 1)
    scales = {'left': (600, 100), 'right': (12000, 2000)}
    title = 'MKK számokban, 2007–2026'
    out = [svg_open(w, h, title), text(w / 2, 40, title, 30, weight=700)]
    for i in range(7):
        y = bottom - i * (bottom - top) / 6
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - right}" y2="{y:.1f}" class="grid"/>')
        out.append(text(left - 12, y + 6, fmt(i * 100), 18, anchor='end', cls='tick'))
        out.append(text(w - right + 12, y + 6, fmt(i * 2000), 18, anchor='start', cls='tick'))
    for i, yr in enumerate(years):
        if (yr % 2 and yr != years[-2]) or yr == years[-1]:
            out.append(text(left + i * sx, bottom + 30, str(yr), 18 if yr != years[-1] else 20, weight=500 if yr != years[-1] else 700, cls='tick' if yr != years[-1] else ''))
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
            out.append(f'<polyline points="{d}" fill="none" stroke="{s["color"]}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
        if pts[-1]:
            x, y = pts[-1]
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{s["color"]}" stroke="#fff" stroke-width="2"/>')
    out.append(f'<g transform="translate(0 {bottom + 62})">{legend}</g>')
    out.append('</svg>')
    return '\n'.join(out)


def legend_svg(items, w, line=False, size=20):
    # centered legend rows; items: (key, label, color); color None: the hatch sample
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
        y = r * 30
        for (key, label, color), iw in row:
            if line:
                out.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + 24:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')
            else:
                fill = color or 'url(#hatch-sample)'
                out.append(f'<rect x="{x:.1f}" y="{y - 9:.1f}" width="20" height="18" fill="{fill}"/>')
            out.append(text(x + 32, y + 7, label, size, anchor='start'))
            x += iw
    return len(rows), ''.join(out)


def hatch_defs(series):
    pats = [
        f'<pattern id="hatch-{key}" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="10" height="10" fill="{color}" opacity="0.45"/><rect width="5" height="10" fill="{color}"/></pattern>'
        for key, _, color in series
    ]
    pats.append(
        '<pattern id="hatch-sample" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="10" height="10" fill="#bbb" opacity="0.45"/><rect width="5" height="10" fill="#bbb"/></pattern>'
    )
    return f'<defs>{"".join(pats)}</defs>'


def svg_open(w, h, label):
    return f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'


def text(x, y, s, size, anchor='middle', weight=500, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"{c}>{escape(s)}</text>'


def fmt(n):
    # Hungarian thousands separator: a space (thin no-break space)
    return f'{n:,}'.replace(',', '\u202f')
