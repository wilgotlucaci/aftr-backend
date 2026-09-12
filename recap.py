from datetime import datetime
from enum import Enum

from events.dynamic_duo import detect_dynamic_duo
from events.early_checkout import detect_early_checkout
from events.group_split import detect_group_splits
from events.houdini import detect_houdini
from events.late_arrival import detect_late_arrivals
from events.most_distance import detect_most_distance
from events.most_independent import detect_most_independent
from events.reunion import detect_reunions
from events.side_quest import detect_side_quest

from utils.fun_copy import generate_fun_copy
from utils.fun_recap import build_fun_facts, build_group_facts
from utils.movement import build_movement_stats
from utils.route import build_route
from utils.venue_timeline import build_venue_timeline

from events.venue_stats import build_venue_stats


def serialize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            key: serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            serialize_value(item)
            for item in value
        ]

    return value


def _safe(label, function, default):
    """Run one recap section. If it raises, log it and fall back to
    ``default`` so a single broken detector can never stop a Night from
    ending.
    """
    try:
        return function()
    except Exception as error:
        print(f"Recap section '{label}' failed: {error}")
        return default


def build_recap(night, language=None):
    events = {
        "group_splits": _safe(
            "group_splits",
            lambda: detect_group_splits(night),
            [],
        ),
        "houdini": _safe(
            "houdini",
            lambda: detect_houdini(night),
            [],
        ),
        "side_quests": _safe(
            "side_quests",
            lambda: detect_side_quest(night),
            [],
        ),
        "dynamic_duo": _safe(
            "dynamic_duo",
            lambda: detect_dynamic_duo(night),
            [],
        ),
        "reunions": _safe(
            "reunions",
            lambda: detect_reunions(night),
            [],
        ),
        "most_independent": _safe(
            "most_independent",
            lambda: detect_most_independent(night),
            [],
        ),
        "early_checkout": _safe(
            "early_checkout",
            lambda: detect_early_checkout(night),
            [],
        ),
        "late_arrivals": _safe(
            "late_arrivals",
            lambda: detect_late_arrivals(night),
            [],
        ),
        "most_distance": _safe(
            "most_distance",
            lambda: detect_most_distance(night),
            None,
        ),
    }

    venue_timeline = _safe(
        "venue_timeline",
        lambda: build_venue_timeline(night),
        [],
    )

    route = _safe(
        "route",
        lambda: build_route(night),
        [],
    )

    venue_stats = _safe(
        "venue_stats",
        lambda: build_venue_stats(night),
        {},
    )

    movement_stats = _safe(
        "movement_stats",
        lambda: build_movement_stats(night.locations),
        {
            "stationary_minutes": 0,
            "walking_minutes": 0,
            "fast_movement_minutes": 0,
            "vehicle_minutes": 0,
            "unknown_minutes": 0,
        },
    )

    recap = {
        "night_id": night.id,
        "title": night.title,
        "started_at": night.started_at,
        "ended_at": night.ended_at,
        "status": night.status,

        "participants": [
            {
                "id": participant.id,
                "name": participant.name,
            }
            for participant in night.participants
        ],

        "events": events,

        "venue_timeline": venue_timeline,
        "venue_stats": venue_stats,
        "movement_stats": movement_stats,
        "route": route,
    }

    # AI copy generation must never be able to break a Night. If it fails
    # for any reason, the recap is still saved with an empty
    # fun_highlights list and the error is logged.
    recap["fun_highlights"] = []

    fun_facts = _safe(
        "fun_facts",
        lambda: build_fun_facts(recap),
        [],
    )

    if fun_facts:
        recap["fun_highlights"] = _safe(
            "fun_highlights",
            lambda: generate_fun_copy(fun_facts, language=language),
            [],
        )

    # The group page's own highlights - independent from fun_highlights
    # above so the original recap page's content/behavior never changes.
    recap["group_highlights"] = []

    group_facts = _safe(
        "group_facts",
        lambda: build_group_facts(recap),
        [],
    )

    if group_facts:
        recap["group_highlights"] = _safe(
            "group_highlights",
            lambda: generate_fun_copy(group_facts, language=language),
            [],
        )

    return recap


def build_serialized_recap(night, language=None):
    return serialize_value(
        build_recap(night, language=language)
    )
