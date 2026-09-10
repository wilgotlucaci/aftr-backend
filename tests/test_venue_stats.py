from events.venue_stats import build_venue_stats


class _FakeNight:
    id = "n1"


def test_no_known_venues_returns_empty(monkeypatch):
    monkeypatch.setattr(
        "events.venue_stats.build_venue_timeline",
        lambda _night: [
            {"venue_id": None, "venue_name": "Unknown location",
             "category": None, "duration_minutes": 20,
             "arrived_at": "t", "left_at": "t"}
        ],
    )
    assert build_venue_stats(_FakeNight()) == {}


def test_stats_expose_total_places_for_the_client(monkeypatch):
    timeline = [
        {"venue_id": "v1", "venue_name": "Bar X", "category": "bar",
         "duration_minutes": 40, "arrived_at": "t1", "left_at": "t2"},
        {"venue_id": "v2", "venue_name": "Diner", "category": "restaurant",
         "duration_minutes": 55, "arrived_at": "t3", "left_at": "t4"},
        {"venue_id": "v3", "venue_name": "Club Z", "category": "night_club",
         "duration_minutes": 120, "arrived_at": "t5", "left_at": "t6"},
    ]
    monkeypatch.setattr(
        "events.venue_stats.build_venue_timeline",
        lambda _night: timeline,
    )

    stats = build_venue_stats(_FakeNight())

    assert stats["total_places"] == 3
    assert stats["nightlife_minutes"] == 160   # bar + night_club
    assert stats["food_minutes"] == 55
    assert stats["longest_stop"]["name"] == "Club Z"
    assert stats["first_venue"]["name"] == "Bar X"
    assert stats["last_venue"]["name"] == "Club Z"
