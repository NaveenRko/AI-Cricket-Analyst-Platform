SCHEMA = """
Generate valid DuckDB SELECT SQL for IPL season analytics.

Return ONLY SQL. No markdown. No explanation.
Never invent tables or columns.
Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.

TABLES
------

player_season_stats:
season, batter, matches, runs, balls, dismissals,
fifties, hundreds, fours, sixes, strike_rate, average

bowler_season_stats:
season, bowler, matches, runs_conceded, wickets,
overs, economy, strike_rate

team_season_stats:
season, team, matches, wins, losses, points,
position, net_run_rate

players:
player_name, player_id, alias_name


PLAYER IDENTITY
---------------

Use players to resolve player names.

Batting:

JOIN players p
ON LOWER(TRIM(ps.batter)) = LOWER(TRIM(p.player_name))

Bowling:

JOIN players p
ON LOWER(TRIM(bs.bowler)) = LOWER(TRIM(p.player_name))

Search with:

LOWER(TRIM(p.alias_name))
LIKE LOWER('%player name%')

Never group by alias_name.

Return p.player_id and p.player_name for player results.


TABLE GRAIN
----------

player_season_stats = one row per player per season.
bowler_season_stats = one row per bowler per season.
team_season_stats = one row per team per season.

These are already season aggregates.

For a single season:
DO NOT SUM season statistics.

Use direct columns.

Example:
ps.runs
bs.wickets
ts.points


TABLE SELECTION
---------------

Batting season questions → player_season_stats.

Bowling season questions → bowler_season_stats.

Team standings/questions → team_season_stats.

Do not join matches just to filter season.


SEASON RULE
-----------

Explicit season:

WHERE season = 2024

Current/latest season:

WHERE season = (
    SELECT MAX(season)
    FROM relevant_season_table
)


RANKING RULE
------------

Most runs → ORDER BY ps.runs DESC.

Most wickets → ORDER BY bs.wickets DESC.

Best batting average → ORDER BY ps.average DESC.

Best batting strike rate → ORDER BY ps.strike_rate DESC.

Best economy → ORDER BY bs.economy ASC.

Top N → LIMIT N.

Ranking without N → LIMIT 10.


TEAM STANDINGS
--------------

Champion = position 1.

Runner-up = position 2.

Points table = all teams ordered by position.

Do not LIMIT a points table unless explicitly requested.


EXAMPLES
--------

Question: Orange Cap 2024

SELECT
    p.player_id,
    p.player_name,
    ps.runs
FROM player_season_stats ps
JOIN players p
    ON LOWER(TRIM(ps.batter)) = LOWER(TRIM(p.player_name))
WHERE ps.season = 2024
ORDER BY ps.runs DESC
LIMIT 1;

Question: Purple Cap 2024

SELECT
    p.player_id,
    p.player_name,
    bs.wickets
FROM bowler_season_stats bs
JOIN players p
    ON LOWER(TRIM(bs.bowler)) = LOWER(TRIM(p.player_name))
WHERE bs.season = 2024
ORDER BY bs.wickets DESC
LIMIT 1;

Question: IPL Champion 2024

SELECT
    team,
    position
FROM team_season_stats
WHERE season = 2024
AND position = 1
LIMIT 1;

Question: Points table 2024

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
"""