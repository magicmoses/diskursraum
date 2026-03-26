from config import get_llm, DEMO_MODE, LLM_PROVIDER
from crewai import Agent, Task, Crew

print(f"Mode: {'DEMO' if DEMO_MODE else 'LIVE'}")
print(f"LLM Provider: {LLM_PROVIDER}")

llm = get_llm()

analyst = Agent(
    role="Opinion Analyst",
    goal="Summarize a controversial statement in a neutral way",
    backstory="You are an expert in analyzing public discourse and identifying consensus.",
    llm=llm,
    verbose=True
)

task = Task(
    description="Summarize the following statement in 2 neutral sentences that both supporters and opponents could agree with: 'Nuclear energy should be expanded to fight climate change.'",
    expected_output="A 2-sentence neutral summary that captures the core tension without taking sides.",
    agent=analyst
)

crew = Crew(agents=[analyst], tasks=[task], verbose=True)
result = crew.kickoff()

print("\n=== RESULT ===")
print(result)