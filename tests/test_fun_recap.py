from utils.fun_recap import build_fun_facts, build_group_facts


def _types(facts):
    return {fact["type"] for fact in facts}


def test_handles_most_independent_as_a_list():
    # Regression: build_fun_facts used to call .get() on this list.
    recap = {
        "events": {
            "most_independent": [
                {"name": "Erik", "solo_minutes": 50},
            ],
        },
    }

    facts = build_fun_facts(recap)
    fact = next(f for f in facts if f["type"] == "most_independent")

    assert fact["participant_name"] == "Erik"
    assert fact["solo_minutes"] == 50


def test_empty_recap_yields_only_a_quiet_night_fact():
    for recap in ({}, {"events": {}}):
        facts = build_fun_facts(recap)
        assert [f["type"] for f in facts] == ["quiet_night"]


def test_a_real_length_night_always_has_at_least_one_fact():
    from datetime import datetime

    recap = {
        "events": {},
        "started_at": datetime(2026, 9, 10, 22, 0),
        "ended_at": datetime(2026, 9, 11, 3, 20),
    }
    facts = build_fun_facts(recap)
    length = next(f for f in facts if f["type"] == "night_length")
    assert length["hours"] == 5 and length["minutes"] == 20


def test_a_trivial_length_night_falls_back_to_quiet_night():
    from datetime import datetime

    recap = {
        "events": {},
        "started_at": datetime(2026, 9, 10, 22, 0),
        "ended_at": datetime(2026, 9, 10, 22, 10),
    }
    facts = build_fun_facts(recap)
    assert [f["type"] for f in facts] == ["quiet_night"]
    assert facts[0]["total_minutes"] == 10


def test_pulls_a_broad_set_of_facts():
    recap = {
        "participants": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        "events": {
            "most_distance": {"participant_name": "A", "distance_km": 4.2},
            "houdini": [{"name": "B", "duration_minutes": 30}],
            "side_quests": [
                {"name": "B", "distance_km": 1.5, "duration_minutes": 30}
            ],
            "reunions": [{"duration_minutes": 20}, {"duration_minutes": 40}],
            "late_arrivals": [{"name": "C", "minutes_late": 45}],
            "early_checkout": [{"name": "A", "minutes_before_end": 60}],
        },
        "venue_timeline": [
            {"venue_name": "Bar X", "duration_minutes": 40},
            {"venue_name": "Club Y", "duration_minutes": 120},
        ],
        "movement_stats": {
            "walking_minutes": 25,
            "fast_movement_minutes": 0,
            "vehicle_minutes": 0,
        },
    }

    types = _types(build_fun_facts(recap))

    assert {
        "group_size",
        "most_distance",
        "houdini",
        "side_quest",
        "reunions",
        "late_arrival",
        "early_checkout",
        "venues",
        "movement",
    } <= types


def test_short_distance_is_not_a_distance_fact():
    recap = {"events": {"most_distance": {"participant_name": "A", "distance_km": 0.2}}}
    assert _types(build_fun_facts(recap)) == {"quiet_night"}


def test_unknown_location_venue_is_ignored():
    recap = {
        "events": {},
        "venue_timeline": [
            {"venue_name": "Unknown location", "duration_minutes": 30}
        ],
    }
    assert _types(build_fun_facts(recap)) == {"quiet_night"}


def test_group_facts_solo_night_is_just_the_one_fact():
    for recap in (
        {"participants": []},
        {"participants": [{"name": "Wilgot"}]},
    ):
        facts = build_group_facts(recap)
        assert [f["type"] for f in facts] == ["solo_night"]


def test_group_facts_with_no_events_falls_back_to_uneventful():
    recap = {
        "participants": [{"name": "A"}, {"name": "B"}],
        "events": {},
    }
    facts = build_group_facts(recap)
    assert [f["type"] for f in facts] == ["uneventful_group_night"]
    assert facts[0]["people"] == 2


def test_group_facts_never_includes_individual_only_types():
    # most_distance, venues, movement, night_length are on the recap's
    # own page (build_fun_facts) - the group page must not duplicate them.
    recap = {
        "participants": [{"name": "A"}, {"name": "B"}],
        "started_at": "2026-09-10T22:00:00",
        "ended_at": "2026-09-11T03:20:00",
        "events": {
            "most_distance": {"participant_name": "A", "distance_km": 4.2},
            "houdini": [{"name": "B", "duration_minutes": 30}],
        },
        "venue_timeline": [
            {"venue_name": "Bar X", "duration_minutes": 40},
        ],
        "movement_stats": {"walking_minutes": 25},
    }

    types = _types(build_group_facts(recap))

    assert types == {"houdini"}
    assert "most_distance" not in types
    assert "venues" not in types
    assert "movement" not in types
    assert "night_length" not in types


def test_group_facts_pulls_the_full_group_only_set():
    recap = {
        "participants": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        "events": {
            "group_splits": [{"duration_minutes": 15}],
            "houdini": [{"name": "B", "duration_minutes": 30}],
            "side_quests": [
                {"name": "B", "distance_km": 1.5, "duration_minutes": 30}
            ],
            "reunions": [{"duration_minutes": 20}, {"duration_minutes": 40}],
            "dynamic_duo": {
                "name_a": "A",
                "name_b": "C",
                "together_percentage": 90,
            },
            "most_independent": [{"name": "B", "solo_minutes": 50}],
            "late_arrivals": [{"name": "C", "minutes_late": 45}],
            "early_checkout": [{"name": "A", "minutes_before_end": 60}],
        },
    }

    types = _types(build_group_facts(recap))

    assert {
        "group_splits",
        "houdini",
        "side_quest",
        "reunions",
        "dynamic_duo",
        "most_independent",
        "late_arrival",
        "early_checkout",
    } <= types
