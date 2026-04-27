"""
export_analytics.py — Pre-compute and export all analytics data as JSON.

Since Railway deployment uses no persistent DB, all analytics data
is pre-computed locally and committed as JSON files.
Called daily by GitHub Actions after ML processing.
Results are overwritten on each run — always reflect latest data.
"""

import sqlite3
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "news.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "results", "analytics")


def export(filename: str, data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(path)
    print(f"  ✅ {filename} ({size // 1024}KB)")


def run():
    import database

    print("\n📊 Exporting analytics data...")
    print(f"   Output: {OUTPUT_DIR}\n")

    export("overview.json",          database.get_overview())
    export("articles_per_day.json",  database.get_articles_per_day())
    export("crawl_history.json",     database.get_crawl_history())
    export("publishing_times.json",  database.get_publishing_times())
    export("weekday_activity.json",  database.get_weekday_activity())
    export("source_details.json",    database.get_articles_per_day_per_source())
    export("emotions_per_bias.json", database.get_emotions_per_bias_filtered())
    export("editorial_profiles.json",database.get_source_editorial_profile())

    # Trending Topics 
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from clusterer import get_trending_topics
        trending = get_trending_topics(days_back=7, top_n=20)
        export("trending_topics.json", trending)
    except Exception as e:
        print(f"  ⚠ trending_topics skipped: {e}")

    print("\n✅ All analytics exported — ready to commit")


if __name__ == "__main__":
    run()