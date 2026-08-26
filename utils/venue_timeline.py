from models import Night

from utils.location_clusters import build_location_clusters
from utils.venue_resolver import resolve_location_clusters


def build_venue_timeline(night: Night):
    clusters = build_location_clusters(night)

    resolved_clusters = resolve_location_clusters(
        night,
        clusters,
)
    timeline = []

    for item in resolved_clusters:
        venue = item["venue"]

        if venue is None:
            timeline.append(
                {
                    "venue_id": None,
                    "venue_name": "Unknown location",
                    "category": None,
                    "arrived_at": item["started_at"],
                    "left_at": item["ended_at"],
                    "duration_minutes": item["duration_minutes"],
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "confidence": "low",
                }
            )

            continue

        timeline.append(
            {
                "venue_id": venue["venue_id"],
                "venue_name": venue["venue_name"],
                "category": venue["category"],
                "arrived_at": item["started_at"],
                "left_at": item["ended_at"],
                "duration_minutes": item["duration_minutes"],
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "distance_meters": venue["distance_meters"],
                "score": venue["score"]["total"],
                "confidence": venue["confidence"],
            }
        )

    return timeline