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


class SeasonGraph:
    def __init__(self):
        self.teams = {}


class TeamNode:
    def __init__(self, name):
        self.name = name
        self.edges = {}
        self.score = 0.0


class GameEdge:
    def __init__(self, points_for, points_against, location, date):
        self.points_for = points_for
        self.points_against = points_against
        self.location = location
        self.date = date
        self.score = 0.0


def make_graph():
    sg = SeasonGraph()

    ranker_log.info("Collecting teams...")
    sr_teams = Teams(year=2020)
    for t in sr_teams:
        ranker_log.debug('{}'.format(t.abbreviation.upper()))
        sg.teams[t.abbreviation.upper()] = TeamNode(t.abbreviation.upper())

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
            else:
                sg.teams[t.abbreviation.upper()].edges[g.opponent_abbr.upper()] = \
                    GameEdge(g.points_for, g.points_against, g.location, g.datetime)

    return sg


def get_win_pct(graph, team_key):
    team = graph.teams[team_key]
    wins = 0.0
    for game in team.edges.values():
        if game.points_for > game.points_against:
            wins += 1.0

    return wins/len(team.edges)


def main():
    g = make_graph()
    for team_key, team in g.teams.items():
        ranker_log.debug("{}".format(team_key))
        sum_game_scores = 0.0
        for opponent_key, game in team.edges.items():
            if game.location == 'Home':
                location_score = .9
            elif game.location == 'Neutral':
                location_score = .95
            elif game.location == 'Away':
                location_score = 1.0
            else:
                raise TypeError

            point_diff = max(min(game.points_for - game.points_against, 20), -20)
            win_score = 1 + 0.05 * (point_diff / abs(point_diff)) + (point_diff * 0.01)

            opp_win_pct = get_win_pct(g, opponent_key)

            opponent = g.teams[opponent_key]
            opp_opp_win_pct_total = 0.0
            for opp_opp_key in opponent.edges.keys():
                opp_opp_win_pct_total += get_win_pct(g, opp_opp_key)

            opp_opp_win_pct = opp_opp_win_pct_total/len(opponent.edges)

            game.score = location_score * (win_score + opp_win_pct * .75 + opp_opp_win_pct * .25)
            sum_game_scores += game.score

        team.score = sum_game_scores/len(team.edges)

    for i, team in enumerate(sorted(g.teams.values(), key=lambda t: t.score, reverse=True)):
        print("#{} - {} - {}".format(i+1, team.name, team.score))


if __name__ == '__main__':
    main()
