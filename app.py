# app.py
import os
import yaml
from falkordb import FalkorDB

# -----------------------------
# Connection (env-friendly)
# -----------------------------
FALKOR_HOST = os.getenv("FALKOR_HOST", "localhost")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "6379"))
FALKOR_PASSWORD = os.getenv("FALKOR_PASSWORD")  # optional
GRAPH_NAME = os.getenv("GRAPH_NAME", "subsidy_demo")
RESET_GRAPH = os.getenv("RESET_GRAPH", "1")  # "1" to reset on run (dev only)

def get_graph():
    client = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT, password=FALKOR_PASSWORD)
    return client.select_graph(GRAPH_NAME)

g = get_graph()

# -----------------------------
# Ontology
# -----------------------------
with open("ontology.yaml", "r") as f:
    ONT = yaml.safe_load(f)

def ensure_label(label: str):
    if label not in ONT["nodes"]:
        raise ValueError(f"Unknown node label: {label}")

def ensure_rel(rel: str, src: str, dst: str):
    if rel not in ONT["relations"]:
        raise ValueError(f"Unknown relation: {rel}")
    spec = ONT["relations"][rel]
    if spec["from"] != src or spec["to"] != dst:
        raise ValueError(f"{rel} must be {spec['from']} -> {spec['to']}")

# -----------------------------
# Upsert helpers
# -----------------------------
def merge_node(label: str, props: dict):
    """Upsert node by `name` (your chosen key across labels)."""
    ensure_label(label)
    if label == "Company":
        if props.get("sector") not in ONT["allowed_sectors"]:
            raise ValueError("Sector not allowed")
        if props.get("region") not in ONT["allowed_regions"]:
            raise ValueError("Region not allowed")
        if props.get("size") not in ONT["allowed_sizes"]:
            raise ValueError("Size not allowed")
    if "name" not in props:
        raise ValueError(f"{label} requires a `name` property for MERGE key.")
    g.query(f"MERGE (n:{label} {{name:$name}}) SET n += $props",
            {"name": props["name"], "props": props})

def merge_edge(rel: str, src_label: str, src_name: str, dst_label: str, dst_name: str, eprops: dict | None = None):
    """Upsert relationship with optional edge properties."""
    ensure_rel(rel, src_label, dst_label)
    q = f"""
    MERGE (s:{src_label} {{name:$s}})
    MERGE (d:{dst_label} {{name:$d}})
    MERGE (s)-[r:{rel}]->(d)
    SET r += $eprops
    """
    g.query(q, {"s": src_name, "d": dst_name, "eprops": eprops or {}})

# -----------------------------
# Seed data
# -----------------------------
def seed_demo():
    # Companies
    merge_node("Company", {
        "name": "ACME Maschinenbau GmbH", "sector": "manufacturing",
        "size": "small", "region": "DE-NW", "founded_year": 2018
    })
    merge_node("Company", {
        "name": "TemplateSoftBY", "sector": "software",
        "size": "medium", "region": "DE-BY", "founded_year": 2020
    })
    merge_node("Company", {
        "name": "TemplateEnergyBE", "sector": "energy",
        "size": "small", "region": "DE-BE", "founded_year": 2019
    })

    # Authorities
    merge_node("Authority", {"name": "BMWK", "country": "DE", "url": "https://www.bmwk.de"})
    merge_node("Authority", {"name": "KfW",  "country": "DE", "url": "https://www.kfw.de"})

    # Documents
    for n, d in [
        ("Business Plan", "Kurzbeschreibung"),
        ("Financial Statements", "Bilanzen/GuV 2 Jahre"),
        ("Company Registration", "Handelsregisterauszug"),
        ("Energy Audit Report", "DIN 18599/16247"),
    ]:
        merge_node("Document", {"name": n, "description": d})

    # Criteria
    for code, desc in [
        ("SME_DEF", "EU-KMU"),
        ("REGION_TARGET", "Sitz in Zielregion"),
        ("ENERGY_SAVING", ">10% Energieeinsparung"),
    ]:
        merge_node("EligibilityCriterion", {"name": code, "code": code, "description": desc})

    # Programs
    merge_node("SubsidyProgram", {
        "name": "KMU Innovationsgutschein", "level": "federal",
        "max_amount_eur": 25000, "cofund_rate": 0.5, "deadline": "rolling"
    })
    merge_node("SubsidyProgram", {
        "name": "Digitalisierung Mittelstand NRW", "level": "state",
        "max_amount_eur": 15000, "cofund_rate": 0.4, "deadline": "2025-12-31"
    })
    merge_node("SubsidyProgram", {
        "name": "Energieeffizienz Plus", "level": "federal",
        "max_amount_eur": 50000, "cofund_rate": 0.6, "deadline": "rolling"
    })

    # Program ↔ Template companies (demo)
    merge_edge("APPLIES_TO_SECTOR", "SubsidyProgram", "KMU Innovationsgutschein", "Company", "TemplateSoftBY")
    merge_edge("APPLIES_TO_REGION", "SubsidyProgram", "KMU Innovationsgutschein", "Company", "TemplateSoftBY")

    merge_edge("APPLIES_TO_SECTOR", "SubsidyProgram", "Energieeffizienz Plus", "Company", "TemplateEnergyBE")
    merge_edge("APPLIES_TO_REGION", "SubsidyProgram", "Energieeffizienz Plus", "Company", "TemplateEnergyBE")

    # Program ↔ ACME
    for prog in ["KMU Innovationsgutschein", "Digitalisierung Mittelstand NRW", "Energieeffizienz Plus"]:
        merge_edge("APPLIES_TO_SECTOR", "SubsidyProgram", prog, "Company", "ACME Maschinenbau GmbH")
        merge_edge("APPLIES_TO_REGION", "SubsidyProgram", prog, "Company", "ACME Maschinenbau GmbH")

    # Program ↔ Authority
    merge_edge("MANAGED_BY", "SubsidyProgram", "KMU Innovationsgutschein", "Authority", "BMWK")
    merge_edge("MANAGED_BY", "SubsidyProgram", "Digitalisierung Mittelstand NRW", "Authority", "BMWK")
    merge_edge("MANAGED_BY", "SubsidyProgram", "Energieeffizienz Plus", "Authority", "KfW")

    # Program ↔ Required documents
    for prog, doc in [
        ("KMU Innovationsgutschein", "Business Plan"),
        ("KMU Innovationsgutschein", "Company Registration"),
        ("Digitalisierung Mittelstand NRW", "Business Plan"),
        ("Digitalisierung Mittelstand NRW", "Financial Statements"),
        ("Energieeffizienz Plus", "Energy Audit Report"),
        ("Energieeffizienz Plus", "Company Registration"),
    ]:
        merge_edge("REQUIRES_DOCUMENT", "SubsidyProgram", prog, "Document", doc)

    # Program ↔ Eligibility
    merge_edge("ELIGIBLE_IF", "SubsidyProgram", "KMU Innovationsgutschein", "EligibilityCriterion", "SME_DEF")
    merge_edge("ELIGIBLE_IF", "SubsidyProgram", "Digitalisierung Mittelstand NRW", "EligibilityCriterion", "SME_DEF")
    merge_edge("ELIGIBLE_IF", "SubsidyProgram", "Digitalisierung Mittelstand NRW", "EligibilityCriterion", "REGION_TARGET")
    merge_edge("ELIGIBLE_IF", "SubsidyProgram", "Energieeffizienz Plus", "EligibilityCriterion", "ENERGY_SAVING")

    # Optional: provenance sample (only if defined in ontology)
    if "SourceDoc" in ONT["nodes"] and "EXTRACTED_FROM" in ONT["relations"]:
        merge_node("SourceDoc", {
            "name": "seed_demo.pdf",  # we key by name as elsewhere
            "id": "seed_demo.pdf",
            "title": "Seed Demo Source",
            "url": None,
            "ingest_ts": 1720000000
        })
        merge_edge("EXTRACTED_FROM", "SubsidyProgram", "KMU Innovationsgutschein", "SourceDoc", "seed_demo.pdf", {"confidence": 0.9})

# -----------------------------
# Query helper
# -----------------------------
def run(q: str):
    rs = g.query(q).result_set
    print("\nCypher:\n", q.strip(), "\nResult:")
    for row in rs:
        print(row)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    if RESET_GRAPH == "1":
        g.query("MATCH (n) DETACH DELETE n")

    seed_demo()
    print("Seeded ✅")

    # sample queries
    run("""
    MATCH (:Company {name:'ACME Maschinenbau GmbH'})
          <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
    RETURN DISTINCT p.name, p.max_amount_eur, p.cofund_rate, p.deadline
    ORDER BY p.max_amount_eur DESC
    """)

    run("""
    MATCH (p:SubsidyProgram)-[:REQUIRES_DOCUMENT]->(d:Document)
    RETURN p.name AS program, collect(d.name) AS docs
    ORDER BY program
    """)

    run("""
    MATCH (:Company {name:'ACME Maschinenbau GmbH'})
        <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
    OPTIONAL MATCH (p)-[:REQUIRES_DOCUMENT]->(d:Document)
    OPTIONAL MATCH (p)-[:MANAGED_BY]->(a:Authority)
    RETURN p.name AS program, a.name AS authority, collect(DISTINCT d.name) AS docs
    ORDER BY program
    """)
