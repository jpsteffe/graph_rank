import neo4j


def main():
    with neo4j.GraphDatabase.driver("neo4j://localhost:7687", auth=None) as driver:
        teams, _, _ = driver.execute_query(
            """
            match (t:Team)-[g]->()
            return t, avg(g.mcbr_score) as mcbr_score
            ORDER BY mcbr_score DESC
            """
        )
        for rank, team in enumerate(teams):
            team, score = team
            print(f"#{rank+1} - {team['name']} - {score}")


if __name__ == "__main__":
    main()
