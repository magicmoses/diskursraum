"""
bridging_scorer.py — Manifesto Bridging Score (zwei-Signal-Modell)

Design-Entscheidungen:
- Gewichtung 40/60 (semantisch/thematisch): ManifestoBERTa-Kategorien sind
  inhaltlich aussagekraeftiger als Embedding-Aehnlichkeit, weil gleichsprachige
  politische Texte Kosinus-Werte nahe 1.0 erzeugen - zu wenig Spreizung.
  Thematische Ueberschneidung differenziert besser zwischen Programmpositionen.
- PCA-Dimensionszahl datengetrieben: n Komponenten fuer kumulierte Explained
  Variance >= 80%, maximal n_parties - 1. Kein fixer Hyperparameter.
- Normalisierung ist Jahr x Thema-relativ: absolute Scores sind nicht ueber
  verschiedene Jahr-/Thema-Kontexte hinweg vergleichbar.
- Closeness-Zentralitaet statt Betweenness: Betweenness ist 0 fuer alle Knoten
  in einem vollstaendigen Graphen (direkter Pfad immer kuerzester). Closeness
  misst die mittlere Distanz zu allen anderen Parteien und ist das korrekte
  Mass fuer "ideologische Zentralitaet" in einem vollstaendigen Aehnlichkeitsgraph.
"""

import numpy as np


def compute_weighted_mean_embedding(
    chunks: list,
    embeddings: np.ndarray,
) -> np.ndarray:
    """Weighted mean - chunk word count as importance proxy."""
    if embeddings.shape[0] == 0:
        return np.zeros(embeddings.shape[1] if embeddings.ndim > 1 else 768)
    if not chunks or embeddings.shape[0] != len(chunks):
        return embeddings.mean(axis=0)
    weights = np.array([max(len(c.split()), 1) for c in chunks], dtype=float)
    weights /= weights.sum()
    return (embeddings * weights[:, np.newaxis]).sum(axis=0)


def _minmax_normalize(d: dict) -> dict:
    if not d:
        return {}
    lo, hi = min(d.values()), max(d.values())
    if hi == lo:
        return {k: 0.5 for k in d}
    return {k: (v - lo) / (hi - lo) for k, v in d.items()}


def compute_pca_similarity(
    mean_embeddings: dict,
) -> dict:
    """
    PCA on party mean embeddings, then min-max normalized cosine similarity.
    n_components = minimum for >= 80% explained variance, capped at n_parties - 1.
    Returns {pair_key: normalized_score} in [0, 1].
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import normalize
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim

    party_ids = list(mean_embeddings.keys())
    n = len(party_ids)
    if n < 2:
        return {}

    X = normalize(np.array([mean_embeddings[p] for p in party_ids]))

    n_max = min(n - 1, X.shape[1])
    if n_max < 1:
        sims = cos_sim(X)
    else:
        pca = PCA(n_components=n_max)
        X_pca = pca.fit_transform(X)
        cumvar = np.cumsum(pca.explained_variance_ratio_)
        n_keep = min(int(np.searchsorted(cumvar, 0.80)) + 1, n_max)
        sims = cos_sim(X_pca[:, :n_keep])

    raw = {}
    for i, p1 in enumerate(party_ids):
        for j, p2 in enumerate(party_ids):
            if i >= j:
                continue
            key = "__".join(sorted([p1, p2]))
            raw[key] = float(sims[i, j])

    return _minmax_normalize(raw)


def compute_jaccard_manifesto(
    dist_A: dict,
    dist_B: dict,
) -> float:
    """
    Weighted Jaccard on ManifestoBERTa category distributions.
    J(A,B) = sum(min(p_A[c], p_B[c])) / sum(max(p_A[c], p_B[c]))
    """
    if not dist_A or not dist_B:
        return 0.0
    all_cats = set(dist_A) | set(dist_B)
    total_A = sum(dist_A.values()) or 1
    total_B = sum(dist_B.values()) or 1
    p_A = {c: dist_A.get(c, 0) / total_A for c in all_cats}
    p_B = {c: dist_B.get(c, 0) / total_B for c in all_cats}
    num = sum(min(p_A[c], p_B[c]) for c in all_cats)
    den = sum(max(p_A[c], p_B[c]) for c in all_cats)
    return float(num / den) if den > 0 else 0.0


def compute_pair_scores(
    party_chunks: dict,
    party_embeddings: dict,
    party_cat_distributions: dict = None,
) -> dict:
    """
    Combines two signals per party pair:
      Signal 1 (40%): PCA-reduced, min-max normalized cosine similarity
      Signal 2 (60%): Weighted Jaccard on ManifestoBERTa categories
    Falls back to Signal 1 only when category data is unavailable.
    Returns {pair_key: combined_score}.
    """
    mean_embeddings = {
        pid: compute_weighted_mean_embedding(
            chunks=party_chunks.get(pid, []),
            embeddings=emb,
        )
        for pid, emb in party_embeddings.items()
    }

    signal1 = compute_pca_similarity(mean_embeddings)
    if not signal1:
        return {}

    has_cat = (
        party_cat_distributions is not None
        and len(party_cat_distributions) >= 2
    )

    combined = {}
    for key, s1 in signal1.items():
        if has_cat:
            p1, p2 = key.split("__")
            d1 = party_cat_distributions.get(p1, {})
            d2 = party_cat_distributions.get(p2, {})
            if d1 and d2:
                jac = compute_jaccard_manifesto(d1, d2)
                combined[key] = round(0.4 * s1 + 0.6 * jac, 4)
                continue
        combined[key] = round(s1, 4)

    return combined


def compute_betweenness_bridging(
    pair_scores: dict,
    parties: dict,
) -> dict:
    """
    Builds weighted graph from pair_scores, computes closeness centrality.

    Betweenness centrality is 0 for all nodes in a complete graph (direct
    paths are always shortest). Closeness centrality is the correct measure:
    closeness(v) = (n-1) / sum(distance(v, u) for u != v)
    where distance = 1 - pair_score. A party with high closeness is on
    average most similar to all other parties - the operational definition
    of ideological bridge-building. Output key 'bridging_scores' preserved
    for interface compatibility with graph_builder and analyze_historical.
    """
    import networkx as nx

    G = nx.Graph()
    G.add_nodes_from(parties.keys())

    for key, score in pair_scores.items():
        parts = key.split("__")
        if len(parts) == 2 and parts[0] in parties and parts[1] in parties:
            G.add_edge(parts[0], parts[1], weight=max(1.0 - score, 1e-6))

    active = {p for key in pair_scores for p in key.split("__")}

    if G.number_of_edges() == 0:
        return {
            "bridging_scores": {p: 0.5 for p in active},
            "most_bridging_party": None,
            "most_bridging_party_name": None,
        }

    raw = nx.closeness_centrality(G, distance="weight")
    close = {p: raw.get(p, 0.0) for p in active}

    scores = _minmax_normalize(close)
    most = max(scores, key=scores.get) if scores else None

    return {
        "bridging_scores": {p: round(scores.get(p, 0.0), 4) for p in active},
        "most_bridging_party": most,
        "most_bridging_party_name": parties.get(most, {}).get("name") if most else None,
    }
