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


def normalize_question(question: str):

    normalized = question

    lower_question = question.lower()

    # longest names first
    names = sorted(
        PLAYER_LOOKUP.keys(),
        key=len,
        reverse=True
    )

    for player in names:

        pattern = r"\b" + re.escape(player) + r"\b"

        if re.search(
            pattern,
            lower_question,
            flags=re.IGNORECASE
        ):

            normalized = re.sub(

                pattern,

                PLAYER_LOOKUP[player],

                normalized,

                flags=re.IGNORECASE

            )

            lower_question = normalized.lower()

    return normalized


#print(normalize_question("How many runs did sehwag score?"))