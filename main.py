from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Define the LLM with model from environment variable
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),  # Default to gpt-5-nano
    temperature=1,  # Explicitly set to 1 for gpt-5-nano compatibility
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define your agents
researcher = Agent(
    role="Research Analyst",
    goal="Research a given topic deeply and provide clear findings",
    backstory="You're a seasoned researcher known for producing accurate and concise insights.",
    verbose=True,
    llm=llm
)

writer = Agent(
    role="Article Writer",
    goal="Write a short, compelling article based on the research",
    backstory="You're a skilled writer who turns insights into engaging prose.",
    verbose=True,
    llm=llm
)

editor = Agent(
    role="Editor",
    goal="Polish the article for tone, flow, and clarity",
    backstory="You're a language expert who makes content shine.",
    verbose=True,
    llm=llm
)

tweeter = Agent(
    role="Social Media Strategist",
    goal="Summarise the article into a tweet for engagement",
    backstory="You're great at distilling ideas into bite-sized, high-impact tweets.",
    verbose=True,
    llm=llm
)

# Choose a topic
topic = "How AI is transforming creative industries"

# Define tasks with expected outputs
task1 = Task(
    description=f"Research the topic: {topic}",
    expected_output="A list of 3–5 key insights about the topic.",
    agent=researcher
)

task2 = Task(
    description="Write a 400-word article based on the research",
    expected_output="A complete article, written in natural language, based on the research insights.",
    agent=writer
)

task3 = Task(
    description="Edit the article for tone, clarity, and structure",
    expected_output="A refined version of the article with improved tone and readability.",
    agent=editor
)

task4 = Task(
    description="Summarise the article in a single tweet (max 280 characters)",
    expected_output="A concise, engaging tweet that captures the article's core idea.",
    agent=tweeter
)

# Create the Crew
crew = Crew(
    agents=[researcher, writer, editor, tweeter],
    tasks=[task1, task2, task3, task4],
    verbose=True
)

# Run the crew
result = crew.kickoff()
print("\n\n✅ Final Output:\n")
print(result)
