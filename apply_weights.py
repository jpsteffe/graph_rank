import neo4j


def mcbr_game_weights(driver, game):
    """
    Currently this function doesn't take into account that multiple games can be played between the same teams.
    Because we look up the edges based on the node IDs
    :param driver:
    :param game:
    :return:
    """
    team, game, opponent, avg_2nd_order_win_percent = game
    # print(f"Calulating score for game between: {team['name']} and {opponent['name']}")
    if game['neutral']:
        location_coefficient = 0.95
    elif game['location'] == team['name']:
        location_coefficient = 0.9
    else:
        location_coefficient = 1.0

    if game['point_diff'] > 0:
        win_score = 1 + 0.05 + (game['point_diff'] * 0.01)
    else:
        win_score = 1 - 0.05 + (game['point_diff'] * 0.01)

    game_score = location_coefficient * (win_score + opponent['win_percent'] * .75 + avg_2nd_order_win_percent * .25)

    driver.execute_query(
        """
        MATCH ()-[g]->()
        WHERE elementId(g) = $id
        SET g.mcbr_score=$score
        """,
        id=game.element_id,
        score=game_score
    )


def main():

    with neo4j.GraphDatabase.driver("neo4j://localhost:7687", auth=None) as driver:
        games, _, _ = driver.execute_query(
            """
            MATCH (t)-[g]->(o)
            WITH *
            MATCH (o)-[]->(oo)
            RETURN t,g,o,avg(oo.win_percent) as avg_2nd_order_win_percent
            """
        )
        for game in games:
            mcbr_game_weights(driver, game)


if __name__ == "__main__":
    main()
