"""
graph_builder.py — Semantic Search, Bridging Score, NetworkX Graph

RAG pipeline:
  - Query Expansion via LLM (better recall in political texts)
  - Contextual Compression (removes off-topic noise before re-embedding)

Graph structure:
  - Main graph: all parties, similarity aggregated across topics
  - Topic subgraphs: per-topic clustering (parties may align differently on migration vs. digitalization)
  - Complement graph: who is farthest apart
  - GML export: for D3.js / Gephi / Sigma.js
  - DiGraph stub: ready for 2017→2021→2025 time-series
"""

import os
import json
import re
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def call_llm(prompt: str, max_tokens: int = 400) -> str:
    """Unified LLM call — reads LLM_PROVIDER from env (groq or anthropic)."""
    from manifesto_analyzer import call_llm as _call_llm
    return _call_llm(prompt, max_tokens)


def expand_query(topic_keywords: list[str], topic_label: str) -> list[str]:
    """LLM-based keyword expansion — political manifestos use formal language
    that often doesn't match our keyword list directly."""
    prompt = f"""Du bist ein Experte für deutsche Politiksprache.

Thema: {topic_label}
Ausgangsbegriffe: {', '.join(topic_keywords)}

Generiere 8-10 zusätzliche deutsche Suchbegriffe für dieses politische Thema.
Typische Formulierungen in Wahlprogrammen, Synonyme, Fachbegriffe.

Antworte NUR mit einem JSON-Array: ["begriff1", "begriff2", ...]"""

    try:
        raw = call_llm(prompt, max_tokens=200)
        raw = re.sub(r'```json|```', '', raw).strip()
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            extra = json.loads(match.group())
            combined = list(dict.fromkeys(topic_keywords + extra))
            print(f"    Query expanded: {len(topic_keywords)} → {len(combined)} terms")
            return combined
    except Exception as e:
        print(f"    Query expansion failed: {e}")
    return topic_keywords


def compress_chunks(chunks: list[str], topic_label: str, party_name: str) -> list[str]:
    """All chunks for one party+topic in a single LLM call instead of one per chunk.
    Reduces token usage from ~96k to ~12k for the full pipeline run."""
    numbered = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)])

    prompt = f"""Du analysierst Abschnitte aus dem Wahlprogramm der Partei {party_name}.
Thema: "{topic_label}"

Für jeden nummerierten Abschnitt extrahiere ausschließlich Sätze die eine konkrete
politische Position, Forderung oder Maßnahme zu diesem Thema enthalten.
Allgemeine Floskeln, Einleitungen oder themenfremde Inhalte weglassen.
Falls ein Abschnitt nichts Relevantes enthält: [NICHT RELEVANT]

{numbered}

Antwortformat:
[1] extrahierter text oder [NICHT RELEVANT]
[2] extrahierter text oder [NICHT RELEVANT]
..."""

    try:
        raw = call_llm(prompt, max_tokens=1000)

        compressed = []
        for i, chunk in enumerate(chunks):
            match = re.search(
                rf'\[{i+1}\]\s*(.*?)(?=\[{i+2}\]|\Z)',
                raw,
                re.DOTALL
            )
            if match:
                result = match.group(1).strip()
                if result and "[NICHT RELEVANT]" not in result and len(result) > 50:
                    compressed.append(result)
                else:
                    compressed.append(chunk)
            else:
                compressed.append(chunk)

        return compressed

    except Exception as e:
        print(f"    Compression failed: {e} — using original chunks")
        return chunks


def get_party_topic_embeddings(
    party_id: str,
    topic_id: str,
    topic_keywords: list[str],
    topic_label: str,
    party_name: str,
    year: int,
    chroma_dir: Path,
    model,
    n_results: int = 8,
) -> tuple[list[str], np.ndarray, list[float]] | tuple[None, None, None]:
    """
    1. Expand query keywords via LLM
    2. Search ChromaDB (n_results=8, more than needed — compression will trim)
    3. Compress chunks to topic-relevant sentences only
    4. Re-embed compressed text (scores should reflect topic focus, not noise)

    E5 model requires 'query:' prefix for retrieval queries,
    'passage:' for documents — asymmetric retrieval design.
    """
    import chromadb
    from sklearn.preprocessing import normalize

    client = chromadb.PersistentClient(path=str(chroma_dir))
    try:
        collection = client.get_collection(f"manifestos_{year}")
    except Exception:
        print(f"    Collection manifestos_{year} not found")
        return None, None, None

    expanded_keywords = expand_query(topic_keywords, topic_label)
    query_text = "query: " + " ".join(expanded_keywords[:8])
    query_embedding = normalize(np.array(model.encode([query_text])))[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"party_id": party_id},
        include=["documents", "distances", "embeddings"],
    )

    if not results["documents"][0]:
        return None, None, None

    raw_chunks = results["documents"][0]
    distances = results["distances"][0]

    print(f"    Compressing {len(raw_chunks)} chunks for {party_name}...")
    compressed_chunks = compress_chunks(raw_chunks, topic_label, party_name)

    prefixed = ["passage: " + c for c in compressed_chunks]
    chunk_embeddings = normalize(np.array(model.encode(prefixed, show_progress_bar=False)))

    return compressed_chunks, chunk_embeddings, distances[:len(compressed_chunks)]


def compute_bridging_scores(
    topic_id: str,
    party_embeddings: dict,
    parties: dict,
    party_chunks: dict = None,
    cat_distributions: dict = None,
) -> dict:
    """
    Two-signal bridging score: semantic similarity (40%) + thematic overlap (60%).
    party_chunks: {party_id: list[str]} for weighted mean embedding.
    cat_distributions: {party_id: {category: count}} for Jaccard signal.
    Falls back to Signal 1 only when category data is absent.
    """
    from bridging_scorer import compute_pair_scores, compute_betweenness_bridging

    chunks = party_chunks or {p: [] for p in party_embeddings}

    pair_scores = compute_pair_scores(chunks, party_embeddings, cat_distributions)

    if not pair_scores:
        return {
            "topic_id": topic_id,
            "bridging_scores": {},
            "most_bridging_party": None,
            "most_bridging_party_name": None,
            "pairwise_similarity": {},
        }

    bridging = compute_betweenness_bridging(pair_scores, parties)
    bridging["topic_id"] = topic_id
    bridging["pairwise_similarity"] = pair_scores
    return bridging


def build_party_graph(
    all_topic_results: dict,
    parties: dict,
    output_dir: Path = None,
) -> dict:
    import networkx as nx

    # Main graph — weighted by mean similarity across all topics.
    # Think of it as the overall ideological distance map.
    G = nx.Graph()
    for party_id, info in parties.items():
        G.add_node(party_id, **info)

    edge_data = {}
    for topic_id, topic_data in all_topic_results.items():
        pairwise = topic_data.get("bridging", {}).get("pairwise_similarity", {})
        for pair, sim in pairwise.items():
            parts = pair.split("__")
            if len(parts) != 2:
                continue
            key = tuple(sorted(parts))
            if key not in edge_data:
                edge_data[key] = {"sims": [], "topics": []}
            edge_data[key]["sims"].append(sim)
            edge_data[key]["topics"].append(topic_id)

    for (p1, p2), data in edge_data.items():
        if p1 in parties and p2 in parties:
            G.add_edge(p1, p2, weight=round(float(np.mean(data["sims"])), 4), topics=data["topics"])

    # Closeness centrality on distance graph (distance = 1 - similarity).
    # Betweenness is 0 for all nodes in a complete graph; closeness correctly
    # identifies parties that are on average most similar to all others.
    # A copy with inverted weights is used so ForceGraph edges keep similarity
    # for thickness, while node sizes reflect true ideological centrality.
    G_dist = G.copy()
    for u, v, d in G_dist.edges(data=True):
        G_dist[u][v]["weight"] = max(1.0 - d["weight"], 1e-6)

    degree_centrality     = nx.degree_centrality(G)
    betweenness_centrality = nx.closeness_centrality(G_dist, distance="weight")

    for node in G.nodes():
        G.nodes[node]["degree_centrality"]     = round(degree_centrality.get(node, 0), 4)
        G.nodes[node]["betweenness_centrality"] = round(betweenness_centrality.get(node, 0), 4)

    most_central = max(betweenness_centrality, key=betweenness_centrality.get) if betweenness_centrality else None

    # Community detection without specifying k — algorithm finds natural clusters.
    # On 6 nodes this typically yields 2-3 groups (left/center/right).
    communities = {}
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        for i, community in enumerate(greedy_modularity_communities(G, weight="weight")):
            for node in community:
                communities[node] = i
    except Exception:
        pass

    for node in G.nodes():
        G.nodes[node]["community"] = communities.get(node, 0)

    # Topic subgraphs — same parties, but edges weighted by topic-specific similarity.
    # Useful because parties that agree on climate may strongly disagree on migration.
    topic_subgraphs = {}
    for topic_id, topic_data in all_topic_results.items():
        pairwise = topic_data.get("bridging", {}).get("pairwise_similarity", {})
        if not pairwise:
            continue
        T = nx.Graph()
        for pair, sim in pairwise.items():
            parts = pair.split("__")
            if len(parts) != 2:
                continue
            p1, p2 = parts
            if p1 in parties and p2 in parties:
                if p1 not in T:
                    T.add_node(p1, **parties[p1])
                if p2 not in T:
                    T.add_node(p2, **parties[p2])
                T.add_edge(p1, p2, weight=round(sim, 4))

        if T.number_of_edges() > 0:
            T_dist = T.copy()
            for u, v, d in T_dist.edges(data=True):
                T_dist[u][v]["weight"] = max(1.0 - d["weight"], 1e-6)
            t_between = nx.closeness_centrality(T_dist, distance="weight")
            topic_most_central = max(t_between, key=t_between.get) if t_between else None
            topic_subgraphs[topic_id] = {
                "nodes": [{"id": n, **T.nodes[n]} for n in T.nodes()],
                "edges": [{"source": u, "target": v, "weight": d["weight"]} for u, v, d in T.edges(data=True)],
                "most_bridging_party": topic_most_central,
                "most_bridging_party_name": parties.get(topic_most_central, {}).get("name") if topic_most_central else None,
            }

    # Complement graph — answers "who is farthest apart?"
    complement_edges = []
    if G.number_of_edges() > 0:
        for u, v in nx.complement(G).edges():
            orig_weight = G[u][v]["weight"] if G.has_edge(u, v) else 0.0
            complement_edges.append({"source": u, "target": v, "dissimilarity": round(1 - orig_weight, 4)})

    # GML export — readable by Gephi, yEd, D3.js loaders.
    # Lists need to be stringified since GML only supports primitives.
    if output_dir is not None:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            G_export = G.copy()
            for node in G_export.nodes():
                for key, val in list(G_export.nodes[node].items()):
                    if isinstance(val, list):
                        G_export.nodes[node][key] = str(val)
            nx.write_gml(G_export, str(output_dir / "party_graph.gml"))
            print(f"  GML exported to {output_dir / 'party_graph.gml'}")
        except Exception as e:
            print(f"  GML export failed: {e}")

    # DiGraph stub — directed graph for future time-series (2017→2021→2025).
    DG = nx.DiGraph()
    for party_id, info in parties.items():
        DG.add_node(party_id, **info)

    return {
        "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes()],
        "edges": [{"source": u, "target": v, "weight": d["weight"], "topics": d.get("topics", [])} for u, v, d in G.edges(data=True)],
        "most_bridging_party": most_central,
        "most_bridging_party_name": parties.get(most_central, {}).get("name") if most_central else None,
        "topic_subgraphs": topic_subgraphs,
        "complement_edges": complement_edges,
    }