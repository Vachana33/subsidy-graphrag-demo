from falkordb import FalkorDB
import yaml

# --- connect ---
db = FalkorDB(host="localhost", port=6379)
g = db.select_graph("subsidy_demo")

# --- ontology ---
with open("ontology.yaml","r") as f:
    ONT = yaml.safe_load(f)

def ensure_label(label):
    if label not in ONT["nodes"]:
        raise ValueError(f"Unknown node label: {label}")

def ensure_rel(rel, src, dst):
    if rel not in ONT["relations"]:
        raise ValueError(f"Unknown relation: {rel}")
    spec = ONT["relations"][rel]
    if spec["from"] != src or spec["to"] != dst:
        raise ValueError(f"{rel} must be {spec['from']} -> {spec['to']}")

def merge_node(label, props):
    ensure_label(label)
    if label == "Company":
        if props.get("sector") not in ONT["allowed_sectors"]:
            raise ValueError("Sector not allowed")
        if props.get("region") not in ONT["allowed_regions"]:
            raise ValueError("Region not allowed")
        if props.get("size") not in ONT["allowed_sizes"]:
            raise ValueError("Size not allowed")
    g.query(f"MERGE (n:{label} {{name:$name}}) SET n += $props",
            {"name": props["name"], "props": props})

def merge_edge(rel, src_label, src_name, dst_label, dst_name, eprops=None):
    ensure_rel(rel, src_label, dst_label)
    q = f"""
    MERGE (s:{src_label} {{name:$s}})
    MERGE (d:{dst_label} {{name:$d}})
    MERGE (s)-[r:{rel}]->(d)
    SET r += $eprops
    """
    g.query(q, {"s": src_name, "d": dst_name, "eprops": eprops or {}})

# --- reset demo data (dev only) ---
g.query("MATCH (n) DETACH DELETE n")

# --- seed ---
merge_node("Company", {"name":"ACME Maschinenbau GmbH","sector":"manufacturing","size":"small","region":"DE-NW","founded_year":2018})
merge_node("Authority", {"name":"BMWK","country":"DE","url":"https://www.bmwk.de"})
merge_node("Authority", {"name":"KfW","country":"DE","url":"https://www.kfw.de"})

for n,d in [("Business Plan","Kurzbeschreibung"),
            ("Financial Statements","Bilanzen/GuV 2 Jahre"),
            ("Company Registration","Handelsregisterauszug"),
            ("Energy Audit Report","DIN 18599/16247")]:
    merge_node("Document", {"name":n, "description":d})

for code,desc in [("SME_DEF","EU-KMU"),
                  ("REGION_TARGET","Sitz in Zielregion"),
                  ("ENERGY_SAVING",">10% Energieeinsparung")]:
    merge_node("EligibilityCriterion", {"name":code,"code":code,"description":desc})

merge_node("SubsidyProgram", {"name":"KMU Innovationsgutschein","level":"federal","max_amount_eur":25000,"cofund_rate":0.5,"deadline":"rolling"})
merge_node("SubsidyProgram", {"name":"Digitalisierung Mittelstand NRW","level":"state","max_amount_eur":15000,"cofund_rate":0.4,"deadline":"2025-12-31"})
merge_node("SubsidyProgram", {"name":"Energieeffizienz Plus","level":"federal","max_amount_eur":50000,"cofund_rate":0.6,"deadline":"rolling"})

merge_edge("MANAGED_BY","SubsidyProgram","KMU Innovationsgutschein","Authority","BMWK")
merge_edge("MANAGED_BY","SubsidyProgram","Digitalisierung Mittelstand NRW","Authority","BMWK")
merge_edge("MANAGED_BY","SubsidyProgram","Energieeffizienz Plus","Authority","KfW")

for prog in ["KMU Innovationsgutschein","Digitalisierung Mittelstand NRW","Energieeffizienz Plus"]:
    merge_edge("APPLIES_TO_SECTOR","SubsidyProgram",prog,"Company","ACME Maschinenbau GmbH")
    merge_edge("APPLIES_TO_REGION","SubsidyProgram",prog,"Company","ACME Maschinenbau GmbH")

for prog,doc in [("KMU Innovationsgutschein","Business Plan"),
                 ("KMU Innovationsgutschein","Company Registration"),
                 ("Digitalisierung Mittelstand NRW","Business Plan"),
                 ("Digitalisierung Mittelstand NRW","Financial Statements"),
                 ("Energieeffizienz Plus","Energy Audit Report"),
                 ("Energieeffizienz Plus","Company Registration")]:
    merge_edge("REQUIRES_DOCUMENT","SubsidyProgram",prog,"Document",doc)

merge_edge("ELIGIBLE_IF","SubsidyProgram","KMU Innovationsgutschein","EligibilityCriterion","SME_DEF")
merge_edge("ELIGIBLE_IF","SubsidyProgram","Digitalisierung Mittelstand NRW","EligibilityCriterion","SME_DEF")
merge_edge("ELIGIBLE_IF","SubsidyProgram","Digitalisierung Mittelstand NRW","EligibilityCriterion","REGION_TARGET")
merge_edge("ELIGIBLE_IF","SubsidyProgram","Energieeffizienz Plus","EligibilityCriterion","ENERGY_SAVING")

print("Seeded ✅")

def run(q):
    rs = g.query(q).result_set
    print("\nCypher:\n", q.strip(), "\nResult:")
    for row in rs:
        print(row)

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
