"""The recap build must never raise, even if a section blows up."""

import recap as recap_module
from mock_night import mock_night


def test_build_recap_survives_a_failing_detector(monkeypatch):
    def boom(_night):
        raise RuntimeError("detector exploded")

    monkeypatch.setattr(recap_module, "detect_group_splits", boom)
    monkeypatch.setattr(
        recap_module, "build_venue_timeline", lambda _n: []
    )
    monkeypatch.setattr(
        recap_module, "generate_fun_copy", lambda _f: []
    )

    result = recap_module.build_recap(mock_night)

    assert result["events"]["group_splits"] == []
    assert result["night_id"] == mock_night.id
    assert "route" in result
    assert result["fun_highlights"] == []


def test_build_recap_survives_failing_ai(monkeypatch):
    monkeypatch.setattr(
        recap_module, "build_venue_timeline", lambda _n: []
    )

    def ai_boom(_facts):
        raise RuntimeError("no credits")

    monkeypatch.setattr(recap_module, "generate_fun_copy", ai_boom)

    result = recap_module.build_recap(mock_night)
    assert result["fun_highlights"] == []


def test_build_recap_includes_route_per_participant(monkeypatch):
    monkeypatch.setattr(
        recap_module, "build_venue_timeline", lambda _n: []
    )
    monkeypatch.setattr(
        recap_module, "generate_fun_copy", lambda _f: []
    )

    result = recap_module.build_recap(mock_night)
    route_names = {r["name"] for r in result["route"]}

    assert route_names == {p.name for p in mock_night.participants}
