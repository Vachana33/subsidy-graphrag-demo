Perfect 💪 — you’ve now got a fully working **Graph-RAG prototype for subsidy intelligence**, so here’s your polished **README.md** written in the same structured, visual style as your DME project:

🧭 Subsidy GraphRAG Demo (FalkorDB + Streamlit + LLMs)
======================================================

This project demonstrates how to connect **structured graph data** and **unstructured natural language** using a **Graph-RAG (Retrieval-Augmented Generation)** workflow.It models a simplified _German subsidy knowledge base_ with **FalkorDB**, and allows users to:

*   🗺️ Explore company–subsidy–authority relationships
    
*   💬 Ask natural language questions (NL → Cypher → Graph query)
    
*   📊 View tabular and graph-based answers
    
*   🤖 Get **Top-5 subsidy recommendations** based on company attributes
    

⚙️ Key Features
---------------

FeatureDescription**FalkorDB Integration**Uses FalkorDB (RedisGraph successor) to store and query subsidy data as a graph**Ontology-driven structure**Defines entities (Company, Authority, SubsidyProgram, Document, etc.) and valid relations (MANAGED\_BY, REQUIRES\_DOCUMENT, …)**NL → Cypher Conversion**Converts user questions into Cypher queries using rules or an LLM**Graph Visualization**Interactive PyVis graph view embedded in Streamlit**Top-5 Recommender**Suggests subsidies based on company sector, size, and region**Extendable Framework**Ready to connect to retrieval or agentic layers (LangChain / LangGraph)

🧩 Project Structure
--------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   subsidy-graphrag/  ├── app.py                    # Seeds graph with fake but structured data  ├── ontology.yaml             # Defines node + relation types (the ontology)  ├── smoke.py                  # Quick FalkorDB connectivity test  ├── streamlit_app.py          # Streamlit UI (NL→Cypher, Graph, Recommender)  │  ├── ingest.py                 # (Planned) PDF → Graph ingestion pipeline  ├── agent_tools.py            # (Planned) LangChain tools for Cypher + inserts  ├── agent.py                  # (Planned) Agent using LLM + tool-calling  │  ├── requirements.txt          # Python dependencies  ├── .gitignore  └── README.md                 # 📄 This file   `

🚀 Quick Start
--------------

### 1️⃣ Clone the repo

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   git clone https://github.com/Vachana33/subsidy-graphrag-demo.git  cd subsidy-graphrag   `

### 2️⃣ Start FalkorDB

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   docker run --name falkordb -d \    -p 6379:6379 -p 3000:3000 \    -v falkordata:/var/lib/falkordb \    falkordb/falkordb:latest   `

👉 FalkorDB dashboard: [http://localhost:3000](http://localhost:3000/)

### 3️⃣ Create & activate virtual environment

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python3 -m venv env  source env/bin/activate  pip install --upgrade pip  pip install -r requirements.txt   `

### 4️⃣ Seed the graph

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python app.py   `

Expected output:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Seeded ✅  Cypher: MATCH (:Company {name:'ACME Maschinenbau GmbH'}) ...  Result: ['Energieeffizienz Plus', 50000, 0.6, 'rolling']  ...   `

### 5️⃣ Launch Streamlit UI

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   streamlit run streamlit_app.py   `

🌐 Open [http://localhost:8501](http://localhost:8501/)

💻 Streamlit Dashboard
----------------------

### Tabs Overview

TabDescription**Ask & Results**Ask natural-language questions → generates Cypher → executes on FalkorDB**Graph Visualization**Interactive PyVis view (company ↔ programs ↔ docs/authority)**Top-5 Recommender**Suggests top subsidy programs for given company attributes (sector, region, size)

🧠 Data Model (Ontology)
------------------------

### Node Types

*   **Company** → {name, sector, size, region}
    
*   **SubsidyProgram** → {name, level, max\_amount\_eur, cofund\_rate, deadline}
    
*   **Authority** → {name, country, url}
    
*   **Document** → {name, description}
    
*   **EligibilityCriterion** → {name, description}
    

### Relation Types

RelationMeaningMANAGED\_BYProgram ↔ AuthorityREQUIRES\_DOCUMENTProgram ↔ DocumentAPPLIES\_TO\_SECTOR / REGIONProgram ↔ CompanyELIGIBLE\_IFProgram ↔ EligibilityCriterion

🧮 Example Cypher Queries
-------------------------

**1️⃣ Subsidies for ACME**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   MATCH (:Company {name:'ACME Maschinenbau GmbH'})  <-[:APPLIES_TO_SECTOR|:APPLIES_TO_REGION]-(p:SubsidyProgram)  RETURN p.name, p.max_amount_eur, p.cofund_rate, p.deadline  ORDER BY p.max_amount_eur DESC   `

**2️⃣ Documents required per program**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   MATCH (p:SubsidyProgram)-[:REQUIRES_DOCUMENT]->(d:Document)  RETURN p.name, collect(d.name)   `

🧩 Next Steps (Roadmap)
-----------------------

StageGoal**✅ Phase 1**Static ontology + demo data + Streamlit GraphRAG UI**🚧 Phase 2**Add ingestion pipeline (ingest.py) to parse real subsidy PDFs & inject nodes**🚧 Phase 3**Integrate LLM tool-calling agent (LangChain/LangGraph) for autonomous graph exploration**🚀 Phase 4**Deploy demo on Streamlit Cloud or Docker Compose stack**🌍 Phase 5**Extend to multilingual queries (German ↔ English) & SME-focused recommendation logic

📦 Dependencies
---------------

From requirements.txt:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   streamlit  falkordb  pyvis  pyyaml  openai  requests   `

Optional (for next phases):

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   langchain  langgraph  pymupdf  unstructured  rapidfuzz   `

🧰 Example Commands
-------------------

TaskCommandStart FalkorDBdocker start falkordbReseed datapython app.pyRun UIstreamlit run streamlit\_app.pyStop containerdocker stop falkordb

👤 Author
---------

Developed by [**Vachana Visweswaraiah**](https://github.com/VachanaVisweswaraiah)Exploring **Graph-RAG**, **FalkorDB**, and **Agentic AI** for intelligent subsidy analysis and SME decision support.

🧠 Inspiration
--------------

> _“Graphs make relationships explicit — LLMs make them meaningful.”_— Bridging structured & unstructured knowledge for real-world policy intelligence.

Would you like me to include a **diagram (PlantUML / Typst / image)** showing the ontology structure (Company ↔ Program ↔ Authority) at the top of the README? It makes the repo visually pop for GitHub viewers.