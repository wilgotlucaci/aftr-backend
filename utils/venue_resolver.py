import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from models import Night
from utils.distance import distance_meters


load_dotenv()


GOOGLE_PLACES_URL = (
    "https://places.googleapis.com/v1/places:searchNearby"
)


NIGHTLIFE_TYPES = {
    "night_club",
    "bar",
    "pub",
    "cocktail_bar",
}

FOOD_TYPES = {
    "restaurant",
    "food",
    "meal_takeaway",
    "fast_food_restaurant",
    "cafe",
}

LOW_RELEVANCE_TYPES = {
    "service",
    "real_estate_agency",
    "insurance_agency",
    "accounting",
    "lawyer",
    "bank",
    "car_repair",
}


def resolve_personal_location(
    night: Night,
    cluster: dict,
):
    matches = []

    for personal_location in night.personal_locations:
        distance = distance_meters(
            cluster["latitude"],
            cluster["longitude"],
            personal_location.latitude,
            personal_location.longitude,
        )

        if distance > personal_location.radius_meters:
            continue

        matches.append(
            {
                "venue_id": personal_location.id,
                "venue_name": personal_location.name,
                "category": "personal_location",
                "types": ["personal_location"],
                "latitude": personal_location.latitude,
                "longitude": personal_location.longitude,
                "distance_meters": round(distance),
                "source": "personal_location",
                "confidence": "high",
                "score": {
                    "total": 999.0,
                    "distance": 0.0,
                    "category": 0.0,
                    "duration": 0.0,
                    "time": 0.0,
                },
            }
        )

    if not matches:
        return None

    matches.sort(
        key=lambda location: location["distance_meters"]
    )

    return matches[0]


def get_time_score(
    category: str | None,
    timestamp: datetime,
):
    if category is None:
        return 0.0

    hour = timestamp.hour

    if category in NIGHTLIFE_TYPES:
        if hour >= 22 or hour <= 4:
            return 30.0

        if hour >= 18:
            return 15.0

    if category in FOOD_TYPES:
        if 17 <= hour <= 23:
            return 20.0

        if hour <= 4:
            return 15.0

    return 0.0


def get_duration_score(
    category: str | None,
    duration_minutes: int,
):
    if category is None:
        return 0.0

    if category in NIGHTLIFE_TYPES:
        if duration_minutes >= 60:
            return 25.0

        if duration_minutes >= 30:
            return 15.0

    if category in FOOD_TYPES:
        if 30 <= duration_minutes <= 150:
            return 20.0

    return 0.0


def get_category_score(
    category: str | None,
    types: list[str],
):
    score = 0.0

    if category in NIGHTLIFE_TYPES:
        score += 40.0

    elif category in FOOD_TYPES:
        score += 30.0

    if any(
        place_type in NIGHTLIFE_TYPES
        for place_type in types
    ):
        score += 10.0

    if any(
        place_type in FOOD_TYPES
        for place_type in types
    ):
        score += 5.0

    if category in LOW_RELEVANCE_TYPES:
        score -= 50.0

    return score


def get_distance_score(
    distance_meters_value: float,
):
    if distance_meters_value <= 10:
        return 40.0

    if distance_meters_value <= 25:
        return 35.0

    if distance_meters_value <= 50:
        return 25.0

    if distance_meters_value <= 75:
        return 15.0

    if distance_meters_value <= 100:
        return 5.0

    return 0.0


def calculate_venue_score(
    cluster: dict,
    candidate: dict,
):
    distance_score = get_distance_score(
        candidate["distance_meters"]
    )

    category_score = get_category_score(
        candidate["category"],
        candidate["types"],
    )

    duration_score = get_duration_score(
        candidate["category"],
        cluster["duration_minutes"],
    )

    time_score = get_time_score(
        candidate["category"],
        cluster["started_at"],
    )

    total_score = (
        distance_score
        + category_score
        + duration_score
        + time_score
    )

    return {
        "total": round(total_score, 1),
        "distance": round(distance_score, 1),
        "category": round(category_score, 1),
        "duration": round(duration_score, 1),
        "time": round(time_score, 1),
    }


def calculate_confidence(
    best_score: float,
    second_best_score: float | None,
):
    if second_best_score is None:
        margin = best_score
    else:
        margin = best_score - second_best_score

    if best_score >= 90 and margin >= 20:
        return "high"

    if best_score >= 60 and margin >= 10:
        return "medium"

    return "low"


def get_google_candidates(
    cluster: dict,
    search_radius_meters: float = 100,
):
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_PLACES_API_KEY is missing from .env"
        )

    body = {
        "maxResultCount": 10,
        "rankPreference": "DISTANCE",
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": cluster["latitude"],
                    "longitude": cluster["longitude"],
                },
                "radius": search_radius_meters,
            }
        },
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.primaryType,"
            "places.types,"
            "places.location"
        ),
    }

    response = requests.post(
        GOOGLE_PLACES_URL,
        json=body,
        headers=headers,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    candidates = []

    for place in data.get("places", []):
        location = place.get("location", {})

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if latitude is None or longitude is None:
            continue

        distance = distance_meters(
            cluster["latitude"],
            cluster["longitude"],
            latitude,
            longitude,
        )

        candidate = {
            "venue_id": place.get("id"),
            "venue_name": place.get(
                "displayName",
                {},
            ).get(
                "text",
                "Unknown place",
            ),
            "category": place.get("primaryType"),
            "types": place.get("types", []),
            "latitude": latitude,
            "longitude": longitude,
            "distance_meters": round(distance),
            "source": "google_places",
        }

        candidate["score"] = calculate_venue_score(
            cluster,
            candidate,
        )

        candidates.append(candidate)

    candidates.sort(
        key=lambda candidate: candidate["score"]["total"],
        reverse=True,
    )

    return candidates


def resolve_cluster_with_google(
    cluster: dict,
    search_radius_meters: float = 100,
):
    candidates = get_google_candidates(
        cluster,
        search_radius_meters,
    )

    if not candidates:
        return None

    best = candidates[0]

    second_best_score = None

    if len(candidates) > 1:
        second_best_score = candidates[1]["score"]["total"]

    best["confidence"] = calculate_confidence(
        best["score"]["total"],
        second_best_score,
    )

    if best["confidence"] == "low":
        return None

    return best


def resolve_cluster(
    night: Night,
    cluster: dict,
):
    personal_location = resolve_personal_location(
        night,
        cluster,
    )

    if personal_location is not None:
        return personal_location

    return resolve_cluster_with_google(cluster)


def resolve_location_clusters(
    night: Night,
    clusters: list[dict],
):
    resolved = []

    for cluster in clusters:
        venue = resolve_cluster(
            night,
            cluster,
        )

        resolved.append(
            {
                **cluster,
                "venue": venue,
            }
        )

    return resolved