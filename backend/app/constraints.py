"""The three mandatory constraint groups, as one testable function.

Qualification: ticket.required_skill must be in engineer.skills.
Time:         the ticket window must fit inside the engineer's shift.
Resource:     if the ticket names a vehicle type, the engineer must have it.

`engineer_can_take` returns WHICH constraint failed - this feeds the
explanation feature for free.
"""
SKILL_LABELS = {
    'local': 'локальные работы',
    'connection': 'подключение и дозаказы',
    'emergency': 'аварийные работы',
}
VEHICLE_LABELS = {
    'car': 'автомобиль',
    'pedestrian': 'пешком',
    'bicycle': 'велосипед',
    'public transport': 'общественный транспорт',
}


def engineer_can_take(engineer, ticket):
    """Return (ok, failed_constraint, human_readable_reason)."""
    if ticket.required_skill not in engineer.skills:
        return False, 'skill', (
            'нет навыка «{}» (у инженера: {})'.format(
                SKILL_LABELS.get(ticket.required_skill, ticket.required_skill),
                ', '.join(SKILL_LABELS.get(s, s) for s in engineer.skills)))
    if ticket.required_vehicle and ticket.required_vehicle != engineer.vehicle_type:
        return False, 'vehicle', (
            'нужен транспорт «{}», у инженера — «{}»'.format(
                VEHICLE_LABELS.get(ticket.required_vehicle, ticket.required_vehicle),
                VEHICLE_LABELS.get(engineer.vehicle_type, engineer.vehicle_type)))
    if ticket.window_start < engineer.shift_start or ticket.window_end > engineer.shift_end:
        return False, 'time', (
            'окно заявки {:02d}:{:02d}–{:02d}:{:02d} не входит в смену {:02d}:{:02d}–{:02d}:{:02d}'.format(
                ticket.window_start // 60, ticket.window_start % 60,
                ticket.window_end // 60, ticket.window_end % 60,
                engineer.shift_start // 60, engineer.shift_start % 60,
                engineer.shift_end // 60, engineer.shift_end % 60))
    return True, None, None
