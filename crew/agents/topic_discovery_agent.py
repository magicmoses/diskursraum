# NOTE: This agent was prototyped but not integrated into CI/CD.
# Topic discovery runs on-demand via FastAPI instead.
# Kept for reference and potential future use.

import os
import sys
import json
import sqlite3
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "tools"))

from config import get_llm
from topic_store import init_topic_tables, save_snapshot, get_previous_topics

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "news.db"
)

# ── Tools ─────────────────────────────────────────

@tool("sample_recent_articles")
def sample_recent_articles(hours_back: int = 24) -> str:
    """
    Samples recent article titles from the database.
    Returns a JSON string with article titles and sources.
    """
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT title, source, bias
        FROM articles
        WHERE crawled_at >= datetime('now', ?)
        AND word_count >= 15
        ORDER BY RANDOM()
        LIMIT 30
    """, (f'-{hours_back} hours',)).fetchall()
    conn.close()

    articles = [
        {
            "title": row[0],
            "source": row[1],
            "bias": row[2]
        }
        for row in rows
    ]

    return json.dumps({
        "count": len(articles),
        "articles": articles
    }, ensure_ascii=False)


@tool("get_previous_topics_tool")
def get_previous_topics_tool(days_back: int = 3) -> str:
    """
    Returns topics that were discovered in the last N days.
    Use this to detect new vs. recurring topics.
    """
    previous = get_previous_topics(days_back)
    return json.dumps({
        "previous_topics": previous,
        "count": len(previous)
    })


@tool("count_articles_for_topic")
def count_articles_for_topic(keyword: str) -> str:
    """
    Counts how many articles in the DB mention a given keyword.
    Use this to verify topic relevance before reporting it.
    """
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("""
        SELECT COUNT(*) FROM articles
        WHERE text LIKE ?
        AND crawled_at >= datetime('now', '-7 days')
    """, (f'%{keyword}%',)).fetchone()[0]

    sample_titles = conn.execute("""
        SELECT title FROM articles
        WHERE text LIKE ?
        AND crawled_at >= datetime('now', '-7 days')
        LIMIT 3
    """, (f'%{keyword}%',)).fetchall()
    conn.close()

    return json.dumps({
        "keyword": keyword,
        "article_count": count,
        "sample_titles": [row[0] for row in sample_titles]
    })


@tool("save_discovered_topics")
def save_discovered_topics(topics_json: str) -> str:
    """
    Saves the discovered topics to the database.
    Input must be a JSON array of topic objects with fields:
    topic, relevance (0-1), article_count, sample_titles, is_new, trend
    """
    try:
        topics = json.loads(topics_json)
        save_snapshot(topics)
        return json.dumps({
            "status": "success",
            "saved": len(topics)
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ── Agent ─────────────────────────────────────────

def run_topic_discovery():
    """
    Runs the Topic Discovery Agent.
    Agent autonomously decides which topics are relevant,
    compares with previous runs, and saves results.
    """
    init_topic_tables()

    llm = get_llm()

    discovery_agent = Agent(
        role="Topic Discovery Analyst",
        goal="""Discover the most relevant and discussed topics 
                in recent German news articles. Identify emerging topics,
                track which topics are gaining or losing relevance,
                and save a structured snapshot for historical tracking.""",
        backstory="""You are an expert in media analysis and topic modeling.
                     You analyze German news articles to identify what society
                     is currently discussing. You are thorough, systematic,
                     and always verify your findings with data before reporting them.""",
        tools=[
            sample_recent_articles,
            get_previous_topics_tool,
            count_articles_for_topic,
            save_discovered_topics
        ],
        llm=llm,
        verbose=True
    )

    task = Task(
        description="""
        Analyze recent German news articles and discover the top topics being discussed.

        Your process:
        1. Use sample_recent_articles to get a sample of recent articles
        2. Identify 5-7 distinct topics from the article titles
        3. For each candidate topic, use count_articles_for_topic to verify
           how many articles cover it — only verify your top 5 candidates,
           not all of them
        4. Use get_previous_topics_tool to check which topics are new vs recurring
        5. For each topic determine the trend: 'rising', 'stable', or 'falling'
        6. Save all verified topics using save_discovered_topics

        STRICT RULES for topic naming:
        - Use real, recognizable German political/social topics only
        - Maximum 3 words per topic name
        - Use simple nouns or noun phrases: "Migration", "Rente", "Atomkraft",
          "Ukraine Krieg", "Klimaschutz", "Bundeswehr", "Inflation", "AfD",
          "Gesundheitsreform", "Wohnungsnot"
        - NEVER invent compound words like "Merkel-Regierungsbauer" or
          "Wirtschaftsboom-Prognose" — these are not real topics
        - NEVER combine unrelated concepts into one topic name
        - If unsure about a topic name, use the most common single keyword
          that appears in the article titles (e.g. just "Rente" not "Rentenreform-Debatte")
        - Topics must be things a German newspaper editor would use as a category

        Good examples: "Migration", "Ukraine Krieg", "Rente", "Klimaschutz",
                       "Bundeswehr", "AfD", "Inflation", "Gaza Konflikt",
                       "Energiepreise", "Wohnungsnot"

        Bad examples: "Merkel-Regierungsbauer", "Wirtschaftsboom-Prognose",
                      "Sozialhilfe-Diskussion", "Migrantenaufnahme-Debatte"

        Output format for save_discovered_topics (JSON array):
        [
          {
            "topic": "Migration",
            "relevance": 0.85,
            "article_count": 32,
            "sample_titles": ["actual title 1", "actual title 2", "actual title 3"],
            "is_new": false,
            "trend": "rising"
          }
        ]

        Important:
        - sample_titles must be REAL titles copied verbatim from the article titles you received
        - For the topic NAME however, normalize freely:
          "Migrations-Debatte" → "Migration"
          "Rentenreform-Diskussion" → "Rente"  
          "Bundeswehr-Finanzierung" → "Bundeswehr"
          Always reduce to the core concept — ideally 1 word, maximum 2 words
          Single word strongly preferred: "Migration" not "Migration Debatte"
        - Only include topics with at least 5 articles in the last 7 days
        - Relevance score should reflect article count relative to other topics
        """,
        expected_output="""A confirmation that topics were saved successfully,
                          with a summary of how many topics were discovered
                          and which ones are new.""",
        agent=discovery_agent
    )

    crew = Crew(
        agents=[discovery_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return result


if __name__ == "__main__":
    result = run_topic_discovery()
    print("\n=== Discovery Result ===")
    print(result)