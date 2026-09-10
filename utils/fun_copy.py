import os
import json

import anthropic
from dotenv import load_dotenv


load_dotenv()


# The model used to write the recap highlights. This is a short, creative
# task, so the cheapest model handles it well. Bump to "claude-sonnet-5"
# if the jokes ever feel flat.
MODEL = "claude-haiku-4-5"


_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Build the Anthropic client on first use so importing this module
    never requires a key (keeps tests and offline runs working)."""
    global _client

    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    return _client


SYSTEM_PROMPT = """
You are the personality engine for AFTR, a social nightlife recap app.

You are given a list of structured facts from a night out. Pick the 3 to 5
most entertaining ones and turn each into a short, funny recap highlight.
Ignore the rest. A quiet night with only one or two real facts should
produce only one or two highlights - never pad. If the only fact is
"quiet_night", return exactly one highlight that bluntly, funnily calls
out how little happened - dead night, nothing to report, boring - short
and a bit cheeky, never a lecture.

Tone:
- playful
- dry humor
- slightly cheeky
- confident
- sounds like a funny friend
- can be a little mean, but never aggressive
- never overly enthusiastic
- never corporate
- no emojis
- maximum 2 short sentences per highlight

Rules:
- Only use facts that are provided.
- You may joke or speculate playfully ("Did he meet his ex?"), but never
  present invented events as facts, and never invent people, places,
  relationships or events that are not in the facts.
- Vary the wording and the titles every time. Avoid generic AI phrases.
- Give each highlight a short title (2-4 words).
- "type" must be copied from the fact you used.
- Return valid JSON only, no surrounding text, no markdown code fences.

Return a JSON array in exactly this shape:

[
  {
    "type": "most_distance",
    "title": "Cardio King",
    "text": "Wilgot covered 4.8 km tonight. Apparently sitting down wasn't part of the plan."
  }
]
""".strip()


def _strip_code_fences(text: str) -> str:
    text = text.strip()

    if not text.startswith("```"):
        return text

    lines = text.splitlines()

    # Drop the opening fence line (``` or ```json).
    lines = lines[1:]

    # Drop the closing fence line if present.
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]

    return "\n".join(lines).strip()


def _extract_json_array(text: str):
    """Best-effort parse of a JSON array from the model output.

    Handles the common cases where the model wraps the JSON in a
    markdown fence or adds a stray sentence before/after it.
    """
    cleaned = _strip_code_fences(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")

    if start != -1 and end != -1 and end > start:
        return json.loads(cleaned[start:end + 1])

    raise ValueError(
        f"Could not parse fun copy JSON from model output: {text[:500]!r}"
    )


def _normalise_highlights(raw) -> list[dict]:
    if not isinstance(raw, list):
        raise ValueError(
            f"Fun copy response was not a list: {type(raw).__name__}"
        )

    highlights = []

    for item in raw:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "")).strip()
        text = str(item.get("text", "")).strip()

        if not title or not text:
            continue

        highlights.append(
            {
                "type": str(item.get("type", "")).strip(),
                "title": title,
                "text": text,
            }
        )

    return highlights


def _language_name(code: str | None) -> str | None:
    if not code:
        return None
    base = code.split("-")[0].split("_")[0].lower()
    return {
        "en": None,  # default, no instruction needed
        "sv": "Swedish",
        "no": "Norwegian",
        "nb": "Norwegian",
        "da": "Danish",
        "de": "German",
        "fr": "French",
        "es": "Spanish",
        "it": "Italian",
        "nl": "Dutch",
        "pt": "Portuguese",
        "fi": "Finnish",
        "pl": "Polish",
    }.get(base, None)


def generate_fun_copy(
    facts: list[dict],
    language: str | None = None,
) -> list[dict]:
    if not facts:
        return []

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is missing from .env")

    system_prompt = SYSTEM_PROMPT
    language_name = _language_name(language)
    if language_name:
        system_prompt += (
            f"\n\nWrite every title and text in {language_name}. "
            "Keep the humour natural in that language - don't translate "
            "word for word."
        )

    user_message = (
        "Here are the facts from tonight's Night. Write the highlights.\n\n"
        + json.dumps(facts, indent=2)
    )

    response = get_client().messages.create(
        model=MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    text = "".join(
        block.text
        for block in response.content
        if block.type == "text"
    ).strip()

    if not text:
        raise ValueError("Fun copy response was empty")

    parsed = _extract_json_array(text)

    return _normalise_highlights(parsed)
