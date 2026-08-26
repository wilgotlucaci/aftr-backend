from models import Night
from utils.participant_lifecycle import build_participant_lifecycles


def detect_late_arrivals(
    night: Night,
    minimum_minutes_late: int = 30,
):
    lifecycles = build_participant_lifecycles(night)

    observations = []

    for lifecycle in lifecycles:
        if lifecycle["minutes_after_start"] < minimum_minutes_late:
            continue

        observations.append(
            {
                "type": "late_arrival",
                "participant_id": lifecycle["participant_id"],
                "name": lifecycle["name"],
                "arrived_at": lifecycle["joined_at"],
                "minutes_late": lifecycle["minutes_after_start"],
                "text": (
                    f"{lifecycle['name']} joined the Night "
                    f"{lifecycle['minutes_after_start']} minutes late."
                ),
            }
        )

    return observations