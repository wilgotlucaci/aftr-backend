"""Monthly wrap - personal stats across a user's finished Nights in a
calendar month, built from the saved recaps."""

from datetime import datetime

from utils.distance import distance_meters


def _parse(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def build_wrap(user: dict, month: str, nights: list[dict], recap_repository):
    user_id = user["id"]

    total_minutes = 0
    distance_meters_total = 0.0
    venue_counts: dict[str, int] = {}
    people_counts: dict[str, int] = {}
    weekday_counts: dict[int, int] = {}
    latest_end_hour: float | None = None

    for night in nights:
        started = _parse(night.get("started_at"))
        ended = _parse(night.get("ended_at")) or started

        if started and ended:
            total_minutes += max(
                0, int((ended - started).total_seconds() / 60)
            )
            # Monday=0 .. Sunday=6 - language-agnostic. The client
            # localizes this to a weekday name via Foundation's Calendar,
            # so the app stays in the user's system language.
            weekday = started.weekday()
            weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1

            hour = ended.hour + ended.minute / 60
            latest_end_hour = (
                hour if latest_end_hour is None
                else max(latest_end_hour, hour)
            )

        saved = recap_repository.get_by_night_id(night["id"])
        if not saved:
            continue

        recap = saved.get("recap_data", {}) or {}

        for venue in recap.get("venue_timeline", []) or []:
            name = venue.get("venue_name")
            if name and name != "Unknown location":
                venue_counts[name] = venue_counts.get(name, 0) + 1

        for participant in recap.get("participants", []) or []:
            if participant.get("id") != user_id and participant.get("name"):
                key = participant["name"]
                people_counts[key] = people_counts.get(key, 0) + 1

        for route in recap.get("route", []) or []:
            if route.get("participant_id") != user_id:
                continue
            points = route.get("points", []) or []
            for a, b in zip(points, points[1:]):
                distance_meters_total += distance_meters(
                    a["lat"], a["lon"], b["lat"], b["lon"]
                )

    top_venues = sorted(
        venue_counts.items(), key=lambda kv: kv[1], reverse=True
    )[:3]
    top_people = sorted(
        people_counts.items(), key=lambda kv: kv[1], reverse=True
    )[:3]
    busiest_weekday_index = (
        max(weekday_counts, key=weekday_counts.get)
        if weekday_counts else None
    )

    return {
        "month": month,
        "nights": len(nights),
        "hours_out": round(total_minutes / 60, 1),
        "distance_km": round(distance_meters_total / 1000, 1),
        "venues_visited": sum(venue_counts.values()),
        "unique_venues": len(venue_counts),
        "top_venues": [
            {"name": name, "count": count} for name, count in top_venues
        ],
        "top_people": [
            {"name": name, "count": count} for name, count in top_people
        ],
        "busiest_weekday_index": busiest_weekday_index,
        "latest_end_hour": (
            round(latest_end_hour, 1)
            if latest_end_hour is not None else None
        ),
    }
