"""Data layer: loads the frozen processed CSVs (the week-1 contract).

Ticket / engineer objects are simple namespaces so the solver stays
framework-agnostic. `load_raw_region` additionally demonstrates reading the
original cp1251 CSVs directly (footer rows -> depots, junk rows dropped).
"""
import os
import pandas as pd
from types import SimpleNamespace

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'data', 'processed')


def make_ticket(row):
    return SimpleNamespace(
        id=str(row['id']), region=row['region'], type_bk=row['type_bk'],
        type_hd=row['type_hd'], required_skill=row['required_skill'],
        priority=row['priority'],
        window_start=int(row['window_start']), window_end=int(row['window_end']),
        duration_min=int(row['duration_min']), district=row['district'],
        address=row['address'], lat=float(row['lat']), lon=float(row['lon']),
        coord_approx=bool(row.get('coord_approx', True)),
        required_vehicle=(None if str(row.get('required_vehicle')) in ('', 'nan', 'None')
                          else row.get('required_vehicle')),
        gigabit=row.get('gigabit'), arrival_order=int(row['arrival_order']))


def make_engineer(row):
    return SimpleNamespace(
        id=row['id'], name=row['name'], home_district=row['home_district'],
        start_lat=float(row['start_lat']), start_lon=float(row['start_lon']),
        shift_start=int(row['shift_start']), shift_end=int(row['shift_end']),
        skills=row['skills'].split('|'), vehicle_type=row['vehicle_type'])


def load_tickets(path=None):
    df = pd.read_csv(path or os.path.join(DATA_DIR, 'tickets.csv'))
    return [make_ticket(r) for _, r in df.iterrows()]


def load_engineers(path=None):
    df = pd.read_csv(path or os.path.join(DATA_DIR, 'engineers.csv'))
    return [make_engineer(r) for _, r in df.iterrows()]


def load_depots():
    return pd.read_csv(os.path.join(DATA_DIR, 'depots.csv')).to_dict('records')


def load_raw_region(path, region):
    """Read an original synthetic cp1251 CSV. Footer 'Адрес офиса' row is
    returned as the depot; blank rows and misaligned rows are dropped."""
    df = pd.read_csv(path, sep=';', encoding='cp1251', dtype=str)
    office = df[df['Тип заявки BK'].astype(str).str.contains('офиса', case=False, na=False)]
    depot = None
    if len(office):
        depot = {'region': region, 'address': office.iloc[0]['Тип заявки BK']}
    df = df[df['Заявка'].astype(str).str.match(r'^\d+$', na=False)]
    return df, depot
