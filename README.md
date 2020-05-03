# Graph Rank
Graph Rank is an idea to rank sports teams based on the idea to convert their seasons into a computer science graph where each node is a team and the edges represent games played. It began as a NCAA Basketball ranking algorithm but could be further extended to include teams from any sport.

There are two algorithms currently implemented, one is a typical PageRank algorithm, and the other the MCBR (Mitchell's College Basketball Ranker) algorithm is essentially a modified version of PageRank developed by Mitchell Steffensmeier.

## Algorithms
### Graph Creation
Both algorithms work by using the sportsreference python package to scrape the teams and games into a locally stored connected di-graph for data processing. 

The nodes are created first and the identifiers cached in the graph to reduce network calls. The teams are then looped and their schedules are queries. The edges are created as long as they meet all of the following criteria:
  1. Both teams are in the nodes list
  2. The game has been played (it is not on a future date)
  3. The game was a part of the regular season

### PageRank
The PageRank algorithm adds one additional constraint to edge creation which is that edges will only be created in the direction from the loser to the winner. This way the team that lost the game will give that portion of their score to the team that won the game. 

More information on the PageRank algorithm is available [here](https://en.wikipedia.org/wiki/PageRank).

### MCBR
The MCBR algorithm computes a more sports oriented score for each edge of the graph. It then sums these scores for each team to come up with that team's overall score. The directinality of the edges is ignored in this algorithm and the overall score is not passed along to other teams during the edge score creation process, in this way it is different than PageRank. Since team score is not passed along to other teams, this means that only one round of iteration is required for the algorithm to converge.

This is the formula to calculate the MCBR score of one team:
<img src='https://jpsteffe.com/content/images/2020/05/MCBR-2.png'>

Where <img src='https://jpsteffe.com/content/images/2020/05/G_v.png' height='16'> is the set of vertices connected to v, and <img src='https://jpsteffe.com/content/images/2020/05/ell-1.png' height='16'> is a location scaling factor.

The formula for the location factor is below:
<img src='https://jpsteffe.com/content/images/2020/05/xell_u_v.png.pagespeed.ic.gMTzVmajvc.webp'>

The last piece is the Game Score Formula which is:
<img src='https://jpsteffe.com/content/images/2020/05/W_u_v.png'>

Where <img src='https://jpsteffe.com/content/images/2020/05/delta_score.png' height='16'> is the score differential of the game between u and v capped at plus or minus 20.
