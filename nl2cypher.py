import os
import requests

SCHEMA_TEXT = """
You are a Cypher generator for a FalkorDB/OpenCypher graph.

Nodes:
  - Company(name, sector, size, region, founded_year)
  - SubsidyProgram(name, level, max_amount_eur, cofund_rate, deadline)
  - Authority(name, country, url)
  - Document(name, description)
  - EligibilityCriterion(name, code, description)

Relationships:
  - (SubsidyProgram)-[:MANAGED_BY]->(Authority)
  - (SubsidyProgram)-[:APPLIES_TO_SECTOR]->(Company)
  - (SubsidyProgram)-[:APPLIES_TO_REGION]->(Company)
  - (SubsidyProgram)-[:REQUIRES_DOCUMENT]->(Document)
  - (SubsidyProgram)-[:ELIGIBLE_IF]->(EligibilityCriterion)

Rules:
- Use only labels/relations above.
- No destructive queries (no DELETE).
- Return a compact, useful set of columns.
"""

FEW_SHOTS = [
    {
        "q": "Which subsidies apply to small companies in NRW?",
        "cypher": """
MATCH (c:Company {size:'small', region:'DE-NW'})
      <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
RETURN DISTINCT p.name AS program, p.max_amount_eur AS max_eur, p.cofund_rate AS cofund, p.deadline AS deadline
ORDER BY max_eur DESC
""".strip()
    },
    {
        "q": "What documents are required for each program?",
        "cypher": """
MATCH (p:SubsidyProgram)-[:REQUIRES_DOCUMENT]->(d:Document)
RETURN p.name AS program, collect(DISTINCT d.name) AS required_docs
ORDER BY program
""".strip()
    },
    {
        "q": "Who manages each program?",
        "cypher": """
MATCH (p:SubsidyProgram)-[:MANAGED_BY]->(a:Authority)
RETURN p.name AS program, a.name AS authority
ORDER BY program
""".strip()
    },
]

def _prompt(user_q: str) -> str:
    examples = "\n\n".join([f"Q: {e['q']}\nCypher:\n{e['cypher']}" for e in FEW_SHOTS])
    return f"""{SCHEMA_TEXT}

Translate the user's question into a single OpenCypher query.
Return ONLY the Cypher query, nothing else.

Examples:
{examples}

User question:
{user_q}
Cypher:
""".strip()

def generate_with_openai(user_q: str) -> str:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You output only valid OpenCypher. No prose."},
            {"role":"user","content": _prompt(user_q)},
        ],
        temperature=0.1,
        max_tokens=400,
    )
    return resp.choices[0].message.content.strip()

def generate_with_ollama(user_q: str, model: str = "llama3.1") -> str:
    data = {
        "model": model,
        "prompt": f"System: You output only valid OpenCypher. No prose.\n\nUser:\n{_prompt(user_q)}",
        "options": {"temperature": 0.1},
    }
    r = requests.post("http://localhost:11434/api/generate", json=data, timeout=120)
    r.raise_for_status()
    return r.json().get("response","").strip()

def generate_with_rules(user_q: str) -> str:
    q = user_q.lower()
    if ("subsid" in q) and ("apply" in q):
        size = "small" if "small" in q else None
        region = "DE-NW" if ("nrw" in q or "north rhine" in q or "nordrhein" in q) else None
        if size and region:
            return f"""
MATCH (c:Company {{size:'{size}', region:'{region}'}})
      <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
RETURN DISTINCT p.name AS program, p.max_amount_eur AS max_eur, p.cofund_rate AS cofund, p.deadline AS deadline
ORDER BY max_eur DESC
""".strip()
        return """
MATCH (:Company {name:'ACME Maschinenbau GmbH'})
      <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
RETURN DISTINCT p.name AS program, p.max_amount_eur AS max_eur, p.cofund_rate AS cofund, p.deadline AS deadline
ORDER BY max_eur DESC
""".strip()
    if "document" in q and ("need" in q or "required" in q or "require" in q):
        return """
MATCH (p:SubsidyProgram)-[:REQUIRES_DOCUMENT]->(d:Document)
RETURN p.name AS program, collect(DISTINCT d.name) AS required_docs
ORDER BY program
""".strip()
    if "manage" in q or "authority" in q:
        return """
MATCH (p:SubsidyProgram)-[:MANAGED_BY]->(a:Authority)
RETURN p.name AS program, a.name AS authority
ORDER BY program
""".strip()
    # default demo
    return """
MATCH (:Company {name:'ACME Maschinenbau GmbH'})
      <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
RETURN DISTINCT p.name AS program, p.max_amount_eur AS max_eur, p.cofund_rate AS cofund, p.deadline AS deadline
ORDER BY max_eur DESC
""".strip()

def generate_cypher(user_q: str, provider: str = "Rules", ollama_model: str = "llama3.1") -> str:
    p = (provider or "Rules").lower()
    if p == "openai":
        return generate_with_openai(user_q)
    if p == "ollama":
        return generate_with_ollama(user_q, model=ollama_model)
    return generate_with_rules(user_q)
