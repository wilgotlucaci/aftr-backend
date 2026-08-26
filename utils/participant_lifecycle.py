from models import Night
from events.group_split import build_group_split_events


def build_participant_lifecycles(night: Night):
    split_events = build_group_split_events(night)

    lifecycles = []

    for participant in night.participants:
        participant_locations = sorted(
            [
                location
                for location in night.locations
                if location.participant_id == participant.id
            ],
            key=lambda location: location.timestamp,
        )

        if not participant_locations:
            continue

        first_seen = participant_locations[0].timestamp
        last_location_at = participant_locations[-1].timestamp

        joined_at = first_seen
        left_night_at = None

        for split in split_events:
            if split["rejoined"]:
                continue

            groups = split["initial_groups"]

            if len(groups) != 2:
                continue

            smaller_group = min(groups, key=len)

            if (
                len(smaller_group) == 1
                and smaller_group[0] == participant.id
            ):
                left_night_at = split["started_at"]

        effective_end = (
            left_night_at
            if left_night_at is not None
            else night.ended_at
        )

        minutes_after_start = int(
            (
                joined_at - night.started_at
            ).total_seconds()
            / 60
        )

        minutes_before_end = int(
            (
                night.ended_at - effective_end
            ).total_seconds()
            / 60
        )

        active_minutes = int(
            (
                effective_end - joined_at
            ).total_seconds()
            / 60
        )

        lifecycles.append(
            {
                "participant_id": participant.id,
                "name": participant.name,
                "joined_at": joined_at,
                "last_location_at": last_location_at,
                "left_night_at": left_night_at,
                "minutes_after_start": max(
                    minutes_after_start,
                    0,
                ),
                "minutes_before_end": max(
                    minutes_before_end,
                    0,
                ),
                "active_minutes": max(
                    active_minutes,
                    0,
                ),
            }
        )

    return lifecycles