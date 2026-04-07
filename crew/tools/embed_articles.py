"""
embed_articles.py — Incremental Embedding Cache

Computes sentence embeddings for new articles and stores them in DB.
Uses jinaai/jina-embeddings-v2-base-de for German/English bilingual text.

Run this after each crawl to keep embeddings up to date.
Called by GitHub Actions daily.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from clusterer import init_embedding_cache, compute_and_cache_embeddings

if __name__ == "__main__":
    init_embedding_cache()
    compute_and_cache_embeddings()
    print("Embedding cache up to date")