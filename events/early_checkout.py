from models import Night
from utils.participant_lifecycle import build_participant_lifecycles


def detect_early_checkout(
    night: Night,
    minimum_minutes_before_end: int = 30,
):
    lifecycles = build_participant_lifecycles(night)

    observations = []

    for lifecycle in lifecycles:
        if lifecycle["left_night_at"] is None:
            continue

        if (
            lifecycle["minutes_before_end"]
            < minimum_minutes_before_end
        ):
            continue

        observations.append(
            {
                "type": "early_checkout",
                "participant_id": lifecycle["participant_id"],
                "name": lifecycle["name"],
                "left_at": lifecycle["left_night_at"],
                "minutes_before_end": lifecycle["minutes_before_end"],
                "text": (
                    f"{lifecycle['name']} called it a Night "
                    f"{lifecycle['minutes_before_end']} minutes "
                    f"before the end."
                ),
            }
        )

    return observations