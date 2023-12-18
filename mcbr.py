"""
match (t:Team) -[g]->()
return t, avg(g.mcbr_score) as mcbr_score
ORDER BY mcbr_score DESC
"""