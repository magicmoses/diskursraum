import sqlite3
import json
from collections import Counter

conn = sqlite3.connect("../../data/news.db")

# Emotion Verteilung gesamt
print("=== Dominant Emotions (gesamt) ===")
rows = conn.execute("""
    SELECT emotion, COUNT(*) as count
    FROM articles
    WHERE emotion IS NOT NULL
    GROUP BY emotion
    ORDER BY count DESC
""").fetchall()
for row in rows:
    print(f"  {row[0]:<20} {row[1]}")

# Emotion pro Bias
print("\n=== Top Emotion pro Bias ===")
rows = conn.execute("""
    SELECT bias, emotion, COUNT(*) as count
    FROM articles
    WHERE emotion IS NOT NULL
    GROUP BY bias, emotion
    ORDER BY bias, count DESC
""").fetchall()

current_bias = None
for row in rows:
    if row[0] != current_bias:
        current_bias = row[0]
        print(f"\n  [{current_bias}]")
    print(f"    {row[1]:<20} {row[2]}")

conn.close()