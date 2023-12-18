from datetime import datetime

import neo4j
import polars
import sportsdataverse


def add_game(driver: neo4j.Driver, home_team, home_score, away_team, away_score, neutral_site):
    home_point_diff = max(min(home_score - away_score, 20), -20)
    if home_score > away_score:
        game_string = """
        MERGE (home)-[:WON {location: %s, score: $home_score, opponent_score: $away_score, point_diff: %s}]->(away)
        MERGE (away)-[:LOST {location: %s, score: $away_score, opponent_score: $home_score, point_diff: %s}]->(home)
        """ % (
            "'NEUTRAL'" if neutral_site else "'HOME'",
            home_point_diff,
            "'NEUTRAL'" if neutral_site else "'AWAY'",
            -home_point_diff
        )
    else:
        game_string = """
        MERGE (home)-[:LOST {location: %s, score: $home_score, opponent_score: $away_score, point_diff: %s}]->(away)
        MERGE (away)-[:WON {location: %s, score: $away_score, opponent_score: $home_score, point_diff: %s}]->(home)
        """ % (
            "'NEUTRAL'" if neutral_site else "'HOME'",
            home_point_diff,
            "'NEUTRAL'" if neutral_site else "'AWAY'",
            -home_point_diff
        )
    driver.execute_query(
        """
        MERGE (home:Team {name: $home_team})
        MERGE (away:Team {name: $away_team})
        """ + game_string,
        home_team=home_team,
        home_score=home_score,
        away_team=away_team,
        away_score=away_score
    )


def main():
    with neo4j.GraphDatabase.driver("neo4j://localhost:7687", auth=None) as driver:
        games: polars.DataFrame = (
            sportsdataverse.load_mbb_schedule(sportsdataverse.most_recent_mbb_season())
            .filter(polars.col("date") < str(datetime.now()))
        )
        for game in games.iter_rows(named=True):
            add_game(
                driver,
                game['home_location'],
                game['home_score'],
                game['away_location'],
                game['away_score'],
                game['neutral_site']
            )

        # Set every team's individual win percentage
        driver.execute_query(
            """
            MATCH (t:Team)
            MATCH (t)-[g]->()
            SET t.win_percent = 0.0
            WITH t, count(g) as games
            MATCH (t)-[w:WON]->()
            WITH t, games, count(w) as wins
            SET t.win_percent = toFloat(wins)/games
            RETURN t.name, wins, games, toFloat(wins)/games as win_percent
            """
        )


if __name__ == "__main__":
    main()
