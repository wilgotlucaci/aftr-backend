import json

from repositories.night_repository import NightRepository
from recap import build_serialized_recap


def main():
    repository = NightRepository()

    night = repository.get_by_id(
        "b919f98e-a335-42ab-b563-84e2e3bf8640"
    )

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