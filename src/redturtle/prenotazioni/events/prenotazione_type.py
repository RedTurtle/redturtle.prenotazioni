from redturtle.prenotazioni.content.prenotazione_type import (
    get_time_range_duration_minutes,
)


def update_duration_from_time_range(obj, event):
    """Keep duration aligned with start/end time when both are provided."""
    start_time = getattr(obj, "start_time", None)
    end_time = getattr(obj, "end_time", None)

    if not start_time or not end_time:
        return

    duration_minutes = get_time_range_duration_minutes(start_time, end_time)
    computed_duration = str(duration_minutes)
    if getattr(obj, "duration", None) != computed_duration:
        obj.duration = computed_duration
