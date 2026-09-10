"""Run the event detectors against the mock Night.

mock_night.py is a hand-built 6-person, 4-venue night with a deliberate
side quest (Erik), an early checkout (Anton) and two late arrivals
(Emma, Lucas). These tests pin that behaviour so a detector change that
breaks it is caught.
"""

from mock_night import mock_night

from events.dynamic_duo import detect_dynamic_duo
from events.early_checkout import detect_early_checkout
from events.group_split import detect_group_splits
from events.houdini import detect_houdini
from events.late_arrival import detect_late_arrivals
from events.most_distance import detect_most_distance
from events.most_independent import detect_most_independent
from events.reunion import detect_reunions
from events.side_quest import detect_side_quest


def test_group_splits_are_detected():
    assert len(detect_group_splits(mock_night)) > 0


def test_houdini_is_erik():
    houdini = detect_houdini(mock_night)
    assert len(houdini) == 1
    assert houdini[0]["name"] == "Erik"
    assert houdini[0]["duration_minutes"] >= 20


def test_side_quest_is_erik():
    side_quests = detect_side_quest(mock_night)
    assert len(side_quests) == 1
    assert side_quests[0]["name"] == "Erik"
    assert side_quests[0]["distance_km"] > 0


def test_reunions_detected():
    assert len(detect_reunions(mock_night)) >= 1


def test_most_independent_returns_a_single_list_entry():
    result = detect_most_independent(mock_night)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "Erik"


def test_late_arrivals_are_emma_and_lucas():
    names = {e["name"] for e in detect_late_arrivals(mock_night)}
    assert names == {"Emma", "Lucas"}


def test_early_checkout_is_anton():
    early = detect_early_checkout(mock_night)
    assert [e["name"] for e in early] == ["Anton"]


def test_most_distance_returns_a_named_participant():
    result = detect_most_distance(mock_night)
    assert result["type"] == "most_distance"
    assert result["participant_name"] in {
        p.name for p in mock_night.participants
    }
    assert result["distance_km"] > 0


def test_dynamic_duo_shape_is_a_list():
    assert isinstance(detect_dynamic_duo(mock_night), list)
