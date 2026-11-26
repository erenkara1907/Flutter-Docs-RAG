"""Write/read an index: index/<config>/chunks.jsonl + embeddings.npy (float16)."""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rag.chunk import Chunk, chunk_by_heading, chunk_fixed, chunk_pages
from rag.config import RunConfig, load_config
from rag.embed import (
    DEFAULT_CACHE_DIR,
    EMBEDDING_SPECS,
    Embedder,
    EmbeddingCache,
    embed_texts,
    load_embedder,
)
from rag.ingest import DEFAULT_OUTPUT, Page, load_pages

logger = logging.getLogger(__name__)

INDEX_ROOT = Path("index")
CHUNKS_FILE = "chunks.jsonl"
EMBEDDINGS_FILE = "embeddings.npy"


@dataclass(frozen=True)
class Index:
    chunks: list[Chunk]
    embeddings: np.ndarray  # float32, shape (len(chunks), dim), rows have length 1


def _check_row_count(n_chunks: int, n_rows: int) -> None:
    if n_chunks != n_rows:
        raise ValueError(f"{n_chunks} chunks but {n_rows} embedding rows")


def write_index(directory: Path, chunks: list[Chunk], embeddings: np.ndarray) -> None:
    _check_row_count(len(chunks), len(embeddings))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / CHUNKS_FILE).open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk.model_dump_json() + "\n")
    np.save(directory / EMBEDDINGS_FILE, embeddings.astype(np.float16))


def read_index(directory: Path) -> Index:
    directory = Path(directory)
    with (directory / CHUNKS_FILE).open(encoding="utf-8") as f:
        chunks = [Chunk.model_validate_json(line) for line in f if line.strip()]
    embeddings = np.load(directory / EMBEDDINGS_FILE).astype(np.float32)
    _check_row_count(len(chunks), len(embeddings))
    return Index(chunks=chunks, embeddings=embeddings)


CHUNKERS = {"fixed": chunk_fixed, "heading": chunk_by_heading}


def build_index(
    config: RunConfig,
    pages: list[Page],
    embedder: Embedder | None,
    cache: EmbeddingCache,
    model: str,
    root: Path = INDEX_ROOT,
) -> None:
    """Chunk the pages the way `config` says, embed them, write index/<config.name>/.

    A 'bm25' config has no vectors: the matrix is stored with zero columns.
    """
    chunks = chunk_pages(pages, CHUNKERS[config.chunker])
    if config.embedding == "bm25":
        embeddings = np.zeros((len(chunks), 0), dtype=np.float32)
    else:
        embeddings = embed_texts([c.text for c in chunks], embedder, cache, model)
    write_index(Path(root) / config.name, chunks, embeddings)
    logger.info("%s: %d chunks, embeddings %s", config.name, len(chunks), embeddings.shape)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    config = load_config(sys.argv[1] if len(sys.argv) > 1 else "r0")
    pages = load_pages(DEFAULT_OUTPUT)
    if config.embedding == "bm25":
        build_index(config, pages, None, EmbeddingCache(DEFAULT_CACHE_DIR), "")
        return
    spec = EMBEDDING_SPECS.get(config.embedding)
    if spec is None:
        raise SystemExit(f"embedding {config.embedding!r} is not implemented yet")
    build_index(config, pages, load_embedder(spec), EmbeddingCache(DEFAULT_CACHE_DIR), spec.doc_cache_key)


if __name__ == "__main__":
    main()
