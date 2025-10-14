# agent_tools.py
from langchain.tools import tool
from falkordb import FalkorDB
import os

FALKOR_HOST = os.getenv("FALKOR_HOST", "localhost")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "6379"))
FALKOR_PASSWORD = os.getenv("FALKOR_PASSWORD")
GRAPH_NAME = os.getenv("GRAPH_NAME", "subsidy_demo")
_graph = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT, password=FALKOR_PASSWORD).select_graph(GRAPH_NAME)

@tool("run_cypher", return_direct=False)
def run_cypher(query: str) -> str:
    """Run a safe OpenCypher query (no DELETE/DROP/UPDATE). Returns rows."""
    U = query.upper()
    if any(k in U for k in [" DELETE ", " DROP ", " UPDATE ", " REMOVE ", " DETACH "]):
        return "Refused: destructive query."
    try:
        rs = _graph.query(query).result_set
        return "\n".join([", ".join(map(lambda x: str(x), row)) for row in rs]) or "(no results)"
    except Exception as e:
        return f"(error) {e}"

@tool("upsert_program", return_direct=False)
def upsert_program(name: str, authority: str = "", max_amount_eur: int | None = None) -> str:
    """Create/Update a SubsidyProgram and link to Authority."""
    _graph.query("MERGE (p:SubsidyProgram {name:$n}) SET p.max_amount_eur=coalesce($m,p.max_amount_eur)", {"n": name, "m": max_amount_eur})
    if authority:
        _graph.query("MERGE (a:Authority {name:$a})", {"a": authority})
        _graph.query("""MATCH (p:SubsidyProgram {name:$n}),(a:Authority {name:$a}) MERGE (p)-[:MANAGED_BY]->(a)""",
                    {"n": name, "a": authority})
    return f"Upserted program='{name}', authority='{authority or '(none)'}', max={max_amount_eur}"
