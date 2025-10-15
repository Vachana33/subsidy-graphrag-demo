Subsidy GraphRAG Demo (FalkorDB + Streamlit + LLMs)
===================================================

This project demonstrates how to connect **structured graph data** and **unstructured natural language** using a **Graph-RAG (Retrieval-Augmented Generation)** workflow.It models a simplified _German subsidy knowledge base_ with **FalkorDB**, and allows users to:

*   🗺️ Explore company–subsidy–authority relationships
    
*   💬 Ask natural language questions (NL → Cypher → Graph query)
    
*   📊 View tabular and graph-based answers
    
*   🤖 Get **Top-5 subsidy recommendations** based on company attributes

## ⚙️ Key Features
|          Feature          |                                                          Description                                                         |
|:-------------------------:|:----------------------------------------------------------------------------------------------------------------------------:|
| FalkorDB Integration      | Uses FalkorDB (RedisGraph successor) to store and query subsidy data as a graph                                              |
| Ontology-driven structure | Defines entities (Company, Authority, SubsidyProgram, Document, etc.) and valid relations (MANAGED_BY, REQUIRES_DOCUMENT, …) |
| NL → Cypher Conversion    | Converts user questions into Cypher queries using rules or an LLM                                                            |
| Graph Visualization       | Interactive PyVis graph view embedded in Streamlit                                                                           |
| Top-5 Recommender         | Suggests subsidies based on company sector, size, and region                                                                 |
| Extendable Framework      | Ready to connect to retrieval or agentic layers (LangChain / LangGraph)                                                      |

## 🧩 Project Structure
```
subsidy-graphrag/
├── app.py                    # Seeds graph with fake but structured data
├── ontology.yaml             # Defines node + relation types (the ontology)
├── smoke.py                  # Quick FalkorDB connectivity test
├── streamlit_app.py          # Streamlit UI (NL→Cypher, Graph, Recommender)
│
├── ingest.py                 # (Planned) PDF → Graph ingestion pipeline
├── agent_tools.py            # (Planned) LangChain tools for Cypher + inserts
├──
```

## 🚀 Quick Start

1. **Clone the repo**

```bash
git clone https://github.com/Vachana33/subsidy-graphrag-demo.git
cd subsidy-graphrag
```

2. **Start FalkorDB**

```bash
docker run --name falkordb -d \
  -p 6379:6379 -p 3000:3000 \
  -v falkordata:/var/lib/falkordb \
  falkordb/falkordb:latest
```


- **FalkorDB dashboard** : http://localhost:3000


3. **Create & activate virtual environment**

```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Seed the graph**

```bash
python app.py
```

- **Expected Output** – Seeded ✅
Cypher: MATCH (:Company {name:'ACME Maschinenbau GmbH'}) ...
Result: ['Energieeffizienz Plus', 50000, 0.6, 'rolling']
...


5. **Launch Streamlit UI**

```bash
streamlit run app/streamlit_app.py
```
- **Open** : http://localhost:8501
---

## 💻 Streamlit Dashboard (`streamlit_app.py`)
|         Tab         |                                    Description                                    |
|:-------------------:|:---------------------------------------------------------------------------------:|
| Ask & Results       | Ask natural-language questions → generates Cypher → executes on FalkorDB          |
| Graph Visualization | Interactive PyVis view (company ↔ programs ↔ docs/authority)                      |
| Top-5 Recommender   | Suggests top subsidy programs for given company attributes (sector, region, size) |

## 🧠 Data Model (Ontology)

### Node Types

-   **Company** → `{name, sector, size, region}`
    
-   **SubsidyProgram** → `{name, level, max_amount_eur, cofund_rate, deadline}`
    
-   **Authority** → `{name, country, url}`
    
-   **Document** → `{name, description}`
    
-   **EligibilityCriterion** → `{name, description}`

### Relation Types

|          Relation          |            Meaning            |
|:--------------------------:|:-----------------------------:|
| MANAGED_BY                 | Program ↔ Authority           |
| REQUIRES_DOCUMENT          | Program ↔ Document            |
| APPLIES_TO_SECTOR / REGION | Program ↔ Company             |
| ELIGIBLE_IF                | Program ↔ EligibilityCriterio |

## 🧮 Example Cypher Queries

1. **Subsidies for ACME**

```bash
MATCH (:Company {name:'ACME Maschinenbau GmbH'})
<-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)
RETURN p.name, p.max_amount_eur, p.cofund_rate, p.deadline
ORDER BY p.max_amount_eur DESC

```

2. **Documents required per program**

```bash
MATCH (p:SubsidyProgram)-[:REQUIRES_DOCUMENT]->(d:Document)
RETURN p.name, collect(d.name)
```
## 🧮 Example Commands

|      Task      |             Command            |
|:--------------:|:------------------------------:|
| Start FalkorDB | docker start falkordb          |
| Reseed data    | python app.py                  |
| Run UI         | streamlit run streamlit_app.py |
| Stop container | docker stop falkordb           |

## 👤 Author

Built by [Vachana Visweswaraiah](https://github.com/Vachana33) Exploring Graph-RAG, FalkorDB, and Agentic AI for intelligent subsidy analysis and SME decision support.
