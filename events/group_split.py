from models import Night
from utils.distance import distance_meters


def detect_group_splits(
    night: Night,
    proximity_threshold_meters: float = 150,
):
    timestamps = sorted(
        set(location.timestamp for location in night.locations)
    )

    split_states = []

    for timestamp in timestamps:
        points = [
            location
            for location in night.locations
            if location.timestamp == timestamp
        ]

        if len(points) < 3:
            continue

        groups = []
        unassigned = points.copy()

        while unassigned:
            current = unassigned.pop(0)
            current_group = [current]

            changed = True

            while changed:
                changed = False

                for candidate in unassigned[:]:
                    is_close_to_group = any(
                        distance_meters(
                            candidate.latitude,
                            candidate.longitude,
                            member.latitude,
                            member.longitude,
                        )
                        <= proximity_threshold_meters
                        for member in current_group
                    )

                    if is_close_to_group:
                        current_group.append(candidate)
                        unassigned.remove(candidate)
                        changed = True

            groups.append(current_group)

        participant_groups = [
            [point.participant_id for point in group]
            for group in groups
        ]

        participant_groups.sort(
            key=len,
            reverse=True,
        )

        split_states.append(
            {
                "timestamp": timestamp,
                "groups": participant_groups,
            }
        )

    return split_states

def build_group_split_events(
    night: Night,
    proximity_threshold_meters: float = 150,
):
    states = detect_group_splits(
        night,
        proximity_threshold_meters,
    )

    events = []

    active_split = None

    for state in states:
        groups = state["groups"]

        is_split = len(groups) > 1

        if is_split and active_split is None:
            active_split = {
                "type": "group_split",
                "started_at": state["timestamp"],
                "initial_groups": groups,
            }

        elif not is_split and active_split is not None:
            ended_at = state["timestamp"]

            duration_minutes = int(
                (
                    ended_at
                    - active_split["started_at"]
                ).total_seconds()
                / 60
            )

            active_split["ended_at"] = ended_at
            active_split["duration_minutes"] = duration_minutes
            active_split["rejoined"] = True

            events.append(active_split)

            active_split = None

    if active_split is not None:
        active_split["ended_at"] = night.ended_at

        duration_minutes = int(
            (
                night.ended_at
                - active_split["started_at"]
            ).total_seconds()
            / 60
        )

        active_split["duration_minutes"] = duration_minutes
        active_split["rejoined"] = False

        events.append(active_split)

    return events