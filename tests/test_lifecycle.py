from mock_night import mock_night
from utils.participant_lifecycle import build_participant_lifecycles
from events.group_split import build_group_split_events


def _by_name(rows):
    return {row["name"]: row for row in rows}


def test_lifecycle_row_per_participant_with_points():
    rows = build_participant_lifecycles(mock_night)
    assert {row["name"] for row in rows} == {
        p.name for p in mock_night.participants
    }


def test_late_arrivals_have_positive_minutes_after_start():
    rows = _by_name(build_participant_lifecycles(mock_night))
    # Emma and Lucas join well after the 20:00 start.
    assert rows["Emma"]["minutes_after_start"] >= 30
    assert rows["Lucas"]["minutes_after_start"] >= 30
    # Wilgot is there from the start.
    assert rows["Wilgot"]["minutes_after_start"] == 0


def test_anton_leaves_before_the_end():
    rows = _by_name(build_participant_lifecycles(mock_night))
    assert rows["Anton"]["left_night_at"] is not None
    assert rows["Anton"]["minutes_before_end"] >= 30


def test_group_split_events_have_durations_and_rejoin_flags():
    events = build_group_split_events(mock_night)
    assert events, "mock night should produce at least one split event"

    for event in events:
        assert event["type"] == "group_split"
        assert event["duration_minutes"] >= 0
        assert isinstance(event["rejoined"], bool)
