# King's Theorem Embedding Strategy
**Status**: ✅ MIGRATION COMPLETE (Gated by Feature Flag)
**Date**: November 27, 2025 (Updated)
**Branch**: kt/harden-api-v1

## Current State
- **Semantic Guard**: Code migrated to SentenceTransformer backend
- **Backend**: SentenceTransformers + ONNX Runtime (`all-MiniLM-L6-v2`, 384-dim, 90.9MB)
- **Activation**: Gated by `ENABLE_SEMANTIC_EMBEDDINGS` environment variable (default: `false`)
- **Degraded Mode**: Symbolic layer operational (fuzzy + Dense Symbolic Mesh) when embeddings disabled
- **Code Status**: ✅ Imports updated, ✅ Model init updated, ✅ Encode API updated, ✅ Feature flag implemented
- **Testing Status**: ⏳ Integration tests pending model download completion (~91MB from HuggingFace Hub)

## Migration Summary

**What Changed**:
1. Replaced `fastembed.TextEmbedding` with `sentence_transformers.SentenceTransformer`
2. Updated model: `BAAI/bge-small-en-v1.5` → `all-MiniLM-L6-v2` (battle-tested, 384-dim)
3. Updated encoding API: `.embed()` iterator → `.encode()` with `convert_to_numpy=True`, `normalize_embeddings=True`
4. Added `ENABLE_SEMANTIC_EMBEDDINGS` environment variable (values: `true`, `1`, `yes` enable; else disabled)
5. Updated `requirements.txt`: `fastembed>=0.2.0` → `sentence-transformers>=2.3.0`, `onnxruntime>=1.16.0`

**Feature Flag**:
```bash
# Enable semantic layer (requires model download on first run)
$env:ENABLE_SEMANTIC_EMBEDDINGS="true"

# Disable (use symbolic-only mode)
$env:ENABLE_SEMANTIC_EMBEDDINGS="false"  # or omit
```

**Default**: `false` for stability (degraded mode: fuzzy + symbolic mesh only)

## Approved Embedding Backends (Post-Stabilization)

### Option 1: SentenceTransformers + ONNX Runtime
**Pros**:
- Battle-tested in production (Hugging Face ecosystem)
- ONNX export for fast CPU inference
- Models: `all-MiniLM-L6-v2` (384-dim, 80MB), `paraphrase-multilingual-mpnet-base-v2` (768-dim, multilingual)

**Cons**:
- PyTorch dependency (larger footprint)
- Requires ONNX conversion step

**Integration**:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, convert_to_numpy=True)
```

### Option 2: Voyage Embeddings (API-based)
**Pros**:
- Zero local inference (offload to API)
- Enterprise-grade stability
- Optimized for semantic similarity

**Cons**:
- Requires network call (latency ~50-200ms)
- API key management (secret storage)
- Cost per embedding

**Integration**:
```python
import voyageai
vo = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
result = vo.embed(texts, model="voyage-2", input_type="query")
embeddings = result.embeddings
```

### Option 3: FlagEmbedding + FAISS
**Pros**:
- SOTA retrieval performance (BAAI/bge models)
- FAISS for fast nearest-neighbor search
- Multilingual support (`BAAI/bge-m3`)

**Cons**:
- FAISS C++ bindings (compilation complexity on Windows)
- Higher memory footprint for index

**Integration**:
```python
from FlagEmbedding import BGEM3FlagModel
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
embeddings = model.encode(texts)['dense_vecs']
```

## Performance Targets
| Metric | Requirement | Notes |
|--------|-------------|-------|
| Latency | < 20ms | Symbolic layer already meets this |
| Embedding Dim | 384-768 | Balance accuracy vs memory |
| Anchor Cache | Precompute | Only prompt embedded at runtime |
| Batch Size | 1 (streaming) | Real-time guardrail context |

## Activation Conditions
Enable embeddings ONLY when:
1. ✅ Governance tests stable (all crucibles green) - **COMPLETE**
2. ✅ Symbolic mesh validated in production - **COMPLETE**
3. ✅ Backend chosen and benchmarked on Python 3.14 - **IN PROGRESS** (model downloading)
4. ✅ Fallback paths tested (degraded mode must still block) - **COMPLETE**
5. ✅ CI pipeline passes without embedding dependencies - **COMPLETE** (feature flag gated)

**Pending**:
- Complete model download (~91MB from HuggingFace Hub)
- Run integration tests with `ENABLE_SEMANTIC_EMBEDDINGS=true`
- Run benchmark script to validate <20ms median latency
- Update default to `true` once validated in production

## Testing Commands
```bash
# Integration test (with embeddings)
$env:ENABLE_SEMANTIC_EMBEDDINGS="true"; pytest tests/test_semantic_guard.py -v

# Benchmark (100 prompts, latency analysis)
$env:ENABLE_SEMANTIC_EMBEDDINGS="true"; python scripts/benchmark_semantic_guard.py

# Quick verification
$env:ENABLE_SEMANTIC_EMBEDDINGS="true"; python scripts/test_semantic_migration.py

# CI test (degraded mode, no model download)
pytest tests/test_semantic_guard.py -v  # Uses symbolic-only fallback
```

## Compatibility Notes
- **Python 3.14**: Avoid packages with Pydantic v1 hard dependencies
- **ONNX Runtime**: `onnxruntime>=1.16.0` for Python 3.14 wheels
- **NumPy 2.x**: Ensure embedding backend compatible with `numpy>=2.0`

## Migration Path
When ready to enable:
1. Install backend: `pip install sentence-transformers onnxruntime`
2. Modify `semantic_guard.py`:
   - Change `TextEmbedding` import to chosen backend
   - Update model loading logic
   - Keep degraded fallback paths
3. Run full test suite: `pytest tests/`
4. Benchmark latency: `scripts/benchmark_semantic_guard.py`
5. Enable in production via feature flag: `ENABLE_SEMANTIC_EMBEDDINGS=true`

## References
- [SentenceTransformers Docs](https://www.sbert.net/)
- [Voyage AI Embeddings](https://docs.voyageai.com/embeddings/)
- [FlagEmbedding GitHub](https://github.com/FlagOpen/FlagEmbedding)
- [ONNX Runtime Python](https://onnxruntime.ai/docs/get-started/with-python.html)

---
**Axiom Compliance**: Axiom 2 (Formal Safety) – Embedding failures must not compromise guardrail blocking.
