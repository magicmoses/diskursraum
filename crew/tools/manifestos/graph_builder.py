"""
graph_builder.py — Semantic Search, Bridging Score, NetworkX Graph

RAG pipeline:
  - Query Expansion via Groq (better recall in political texts)
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
import numpy as np
from pathlib import Path


def expand_query(topic_keywords: list[str], topic_label: str) -> list[str]:
    """LLM-based keyword expansion — political manifestos use formal language
    that often doesn't match our keyword list directly."""
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""Du bist ein Experte für deutsche Politiksprache.

Thema: {topic_label}
Ausgangsbegriffe: {', '.join(topic_keywords)}

Generiere 8-10 zusätzliche deutsche Suchbegriffe für dieses politische Thema.
Typische Formulierungen in Wahlprogrammen, Synonyme, Fachbegriffe.

Antworte NUR mit einem JSON-Array: ["begriff1", "begriff2", ...]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        raw = re.sub(r'```json|```', '', response.choices[0].message.content.strip()).strip()
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
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip()

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
    party_embeddings: dict[str, np.ndarray],
    parties: dict,
) -> dict:
    """Mean cosine similarity to all other parties = bridging score.
    Uses mean of chunk embeddings per party as representative vector."""
    from sklearn.metrics.pairwise import cosine_similarity

    scores = {}
    pairwise_raw = {}

    for party_id, emb in party_embeddings.items():
        mean_emb = emb.mean(axis=0).reshape(1, -1)
        sims = []
        for other_id, other_emb in party_embeddings.items():
            if other_id == party_id:
                continue
            sim = float(cosine_similarity(mean_emb, other_emb.mean(axis=0).reshape(1, -1))[0][0])
            sims.append(sim)
            key = "__".join(sorted([party_id, other_id]))
            if key not in pairwise_raw:
                pairwise_raw[key] = []
            pairwise_raw[key].append(sim)
        scores[party_id] = round(np.mean(sims), 4) if sims else 0.0

    pairwise = {k: round(np.mean(v), 4) for k, v in pairwise_raw.items()}
    most_bridging = max(scores, key=scores.get) if scores else None

    return {
        "topic_id": topic_id,
        "bridging_scores": scores,
        "most_bridging_party": most_bridging,
        "most_bridging_party_name": parties.get(most_bridging, {}).get("name") if most_bridging else None,
        "pairwise_similarity": pairwise,
    }


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

    # Betweenness centrality: parties on many shortest paths between others
    # are structural "bridge builders" — independent of raw similarity scores.
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G, weight="weight")

    for node in G.nodes():
        G.nodes[node]["degree_centrality"] = round(degree_centrality.get(node, 0), 4)
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
            t_between = nx.betweenness_centrality(T, weight="weight")
            topic_most_central = max(t_between, key=t_between.get) if t_between else None
            topic_subgraphs[topic_id] = {
                "nodes": [{"id": n, **T.nodes[n]} for n in T.nodes()],
                "edges": [{"source": u, "target": v, "weight": d["weight"]} for u, v, d in T.edges(data=True)],
                "most_bridging_party": topic_most_central,
                "most_bridging_party_name": parties.get(topic_most_central, {}).get("name") if topic_most_central else None,
            }

    # Complement graph — edges where the main graph has none, or inverted weights.
    # Answers "who is farthest apart?" which is as interesting as "who is closest?"
    complement_edges = []
    if G.number_of_edges() > 0:
        for u, v in nx.complement(G).edges():
            orig_weight = G[u][v]["weight"] if G.has_edge(u, v) else 0.0
            complement_edges.append({"source": u, "target": v, "dissimilarity": round(1 - orig_weight, 4)})

    # GML export — standard format readable by Gephi, yEd, D3.js loaders.
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
    # Edges will represent the direction a party moved between elections.
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