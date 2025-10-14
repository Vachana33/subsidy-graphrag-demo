# ingest.py
from pydantic import BaseModel, Field
from typing import List, Optional
import fitz
from falkordb import FalkorDB
from rapidfuzz import process, fuzz
import os, re, time

FALKOR_HOST = os.getenv("FALKOR_HOST", "localhost")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "6379"))
FALKOR_PASSWORD = os.getenv("FALKOR_PASSWORD")
GRAPH_NAME = os.getenv("GRAPH_NAME", "subsidy_demo")

class ProgramExtract(BaseModel):
    name: str
    level: Optional[str] = None
    max_amount_eur: Optional[int] = None
    cofund_rate: Optional[float] = None  # 0..1
    deadline: Optional[str] = None
    documents: List[str] = Field(default_factory=list)
    criteria: List[str] = Field(default_factory=list)
    authority: Optional[str] = None
    confidence: float = 0.6

def pdf_text(path: str) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text("text") for page in doc)

def _grab(text: str, rx: str, cast=lambda x:x):
    m = re.search(rx, text, re.I)
    return cast(m.group(1)) if m else None

def rule_extract(text: str) -> ProgramExtract:
    name = _grab(text, r"(?:Programm|Program|Förderung)\s*:\s*(.+)")
    max_eur = _grab(text, r"(?:Max\.?\s*Betrag|Höchstfördersumme)\s*:\s*€?\s*([\d\.\,]+)",
                    cast=lambda x:int(x.replace(".","").replace(",","")))
    cofund = _grab(text, r"(?:Kofinanzierung|Fördersatz)\s*:\s*([\d\.]+)\s*%?",
                   cast=lambda x: (float(x)/100 if float(x) > 1 else float(x)))
    deadline = _grab(text, r"(?:Stichtag|Deadline)\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|rolling)")
    docs = [d for d in ["Business Plan","Finanzplan","Jahresabschlüsse","Handelsregisterauszug","Energieaudit"]
            if re.search(d, text, re.I)]
    crits = []
    if re.search(r"\bKMU\b|\bSME\b", text): crits.append("SME_DEF")
    if re.search(r"\bNRW\b|Nordrhein", text): crits.append("REGION_NRW")
    if re.search(r"10%\s*Energie|Energy\s*10%", text): crits.append("ENERGY_SAVING")
    auth = _grab(text, r"(?:Bewilligungsstelle|Authority|Träger)\s*:\s*(.+)")
    name = name or "Unbenanntes Programm"
    filled = sum([name is not None, max_eur is not None, cofund is not None, deadline is not None, bool(docs), bool(crits), auth is not None])
    conf = min(0.5 + 0.05 * filled, 0.95)
    return ProgramExtract(name=name, level=None, max_amount_eur=max_eur, cofund_rate=cofund,
                          deadline=deadline, documents=docs, criteria=crits, authority=auth,
                          confidence=conf)

def upsert_program(ext: ProgramExtract, src_title: str, src_url: Optional[str]=None):
    g = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT, password=FALKOR_PASSWORD).select_graph(GRAPH_NAME)
    g.query("MERGE (s:SourceDoc {id:$id}) SET s.title=$title, s.url=$url, s.ingest_ts=$ts",
            {"id": src_title, "title": src_title, "url": src_url, "ts": int(time.time())})
    # authority (fuzzy)
    authority_name = None
    if ext.authority:
        known = [r[0] for r in g.query("MATCH (a:Authority) RETURN a.name").result_set]
        best = process.extractOne(ext.authority, known, scorer=fuzz.WRatio)
        authority_name = best[0] if best and best[1] > 90 else ext.authority
        g.query("MERGE (a:Authority {name:$n})", {"n": authority_name})
    g.query("""
        MERGE (p:SubsidyProgram {name:$name})
        SET p.level=coalesce($level,p.level),
            p.max_amount_eur=coalesce($max,p.max_amount_eur),
            p.cofund_rate=coalesce($rate,p.cofund_rate),
            p.deadline=coalesce($deadline,p.deadline)
        """, {"name": ext.name, "level": ext.level, "max": ext.max_amount_eur,
              "rate": ext.cofund_rate, "deadline": ext.deadline})
    g.query("""
        MATCH (p:SubsidyProgram {name:$p}), (s:SourceDoc {id:$sid})
        MERGE (p)-[r:EXTRACTED_FROM]->(s)
        SET r.confidence=$conf
    """, {"p": ext.name, "sid": src_title, "conf": ext.confidence})
    for d in ext.documents:
        g.query("MERGE (doc:Document {name:$n})", {"n": d})
        g.query("""
            MATCH (p:SubsidyProgram {name:$p}), (doc:Document {name:$d})
            MERGE (p)-[:REQUIRES_DOCUMENT]->(doc)
        """, {"p": ext.name, "d": d})
    for code in ext.criteria:
        g.query("MERGE (c:EligibilityCriterion {code:$n}) SET c.name=coalesce(c.name,$n)", {"n": code})
        g.query("""
            MATCH (p:SubsidyProgram {name:$p}), (c:EligibilityCriterion {code:$code})
            MERGE (p)-[:ELIGIBLE_IF]->(c)
        """, {"p": ext.name, "code": code})
    if authority_name:
        g.query("""
            MATCH (p:SubsidyProgram {name:$p}), (a:Authority {name:$a})
            MERGE (p)-[:MANAGED_BY]->(a)
        """, {"p": ext.name, "a": authority_name})

if __name__ == "__main__":
    text = pdf_text("samples/subsidy_example.pdf")
    ext = rule_extract(text)
    upsert_program(ext, src_title="subsidy_example.pdf")
    print("Ingested:", ext.model_dump())
