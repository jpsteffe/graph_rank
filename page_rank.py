import neo4j

MAX_ITERATIONS = 20
DELTA = 0.00005


def check_ranks_converged(teams):
    for team in teams.values():
        if abs(team.score - team.next_score) > DELTA:
            return False
    return True


def main():
    with neo4j.GraphDatabase.driver("neo4j://localhost:7687", auth=None) as driver:
        team_results, _, _ = driver.execute_query(
            """
            match (t:Team)-[g:LOST]->()
            return t, count(g) as num_edges
            """
        )
        teams = dict()
        for team, num_edges in team_results:
            team.score = 1.0/len(team_results)  # make starting score configurable
            team.next_score = 1.0/len(team_results)  # make starting score configurable
            team.num_edges = num_edges
            teams[team['name']] = team

        for i in range(MAX_ITERATIONS):
            for team in teams.values():
                team.score = team.next_score
                team.next_score = 0.0
            for team in teams.values():
                games, _, _ = driver.execute_query(
                    """
                    MATCH (t:Team WHERE t.name = $name)-[:WON]->(opponent)
                    RETURN opponent
                    """,
                    name=team['name']
                )
                for game in games:
                    opponent = game['opponent']
                    team.next_score += teams[opponent['name']].score / teams[opponent['name']].num_edges

            if check_ranks_converged(teams):
                break

        for rank, team in enumerate(sorted(teams.values(), key=lambda t: t.score, reverse=True)):
            print(f"#{rank+1} - {team['name']} - {team.score}")


if __name__ == "__main__":
    main()
