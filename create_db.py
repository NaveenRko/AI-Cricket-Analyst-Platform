import duckdb
import pandas as pd
import os


def create_database():

    os.makedirs("database", exist_ok=True)

    conn = duckdb.connect("database/ipl.duckdb")

    tables = {
        "matches": "Data/matches.csv",
        "deliveries": "Data/deliveries.csv",
        "players": "Data/players.csv",

        "batting_stats": "Data/batting_stats.csv",
        "bowling_stats": "Data/bowling_stats.csv",

        "team_match_stats": "Data/team_match_stats.csv",
        "team_season_stats": "Data/team_season_stats.csv",

        "player_match_stats": "Data/player_match_stats.csv",
        "player_season_stats": "Data/player_season_stats.csv",

        "phase_batting": "Data/phase_batting.csv",
        "phase_bowling": "Data/phase_bowling.csv",

        "player_vs_player": "Data/player_vs_player.csv",

        "venue_stats": "Data/venue_stats.csv",
        "bowler_match_stats": "Data/bowler_match_stats.csv",
        "bowler_season_stats": "Data/bowler_season_stats.csv",
        "player_milestones": "Data/player_milestones.csv",
        "venue_match_stats": "Data/venue_match_stats.csv"
    }

    for table_name, file_path in tables.items():

        print(f"Creating table: {table_name}")

        df = pd.read_csv(file_path)

        conn.register("temp_df", df)

        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name}
            AS SELECT * FROM temp_df
        """)

    print("\nTables Created Successfully:\n")

    for table in conn.execute("SHOW TABLES").fetchall():
        print(table[0])

    conn.close()


if __name__ == "__main__":
    create_database()