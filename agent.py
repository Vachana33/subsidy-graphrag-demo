# agent.py
import os
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from agent_tools import run_cypher, upsert_program

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def make_agent():
    llm = ChatOpenAI(model=os.getenv("OPENAI_AGENT_MODEL","gpt-4o-mini"), temperature=0)
    return initialize_agent(
        tools=[run_cypher, upsert_program],
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
    )

if __name__ == "__main__":
    agent = make_agent()
    print(agent.run("List programs and their max amounts (top 5). Use Cypher."))
    print(agent.run("Create a program 'Green SME Boost' managed by BMWK with max 40000€"))
    print(agent.run("Now list programs managed by BMWK."))
