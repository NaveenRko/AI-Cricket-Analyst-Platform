SCHEMA = """
Generate valid DuckDB SELECT SQL for IPL venue analytics.

Return ONLY SQL. No markdown. No explanation.
Never invent tables or columns.
Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.

TABLE
-----

matches:
match_id, season, date, venue, city, winner,
toss_winner, toss_decision, player_of_match

Use matches for venue questions unless a dedicated venue table
is explicitly available.


STRING RULE
-----------

For venue/city searches use:

LOWER(TRIM(column))
LIKE LOWER('%search term%')


COMMON VENUE QUESTIONS
----------------------

Use matches for:

- matches played at a venue
- matches won at a venue
- venue by season
- city analysis
- toss results at a venue
- winners at a venue
- match count by venue
- most frequently used venues


SEASON RULE
-----------

If season is specified:

WHERE m.season = 2024

If venue is specified:

AND LOWER(TRIM(m.venue))
LIKE LOWER('%wankhede%')

Do not invent venue columns in other tables.


AGGREGATION
-----------

Count matches:

COUNT(*)

Count matches by venue:

GROUP BY m.venue

Count wins:

SUM(
    CASE
        WHEN ...
        THEN 1
        ELSE 0
    END
)

Do not join player aggregate tables unless explicitly required.


RANKING RULE
------------

Most matches at a venue:

ORDER BY match_count DESC

Top N:

LIMIT N

Ranking without N:

LIMIT 10.


EXAMPLES
--------

Question: How many IPL matches were played at Wankhede Stadium?

SELECT
    COUNT(*) AS match_count
FROM matches m
WHERE LOWER(TRIM(m.venue))
LIKE LOWER('%wankhede%');

Question: Top 5 venues by number of IPL matches?

SELECT
    m.venue,
    COUNT(*) AS match_count
FROM matches m
GROUP BY m.venue
ORDER BY match_count DESC
LIMIT 5;

Question: Matches at Wankhede in IPL 2024?

SELECT
    COUNT(*) AS match_count
FROM matches m
WHERE m.season = 2024
AND LOWER(TRIM(m.venue))
LIKE LOWER('%wankhede%');

Question: Which venue hosted the most IPL matches?

SELECT
    m.venue,
    COUNT(*) AS match_count
FROM matches m
GROUP BY m.venue
ORDER BY match_count DESC
LIMIT 1;
"""