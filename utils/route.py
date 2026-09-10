"""Build the per-participant GPS route for a Night's recap map.

Output shape:

    [
        {
            "participant_id": "wilgot",
            "name": "Wilgot",
            "points": [
                {"lat": 57.7001, "lon": 11.9699, "t": "2026-08-28T20:00:00"},
                ...
            ]
        },
        ...
    ]

Points are time-ordered. This is raw location data, so the recap endpoint
only returns it to Night participants (see api.get_night_recap).
"""

from models import Night


def build_route(night: Night) -> list[dict]:
    names = {
        participant.id: participant.name
        for participant in night.participants
    }

    by_participant: dict[str, list] = {}

    for location in night.locations:
        by_participant.setdefault(
            location.participant_id, []
        ).append(location)

    routes = []

    for participant_id, locations in by_participant.items():
        ordered = sorted(
            locations,
            key=lambda location: location.timestamp,
        )

        points = [
            {
                "lat": round(location.latitude, 6),
                "lon": round(location.longitude, 6),
                "t": location.timestamp.isoformat(),
            }
            for location in ordered
        ]

        if not points:
            continue

        routes.append(
            {
                "participant_id": participant_id,
                "name": names.get(participant_id, participant_id),
                "points": points,
            }
        )

    return routes
