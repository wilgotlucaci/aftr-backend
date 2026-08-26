from models import Night

from events.houdini import detect_houdini
from events.side_quest import detect_side_quest
from events.dynamic_duo import detect_dynamic_duo
from events.reunion import detect_reunions
from events.most_independent import detect_most_independent
from events.early_checkout import detect_early_checkout
from events.late_arrival import detect_late_arrivals
from events.venue_stats import build_venue_stats

from utils.participant_lifecycle import (
    build_participant_lifecycles,
)
from utils.venue_timeline import build_venue_timeline

from datetime import datetime

def build_recap(night: Night):
    return {
        "night": {
            "id": night.id,
            "title": night.title,
            "started_at": night.started_at,
            "ended_at": night.ended_at,
            "participant_count": len(night.participants),
        },

        "events": {
            "houdini": detect_houdini(night),
            "side_quests": detect_side_quest(night),
            "dynamic_duo": detect_dynamic_duo(night),
            "reunions": detect_reunions(night),
            "most_independent": detect_most_independent(night),
            "early_checkout": detect_early_checkout(night),
            "late_arrivals": detect_late_arrivals(night),
        },

        "venues": {
            "timeline": build_venue_timeline(night),
            "stats": build_venue_stats(night),
        },

        "participants": build_participant_lifecycles(night),
    }


def serialize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: serialize_value(item)
            for key, item in value.items()
        }

    return value


def build_serialized_recap(night: Night):
    recap = build_recap(night)

    return serialize_value(recap)