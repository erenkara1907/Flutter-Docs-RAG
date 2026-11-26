import numpy as np
import pytest

from rag.chunk import Chunk
from rag.config import RunConfig
from rag.embed import EmbeddingCache
from rag.index import build_index, read_index, write_index
from rag.ingest import Page


def make_chunks(n: int) -> list[Chunk]:
    return [
        Chunk(url=f"https://docs.flutter.dev/p{i}", title=f"T{i}", section="ui", heading=f"H{i}", text=f"text {i}")
        for i in range(n)
    ]


def make_embeddings(n: int) -> np.ndarray:
    rng = np.random.default_rng(0)
    m = rng.normal(size=(n, 8)).astype(np.float32)
    return m / np.linalg.norm(m, axis=1, keepdims=True)


class TestIndexRoundTrip:
    def test_chunks_survive_round_trip(self, tmp_path):
        chunks = make_chunks(3)
        write_index(tmp_path / "r0", chunks, make_embeddings(3))
        assert read_index(tmp_path / "r0").chunks == chunks

    def test_embeddings_survive_within_float16_precision(self, tmp_path):
        emb = make_embeddings(3)
        write_index(tmp_path / "r0", make_chunks(3), emb)
        assert np.allclose(read_index(tmp_path / "r0").embeddings, emb, atol=1e-3)

    def test_embeddings_are_stored_as_float16_and_loaded_as_float32(self, tmp_path):
        write_index(tmp_path / "r0", make_chunks(2), make_embeddings(2))
        assert np.load(tmp_path / "r0" / "embeddings.npy").dtype == np.float16
        assert read_index(tmp_path / "r0").embeddings.dtype == np.float32


class TestBuildIndex:
    PAGE = Page(
        url="https://docs.flutter.dev/ui/layout", title="Layout", section="ui",
        text="## Row\n\nRows lay out children horizontally.\n\n## Column\n\nColumns lay out vertically.",
    )

    @staticmethod
    def fake_embedder(texts):
        return np.ones((len(texts), 4), dtype=np.float32)

    def build(self, config, tmp_path):
        return build_index(
            config, [self.PAGE], self.fake_embedder, EmbeddingCache(tmp_path / "cache"), "fake", tmp_path / "index"
        )

    def test_heading_chunker_prefixes_chunks_with_page_and_section_title(self, tmp_path):
        self.build(RunConfig(name="r1", chunker="heading"), tmp_path)
        chunks = read_index(tmp_path / "index" / "r1").chunks
        assert [c.heading for c in chunks] == ["Row", "Column"]
        assert chunks[0].text.startswith("Layout > Row")

    def test_fixed_chunker_keeps_the_raw_text(self, tmp_path):
        self.build(RunConfig(name="r0", chunker="fixed"), tmp_path)
        chunks = read_index(tmp_path / "index" / "r0").chunks
        assert len(chunks) == 1 and chunks[0].heading == ""

    def test_index_is_written_under_the_config_name(self, tmp_path):
        self.build(RunConfig(name="r1", chunker="heading"), tmp_path)
        assert (tmp_path / "index" / "r1" / "chunks.jsonl").exists()


class TestIndexValidation:
    def test_write_rejects_row_count_mismatch(self, tmp_path):
        with pytest.raises(ValueError, match="3.*2"):
            write_index(tmp_path / "r0", make_chunks(3), make_embeddings(2))

    def test_read_rejects_missing_index(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_index(tmp_path / "nope")

    def test_read_rejects_corrupted_row_count(self, tmp_path):
        write_index(tmp_path / "r0", make_chunks(3), make_embeddings(3))
        np.save(tmp_path / "r0" / "embeddings.npy", make_embeddings(2).astype(np.float16))
        with pytest.raises(ValueError):
            read_index(tmp_path / "r0")
