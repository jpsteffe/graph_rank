import neo4j
import typer


def check_ranks_converged(teams, delta):
    for team in teams.values():
        if abs(team.score - team.next_score) > delta:
            return False
    return True


def main(max_iterations: int = 20, delta: float = 0.0001, damping: float = 0.85):
    with (neo4j.GraphDatabase.driver("neo4j://localhost:7687", auth=None) as driver):
        team_results, _, _ = driver.execute_query(
            """
            MATCH (t:Team)
            OPTIONAL MATCH (t)-[g:LOST]->()
            RETURN t, count(g) as num_losses
            """
        )
        teams = dict()
        for team, num_losses in team_results:
            team.score = 1.0/len(team_results)
            team.next_score = team.score
            team.num_losses = num_losses
            teams[team['name']] = team

        for i in range(max_iterations):
            print(f"Iteration {i+1}/{max_iterations}")
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
                    team.next_score += (teams[opponent['name']].score / teams[opponent['name']].num_losses) * damping
                team.next_score += (1-damping)/len(teams)

            if check_ranks_converged(teams, delta):
                break

        for rank, team in enumerate(sorted(teams.values(), key=lambda t: t.score, reverse=True)):
            print(f"#{rank+1} - {team['name']} - {team.score}")


if __name__ == "__main__":
    typer.run(main)
