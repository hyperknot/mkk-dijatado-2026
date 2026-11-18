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
    # 'superhero',  # Szuperhős különdíj: none in 2026; uncomment to bring the slide back (src/slides/superhero.html)
    'records',
    'thanks',
    'liga-cover',
    ('liga', 'new_comer'),
    ('liga', 'women'),
    ('liga', 'fun'),
    ('liga', 'sport'),
    ('liga', 'overall'),
    ('liga-records',),
    ('liga-fun',),
    'liga-turns',
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
    'ubalika': '72% 40%', 'homokipisztrang': '55% 40%', 'Onesto': '55% 40%',
}

# The logos on the PG Klub podium slides (assets/img/logos/), by club name; from the clubs' websites
CLUB_LOGOS = {
    'Eged Eagles SE': 'eged-eagles.jpg',
    'Sirius SE': 'sirius.jpg',  # sirius-se.hu, the white star on a dark blue like the site header
    'Winchflyer SE': 'winchflyer.jpg',  # winchflyer.hu
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

# The Liga rankings of AirScore (src/liga.json): slide title and which pilots are in it, as in its
# 'rankings' (Sport: certs A, B, C; Fun: A, B; Women: female pilots)
# The background of the Liga slides (reveal.js draws it over the body background of style.css)
LIGA_BG = 'assets/img/bg-liga.webp'

LIGA = {
    'overall': ('Összetett', lambda p: True),
    'sport': ('Sport', lambda p: p['glider_cert'] in ('A', 'B', 'C')),
    'fun': ('Fun', lambda p: p['glider_cert'] in ('A', 'B')),
    'women': ('Női', lambda p: p['sex'] == 'F'),
    'new_comer': ('Újonc', lambda p: p.get('new_comer')),

}

# The Liga records slide (src/season_stats.json), by value column: title, unit, decimals, and
# the height gained for the thermal
LIGA_RECORDS = {
    'avg_climb_ms': ('Legerősebb termik', 'm/s', 2, True),
    'speed_kmh': ('Legjobb átlagsebesség', 'km/h', 1, False),
    'max_ground_speed_kmh': ('Legnagyobb föld feletti sebesség', 'km/h', 0, False),
    'max_gps_alt': ('Legnagyobb magasság', 'm', 0, False),
}

# The fun stats slides (src/season_stats.json 'awards'): one slide per theme (final glide and goal,
# climbing, flying style), the awards in this order
LIGA_FUN = [
    ['Legjobb majdnem gól', 'Legjobb mentés', 'Legkockázatosabb végsiklás', 'Legóvatosabb végsiklás'],
    ['Legtürelmesebb tekerés', 'Legtöbb magasság egy tekeréssel', 'Leghosszabb tekerés'],
    ['Legprecízebb indulás', 'Leggörbébb repülés', 'Legegyenesebb repülés'],
]

# The Liga pilots on the slides, by AirScore ID: (name on the slide, photo name in assets/img/photos/
# or None). The photo name is the XContest username where the name and the glider match an MKK
# pilot, else a name-based one (pilots without a known XContest username)
LIGA_PILOTS = {
    314: ('Rácz Balázs', 'ENAIRGY'),
    1111: ('Barna János', 'janibar'),
    4: ('Szalóki Zoltán', 'Zale'),
    125: ('Takács Zsolt', 'takacs-zsolt'),
    77: ('Dósa Richárd', 'dosa.richard'),
    485: ('Erő Zsolt', None),
    1966: ('Sörös Róbert', None),
    2727: ('Bartos Miklós', 'Miko27'),
    127: ('Reményi Dániel', None),
    12: ('Kocsis Péter', 'Kojak'),
    78: ('Bruszniczky Balázs', None),
    108: ('Réti Arnold', 'reti-arnold'),
    8080: ('Huszkó Levente', None),
    137: ('Ábel Dániel', None),
    777: ('Ács Tamás', None),
    927: ('Salamon Dorottya', 'S.Dori'),
    2525: ('Tóth András', None),
    417: ('Börcsök Gergő', None),
    2728: ('Vas Judit', None),
    744: ('Resch Ferenc', None),
    88244: ('Kiss-Beck Veronika', 'kiss-beck-veronika'),
    33: ('Jámbor Flóra', None),
    1122: ('Fűrész Dóra', None),
    7777: ('Radnai András', None),
    32: ('Hargitai Dávid', None),
    42: ('Molnar Peter A.', None),
}

ROMAN = {1: 'I.', 2: 'II.', 3: 'III.'}
TYPES = {
    'FREE_FLIGHT': 'Szabadtáv',  # as in the rules (4.1)
    'FREE_TRIANGLE': 'Lapos háromszög',
    'FAI_TRIANGLE': 'FAI háromszög',
}


def main():
    data = json.loads((SRC / 'results.json').read_text())
    liga = json.loads((SRC / 'liga.json').read_text())
    season = json.loads((SRC / 'season_stats.json').read_text())
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
        elif entry[0] == 'liga':
            slides += liga_slides(liga, entry[1], photos)
        elif entry[0] == 'liga-records':
            slides.append(liga_records_slide(season, liga))
        elif entry[0] == 'liga-fun':
            slides += liga_fun_slides(season, liga)
    template = (SRC / 'template.html').read_text()
    html = template.replace('<!-- SLIDES -->', '\n\n'.join(slides))
    (ROOT / 'index.html').write_text(html)
    print(f'index.html: {html.count("<section")} slides')


def class_slides(c, prizes, photos):
    # cover, the podium from III. to I. (the places with a prize), the top 10
    out = [cover(c['name'], f'{c["count"]} pilóta')]
    for r in reversed([r for r in c['rows'] if r['place'] <= prizes]):
        out.append(podium(c['name'], r, photos))
    out.append(ranking(c['name'], c['rows'], photos))
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


def ranking(title, rows, photos, cls=''):
    # the top 3 on a podium (II., I., III. from left to right) with photos, 4-10 in rows below;
    # Liga rows have no username or club, their photo name is 'u'
    top = rows[0]['points']
    steps = '\n'.join(
        f'''    <div class="step p{r["place"]}">
      {photo(r.get('username', r.get('u')), name(r), photos)}
      <div class="step-name">{name(r)}</div>
      <div class="step-club">{escape(r.get("club", ""))}</div>
      <div class="block"><span class="step-place">{r["place"]}.</span><span class="step-pts">{r["points"]:.2f} p.</span></div>
    </div>'''
        for r in [rows[i] for i in (1, 0, 2) if i < len(rows)]
    )
    body = '\n'.join(
        f'        <tr><td><span class="rank p{r["place"]}">{r["place"]}</span></td>'
        f'<td class="who"><b>{escape(r["name"])}</b>'
        + (f' <i>[{escape(r["username"])}]</i>' if r.get('username') else '')
        + (f'<span class="club">{escape(r["club"])}</span>' if r.get('club') else '')
        + f'</td><td class="num pts">{r["points"]:.2f}</td><td>{bar(r["points"], top)}</td></tr>'
        for r in rows[3:]
    )
    table = ''
    if body:
        table = f'''
  <div class="card">
    <table class="list">
      <tbody>
{body}
      </tbody>
    </table>
  </div>'''
    return f'''<section class="ranking stage{cls}">
  <h2>{title}</h2>
  <div class="stairs">
{steps}
  </div>{table}
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
        if c['name'] in CLUB_LOGOS:
            logo = f'\n  <img class="club-logo" src="assets/img/logos/{CLUB_LOGOS[c["name"]]}" alt="{escape(c["name"])}">'
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


def liga_slides(liga, rank, photos):
    # cover, the podium from III. to I. with the task scores, the top 10
    title, member = LIGA[rank]
    pilots = [p for p in liga['results'] if member(p)]
    rows, place = [], 0
    for i, p in enumerate(pilots, 1):
        if i == 1 or p['score'] != pilots[i - 2]['score']:
            place = i  # equal scores share the place
        name, username = LIGA_PILOTS.get(p['ID'], (p['name'], None))
        rows.append({'place': place, 'name': name, 'points': p['score'], 'pilot': p, 'u': username})
    out = [cover(title, f'{len(pilots)} pilóta', ' liga')]
    for r in reversed([r for r in rows if r['place'] <= 3]):
        out.append(liga_podium(title, r, liga, photos))
    out.append(ranking(title, rows[:10], photos, ' liga'))
    return [s.replace('<section ', f'<section data-background-image="{LIGA_BG}" ', 1) for s in out]


def liga_podium(category, r, liga, photos):
    # per task: the place among all pilots, then the points that count for the season ('score', after
    # AirScore's FTV), with the full task points ('pre') crossed out before them where FTV cut them;
    # '–' where the pilot has no task points
    p = r['pilot']
    rows = []
    for t in liga['tasks']:
        res = p['results'][t['task_code']]
        place = 1 + sum(o['results'][t['task_code']]['pre'] > res['pre'] for o in liga['results'])
        full = f'<s>{res["pre"]:.1f}</s> ' if res['pre'] != res['score'] else ''
        rows.append(
            f'        <tr><td>{t["task_code"]}</td><td>{f"{place}." if res["pre"] else "–"}</td>'
            f'<td class="num pts">{full}{res["score"]:.1f} p.</td></tr>'
        )
    body = '\n'.join(rows)
    return f'''<section class="podium liga">
  <div class="head">
    <div><span class="place p{r["place"]}">{ROMAN[r["place"]]}</span></div>
    <div class="category">{category}</div>
    <div class="name">{escape(r["name"])}</div>
    <div class="glider">{escape(p["glider"])}</div>
    <div class="points">{r["points"]:.1f} <small>pont</small></div>
  </div>
  {photo(r["u"], escape(r["name"]), photos)}
      <div class="flights card">
        <table class="list">
          <thead><tr><th>Feladat</th><th>Helyezés</th><th class="num">Pont (FTV {liga["formula"]["validity_param"]:.0%})</th></tr></thead>
          <tbody>
    {body}
          </tbody>
        </table>
      </div>
</section>'''


def liga_records_slide(season, liga):
    # the 4 records of src/season_stats.json (our analysis of the liga IGCs), top 3 each
    def pilot(row):
        return liga_name(row['pilot'], season, liga)

    cards = []
    for rec in season['records']:
        key = list(rec['columns'])[2]
        title, unit, places, gain = LIGA_RECORDS[key]
        rows = '\n'.join(
            f'        <tr><td><span class="rank p{i}">{i}</span></td><td class="who"><b>{escape(pilot(r))}</b></td>'
            + (f'<td class="num gain">+{r["gain_m"]} m</td>' if gain else '')
            + f'<td class="num pts">{f"{r[key]:.{places}f}".replace(".", ",")} {unit}</td></tr>'
            for i, r in enumerate(rec['rows'], 1)
        )
        cards.append(f'''  <div class="card rec{" fragment" if cards else ""}">
    <h3>{title}</h3>
    <table class="list">
      <tbody>
{rows}
      </tbody>
    </table>
  </div>''')
    body = '\n'.join(cards)
    return f'''<section data-background-image="{LIGA_BG}" class="liga liga-records">
{body}
</section>'''

def liga_fun_slides(season, liga):
    # one slide per theme of LIGA_FUN, a card per award (the first shown with the slide, the others on
    # click): award name, then the pilot and the value highlighted
    awards = {a['award']: a for a in season['awards']}
    out = []
    for names in LIGA_FUN:
        cards = []
        for a in (awards[n] for n in names):
            who = escape(', '.join(liga_name(p, season, liga) for p in a['pilots']))
            cards.append(f'''    <div class="card fun{" fragment" if cards else ""}">
      <h3>{escape(a["award"])}</h3>
      <div class="who">{who}</div>
      <div class="value">{escape(a["value"])}</div>
    </div>''')
        body = '\n'.join(cards)
        out.append(f'''<section data-background-image="{LIGA_BG}" class="liga liga-fun">
  <div class="fun-grid">
{body}
  </div>
</section>''')
    return out


def liga_name(pilot, season, liga):
    # the slide name of a pilot of src/season_stats.json (by CIVL ID), else its name there
    by_civl = {p['civl_id']: p['ID'] for p in liga['results']}
    return LIGA_PILOTS.get(by_civl.get(season['civl_ids'].get(pilot)), (pilot,))[0]


def cover(title, count, cls=''):
    return f'<section class="cover{cls}">\n  <h1>{title}</h1>\n  <div class="count">{count}</div>\n</section>'


def name(r):
    return escape(HU.get(r.get('username'), r['name']))


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
