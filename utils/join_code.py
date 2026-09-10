JOIN_CODE_LENGTH = 6


def night_join_code(night_id: str) -> str:
    """Short, shareable code for a Night: the first 6 hex characters of
    its UUID, uppercased. Collisions are vanishingly unlikely among the
    handful of Nights active at any one time."""
    return night_id.replace("-", "")[:JOIN_CODE_LENGTH].upper()


def normalise_join_code(raw: str) -> str:
    return (
        raw.strip()
        .replace("-", "")
        .upper()[:JOIN_CODE_LENGTH]
    )
