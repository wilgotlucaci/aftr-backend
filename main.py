"""Local debug helper: build and print a recap for one Night.

Usage:
    python main.py                 # latest finished Night
    python main.py <night_id>      # a specific Night
"""

import json
import sys

from repositories.night_repository import NightRepository
from recap import build_serialized_recap


def resolve_night_id(repository: NightRepository) -> str | None:
    if len(sys.argv) > 1:
        return sys.argv[1]

    finished = [
        night
        for night in repository.get_all()
        if night.get("status") == "finished"
    ]

    if not finished:
        return None

    finished.sort(
        key=lambda night: night["started_at"],
        reverse=True,
    )

    return finished[0]["id"]


def main():
    repository = NightRepository()

    night_id = resolve_night_id(repository)

    if night_id is None:
        print("No finished Night found. Pass a night_id explicitly.")
        return

    night = repository.get_by_id(night_id)

    if night is None:
        print(f"Night {night_id} not found.")
        return

    recap = build_serialized_recap(night)

    print(
        json.dumps(
            recap,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
