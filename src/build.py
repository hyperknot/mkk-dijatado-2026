#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
# Builds index.html from src/: the hand-written slides (src/slides/*.html) and the result slides
# generated from src/results.json, in the order of DECK.
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'

# The deck: a name is a hand-written slide file (src/slides/<name>.html), ('class', item) the
# slides of a category (cover, III., II., I., top 10), ('kmk',) and ('clubs',) the generated ones.
DECK = [
    'title',
    'sponsors',
    'budget',
    'stats',
    'ceremony',
    ('class', 'standard'),
    ('class', 'sport'),
    ('class', 'tandem'),
    ('class', 'fai1'),
    ('class', 'women'),
    ('class', 'juniors'),
    ('class', 'senior'),
    ('class', 'open'),
    'kmk-cover',
    ('kmk',),
    'clubs-cover',
    ('clubs',),
    'example-flight',
    'superhero',
    'records',
    'thanks',
]

# Engraved names (the cup order, Hungarian order) by XContest username; others keep the XContest name
HU = {
    'Wmpilot': 'Bereznay Attila', 'ENAIRGY': 'Rácz Balázs', 'Tasipepo': 'Tasi Péter',
    'okrosl': 'Ökrös László', 'ubalika': 'Ujhelyi Balázs', 'CZIGLERELEK': 'Czigler Elek',
    'H_Tami': 'Hegedűs Tamara', 'Katapult': 'Stemler Katalin', 'S.Dori': 'Salamon Dorottya',
    'kerenyid': 'Kerényi Dávid', 'janibar': 'Barna János', 'WingsOfFury': 'Páll Csaba',
    'Kojak': 'Kocsis Péter', 'Furge': 'Somfai Csaba', 'Onesto': 'Földi Csaba',
    'homokipisztrang': 'Máté Zoltán', 'Doto': 'Takács Zsolt', 'karip': 'Detki Árpád',
    'CsabaiSanya': 'Csabai Sanya', 'horakgyuszibacsi': 'Horák Gyula',
    'TomiTorkos': 'ifj. Torkos Tamás', 'gszala': 'Szalai Gábor',
    'dosa.richard': 'Dósa Richárd', 'Zale': 'Szalóki Zoltán', 'mlinko': 'Mlinkó László',
    'Vargaz': 'Varga Zoltán', 'Miko27': 'Bartos Miklós', 'szabbbolcs': 'Szalai Szabolcs',
    'stevenso': 'Kátai István', 'boti': 'Nyíri Botond', 'palaga': 'Palaga Zoltán',
    'acsa': 'Ács Attila',
}

# The crop of a photo in its frame (CSS object-position), by username; default: center
FOCUS = {
    'CZIGLERELEK': '35% 30%', 'Doto': '50% 40%', 'H_Tami': '33% 40%', 'S.Dori': '20% 30%',
    'Wmpilot': '85% 50%', 'horakgyuszibacsi': '50% 30%', 'janibar': '38% 30%', 'karip': '50% 30%',
    'ubalika': '72% 40%', 'homokipisztrang': '55% 40%', 'Onesto': '55% 40%', 'okrosl': '50% 40%',
}

# Takeoffs XContest shows as "?" (not named by the pilot): the name the other pilots of the same
# group flight used on XContest, by the flight link (after "reszletei:")
TAKEOFF = {
    'Wmpilot/27.06.2026/09:07': 'Kiskunhalas',
    'Wmpilot/20.06.2026/10:25': 'Kiskunhalas',
    'homokipisztrang/1.05.2026/11:55': 'Tiszavasvári',
    'TomiTorkos/28.05.2026/09:53': 'Tiszavasvári',
}

# Places with a prize (podium slide), by class; default 3. PG Ifi had 2 participants: only the 1st
# place gets a prize (decided after the results post, which said "díjazás nélkül")
PRIZES = {'juniors': 1}

ROMAN = {1: 'I.', 2: 'II.', 3: 'III.'}
TYPES = {
    'FREE_FLIGHT': 'Szabadtáv',  # as in the rules (4.1)
    'FREE_TRIANGLE': 'Lapos háromszög',
    'FAI_TRIANGLE': 'FAI háromszög',
}


def main():
    data = json.loads((SRC / 'results.json').read_text())
    photos = {p.stem for p in (ROOT / 'assets/img/photos').glob('*.jpg')}
    slides = []
    for entry in DECK:
        if isinstance(entry, str):
            slides.append((SRC / 'slides' / f'{entry}.html').read_text().strip())
        elif entry[0] == 'class':
            slides += class_slides(data['classes'][entry[1]], PRIZES.get(entry[1], 3), photos)
        elif entry[0] == 'kmk':
            slides += kmk_slides(data['kmk'], photos)
        elif entry[0] == 'clubs':
            slides += club_slides(data['clubs'])
    template = (SRC / 'template.html').read_text()
    html = template.replace('<!-- SLIDES -->', '\n\n'.join(slides))
    (ROOT / 'index.html').write_text(html)
    print(f'index.html: {html.count("<section")} slides')


def class_slides(c, prizes, photos):
    # cover, the podium from III. to I. (the places with a prize), the top 10
    out = [cover(c['name'], f'{c["count"]} pilóta')]
    for r in reversed([r for r in c['rows'] if r['place'] <= prizes]):
        out.append(podium(c['name'], r, photos))
    out.append(ranking(c['name'], c['rows']))
    return out


def podium(category, r, photos):
    u = r['username']
    rows = '\n'.join(
        f'        <tr><td>{i}</td><td>{day(f)}</td><td>{escape(takeoff(f))}</td>'
        f'<td><span class="type {f["type"]}">{TYPES[f["type"]]}</span></td>'
        f'<td class="num">{f["km"]:.2f} km</td><td class="num pts">{f["points"]:.2f} p.</td></tr>'
        for i, f in enumerate(r['flights'], 1)
    )
    return f'''<section class="podium">
  <div class="head">
    <div><span class="place p{r["place"]}">{ROMAN[r["place"]]}</span></div>
    <div class="category">{category}</div>
    <div class="name">{name(r)}</div>
    <div class="nick">[{escape(u)}]</div>
    <div class="club">{escape(r["club"])}</div>
    <div class="glider">{gliders(r["flights"])}</div>
    <div class="points">{r["points"]:.2f} <small>pont</small></div>
  </div>
  {photo(u, name(r), photos)}
  <div class="flights card">
    <table class="list">
      <thead><tr><th>#</th><th>Dátum</th><th>Starthely</th><th>Típus</th><th class="num">Táv</th><th class="num">Pont</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>
</section>'''


def ranking(title, rows):
    top = rows[0]['points']
    body = '\n'.join(
        f'        <tr><td><span class="rank p{r["place"]}">{r["place"]}</span></td>'
        f'<td class="who"><b>{escape(r["name"])}</b> <i>[{escape(r["username"])}]</i>'
        f'<span class="club">{escape(r["club"])}</span></td>'
        f'<td class="num pts">{r["points"]:.2f}</td><td>{bar(r["points"], top)}</td></tr>'
        for r in rows
    )
    return f'''<section class="ranking">
  <h2>{title}</h2>
  <div class="card">
    <table class="list">
      <tbody>
{body}
      </tbody>
    </table>
  </div>
</section>'''


def kmk_slides(kmk, photos):
    # the winner of KMK 100+ and 200+ with all their flights, then both top 10 lists
    out = []
    for item, km in (('kmk100', 100), ('kmk200', 200)):
        r = kmk[item][0]
        rows = '\n'.join(
            f'        <tr><td>{i}</td><td>{day(f)}</td><td>{escape(takeoff(f))}</td>'
            f'<td class="num pts">{f["km"]:.2f} km</td></tr>'
            for i, f in enumerate(r['flights'], 1)
        )
        out.append(f'''<section class="kmk">
  <div class="head">
    <h2>KMK {km}+</h2>
    <div class="podium-name"><div class="name-md">{name(r)}</div><div class="nick">[{escape(r["username"])}] · {escape(r["club"])}</div></div>
    <div class="facts">
      <div class="fact"><b>{r["count"]}</b><span>repülés {km} km fölött</span></div>
      <div class="fact"><b>{r["longest"]:.2f}</b><span>km a leghosszabb</span></div>
    </div>
    {photo(r["username"], name(r), photos)}
  </div>
  <div class="card">
    <table class="list">
      <thead><tr><th>#</th><th>Dátum</th><th>Starthely</th><th class="num">Szabadtáv</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </div>
</section>''')
    cols = []
    for item, km in (('kmk100', 100), ('kmk200', 200)):
        body = '\n'.join(
            f'        <tr><td><span class="rank p{r["place"]}">{r["place"]}</span></td>'
            f'<td class="who"><b>{escape(r["name"])}</b> <i>[{escape(r["username"])}]</i></td>'
            f'<td class="num pts">{r["count"]}</td><td class="num">{r["longest"]:.1f} km</td></tr>'
            for r in kmk[item]
        )
        cols.append(f'''  <div>
    <h3>KMK {km}+</h3>
    <div class="card">
      <table class="list">
        <thead><tr><th></th><th>Pilóta</th><th class="num">Db</th><th class="num">Leghosszabb</th></tr></thead>
        <tbody>
{body}
        </tbody>
      </table>
    </div>
  </div>''')
    out.append(
        '<section class="two-col ranking-kmk">\n  <h2>KMK 100 és 200</h2>\n'
        + '\n'.join(cols)
        + '\n</section>'
    )
    return out


def club_slides(clubs):
    # III., II., I. with their 5 pilots, then the top 10
    out = []
    for c in reversed(clubs[:3]):
        top = c['members'][0]['points']
        rows = '\n'.join(
            f'        <tr><td>{i}</td><td class="who"><b>{escape(HU.get(m["username"], m["name"]))}</b> <i>[{escape(m["username"])}]</i></td>'
            f'<td class="num pts">{m["points"]:.2f}</td><td>{bar(m["points"], top)}</td></tr>'
            for i, m in enumerate(c['members'], 1)
        )
        logo = ''
        if c['name'] == 'Eged Eagles SE':
            logo = '\n  <img class="club-logo" src="assets/img/logos/eged-eagles.jpg" alt="Eged Eagles SE">'
        out.append(f'''<section class="podium club">
  <div class="head">
    <div><span class="place p{c["place"]}">{ROMAN[c["place"]]}</span></div>
    <div class="category">PG Klub</div>
    <div class="name">{escape(c["name"])}</div>
    <div class="points">{c["points"]:.2f} <small>pont</small></div>
  </div>{logo}
  <div class="club-members card">
    <table class="list ranking">
      <tbody>
{rows}
      </tbody>
    </table>
  </div>
</section>''')
    top = clubs[0]['points']
    body = '\n'.join(
        f'        <tr><td><span class="rank p{c["place"]}">{c["place"]}</span></td><td class="who"><b>{escape(c["name"])}</b></td>'
        f'<td class="num pts">{c["points"]:.2f}</td><td>{bar(c["points"], top)}</td></tr>'
        for c in clubs
    )
    out.append(f'''<section class="ranking">
  <h2>PG Klub</h2>
  <div class="card">
    <table class="list">
      <tbody>
{body}
      </tbody>
    </table>
  </div>
</section>''')
    return out


def cover(title, count):
    return f'<section class="cover">\n  <h1>{title}</h1>\n  <div class="count">{count}</div>\n</section>'


def name(r):
    return escape(HU.get(r['username'], r['name']))


def day(f):
    return f'{f["date"].replace("-", ".")}.'


def takeoff(f):
    return TAKEOFF.get(f['link'].split('reszletei:')[1], f['takeoff'])


def photo(u, alt, photos):
    # assets/img/photos/<username>.jpg, or the initials when there is none
    if u in photos:
        pos = f' style="object-position: {FOCUS[u]}"' if u in FOCUS else ''
        return f'<div class="photo"><img src="assets/img/photos/{u}.jpg" alt="{alt}"{pos}></div>'
    initials = ''.join(w[0] for w in alt.replace('ifj. ', '').split()[:2])
    return f'<div class="photo none">{initials}</div>'


def gliders(flights):
    # the gliders of the counted flights, most used first; spelling variants typed by the pilots
    # ("Rx3.5pro" / "Rx 3.5pro", "rx3.5" / "rx3.5 pro") are one glider
    def key(g):
        return ''.join(c for c in g.lower() if c not in " '’")

    names = [' '.join(f['glider'].replace('’', "'").split()) for f in flights]
    keys = {key(n) for n in names}
    merged = {k: next((o for o in keys if o != k and o.startswith(k)), k) for k in keys}
    groups = {}
    for n in names:
        groups.setdefault(merged[key(n)], []).append(n)
    ordered = sorted(groups.values(), key=lambda g: -len(g))
    return escape(', '.join(max(set(g), key=g.count) for g in ordered))


def bar(value, top):
    return f'<div class="bar"><span style="width: {100 * value / top:.1f}%"></span></div>'


if __name__ == '__main__':
    main()
