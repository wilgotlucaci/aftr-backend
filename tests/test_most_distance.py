from mock_night import mock_night
from events.most_distance import detect_most_distance


def test_walk_home_leg_is_excluded():
    """Anton goes home mid-night (a long jump out to ANTON_HOME). His
    in-Night movement is small, so he must NOT be the most-distance
    winner - Erik (the side quest) should be."""
    result = detect_most_distance(mock_night)

    assert result is not None
    assert result["participant_name"] == "Erik"
    assert result["distance_km"] > 0

    anton_id = next(
        p.id for p in mock_night.participants if p.name == "Anton"
    )
    assert result["participant_id"] != anton_id
