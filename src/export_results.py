# Writes results.json: the MKK rankings from our own flight validation. Not runnable here: it needs
# the private validation repo (xcontest-hun-validate, its lib/ and data). Run it from that repo's
# src/ and copy the output over src/results.json:
#   uv run python /path/to/mkk-dijatado-2026/src/export_results.py > /path/to/mkk-dijatado-2026/src/results.json
# (a "podium check" line printed before the JSON has to be removed)
import json

from lib.scoring import CLASSES, KMK, free_distance, load_flight_jsons, load_pilot_items, load_pilots, local_date, places, rankings
from lib.xcontest import load_flights

TOP = 10


def main():
    ranks = rankings({f['id']: f['status'] for f in load_flights()})
    jsons = {f['id']: f for f in load_flight_jsons()}
    items = {p['id']: p for p in load_pilot_items()}
    pilots = load_pilots()

    def flight(fid, kmk=False):
        j = jsons[fid]
        route = j['league']['route']
        return {
            'date': local_date(j).isoformat(),
            'takeoff': j['takeoff']['name'] if j.get('takeoff') else '',
            'type': route['type'],
            'km': round(free_distance(j) if kmk else route['distance'], 2),
            'points': round(route['points'], 2),
            'glider': j['glider']['name'],
            'link': j['league']['flight']['link'],
        }

    def pilot(e):
        return {'name': e['name'], 'username': items[e['id']]['username'], 'club': pilots[e['id']]['club'] or ''}

    out = {'classes': {}, 'clubs': [], 'kmk': {}}
    for item, (name, _) in CLASSES.items():
        if item == 'fai5':  # not in the rules
            continue
        rows = [
            {'place': p} | pilot(e) | {'points': round(e['points'], 2), 'flights': [flight(x) for x in e['flights']]}
            for p, e in list(zip(places(ranks[item]), ranks[item]))[:TOP]
        ]
        out['classes'][item] = {'name': name, 'count': len(ranks[item]), 'rows': rows}

    open_entries = {e['id']: e for e in ranks['open']}
    for p, e in list(zip(places(ranks['clubs']), ranks['clubs']))[:TOP]:
        members = [
            {'name': open_entries[x]['name'], 'username': items[x]['username'], 'points': round(open_entries[x]['points'], 2)}
            for x in e['flights']
        ]
        out['clubs'].append({'place': p, 'name': e['name'], 'points': e['points'], 'members': members})

    for item in KMK:
        rows = []
        for p, e in list(zip(places(ranks[item]), ranks[item]))[:TOP]:
            fids = sorted(e['flights'], key=lambda x: -free_distance(jsons[x]))
            rows.append(
                {'place': p} | pilot(e)
                | {'count': e['points'], 'longest': round(e['tiebreak'] * 1000, 2), 'flights': [flight(x, True) for x in fids]}
            )
        out['kmk'][item] = rows

    print(json.dumps(out, ensure_ascii=False, indent=1))


main()
