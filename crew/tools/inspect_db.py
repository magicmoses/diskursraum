import sqlite3
import json
from collections import Counter

conn = sqlite3.connect("../../data/news.db")

print("=== Gesamtanzahl Artikel ===")
total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
print(f"  {total} Artikel total")

print("\n=== Artikel pro Quelle ===")
for row in conn.execute("SELECT source, COUNT(*) as c FROM articles GROUP BY source ORDER BY c DESC"):
    print(f"  {row[0]:<30} {row[1]}")

print("\n=== Artikel pro Bias ===")
for row in conn.execute("SELECT bias, COUNT(*) as c FROM articles GROUP BY bias ORDER BY c DESC"):
    print(f"  {row[0]:<25} {row[1]}")

print("\n=== Topic Hints Verteilung ===")
all_hints = []
for row in conn.execute("SELECT topic_hints FROM articles WHERE topic_hints != '[]'"):
    all_hints += json.loads(row[0])
for topic, count in Counter(all_hints).most_common():
    print(f"  {topic:<30} {count}")

print("\n=== Crawl Historie (letzte 5) ===")
for row in conn.execute("""
    SELECT crawled_at, SUM(articles_found), SUM(articles_new)
    FROM crawl_log
    GROUP BY crawled_at
    ORDER BY crawled_at DESC
    LIMIT 5
"""):
    print(f"  {row[0]}   found: {row[1]}   new: {row[2]}")

print("\n=== Sprachen ===")
for row in conn.execute("SELECT language, COUNT(*) as c FROM articles GROUP BY language ORDER BY c DESC"):
    print(f"  {row[0]:<10} {row[1]}")

# Letzte 10 Crawls
print("\n=== Letzte 10 Crawl-Einträge ===")
rows = conn.execute("""
    SELECT crawled_at, COUNT(*) as count 
    FROM articles 
    GROUP BY DATE(crawled_at)
    ORDER BY crawled_at DESC 
    LIMIT 10
""").fetchall()
for row in rows:
    print(f"  {row[0]}  {row[1]} Artikel")

conn.close()


