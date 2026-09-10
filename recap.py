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
from utils.fun_recap import build_fun_facts
from utils.movement import build_movement_stats
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


def build_recap(night):
    group_splits = detect_group_splits(night)
    houdini = detect_houdini(night)
    side_quests = detect_side_quest(night)
    dynamic_duo = detect_dynamic_duo(night)
    reunions = detect_reunions(night)
    most_independent = detect_most_independent(night)
    early_checkout = detect_early_checkout(night)
    late_arrivals = detect_late_arrivals(night)
    most_distance = detect_most_distance(night)

    venue_timeline = build_venue_timeline(night)
    venue_stats = build_venue_stats(night)
    movement_stats = build_movement_stats(
        night.locations
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

        "events": {
            "group_splits": group_splits,
            "houdini": houdini,
            "side_quests": side_quests,
            "dynamic_duo": dynamic_duo,
            "reunions": reunions,
            "most_independent": most_independent,
            "early_checkout": early_checkout,
            "late_arrivals": late_arrivals,
            "most_distance": most_distance,
        },

        "venue_timeline": venue_timeline,
        "venue_stats": venue_stats,
        "movement_stats": movement_stats,
    }

    # AI copy generation must never be able to break a Night.
    # If it fails for any reason, the recap is still saved with
    # an empty fun_highlights list and the error is logged.
    recap["fun_highlights"] = []

    fun_facts = build_fun_facts(recap)

    if fun_facts:
        try:
            recap["fun_highlights"] = generate_fun_copy(
                fun_facts
            )
        except Exception as error:
            print(
                f"Fun copy generation failed: {error}"
            )

    return recap


def build_serialized_recap(night):
    return serialize_value(
        build_recap(night)
    )
