from datetime import datetime, timedelta

from models import LocationPoint
from utils.movement import build_movement_stats


def _line(speeds_mps):
    """Build points 60s apart, moving east at the given speeds."""
    points = []
    t = datetime(2026, 8, 28, 22, 0)
    lat, lon = 57.70, 11.97

    points.append(
        LocationPoint(
            participant_id="a",
            timestamp=t,
            latitude=lat,
            longitude=lon,
        )
    )

    for speed in speeds_mps:
        t = t + timedelta(seconds=60)
        # ~ metres to degrees longitude at this latitude
        lon = lon + (speed * 60) / 63000
        points.append(
            LocationPoint(
                participant_id="a",
                timestamp=t,
                latitude=lat,
                longitude=lon,
                speed=speed,
            )
        )

    return points


def test_empty_or_single_point_is_all_zero():
    stats = build_movement_stats([])
    assert stats["walking_minutes"] == 0
    assert sum(stats.values()) == 0


def test_walking_and_vehicle_are_classified():
    # 3 walking legs (~1.4 m/s) then 3 vehicle legs (~15 m/s)
    stats = build_movement_stats(_line([1.4, 1.4, 1.4, 15, 15, 15]))

    assert stats["walking_minutes"] == 3.0
    assert stats["vehicle_minutes"] == 3.0
    assert stats["fast_movement_minutes"] == 0.0


def test_stationary_is_classified():
    stats = build_movement_stats(_line([0.0, 0.0, 0.0, 0.0]))
    assert stats["stationary_minutes"] == 4.0
