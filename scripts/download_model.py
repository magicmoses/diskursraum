"""
download_model.py — Run during nixpacks build phase to bake the embedding model
into the Docker image. Eliminates model download on every container restart.

Called by nixpacks.toml [phases.build]. Not needed locally.
"""
import os

os.environ.setdefault("HF_HOME", "/app/.cache/huggingface")

from sentence_transformers import SentenceTransformer

MODEL = "intfloat/multilingual-e5-base"
print(f"[build] Downloading {MODEL}...", flush=True)

try:
    # model_O4.onnx = graph-optimised fp32, 555MB — half the size of model.onnx (1.1GB)
    model = SentenceTransformer(
        MODEL, backend="onnx",
        model_kwargs={"file_name": "onnx/model_O4.onnx"},
    )
    print("[build] ONNX (O4 optimised) model ready", flush=True)
except Exception as e:
    print(f"[build] ONNX failed ({e}), falling back to PyTorch", flush=True)
    model = SentenceTransformer(MODEL)
    print("[build] PyTorch model ready", flush=True)

# One warmup encode to verify the model works
vec = model.encode("query: Wahlprogramm", normalize_embeddings=True)
assert len(vec) == 768, f"Expected 768-dim, got {len(vec)}"
print(f"[build] Verified: 768-dim embedding OK", flush=True)
print("[build] Model baked into image.", flush=True)
