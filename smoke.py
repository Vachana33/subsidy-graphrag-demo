from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
g = db.select_graph("hello")

# clean (dev only)
g.query("MATCH (n) DETACH DELETE n")

# write a node + edge
g.query("""
CREATE (:Person {name:'Alice'})-[:KNOWS]->(:Person {name:'Bob'})
""")

# read it back
rs = g.query("""
MATCH (a:Person)-[:KNOWS]->(b:Person)
RETURN a.name, b.name
""").result_set

print("Result:", rs)

# smoke.py
from app import get_graph, seed_minimal

if __name__ == "__main__":
    print(seed_minimal())
    g = get_graph()
    rs = g.query("MATCH (p:SubsidyProgram) RETURN p.name, p.max_amount_eur").result_set
    print("Programs:", rs)
