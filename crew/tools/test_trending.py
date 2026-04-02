import sys
sys.path.append('.')
from clusterer import get_trending_topics

topics = get_trending_topics(days_back=7, top_n=20)
for t in topics:
    bias = max(t["bias_distribution"], key=t["bias_distribution"].get)
    print(f'[{t["article_count"]:4d} articles] {t["topic"]} — bias: {bias}')