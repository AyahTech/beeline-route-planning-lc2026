#!/usr/bin/env python3
"""Raw -> processed data pipeline (run once, commit the output).

Reads the six original cp1251 CSVs from data/raw/ and produces the frozen
week-1 contract: tickets.csv, engineers.csv, depots.csv, coords.csv.

Geocoding: by default uses the bundled district-centroid table with a
deterministic per-address jitter (offline, no network). Pass --geocode to
run a one-time Nominatim pass for the addresses and cache the results
(normalisation: пр-кт.->проспект, ул.->улица, ...; district-centroid
fallback for anything unmatched; approximate points are flagged).
"""
import argparse
import hashlib
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'data', 'processed')
REGIONS = ['Восток', 'Юго-восток', 'Югоцентр']

DIST_COORDS = {  # approximate district centroids, lat/lon
 'Кашира': (54.839, 38.160), 'Ступино': (54.886, 38.078), 'Домодедово': (55.408, 37.554),
 'Таганский': (55.741, 37.653), 'Кузьминки': (55.700, 37.781), 'Текстильщики': (55.709, 37.732),
 'Лефортово': (55.763, 37.688), 'Нижегородский': (55.732, 37.729), 'Рязанский': (55.723, 37.771),
 'Выхино': (55.711, 37.822), 'Царицыно': (55.620, 37.669), 'Бирюлево Восточное': (55.595, 37.659),
 'Бирюлево Западное': (55.602, 37.646), 'Зябликово': (55.612, 37.601),
 'Орехово Борисово Северное': (55.612, 37.701), 'Орехово Борисово Южное': (55.600, 37.721),
 'Братеево': (55.632, 37.762), 'Москворечье - Сабурово': (55.632, 37.733),
 'Нагатинский Затон': (55.681, 37.705), 'Нагатино - Садовники': (55.680, 37.632),
 'Даниловский': (55.708, 37.651), 'Донской': (55.701, 37.601), 'Академический': (55.687, 37.573),
 'Зюзино': (55.662, 37.573), 'Котловка': (55.680, 37.601), 'Нагорный': (55.672, 37.612),
 'Гагаринский': (55.672, 37.553), 'Замоскворечье': (55.731, 37.624), 'Басманный': (55.769, 37.652),
 'Хамовники': (55.748, 37.592), 'Южнопортовый': (55.701, 37.681),
 'GPON Даниловский': (55.708, 37.651), 'Люберцы': (55.678, 37.892),
}

HD_SKILL = {'Авария': 'emergency',
 'Заказ подключения/Дозаказ оборудования': 'connection',
 'Заявка на подключение': 'connection', 'Конвергенция абонента': 'connection',
 'Дозаказ оборудования': 'connection', 'Переключение на Гбит/с': 'connection'}
HD_DUR = {'Авария': 90, 'Заказ подключения/Дозаказ оборудования': 120,
 'Заявка на подключение': 120, 'Конвергенция абонента': 90,
 'Дозаказ оборудования': 60, 'Переключение на Гбит/с': 60, 'Нет линка': 60,
 'Работа с кабелем': 90, 'Информация': 30, 'IP-адрес 169...': 45, 'Разрывы': 60,
 'Рост ошибок на порту': 45, 'Низкая скорость': 45,
 'Роутер. Замена техническим специалистом': 60,
 'TVE/ENT. Замена приставки техником': 45, 'ТВ. Замена приставки техником': 45,
 'TVE/ENT. Другие ошибки': 45, 'Мониторинг': 30}


def h01(s):
    return int(hashlib.md5(str(s).encode()).hexdigest()[:8], 16) / 2 ** 32


def jittered(district, seed):
    lat, lon = DIST_COORDS[district]
    return (round(lat + (h01(seed + 'a') - 0.5) * 0.018, 6),
            round(lon + (h01(seed + 'b') - 0.5) * 0.024, 6))


def norm_address(a):
    a = re.sub(r'^\s*Город Москва,\s*', '', str(a))
    for k, v in [('пр-кт.', 'проспект'), ('ул.', 'улица'), ('пер.', 'переулок'),
                 ('проезд.', 'проезд'), ('ш.', 'шоссе'), ('б-р', 'бульвар'),
                 ('пл.', 'площадь')]:
        a = a.replace(k, v)
    return a


def geocode_nominatim(addresses):
    import urllib.parse, urllib.request, json, time
    cache = {}
    for i, a in enumerate(addresses, 1):
        q = urllib.parse.urlencode({'street': norm_address(a),
                                    'city': 'Москва', 'country': 'Russia',
                                    'format': 'json', 'limit': 1})
        try:
            with urllib.request.urlopen(
                    'https://nominatim.openstreetmap.org/search?' + q,
                    headers={'User-Agent': 'beeline-route-planning-demo/1.0'},
                    timeout=10) as r:
                data = json.loads(r.read())
            if data:
                cache[a] = (float(data[0]['lat']), float(data[0]['lon']), False)
        except Exception:
            pass
        time.sleep(1.1)  # Nominatim usage policy
        print('geocoded %d/%d' % (i, len(addresses)), flush=True)
    return cache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--geocode', action='store_true',
                    help='run one-time Nominatim pass (needs network)')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    # ---- tickets from synthetic files ----
    rows, depots = [], []
    for r in REGIONS:
        df = pd.read_csv(os.path.join(RAW, '%s Синтетические данные.csv' % r),
                         sep=';', encoding='cp1251', dtype=str)
        office = df[df['Тип заявки BK'].astype(str).str.contains('офиса', case=False, na=False)]
        if len(office):
            depots.append({'region': r, 'address': office.iloc[0]['Тип заявки BK'],
                           'lat': None, 'lon': None})
        df = df[df['Заявка'].astype(str).str.match(r'^\d+$', na=False)].copy()
        df['region'] = r
        rows.append(df)
    t = pd.concat(rows, ignore_index=True)
    to_min = lambda s: pd.to_datetime(s, format='%d.%m.%Y %H:%M').dt.hour * 60 + \
        pd.to_datetime(s, format='%d.%m.%Y %H:%M').dt.minute
    t['window_start'] = to_min(t['Начало'])
    t['window_end'] = to_min(t['Окончание'])
    t['duration_min'] = t['Тип заявки HD'].map(HD_DUR).fillna(60).astype(int)
    t['required_skill'] = t['Тип заявки HD'].map(HD_SKILL).fillna('local')
    t['priority'] = np.where((t['Тип заявки BK'] == 'Глобальная проблема') |
                             (t['Тип заявки HD'] == 'Авария'), 'urgent', 'normal')

    # ---- coordinates ----
    geocoded = geocode_nominatim(sorted(t['Адрес'].unique())) if args.geocode else {}
    lats, lons, approx = [], [], []
    for _, x in t.iterrows():
        if x['Адрес'] in geocoded:
            la, lo, ap = geocoded[x['Адрес']]
        else:
            la, lo = jittered(x['Район'], x['Адрес'])
            ap = True
        lats.append(la); lons.append(lo); approx.append(ap)
    t['lat'], t['lon'], t['coord_approx'] = lats, lons, approx
    t['required_vehicle'] = None  # null in the data = 'no constraint' (README)

    tickets = t.rename(columns={'Заявка': 'id', 'Тип заявки BK': 'type_bk',
        'Тип заявки HD': 'type_hd', 'Район': 'district', 'Адрес': 'address',
        'Гигабитное подключение': 'gigabit'})[
        ['id', 'region', 'type_bk', 'type_hd', 'required_skill', 'priority',
         'window_start', 'window_end', 'duration_min', 'district', 'address',
         'lat', 'lon', 'coord_approx', 'required_vehicle', 'gigabit']]
    tickets = tickets.reset_index().rename(columns={'index': 'arrival_order'})
    tickets.to_csv(os.path.join(OUT, 'tickets.csv'), index=False, encoding='utf-8')

    # ---- engineers seeded from historical crew labels ----
    hist = []
    for r in REGIONS:
        f = os.path.join(RAW, '%s Контрольное распределение%s.csv' %
                         (r, '' if r == 'Юго-восток' else '.'))
        hist.append(pd.read_csv(f, sep=';', encoding='cp1251', dtype=str))
    hist = pd.concat(hist, ignore_index=True).dropna(subset=['Бригада']).copy()
    hist['skill'] = hist['Тип заявки HD'].map(HD_SKILL).fillna('local')
    eng_rows = []
    for i, name in enumerate(sorted(hist['Бригада'].unique())):
        h = hist[hist['Бригада'] == name]
        skills = sorted(set(h['skill']))
        if 'local' not in skills:
            skills.append('local')
        skills = skills[:3]
        dists = h['Район'].dropna().tolist()
        home = max(set(dists), key=dists.count) if dists else None
        slots = sorted(set(h['Начало'].dropna().str.extract(r'(\d+):')[0].astype(int)))
        ss_h = max(0, (min(slots) if slots else 10) - 2)
        se_h = min(24, (max(slots) if slots else 22) + 4)
        if se_h <= ss_h:
            se_h = min(24, ss_h + 12)
        outer = {'Кашира', 'Ступино', 'Домодедово', 'Люберцы'}
        central = {'Таганский', 'Басманный', 'Хамовники', 'Замоскворечье', 'Даниловский'}
        if home in outer:
            veh = 'car'
        elif home in central:
            veh = ['pedestrian', 'bicycle', 'public transport'][int(h01(name) * 3) % 3]
        else:
            veh = 'car' if h01(name + 'v') < 0.7 else \
                ['bicycle', 'public transport'][int(h01(name) * 2) % 2]
        la, lo = jittered(home, name) if home in DIST_COORDS else jittered('Даниловский', name)
        eng_rows.append(dict(id='ENG-%02d' % (i + 1), name=name, home_district=home,
            start_lat=la, start_lon=lo, shift_start=ss_h * 60, shift_end=se_h * 60,
            skills='|'.join(skills), vehicle_type=veh))
    pd.DataFrame(eng_rows).to_csv(os.path.join(OUT, 'engineers.csv'),
                                  index=False, encoding='utf-8')

    pd.DataFrame(depots).to_csv(os.path.join(OUT, 'depots.csv'),
                                index=False, encoding='utf-8')
    tickets[['address', 'district', 'lat', 'lon']].drop_duplicates('address').to_csv(
        os.path.join(OUT, 'coords.csv'), index=False, encoding='utf-8')
    print('tickets: %d, engineers: %d, coords: %d' %
          (len(tickets), len(eng_rows), tickets['address'].nunique()))


if __name__ == '__main__':
    sys.exit(main())
