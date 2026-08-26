from models import Night
from events.houdini import detect_houdini
from utils.distance import distance_meters


def calculate_path_distance(locations):
    total_distance = 0.0

    for index in range(1, len(locations)):
        previous = locations[index - 1]
        current = locations[index]

        total_distance += distance_meters(
            previous.latitude,
            previous.longitude,
            current.latitude,
            current.longitude,
        )

    return total_distance


def detect_side_quest(
    night: Night,
    minimum_distance_meters: float = 500,
):
    houdini_events = detect_houdini(night)

    observations = []

    for event in houdini_events:
        participant_locations = sorted(
            [
                location
                for location in night.locations
                if location.participant_id == event["participant_id"]
                and event["left_at"] <= location.timestamp <= event["rejoined_at"]
            ],
            key=lambda location: location.timestamp,
        )

        distance = calculate_path_distance(participant_locations)

        if distance < minimum_distance_meters:
            continue

        observations.append(
            {
                "type": "side_quest",
                "participant_id": event["participant_id"],
                "name": event["name"],
                "duration_minutes": event["duration_minutes"],
                "distance_meters": round(distance),
                "distance_km": round(distance / 1000, 1),
                "text": (
                    f"{event['name']} went on a "
                    f"{round(distance / 1000, 1)} km side quest "
                    f"for {event['duration_minutes']} minutes."
                ),
            }
        )

    return observations