def build_fun_facts(recap: dict) -> list[dict]:
    facts = []

    events = recap.get("events", {})

    most_distance = events.get("most_distance")

    if most_distance:
        facts.append(
            {
                "type": "most_distance",
                "participant_name": most_distance.get("participant_name"),
                "distance_km": most_distance.get("distance_km"),
            }
        )

    most_independent = events.get("most_independent")

    if most_independent:
        facts.append(
            {
                "type": "most_independent",
                "participant_name": most_independent.get("participant_name"),
                "duration_minutes": most_independent.get("duration_minutes"),
            }
        )

    dynamic_duo = events.get("dynamic_duo")

    if dynamic_duo:
        facts.append(
            {
                "type": "dynamic_duo",
                "data": dynamic_duo,
            }
        )

    group_splits = events.get("group_splits")

    if group_splits:
        facts.append(
            {
                "type": "group_splits",
                "count": len(group_splits),
                "data": group_splits,
            }
        )

    return facts