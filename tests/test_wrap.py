from wrap import build_wrap
from utils.fun_copy import _language_name


class _FakeRecapRepo:
    def __init__(self, by_night):
        self._by_night = by_night

    def get_by_night_id(self, night_id):
        data = self._by_night.get(night_id)
        return {"recap_data": data} if data else None


def test_language_name_maps_common_codes():
    assert _language_name("sv") == "Swedish"
    assert _language_name("sv-SE") == "Swedish"
    assert _language_name("de_DE") == "German"
    assert _language_name("en") is None
    assert _language_name(None) is None
    assert _language_name("xx") is None


def test_wrap_aggregates_across_nights():
    nights = [
        {"id": "n1", "started_at": "2026-09-04T21:00:00+00:00",
         "ended_at": "2026-09-05T02:00:00+00:00", "status": "finished"},
        {"id": "n2", "started_at": "2026-09-11T22:00:00+00:00",
         "ended_at": "2026-09-12T03:30:00+00:00", "status": "finished"},
    ]
    recaps = {
        "n1": {
            "participants": [{"id": "me", "name": "Me"},
                             {"id": "e", "name": "Erik"}],
            "venue_timeline": [
                {"venue_name": "Bar X"}, {"venue_name": "Club Z"},
            ],
            "route": [{"participant_id": "me", "points": [
                {"lat": 57.70, "lon": 11.97},
                {"lat": 57.705, "lon": 11.975},
            ]}],
        },
        "n2": {
            "participants": [{"id": "me", "name": "Me"},
                             {"id": "e", "name": "Erik"}],
            "venue_timeline": [{"venue_name": "Bar X"}],
            "route": [{"participant_id": "me", "points": [
                {"lat": 57.70, "lon": 11.97},
                {"lat": 57.71, "lon": 11.98},
            ]}],
        },
    }

    wrap = build_wrap(
        {"id": "me", "name": "Me"}, "2026-09", nights,
        _FakeRecapRepo(recaps),
    )

    assert wrap["nights"] == 2
    assert wrap["hours_out"] > 9
    assert wrap["distance_km"] > 0
    assert wrap["venues_visited"] == 3
    assert wrap["unique_venues"] == 2
    assert wrap["top_venues"][0] == {"name": "Bar X", "count": 2}
    assert wrap["top_people"] == [{"name": "Erik", "count": 2}]
    assert wrap["busiest_weekday"] in {"Friday", "Thursday"}


def test_wrap_handles_no_nights():
    wrap = build_wrap({"id": "me"}, "2026-09", [], _FakeRecapRepo({}))
    assert wrap["nights"] == 0
    assert wrap["distance_km"] == 0.0
    assert wrap["top_venues"] == []
    assert wrap["busiest_weekday"] is None
