"""Rule-based plain-language explanations (deterministic templates, no LLM).

Every ticket gets: why this engineer, which constraints applied.
Every unassigned ticket gets an explicit reason.
"""
from collections import Counter
from .constraints import SKILL_LABELS, VEHICLE_LABELS


def _hm(mins):
    return '{:02d}:{:02d}'.format(int(mins) // 60, int(mins) % 60)


def explain_assignment(engineer, ticket):
    parts = [
        'Назначен на «{}»:'.format(engineer.name),
        'навык «{}» удовлетворён'.format(
            SKILL_LABELS.get(ticket.required_skill, ticket.required_skill)),
        'окно {}–{} входит в смену {}–{}'.format(
            _hm(ticket.window_start), _hm(ticket.window_end),
            _hm(engineer.shift_start), _hm(engineer.shift_end)),
    ]
    if ticket.required_vehicle:
        parts.append('транспорт «{}» совпадает'.format(
            VEHICLE_LABELS.get(ticket.required_vehicle, ticket.required_vehicle)))
    if ticket.priority == 'urgent':
        parts.append('заявка срочная — обработана в первую очередь')
    return '; '.join(parts) + '.'


def explain_unassigned(ticket, attempts):
    if not attempts:
        return ('Заявка не назначена: ни один инженер не может взять её '
                '(нет подходящего навыка/транспорта или окно вне всех смен).')
    counts = Counter(attempts.values())
    top = counts.most_common(3)
    detail = '; '.join('{} — {} инж.'.format(reason, n) for reason, n in top)
    return ('Заявка не назначена. Причины по инженерам: ' + detail + '.')


def explain_route_order(engineer, stops):
    seq = ' → '.join('#{} ({:02d}:{:02d})'.format(
        s['seq'], int(s['start_min']) // 60, int(s['start_min']) % 60) for s in stops)
    return ('Порядок обхода для {}: {} — маршрут выстроен по временным окнам '
            'заявок от точки старта (возврат не требуется).').format(
        engineer.name, seq)
