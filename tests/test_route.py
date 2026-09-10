from datetime import datetime

from models import Night, NightStatus, Participant, LocationPoint
from utils.route import build_route


def _point(pid, minute, lat, lon):
    return LocationPoint(
        participant_id=pid,
        timestamp=datetime(2026, 8, 28, 22, minute),
        latitude=lat,
        longitude=lon,
    )


def _night(locations):
    return Night(
        id="n1",
        title="Test",
        started_at=datetime(2026, 8, 28, 22, 0),
        ended_at=datetime(2026, 8, 28, 23, 0),
        status=NightStatus.FINISHED,
        participants=[
            Participant(id="a", name="Alice"),
            Participant(id="b", name="Bob"),
        ],
        locations=locations,
    )


def test_route_groups_and_time_orders_points():
    night = _night([
        _point("a", 30, 57.70, 11.97),
        _point("a", 0, 57.71, 11.98),
        _point("b", 15, 57.72, 11.99),
    ])

    routes = {r["participant_id"]: r for r in build_route(night)}

    assert set(routes) == {"a", "b"}
    assert routes["a"]["name"] == "Alice"

    minutes = [p["t"][14:16] for p in routes["a"]["points"]]
    assert minutes == ["00", "30"]  # sorted ascending


def test_route_point_shape():
    night = _night([_point("a", 0, 57.700123456, 11.980987654)])
    point = build_route(night)[0]["points"][0]

    assert set(point) == {"lat", "lon", "t"}
    assert point["lat"] == 57.700123  # rounded to 6dp
    assert point["lon"] == 11.980988


def test_route_skips_participants_with_no_points():
    night = _night([_point("a", 0, 57.70, 11.97)])
    routes = build_route(night)

    assert [r["participant_id"] for r in routes] == ["a"]
