from models import Night
from utils.distance import distance_meters


def detect_group_separations(
    night: Night,
    separation_threshold_meters: float = 150,
):
    timestamps = sorted(
        set(location.timestamp for location in night.locations)
    )

    observations = []

    for timestamp in timestamps:
        points = [
            location
            for location in night.locations
            if location.timestamp == timestamp
        ]

        if len(points) < 3:
            continue

        for person in points:
            close_neighbors = 0

            for other in points:
                if other.participant_id == person.participant_id:
                    continue

                distance = distance_meters(
                    person.latitude,
                    person.longitude,
                    other.latitude,
                    other.longitude,
                )

                if distance <= separation_threshold_meters:
                    close_neighbors += 1

            if close_neighbors == 0:
                observations.append(
                    {
                        "participant_id": person.participant_id,
                        "timestamp": timestamp,
                        "status": "separated",
                    }
                )

    return observations