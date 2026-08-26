from models import Night
from utils.distance import distance_meters
from events.group_split import detect_group_splits


def get_cluster_center(samples):
    latitude = sum(
        sample["latitude"]
        for sample in samples
    ) / len(samples)

    longitude = sum(
        sample["longitude"]
        for sample in samples
    ) / len(samples)

    return {
        "latitude": latitude,
        "longitude": longitude,
    }


def get_main_group_center(
    night: Night,
    timestamp,
    participant_ids: list[str],
):
    points = [
        location
        for location in night.locations
        if (
            location.timestamp == timestamp
            and location.participant_id in participant_ids
        )
    ]

    if not points:
        return None

    latitude = sum(
        point.latitude
        for point in points
    ) / len(points)

    longitude = sum(
        point.longitude
        for point in points
    ) / len(points)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "participant_count": len(points),
    }


def build_group_location_samples(night: Night):
    group_states = detect_group_splits(night)

    samples = []

    for state in group_states:
        timestamp = state["timestamp"]

        if not state["groups"]:
            continue

        main_group = max(
            state["groups"],
            key=len,
        )

        center = get_main_group_center(
            night,
            timestamp,
            main_group,
        )

        if center is None:
            continue

        samples.append(
            {
                "timestamp": timestamp,
                "latitude": center["latitude"],
                "longitude": center["longitude"],
                "participant_count": center["participant_count"],
                "main_group": main_group,
            }
        )

    return samples


def create_cluster(
    samples,
    ended_at,
    minimum_duration_minutes: int,
):
    if not samples:
        return None

    started_at = samples[0]["timestamp"]

    duration_minutes = int(
        (
            ended_at - started_at
        ).total_seconds()
        / 60
    )

    if duration_minutes < minimum_duration_minutes:
        return None

    center = get_cluster_center(samples)

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_minutes": duration_minutes,
        "latitude": center["latitude"],
        "longitude": center["longitude"],
        "sample_count": len(samples),
    }


def build_location_clusters(
    night: Night,
    cluster_radius_meters: float = 150,
    minimum_duration_minutes: int = 15,
):
    samples = build_group_location_samples(night)

    if not samples:
        return []

    clusters = []

    current_samples = [samples[0]]

    for sample in samples[1:]:
        center = get_cluster_center(
            current_samples
        )

        distance = distance_meters(
            center["latitude"],
            center["longitude"],
            sample["latitude"],
            sample["longitude"],
        )

        if distance <= cluster_radius_meters:
            current_samples.append(sample)
            continue

        cluster = create_cluster(
            current_samples,
            sample["timestamp"],
            minimum_duration_minutes,
        )

        if cluster is not None:
            clusters.append(cluster)

        current_samples = [sample]

    final_cluster = create_cluster(
        current_samples,
        night.ended_at,
        minimum_duration_minutes,
    )

    if final_cluster is not None:
        clusters.append(final_cluster)

    return clusters