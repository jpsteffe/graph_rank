from datetime import datetime

import neo4j
import polars
import sportsdataverse


def add_game(driver: neo4j.Driver, home_team, home_score, away_team, away_score, neutral_site):
    if home_score > away_score:
        game_string = """
        MERGE (away)-[:LOST_TO {location: $location, neutral: $neutral, home_score: $home_score, away_score: $away_score}]->(home)
        """
    else:
        game_string = """
        MERGE (home)-[:LOST_TO {location: $location, neutral: $neutral, home_score: $home_score, away_score: $away_score}]->(away)
        """
    driver.execute_query(
        """
        MERGE (home:Team {name: $home_team})
        MERGE (away:Team {name: $away_team})
        """ + game_string,
        home_team=home_team,
        away_team=away_team,
        location=home_team,
        neutral=neutral_site,
        home_score=home_score,
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


if __name__ == "__main__":
    main()
