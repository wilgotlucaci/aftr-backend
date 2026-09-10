"""Turn the structured recap into a flat list of candidate "facts".

Each fact is a small, self-contained dict describing one interesting thing
that happened. The AI copy layer (utils/fun_copy) then picks the most
entertaining few and writes the actual highlight text. Nothing in here
calls a model - it is pure data shaping and must never raise on a
partially-populated recap.
"""


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def _first(value) -> dict | None:
    items = _as_list(value)
    return items[0] if items else None


def _to_datetime(value):
    from datetime import datetime

    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def build_fun_facts(recap: dict) -> list[dict]:
    facts: list[dict] = []

    events = recap.get("events", {}) or {}

    # --- How long the night ran -----------------------------------------
    started = _to_datetime(recap.get("started_at"))
    ended = _to_datetime(recap.get("ended_at"))
    if started and ended:
        minutes = int((ended - started).total_seconds() / 60)
        if minutes >= 25:
            facts.append(
                {
                    "type": "night_length",
                    "hours": minutes // 60,
                    "minutes": minutes % 60,
                    "total_minutes": minutes,
                }
            )

    participants = recap.get("participants", []) or []
    if len(participants) >= 2:
        facts.append(
            {
                "type": "group_size",
                "people": len(participants),
                "names": [p.get("name") for p in participants],
            }
        )

    # --- Distance ---------------------------------------------------------
    most_distance = _first(events.get("most_distance"))
    if most_distance and (most_distance.get("distance_km") or 0) >= 0.5:
        facts.append(
            {
                "type": "most_distance",
                "participant_name": most_distance.get("participant_name")
                or most_distance.get("name"),
                "distance_km": most_distance.get("distance_km"),
            }
        )

    # --- Solo / independence -------------------------------------------------
    most_independent = _first(events.get("most_independent"))
    if most_independent:
        facts.append(
            {
                "type": "most_independent",
                "participant_name": most_independent.get("name")
                or most_independent.get("participant_name"),
                "solo_minutes": most_independent.get("solo_minutes")
                or most_independent.get("duration_minutes"),
            }
        )

    # --- Houdini (disappeared, then came back) -----------------------------
    for houdini in _as_list(events.get("houdini")):
        facts.append(
            {
                "type": "houdini",
                "participant_name": houdini.get("name"),
                "duration_minutes": houdini.get("duration_minutes"),
            }
        )

    # --- Side quests ------------------------------------------------------
    for side_quest in _as_list(events.get("side_quests")):
        facts.append(
            {
                "type": "side_quest",
                "participant_name": side_quest.get("name"),
                "distance_km": side_quest.get("distance_km"),
                "duration_minutes": side_quest.get("duration_minutes"),
            }
        )

    # --- Reunions -------------------------------------------------------
    reunions = _as_list(events.get("reunions"))
    if reunions:
        facts.append(
            {
                "type": "reunions",
                "count": len(reunions),
                "longest_apart_minutes": max(
                    (r.get("duration_minutes") or 0) for r in reunions
                ),
            }
        )

    # --- Dynamic duo --------------------------------------------------------
    dynamic_duo = _first(events.get("dynamic_duo"))
    if dynamic_duo:
        facts.append(
            {
                "type": "dynamic_duo",
                "name_a": dynamic_duo.get("name_a"),
                "name_b": dynamic_duo.get("name_b"),
                "together_percentage": dynamic_duo.get("together_percentage"),
            }
        )

    # --- Late arrivals -------------------------------------------------------
    for late in _as_list(events.get("late_arrivals")):
        facts.append(
            {
                "type": "late_arrival",
                "participant_name": late.get("name"),
                "minutes_late": late.get("minutes_late"),
            }
        )

    # --- Early checkout -------------------------------------------------------
    for early in _as_list(events.get("early_checkout")):
        facts.append(
            {
                "type": "early_checkout",
                "participant_name": early.get("name"),
                "minutes_before_end": early.get("minutes_before_end"),
            }
        )

    # --- Venues -----------------------------------------------------------
    timeline = recap.get("venue_timeline", []) or []
    named_venues = [
        v for v in timeline
        if v.get("venue_name") and v.get("venue_name") != "Unknown location"
    ]
    if named_venues:
        longest = max(
            named_venues,
            key=lambda v: v.get("duration_minutes") or 0,
        )
        facts.append(
            {
                "type": "venues",
                "count": len(named_venues),
                "names": [v.get("venue_name") for v in named_venues],
                "longest_stay_venue": longest.get("venue_name"),
                "longest_stay_minutes": longest.get("duration_minutes"),
            }
        )

    # --- Movement -------------------------------------------------------
    movement = recap.get("movement_stats", {}) or {}
    walking = movement.get("walking_minutes") or 0
    fast = movement.get("fast_movement_minutes") or 0
    vehicle = movement.get("vehicle_minutes") or 0
    if walking + fast + vehicle >= 5:
        facts.append(
            {
                "type": "movement",
                "walking_minutes": walking,
                "fast_movement_minutes": fast,
                "vehicle_minutes": vehicle,
            }
        )

    # Nothing notable happened - still give the AI one dry line to land,
    # rather than showing an empty recap.
    if not facts:
        minutes = None
        if started and ended:
            minutes = int((ended - started).total_seconds() / 60)
        facts.append(
            {
                "type": "quiet_night",
                "total_minutes": minutes,
            }
        )

    return facts
