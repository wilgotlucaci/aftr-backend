from itertools import combinations

from models import Night
from utils.distance import distance_meters


def get_locations_at_time(night: Night, timestamp):
    return [
        location
        for location in night.locations
        if location.timestamp == timestamp
    ]


def are_together(
    point_a,
    point_b,
    proximity_threshold_meters: float,
) -> bool:
    distance = distance_meters(
        point_a.latitude,
        point_a.longitude,
        point_b.latitude,
        point_b.longitude,
    )

    return distance <= proximity_threshold_meters


def calculate_proximity_stats(
    night: Night,
    proximity_threshold_meters: float = 100,
):
    timestamps = sorted(
        set(location.timestamp for location in night.locations)
    )

    participant_ids = [
        participant.id
        for participant in night.participants
    ]

    results = []

    for person_a, person_b in combinations(participant_ids, 2):
        together_seconds = 0.0
        apart_seconds = 0.0

        current_together_streak = 0.0
        current_apart_streak = 0.0

        longest_together_seconds = 0.0
        longest_apart_seconds = 0.0

        for index in range(len(timestamps) - 1):
            current_time = timestamps[index]
            next_time = timestamps[index + 1]

            points = get_locations_at_time(
                night,
                current_time,
            )

            points_by_person = {
                point.participant_id: point
                for point in points
            }

            if (
                person_a not in points_by_person
                or person_b not in points_by_person
            ):
                continue

            point_a = points_by_person[person_a]
            point_b = points_by_person[person_b]

            interval_seconds = (
                next_time - current_time
            ).total_seconds()

            together = are_together(
                point_a,
                point_b,
                proximity_threshold_meters,
            )

            if together:
                together_seconds += interval_seconds

                current_together_streak += interval_seconds
                current_apart_streak = 0

                longest_together_seconds = max(
                    longest_together_seconds,
                    current_together_streak,
                )

            else:
                apart_seconds += interval_seconds

                current_apart_streak += interval_seconds
                current_together_streak = 0

                longest_apart_seconds = max(
                    longest_apart_seconds,
                    current_apart_streak,
                )

        total_seconds = together_seconds + apart_seconds

        if total_seconds == 0:
            continue

        together_percentage = (
            together_seconds / total_seconds
        ) * 100

        results.append(
            {
                "person_a": person_a,
                "person_b": person_b,
                "together_minutes": round(
                    together_seconds / 60
                ),
                "apart_minutes": round(
                    apart_seconds / 60
                ),
                "together_percentage": round(
                    together_percentage,
                    1,
                ),
                "longest_together_minutes": round(
                    longest_together_seconds / 60
                ),
                "longest_apart_minutes": round(
                    longest_apart_seconds / 60
                ),
            }
        )

    return results