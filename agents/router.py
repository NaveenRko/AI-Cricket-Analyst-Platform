def route_query(query):

    query = query.lower()

    if any(word in query for word in [
        "runs",
        "batter",
        "strike rate",
        "average",
        "sixes",
        "fours"
    ]):
        return "batting"

    if any(word in query for word in [
        "wickets",
        "economy",
        "bowler"
    ]):
        return "bowling"

    if any(word in query for word in [
        "venue",
        "stadium",
        "ground"
    ]):
        return "venue"

    if any(word in query for word in [
        "against",
        "vs",
        "versus"
    ]):
        return "matchup"

    if any(word in query for word in [
        "history",
        "captain",
        "legacy",
        "greatest",
        "about",
        "journey",
        "career",
        "profile",
        "team",
        "season",
        "summary",
        "who is",
        "tell me about",
        "biography",
        "about",
        "born",
        "achievement"
    ]):
        return "rag"

    return "batting"