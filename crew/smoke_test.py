from crewai import Agent, Task, Crew, LLM

# Ollama lokal als LLM
llm = LLM(
    model="ollama/llama3.1",
    base_url="http://localhost:11434"
)

# Minimaler Test-Agent
analyst = Agent(
    role="Opinion Analyst",
    goal="Summarize a controversial statement in a neutral way",
    backstory="You are an expert in analyzing public discourse and identifying consensus.",
    llm=llm,
    verbose=True
)

# Minimaler Test-Task
task = Task(
    description="Summarize the following statement in 2 neutral sentences that both supporters and opponents could agree with: 'Nuclear energy should be expanded to fight climate change.'",
    expected_output="A 2-sentence neutral summary that captures the core tension without taking sides.",
    agent=analyst
)

# Crew zusammenstellen und ausführen
crew = Crew(
    agents=[analyst],
    tasks=[task],
    verbose=True
)

result = crew.kickoff()
print("\n=== RESULT ===")
print(result)