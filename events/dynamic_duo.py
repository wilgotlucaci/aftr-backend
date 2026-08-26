from models import Night
from utils.locations import calculate_proximity_stats


def get_participant_name(
    night: Night,
    participant_id: str,
) -> str:
    for participant in night.participants:
        if participant.id == participant_id:
            return participant.name

    return participant_id


def detect_dynamic_duo(
    night: Night,
    minimum_percentage: float = 80,
    minimum_lead_percentage_points: float = 5,
):
    pair_stats = calculate_proximity_stats(night)

    if len(pair_stats) < 2:
        return []

    pair_stats = sorted(
        pair_stats,
        key=lambda pair: pair["together_percentage"],
        reverse=True,
    )

    best_pair = pair_stats[0]
    second_best = pair_stats[1]

    best_percentage = best_pair["together_percentage"]
    second_best_percentage = second_best["together_percentage"]

    if best_percentage < minimum_percentage:
        return []

    lead = best_percentage - second_best_percentage

    if lead < minimum_lead_percentage_points:
        return []

    name_a = get_participant_name(
        night,
        best_pair["person_a"],
    )

    name_b = get_participant_name(
        night,
        best_pair["person_b"],
    )

    return [
        {
            "type": "dynamic_duo",
            "person_a": best_pair["person_a"],
            "person_b": best_pair["person_b"],
            "name_a": name_a,
            "name_b": name_b,
            "together_minutes": best_pair["together_minutes"],
            "together_percentage": best_percentage,
            "lead_percentage_points": round(lead, 1),
            "text": (
                f"{name_a} and {name_b} were the Night's dynamic duo, "
                f"spending {best_percentage}% of the Night together."
            ),
        }
    ]