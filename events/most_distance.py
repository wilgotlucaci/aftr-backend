from collections import defaultdict

from models import Night
from utils.distance import distance_meters


def detect_most_distance(night: Night):
    participant_locations = defaultdict(list)

    for location in night.locations:
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

            distance = distance_meters(
                current.latitude,
                current.longitude,
                next_location.latitude,
                next_location.longitude,
            )

            total_distance += distance

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