# streamlit_app.py
import os, json, tempfile, textwrap
import streamlit as st
from falkordb import FalkorDB
from nl2cypher import generate_cypher, top5_by_max_amount

# Optional imports that shouldn't crash the app if missing
try:
    from pyvis.network import Network
    HAS_PYVIS = True
except Exception:
    HAS_PYVIS = False

try:
    from agent import make_agent
except Exception as e:
    make_agent = None
    _agent_import_err = e

st.set_page_config(page_title="Subsidy GraphRAG", layout="wide")
st.title("Subsidy GraphRAG")

# ---------- DB connection (cached) ----------
@st.cache_resource
def get_graph_cached(host: str, port: int, graph_name: str):
    db = FalkorDB(host=host, port=port)
    return db.select_graph(graph_name)

with st.sidebar:
    st.header("Database")
    host = st.text_input("Host", "localhost")
    port = st.number_input("Port", 6379, step=1)
    graph_name = st.text_input("Graph", "subsidy_demo")
    g = get_graph_cached(host, int(port), graph_name)

    st.header("LLM Provider")
    provider = st.selectbox("Choose", ["Rules", "OpenAI", "Ollama"], index=0)
    if provider == "OpenAI":
        st.caption("Set OPENAI_API_KEY in your environment.")
    if provider == "Ollama":
        ollama_model = st.text_input("Ollama model", "llama3.1")
    else:
        ollama_model = None

# One unified tabs row
tab_ask, tab_graph, tab_rec, tab_agent = st.tabs(
    ["Ask & Results", "Graph", "Top-5 Recommender", "Agent"]
)

# ---------- Ask & Results ----------
with tab_ask:
    st.subheader("Ask a question")
    default_q = "Which subsidies apply to small companies in NRW?"
    user_q = st.text_input("Natural language question", value=default_q)
    go = st.button("Generate & Run")

    def run_query(cypher: str):
        try:
            rs = g.query(cypher).result_set
            return rs, None
        except Exception as e:
            return None, str(e)

    if go:
        with st.spinner("Generating Cypher..."):
            cypher = generate_cypher(
                user_q,
                provider=provider,
                ollama_model=(ollama_model or "llama3.1"),
            )
        st.code(cypher, language="cypher")

        with st.spinner("Running on FalkorDB..."):
            rows, err = run_query(cypher)

        if err:
            st.error(f"Query error: {err}")
        else:
            if not rows:
                st.warning("No rows returned.")
            else:
                # infer headers from RETURN aliases where possible
                cols = [f"col_{i}" for i in range(len(rows[0]))]
                try:
                    upper = cypher.upper()
                    if "RETURN" in upper:
                        rp = upper.split("RETURN", 1)[1]
                        rp = rp.split("ORDER BY")[0] if "ORDER BY" in rp else rp
                        headers = [h.strip() for h in rp.split(",")]
                        parsed = [(h.split(" AS ", 1)[1].strip() if " AS " in h else h) for h in headers]
                        if len(parsed) == len(rows[0]): cols = parsed
                except Exception:
                    pass
                st.success(f"{len(rows)} row(s)")
                st.dataframe([dict(zip(cols, r)) for r in rows], use_container_width=True)

# ---------- Graph tab ----------
with tab_graph:
    st.subheader("Graph visualization")
    if not HAS_PYVIS:
        st.info("Install pyvis to enable the interactive graph: `pip install pyvis`")
    vis_mode = st.selectbox(
        "Choose subgraph",
        ["ACME neighborhood (Company ↔ Programs ↔ Docs/Authority)",
         "Everything (limited to 150 edges)"],
        index=0
    )
    build = st.button("Build graph view")

    def node_color(label: str) -> str:
        return {
            "Company": "#4C78A8",
            "SubsidyProgram": "#72B7B2",
            "Authority": "#F58518",
            "Document": "#E45756",
            "EligibilityCriterion": "#54A24B",
        }.get(label, "#999999")

    def normalize_node(ent):
        label, name = "Node", None
        if hasattr(ent, "label"):
            try:
                label = ent.label if not callable(ent.label) else ent.label()
            except Exception:
                pass
        elif hasattr(ent, "labels"):
            try:
                labs = ent.labels() if callable(ent.labels) else ent.labels
                if labs: label = list(labs)[0] if not isinstance(labs, str) else labs
            except Exception:
                pass
        elif isinstance(ent, dict):
            labs = ent.get("labels") or ent.get("label")
            if labs:
                label = list(labs)[0] if isinstance(labs, (list, tuple, set)) else str(labs)
        props = None
        if hasattr(ent, "properties"):
            props = ent.properties
        elif isinstance(ent, dict):
            props = ent.get("properties", ent)
        if isinstance(props, dict):
            name = props.get("name") or props.get("id") or props.get("code")
        if not name:
            name = f"{label}:{id(ent)}"
        return str(name), str(label)

    def normalize_rel(ent):
        if hasattr(ent, "type"):
            try:
                t = ent.type if not callable(ent.type) else ent.type()
                return str(t)
            except Exception:
                pass
        if hasattr(ent, "relation_type"):
            try:
                t = ent.relation_type if not callable(ent.relation_type) else ent.relation_type()
                return str(t)
            except Exception:
                pass
        if isinstance(ent, dict):
            return str(ent.get("type") or ent.get("relationshipType") or "REL")
        return "REL"

    if build and HAS_PYVIS:
        if vis_mode.startswith("ACME"):
            vis_query = """
            MATCH (c:Company {name:'ACME Maschinenbau GmbH'})-[r1]-(p:SubsidyProgram)
            RETURN c AS n, r1 AS r, p AS m
            UNION
            MATCH (p:SubsidyProgram)-[r2:REQUIRES_DOCUMENT]->(d:Document)
            RETURN p AS n, r2 AS r, d AS m
            UNION
            MATCH (p:SubsidyProgram)-[r3:MANAGED_BY]->(a:Authority)
            RETURN p AS n, r3 AS r, a AS m
            LIMIT 200
            """
        else:
            vis_query = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 150
            """

        rs = g.query(vis_query).result_set

        net = Network(height="650px", width="100%", bgcolor="#ffffff", font_color="#222222")
        net.barnes_hut()

        seen = set()
        for row in rs:
            if len(row) != 3:
                continue
            n, r, m = row
            n_name, n_label = normalize_node(n)
            m_name, m_label = normalize_node(m)
            r_type = normalize_rel(r)

            if n_name not in seen:
                net.add_node(n_name, label=n_name, title=n_label, color=node_color(n_label))
                seen.add(n_name)
            if m_name not in seen:
                net.add_node(m_name, label=m_name, title=m_label, color=node_color(m_label))
                seen.add(m_name)
            net.add_edge(n_name, m_name, label=r_type)

        with tempfile.TemporaryDirectory() as td:
            html_path = os.path.join(td, "graph.html")
            net.write_html(html_path, open_browser=False, notebook=False)
            st.components.v1.html(open(html_path, "r", encoding="utf-8").read(), height=680, scrolling=True)

# ---------- Top-5 Recommender ----------
with tab_rec:
    st.subheader("Recommend Top 5 Subsidies by Company Attributes")
    col1, col2, col3 = st.columns(3)
    with col1:
        sector = st.selectbox("Sector", ["manufacturing", "software", "energy", "logistics"], index=0)
    with col2:
        size = st.selectbox("Size", ["micro", "small", "medium"], index=1)
    with col3:
        region = st.selectbox("Region", ["DE-NW", "DE-BE", "DE-BY", "DE-ST", "DE-HH"], index=0)

    col4, col5 = st.columns(2)
    with col4:
        min_amount = st.number_input("Min max_amount_eur", value=0, step=1000)
    with col5:
        min_cofund = st.slider("Min cofund_rate", 0.0, 1.0, 0.0, 0.05)

    if st.button("Recommend"):
        exists_q = """
        MATCH (c:Company {sector:$sector, size:$size, region:$region})
        RETURN count(c) AS cnt
        """
        cnt = g.query(exists_q, {"sector": sector, "size": size, "region": region}).result_set[0][0]

        if cnt > 0:
            rec_q = """
            MATCH (c:Company {sector:$sector, size:$size, region:$region})
                  <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
            WHERE coalesce(p.max_amount_eur,0) >= $min_amount
              AND coalesce(p.cofund_rate,0) >= $min_cofund
            OPTIONAL MATCH (p)-[:MANAGED_BY]->(a:Authority)
            OPTIONAL MATCH (p)-[:REQUIRES_DOCUMENT]->(d:Document)
            RETURN p.name AS program, p.max_amount_eur AS max_eur, p.cofund_rate AS cofund,
                   p.deadline AS deadline, a.name AS authority, collect(DISTINCT d.name) AS docs
            ORDER BY max_eur DESC, cofund DESC
            LIMIT 5
            """
            params = {"sector": sector, "size": size, "region": region,
                      "min_amount": int(min_amount), "min_cofund": float(min_cofund)}
            rows = g.query(rec_q, params).result_set
            source_note = "Matched a Company with those attributes."
        else:
            rec_q = """
            MATCH (p:SubsidyProgram)
            WHERE coalesce(p.max_amount_eur,0) >= $min_amount
              AND coalesce(p.cofund_rate,0) >= $min_cofund
            OPTIONAL MATCH (p)-[:MANAGED_BY]->(a:Authority)
            OPTIONAL MATCH (p)-[:REQUIRES_DOCUMENT]->(d:Document)
            RETURN p.name AS program, p.max_amount_eur AS max_eur, p.cofund_rate AS cofund,
                   p.deadline AS deadline, a.name AS authority, collect(DISTINCT d.name) AS docs
            ORDER BY max_eur DESC, cofund DESC
            LIMIT 5
            """
            params = {"min_amount": int(min_amount), "min_cofund": float(min_cofund)}
            rows = g.query(rec_q, params).result_set
            source_note = "No Company matched those attributes — showing top programs overall."

        if not rows:
            st.warning("No programs matched your filters.")
        else:
            st.caption(source_note)
            table = []
            for r in rows:
                table.append({
                    "Program": r[0],
                    "Max €": r[1],
                    "Cofund": r[2],
                    "Deadline": r[3],
                    "Authority": r[4],
                    "Documents": ", ".join(r[5]) if isinstance(r[5], (list, tuple)) else r[5],
                })
            st.success(f"Top {len(table)} result(s)")
            st.dataframe(table, use_container_width=True)
            with st.expander("Show Cypher"):
                st.code(rec_q, language="cypher")

# ---------- Agent ----------
with tab_agent:
    st.subheader("Agent")
    st.caption("Ask in natural language; the agent will plan tool calls (Cypher/upserts) and show traces.")
    if make_agent is None:
        st.warning(f"Agent module not available: {_agent_import_err if '_agent_import_err' in globals() else 'create agent.py'}")
    if 'agent' not in st.session_state and make_agent is not None:
        try:
            st.session_state.agent = make_agent()
            st.success("Agent ready.")
        except Exception as e:
            st.error(f"Agent init failed: {e}")

    user_q = st.text_area("Your query", "List the top 5 programs by max amount.")
    colA, colB = st.columns([1,1])
    with colA:
        run = st.button("Run Agent")
    with colB:
        if st.button("Show example Cypher"):
            st.code(top5_by_max_amount(), language="cypher")

    if run and 'agent' in st.session_state:
        with st.spinner("Thinking..."):
            try:
                resp = st.session_state.agent.run(user_q)
                st.success("Response")
                st.write(resp)
            except Exception as e:
                st.error(f"Agent error: {e}")

st.markdown("---")
st.caption("Tip: Try “Which subsidies apply to small companies in NRW?”, “What documents are required?”, or “Who manages each program?”.")
