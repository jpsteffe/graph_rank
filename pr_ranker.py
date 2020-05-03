import logging
from datetime import datetime
from sportsreference.ncaab.teams import Teams

log_level = logging.INFO

ranker_log = logging.getLogger('ranker')
ch = logging.StreamHandler()
ch.setLevel(log_level)
ranker_log.setLevel(log_level)
ranker_log.addHandler(ch)

skip_postseason = True
delta = 0.00005


class SeasonGraph:
    def __init__(self):
        self.teams = {}


class TeamNode:
    def __init__(self, name, score=0.0):
        self.name = name
        self.edges = {}
        self.score = None
        self.next_score = score


class GameEdge:
    def __init__(self, points_for, points_against, location, date):
        self.points_for = points_for
        self.points_against = points_against
        self.location = location
        self.date = date


def make_graph():
    sg = SeasonGraph()

    ranker_log.info("Collecting teams...")
    sr_teams = Teams(year=2019)
    num_teams = len(sr_teams)
    for t in sr_teams:
        ranker_log.debug('{}'.format(t.abbreviation.upper()))
        sg.teams[t.abbreviation.upper()] = TeamNode(t.abbreviation.upper(), score=1.0/num_teams)

    ranker_log.info("Collecting games...")
    for t in sr_teams:
        ranker_log.debug('{}'.format(t.abbreviation.upper()))
        for g in t.schedule:
            ranker_log.debug('{}'.format(g.opponent_abbr.upper()))
            if g.opponent_abbr.upper() not in sg.teams.keys():
                ranker_log.warning("Skipping game: '{}' not in graph".format(g.opponent_abbr.upper()))
            elif g.datetime.date() >= datetime.now().date():
                ranker_log.warning("Skipping game: Has not been played yet")
            elif skip_postseason and g.type != 'Reg':
                ranker_log.warning("Skipping game: Not in the regular season")
            elif g.points_for < g.points_against:
                ranker_log.warning("Skipping game: Win")
            else:
                sg.teams[t.abbreviation.upper()].edges[g.opponent_abbr.upper()] = \
                    GameEdge(g.points_for, g.points_against, g.location, g.datetime)

    return sg


def check_ranks_converged(graph: SeasonGraph):
    for team in graph.teams.values():
        if abs(team.score - team.next_score) > delta:
            return False
    return True


def main():
    g = make_graph()
    while True:
        for team in g.teams.values():
            team.score = team.next_score
            team.next_score = 0.0
        for team in g.teams.values():
            for opp_key, game in team.edges.items():
                team.next_score += g.teams[opp_key].score/len(g.teams[opp_key].edges)

        if check_ranks_converged(g):
            break

    for i, team in enumerate(sorted(g.teams.values(), key=lambda t: t.score, reverse=True)):
        print("#{} - {} - {}".format(i+1, team.name, team.score))


if __name__ == '__main__':
    main()
