"""One replanning event, per the spec: urgent new ticket / cancelled ticket /
engineer becomes unavailable. Returns the new plan plus a diff of what
changed (assignments, order, newly unassigned).
"""
import copy


def apply_event(tickets, engineers, event):
    tickets = [copy.deepcopy(t) for t in tickets]
    engineers = [copy.deepcopy(e) for e in engineers]
    etype = event.get('type')
    note = ''
    if etype == 'new_urgent_ticket':
        t = event['ticket']
        t['priority'] = 'urgent'
        t.setdefault('arrival_order', max((x.arrival_order for x in tickets), default=-1) + 1)
        from .data_loader import make_ticket
        tickets.append(make_ticket(t))
        note = 'Добавлена срочная заявка {}'.format(t['id'])
    elif etype == 'cancel_ticket':
        tid = str(event['ticket_id'])
        tickets = [t for t in tickets if str(t.id) != tid]
        note = 'Отменена заявка {}'.format(tid)
    elif etype == 'engineer_unavailable':
        eid = event['engineer_id']
        engineers = [e for e in engineers if e.id != eid]
        note = 'Инженер {} недоступен'.format(eid)
    else:
        raise ValueError('unknown event type: {}'.format(etype))
    return tickets, engineers, note


def diff_plans(old, new):
    def amap(plan):
        return {tid: a['engineer_id'] for tid, a in plan['assignments'].items()}

    def order_map(plan):
        return {r['engineer_id']: [s['ticket_id'] for s in r['stops']]
                for r in plan['routes']}

    old_a, new_a = amap(old), amap(new)
    old_o, new_o = order_map(old), order_map(new)
    changed_engineer = {t for t in new_a if t in old_a and old_a[t] != new_a[t]}
    newly_assigned = {t for t in new_a if t not in old_a}
    newly_unassigned = {u['ticket']['id'] for u in new['unassigned']}
    order_changed = {e for e in new_o if old_o.get(e) and new_o[e] != old_o[e]}
    return {
        'newly_assigned': sorted(newly_assigned),
        'newly_unassigned': sorted(newly_unassigned),
        'changed_engineer': sorted(changed_engineer),
        'order_changed': sorted(order_changed),
        'engineers_used': {'before': old['metrics']['engineers_used'],
                           'after': new['metrics']['engineers_used']},
        'total_distance_km': {'before': old['metrics']['total_distance_km'],
                              'after': new['metrics']['total_distance_km']},
    }
