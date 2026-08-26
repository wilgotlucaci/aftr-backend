from models import Night
from events.group_split import build_group_split_events


def get_participant_name(
    night: Night,
    participant_id: str,
) -> str:
    for participant in night.participants:
        if participant.id == participant_id:
            return participant.name

    return participant_id


def detect_most_independent(
    night: Night,
    minimum_apart_minutes: int = 20,
):
    split_events = build_group_split_events(night)

    solo_separations = {}

    for split in split_events:
        if not split["rejoined"]:
            continue

        groups = split["initial_groups"]

        if len(groups) != 2:
            continue

        smaller_group = min(groups, key=len)

        if len(smaller_group) != 1:
            continue

        participant_id = smaller_group[0]

        if participant_id not in solo_separations:
            solo_separations[participant_id] = 0

        solo_separations[participant_id] += split["duration_minutes"]

    if not solo_separations:
        return []

    participant_id = max(
        solo_separations,
        key=solo_separations.get,
    )

    total_apart_minutes = solo_separations[participant_id]

    if total_apart_minutes < minimum_apart_minutes:
        return []

    name = get_participant_name(
        night,
        participant_id,
    )

    return [
        {
            "type": "most_independent",
            "participant_id": participant_id,
            "name": name,
            "solo_minutes": total_apart_minutes,
            "text": (
                f"{name} spent the most time away from "
                f"the group and still came back."
            ),
        }
    ]