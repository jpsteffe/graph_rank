import neo4j


def get_win_percentage(driver, team) -> float:
    """
    Opportunity to precalculate this value for each team
    :param driver:
    :param team:
    :return:
    """
    wins, _, _ = driver.execute_query(
        """
        MATCH ()-[wins:LOST_TO]->(:Team {name: $name})
        RETURN count(wins)
        """,
        name=team["name"]
    )
    losses, _, _ = driver.execute_query(
        """
        MATCH (:Team {name: $name})-[losses:LOST_TO]->()
        RETURN count(losses)
        """,
        name=team["name"]
    )
    wins = wins[0][0]
    losses = losses[0][0]
    games = wins + losses
    return wins/games if games > 0 else 0.0


def calculate_mcbr_game(driver, game, team, opponent) -> float:
    if game['neutral']:
        location_coefficient = 0.95
    elif game['location'] == team['name']:
        location_coefficient = 0.9
    else:
        location_coefficient = 1.0

    if team['name'] == game['home_team']:
        point_diff = max(min(game['home_score'] - game['away_score'], 20), -20)
    else:
        point_diff = max(min(game['away_score'] - game['home_score'], 20), -20)

    if point_diff > 0:
        win_score = 1 + 0.05 * (point_diff / abs(point_diff)) + (point_diff * 0.01)
    else:
        win_score = 1.0
    opponent_win_percentage = get_win_percentage(driver, opponent)

    second_tier_opponents, _, _ = driver.execute_query(
        """
        MATCH (t:Team)--(:Team {name:$team})
        RETURN t
        """,
        team=opponent['name']
    )
    second_tier_win_percentages = [get_win_percentage(driver, team) for team in second_tier_opponents[0]]
    second_tier_average_win_percentage = sum(second_tier_win_percentages)/len(second_tier_win_percentages)

    return location_coefficient * (win_score + opponent_win_percentage * .75 + second_tier_average_win_percentage * .25)


def mcbr_game_weights(driver, game):
    """
    Currently this function doesn't take into account that multiple games can be played between the same teams.
    Because we look up the edges based on the node IDs
    :param driver:
    :param game:
    :return:
    """
    loser, game, winner = game
    winner_game_score = calculate_mcbr_game(driver, game, winner, loser)
    print(winner.element_id)
    print(game.element_id)
    driver.execute_query(
        """
        MATCH (l)-[g:LOST_TO]->(w)
        WHERE ID(w) = $winner_id AND ID(l) = $loser_id
        SET g.mcbr_winner_score=$score
        """,
        winner_id=winner.id,
        loser_id=loser.id,
        score=winner_game_score
    )
    loser_game_score = calculate_mcbr_game(driver, game, loser, winner)
    driver.execute_query(
        """
        MATCH (l)-[g:LOST_TO]->(w)
        WHERE ID(w) = $winner_id AND ID(l) = $loser_id
        SET g.mcbr_loser_score=$score
        """,
        winner_id=winner.id,
        loser_id=loser.id,
        score=loser_game_score
    )


def main(weight_functions=None):
    if weight_functions is None:
        weight_functions = list()

    with neo4j.GraphDatabase.driver("neo4j://localhost:7687", auth=None) as driver:
        games, _, _ = driver.execute_query(
            """
            MATCH (loser)-[game]->(winner)
            RETURN loser, game, winner
            """
        )
        for game in games:
            for func in weight_functions:
                func(driver, game)


if __name__ == "__main__":
    main(weight_functions=[mcbr_game_weights])
