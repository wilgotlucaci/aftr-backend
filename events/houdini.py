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


def detect_houdini(
    night: Night,
    minimum_duration_minutes: int = 20,
):
    split_events = build_group_split_events(night)

    observations = []

    for split in split_events:
        if not split["rejoined"]:
            continue

        if split["duration_minutes"] < minimum_duration_minutes:
            continue

        groups = split["initial_groups"]

        if len(groups) != 2:
            continue

        main_group = max(groups, key=len)
        smaller_group = min(groups, key=len)

        if len(smaller_group) != 1:
            continue

        participant_id = smaller_group[0]

        name = get_participant_name(
            night,
            participant_id,
        )

        observations.append(
            {
                "type": "houdini",
                "participant_id": participant_id,
                "name": name,
                "left_at": split["started_at"],
                "rejoined_at": split["ended_at"],
                "duration_minutes": split["duration_minutes"],
                "main_group": main_group,
                "text": (
                    f"{name} disappeared for "
                    f"{split['duration_minutes']} minutes."
                ),
            }
        )

    return observations