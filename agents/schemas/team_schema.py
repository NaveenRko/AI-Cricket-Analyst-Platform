SCHEMA = """
Generate valid DuckDB SELECT SQL for IPL team analytics.

Return ONLY SQL. No markdown. No explanation.
Never invent tables or columns.
Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.

TABLES
------

team_season_stats:
season, team, matches, wins, losses, points,
position, net_run_rate

team_matchup:
team1, team2, matches, team1_wins, team2_wins,
ties, no_results

matches:
match_id, season, date, venue, city, winner,
toss_winner, toss_decision, player_of_match


TABLE SELECTION
---------------

Use team_season_stats for:

- points table
- team position
- wins/losses by season
- points
- net run rate
- champion
- runner-up
- season standings

Use team_matchup for:

- team vs team historical matchup
- head-to-head record

Use matches for:

- individual match results
- match dates
- venues
- cities
- toss information
- player of the match


TEAM SEASON GRAIN
-----------------

team_season_stats = one row per team per season.

Therefore:

"MI wins in IPL 2024"
→ ts.wins

"Top team in IPL 2024"
→ position

"MI points in IPL 2024"
→ ts.points

Do NOT SUM team_season_stats values.

Do not join matches just to filter season.


SEASON RULE
-----------

Explicit season:

WHERE ts.season = 2024

Current/latest season:

WHERE ts.season = (
    SELECT MAX(season)
    FROM team_season_stats
)


STANDINGS
---------

Champion = position 1.

Runner-up = position 2.

Points table = all teams ordered by position ASC.

Do not LIMIT a complete points table.


TEAM STRING RULE
----------------

For team searches use:

LOWER(TRIM(team))
LIKE LOWER('%mumbai indians%')

For matches.winner:

LOWER(TRIM(m.winner))
LIKE LOWER('%mumbai indians%')


RANKING RULE
------------

Most wins:

ORDER BY wins DESC

Most points:

ORDER BY points DESC

Best position:

ORDER BY position ASC

Top N:

LIMIT N.


EXAMPLES
--------

Question: IPL champion 2024?

SELECT
    team,
    position
FROM team_season_stats
WHERE season = 2024
AND position = 1
LIMIT 1;

Question: Runner-up in IPL 2024?

SELECT
    team,
    position
FROM team_season_stats
WHERE season = 2024
AND position = 2
LIMIT 1;

Question: Points table IPL 2024?

SELECT
    team,
    matches,
    wins,
    losses,
    points,
    net_run_rate,
    position
FROM team_season_stats
WHERE season = 2024
ORDER BY position ASC;

Question: Top 5 teams by wins in IPL 2024?

SELECT
    team,
    wins
FROM team_season_stats
WHERE season = 2024
ORDER BY wins DESC
LIMIT 5;

Question: Mumbai Indians vs Chennai Super Kings?

SELECT
    matches,
    team1_wins,
    team2_wins,
    ties,
    no_results
FROM team_matchup
WHERE LOWER(TRIM(team1))
LIKE LOWER('%mumbai indians%')
AND LOWER(TRIM(team2))
LIKE LOWER('%chennai super kings%');
"""