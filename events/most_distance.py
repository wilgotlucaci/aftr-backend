from collections import defaultdict

from models import Night
from utils.distance import distance_meters
from utils.participant_lifecycle import build_participant_lifecycles


def detect_most_distance(night: Night):
    # Only count movement while a participant is still part of the Night -
    # the walk (or drive) home after they've split off doesn't count.
    lifecycles = build_participant_lifecycles(night)

    # (start, end, end_is_exclusive) per participant. A participant who
    # split off has an exclusive end at that moment, so the first "I'm
    # home now" ping - and the long jump to it - is dropped.
    window = {}
    for lifecycle in lifecycles:
        if lifecycle["left_night_at"] is not None:
            window[lifecycle["participant_id"]] = (
                lifecycle["joined_at"],
                lifecycle["left_night_at"],
                True,
            )
        else:
            window[lifecycle["participant_id"]] = (
                lifecycle["joined_at"],
                night.ended_at,
                False,
            )

    participant_locations = defaultdict(list)

    for location in night.locations:
        bounds = window.get(location.participant_id)

        if bounds is not None:
            start, end, end_is_exclusive = bounds
            if location.timestamp < start:
                continue
            if end is not None:
                if end_is_exclusive and location.timestamp >= end:
                    continue
                if not end_is_exclusive and location.timestamp > end:
                    continue

        participant_locations[location.participant_id].append(location)

    distances = {}

    for participant_id, locations in participant_locations.items():
        sorted_locations = sorted(
            locations,
            key=lambda location: location.timestamp,
        )

        total_distance = 0.0

        for index in range(len(sorted_locations) - 1):
            current = sorted_locations[index]
            next_location = sorted_locations[index + 1]

            total_distance += distance_meters(
                current.latitude,
                current.longitude,
                next_location.latitude,
                next_location.longitude,
            )

        distances[participant_id] = total_distance

    if not distances:
        return None

    participant_id = max(
        distances,
        key=distances.get,
    )

    participant = next(
        (
            participant
            for participant in night.participants
            if participant.id == participant_id
        ),
        None,
    )

    if participant is None:
        return None

    return {
        "type": "most_distance",
        "participant_id": participant.id,
        "participant_name": participant.name,
        "distance_meters": round(
            distances[participant_id],
            1,
        ),
        "distance_km": round(
            distances[participant_id] / 1000,
            2,
        ),
    }
