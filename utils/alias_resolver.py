import re
import pandas as pd

players = pd.read_csv("Data/players.csv")

players["player_name"] = players["player_name"].str.strip()
players["alias_name"] = players["alias_name"].str.lower().str.strip()

# dictionary:
# virat kohli -> V Kohli

PLAYER_LOOKUP = dict(
    zip(
        players["alias_name"],
        players["player_name"]
    )
)

# Build ONE combined pattern instead of looping re.sub per alias. Looping
# was the bug: each sequential re.sub re-scans the FULL (already partially
# normalized) text, so once "virat kohli" -> "V Kohli" fires, the next
# alias "kohli" still matches the "Kohli" just inserted and fires again,
# producing "V V Kohli". A single combined alternation pattern matches each
# span of the original text exactly once, so already-substituted text is
# never re-scanned. Aliases are ordered longest-first so "virat kohli" wins
# over the shorter "kohli" alternative at the same position.
_ALIASES_BY_LENGTH = sorted(PLAYER_LOOKUP.keys(), key=len, reverse=True)
_COMBINED_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(a) for a in _ALIASES_BY_LENGTH) + r")\b",
    flags=re.IGNORECASE,
)


def normalize_question(question: str) -> str:

    def _replace(match):
        return PLAYER_LOOKUP[match.group(0).lower()]

    return _COMBINED_PATTERN.sub(_replace, question)


#print(normalize_question("How many runs did sehwag score?"))