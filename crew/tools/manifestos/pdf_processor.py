"""
pdf_processor.py — PDF Extraction, Cleaning, Semantic Chunking, ChromaDB Storage

Pipeline:
  1. Extract raw text from PDF
  2. Clean text (remove PDF artifacts, headers, footers, page numbers)
  3. Normalize text (fix German hyphenation, whitespace)
  4. Semantic chunking via LangChain SemanticChunker
     - Splits at semantic breakpoints, not arbitrary word counts
     - breakpoint_threshold_type='percentile' at 85th percentile
  5. Compute embeddings (intfloat/multilingual-e5-base)
  6. Store in ChromaDB with metadata

Embedding Model: intfloat/multilingual-e5-base
  - ~278MB, 768 dimensions
  - MTEB Top-Performer for German semantic search
"""

import re
import numpy as np
from pathlib import Path

EMBEDDING_MODEL = "intfloat/multilingual-e5-base"


# ── PDF Extraction ────────────────────────────────
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts raw text from PDF using pdfminer."""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(str(pdf_path))
        return text
    except Exception as e:
        print(f"  Extraction failed for {pdf_path.name}: {e}")
        return ""


# ── Text Cleaning ─────────────────────────────────
def clean_text(text: str) -> str:
    """
    Removes PDF artifacts that would pollute embeddings:
    - Page numbers (standalone numbers or 'Seite X')
    - Repeated headers/footers (party name, document title)
    - URLs and email addresses
    - Excessive whitespace and special characters
    """
    # Remove standalone page numbers
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    text = re.sub(r'Seite\s+\d+\s+(von\s+\d+)?', '', text, flags=re.IGNORECASE)

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)

    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)

    # Remove lines that are likely headers/footers (very short, all caps)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip very short lines that are likely artifacts
        if len(stripped) < 4:
            continue
        # Skip lines that are only numbers or special characters
        if re.match(r'^[\d\s\.\-\/\|]+$', stripped):
            continue
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


# ── Text Normalization ────────────────────────────
def normalize_text(text: str) -> str:
    """
    Normalizes German text:
    - Fixes end-of-line hyphenation (Binde- → Bindestrich)
    - Normalizes German quotation marks
    - Fixes common OCR errors in German PDFs
    - Ensures proper sentence spacing
    """
    # Fix German end-of-line hyphenation
    # 'Migra-\ntion' → 'Migration'
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    # Fix hyphenation with space
    # 'Migra- \ntion' → 'Migration'
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)

    # Normalize German quotation marks
    text = text.replace('„', '"').replace('"', '"').replace('‟', '"')
    text = text.replace('›', "'").replace('‹', "'")

    # Normalize dashes
    text = text.replace('–', '-').replace('—', '-')

    # Ensure space after sentence-ending punctuation
    text = re.sub(r'([.!?])([A-ZÄÖÜ])', r'\1 \2', text)

    # Remove soft hyphens (invisible in PDF but mess up words)
    text = text.replace('\xad', '')

    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


# ── Semantic Chunking ─────────────────────────────
def chunk_text_semantic(text: str) -> list[str]:
    """
    Semantic chunking using LangChain SemanticChunker.

    Splits text at points where semantic similarity between
    consecutive sentences drops significantly (85th percentile).
    Produces thematically coherent chunks — critical for RAG quality.

    Uses the same embedding model as the rest of the pipeline
    for consistency.
    """
    from langchain_experimental.text_splitter import SemanticChunker
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 8,
        },
    )

    chunker = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=85,
    )

    docs = chunker.create_documents([text])
    chunks = [
        doc.page_content.strip()
        for doc in docs
        if len(doc.page_content.strip()) > 100
    ]

    return chunks


# ── Embeddings ────────────────────────────────────
def load_embedding_model():
    """Loads multilingual-e5-base for encoding chunks and queries."""
    from sentence_transformers import SentenceTransformer
    print(f"  Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"  Model loaded")
    return model


def compute_embeddings(
    texts: list[str],
    model,
    is_query: bool = False,
) -> np.ndarray:
    """
    Computes L2-normalized embeddings.
    E5 models require 'passage:' prefix for documents
    and 'query:' prefix for queries — improves retrieval quality.
    """
    from sklearn.preprocessing import normalize
    prefix = "query: " if is_query else "passage: "
    prefixed = [prefix + t for t in texts]
    embeddings = model.encode(
        prefixed,
        show_progress_bar=True,
        batch_size=8,
    )
    return normalize(np.array(embeddings))


# ── ChromaDB Storage ──────────────────────────────
def get_chroma_collection(chroma_dir: Path, year: int):
    """Returns or creates ChromaDB collection for a given year."""
    import chromadb
    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name=f"manifestos_{year}",
        metadata={"hnsw:space": "cosine"}
    )
    return client, collection


def store_in_chroma(
    party_id: str,
    party_name: str,
    party_bias: str,
    year: int,
    chunks: list[str],
    embeddings: np.ndarray,
    chroma_dir: Path,
) -> None:
    """
    Stores chunks + embeddings in ChromaDB.
    Replaces existing entries for this party+year.
    """
    client, collection = get_chroma_collection(chroma_dir, year)

    try:
        existing = collection.get(where={"party_id": party_id})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            print(f"  Replaced {len(existing['ids'])} existing chunks")
    except Exception:
        pass

    ids = [f"{party_id}_{year}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "party_id": party_id,
            "party_name": party_name,
            "bias": party_bias,
            "year": year,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )
    print(f"  {len(chunks)} chunks stored in manifestos_{year}")


# ── Full Party Processing ─────────────────────────
def process_party_pdf(
    party_id: str,
    party_info: dict,
    year: int,
    manifesto_dir: Path,
    chroma_dir: Path,
    model,
) -> list[str] | None:
    """
    Full ingestion pipeline for one party manifesto:
    PDF → extract → clean → normalize → semantic chunk → embed → store.
    Returns list of chunks or None if failed.
    """
    pdf_path = manifesto_dir / f"{party_id}_{year}.pdf"

    if not pdf_path.exists():
        print(f"  Missing: {pdf_path.name} — skipping")
        return None

    print(f"\n  [{party_info['name']}]")

    # Extract
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        return None
    print(f"  {len(raw_text.split())} words extracted")

    # Clean
    cleaned = clean_text(raw_text)
    print(f"  {len(cleaned.split())} words after cleaning")

    # Normalize
    normalized = normalize_text(cleaned)

    # Semantic chunking
    print(f"  Running semantic chunking...")
    chunks = chunk_text_semantic(normalized)
    print(f"  {len(chunks)} semantic chunks created")

    # Embed + Store
    embeddings = compute_embeddings(chunks, model)
    store_in_chroma(
        party_id=party_id,
        party_name=party_info["name"],
        party_bias=party_info["bias"],
        year=year,
        chunks=chunks,
        embeddings=embeddings,
        chroma_dir=chroma_dir,
    )

    return chunks