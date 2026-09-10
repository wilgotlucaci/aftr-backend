from models import LocationPoint
from utils.distance import distance_meters


def classify_movement(
    current: LocationPoint,
    next_location: LocationPoint,
) -> str:
    seconds = (
        next_location.timestamp
        - current.timestamp
    ).total_seconds()

    if seconds <= 0:
        return "unknown"

    distance = distance_meters(
        current.latitude,
        current.longitude,
        next_location.latitude,
        next_location.longitude,
    )

    calculated_speed = distance / seconds

    reported_speed = current.speed

    if reported_speed is None:
        speed = calculated_speed
    else:
        speed = max(
            reported_speed,
            calculated_speed,
        )

    if distance < 15 and speed < 0.5:
        return "stationary"

    if speed < 3:
        return "walking"

    if speed < 10:
        return "fast_movement"

    return "vehicle"


def build_movement_stats(
    locations: list[LocationPoint],
) -> dict:
    if len(locations) < 2:
        return {
            "stationary_minutes": 0,
            "walking_minutes": 0,
            "fast_movement_minutes": 0,
            "vehicle_minutes": 0,
            "unknown_minutes": 0,
        }

    totals = {
        "stationary": 0.0,
        "walking": 0.0,
        "fast_movement": 0.0,
        "vehicle": 0.0,
        "unknown": 0.0,
    }

    sorted_locations = sorted(
        locations,
        key=lambda location: location.timestamp,
    )

    for index in range(
        len(sorted_locations) - 1
    ):
        current = sorted_locations[index]
        next_location = sorted_locations[index + 1]

        seconds = (
            next_location.timestamp
            - current.timestamp
        ).total_seconds()

        if seconds <= 0:
            continue

        movement_type = classify_movement(
            current,
            next_location,
        )

        totals[movement_type] += seconds

    return {
        "stationary_minutes": round(
            totals["stationary"] / 60,
            1,
        ),
        "walking_minutes": round(
            totals["walking"] / 60,
            1,
        ),
        "fast_movement_minutes": round(
            totals["fast_movement"] / 60,
            1,
        ),
        "vehicle_minutes": round(
            totals["vehicle"] / 60,
            1,
        ),
        "unknown_minutes": round(
            totals["unknown"] / 60,
            1,
        ),
    }