from models import Night
from events.group_split import build_group_split_events


def detect_reunions(night: Night):
    split_events = build_group_split_events(night)

    observations = []

    for split in split_events:
        if not split["rejoined"]:
            continue

        observations.append(
            {
                "type": "reunion",
                "rejoined_at": split["ended_at"],
                "duration_minutes": split["duration_minutes"],
                "groups_before_reunion": split["initial_groups"],
                "text": (
                    f"The group reunited after "
                    f"{split['duration_minutes']} minutes apart."
                ),
            }
        )

    return observations