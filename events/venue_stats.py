from models import Night
from utils.venue_timeline import build_venue_timeline


NIGHTLIFE_TYPES = {
    "night_club",
    "bar",
    "pub",
    "cocktail_bar",
}


FOOD_TYPES = {
    "restaurant",
    "food",
    "fast_food_restaurant",
    "hamburger_restaurant",
    "cafe",
}


def build_venue_stats(night: Night):
    timeline = build_venue_timeline(night)

    known_stops = [
        stop
        for stop in timeline
        if stop["venue_id"] is not None
    ]

    if not known_stops:
        return {}

    longest_stop = max(
        known_stops,
        key=lambda stop: stop["duration_minutes"],
    )

    first_stop = known_stops[0]
    last_stop = known_stops[-1]

    nightlife_minutes = sum(
        stop["duration_minutes"]
        for stop in known_stops
        if stop["category"] in NIGHTLIFE_TYPES
    )

    food_minutes = sum(
        stop["duration_minutes"]
        for stop in known_stops
        if stop["category"] in FOOD_TYPES
    )

    return {
        "type": "venue_stats",
        # total_places is what the iOS client reads; places_visited kept
        # for any existing callers.
        "total_places": len(known_stops),
        "places_visited": len(known_stops),
        "first_venue": {
            "name": first_stop["venue_name"],
            "arrived_at": first_stop["arrived_at"],
        },
        "last_venue": {
            "name": last_stop["venue_name"],
            "arrived_at": last_stop["arrived_at"],
        },
        "longest_stop": {
            "name": longest_stop["venue_name"],
            "duration_minutes": longest_stop["duration_minutes"],
        },
        "nightlife_minutes": nightlife_minutes,
        "food_minutes": food_minutes,
    }