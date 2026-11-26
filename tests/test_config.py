from pathlib import Path

import pytest
from pydantic import ValidationError

from rag.config import RunConfig, load_config


def write_yaml(directory: Path, name: str, body: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.yaml").write_text(body, encoding="utf-8")


class TestRunConfig:
    def test_defaults_describe_the_baseline(self):
        config = RunConfig(name="r0")
        assert (config.chunker, config.embedding) == ("fixed", "minilm")
        assert not (config.hybrid or config.rewrite or config.rerank)
        assert config.top_k == 5

    def test_is_frozen(self):
        with pytest.raises(ValidationError):
            RunConfig(name="r0").top_k = 3

    def test_unknown_field_is_rejected(self):
        with pytest.raises(ValidationError):
            RunConfig(name="r0", chunkr="heading")

    def test_unknown_chunker_is_rejected(self):
        with pytest.raises(ValidationError):
            RunConfig(name="r0", chunker="sentence")

    def test_rerank_needs_more_candidates_than_top_k(self):
        with pytest.raises(ValidationError, match="candidates"):
            RunConfig(name="r5", rerank=True, top_k=5, candidates=5)


class TestLoadConfig:
    def test_reads_yaml_by_name(self, tmp_path):
        write_yaml(tmp_path, "r1", "name: r1\nchunker: heading\n")
        assert load_config("r1", tmp_path) == RunConfig(name="r1", chunker="heading")

    def test_name_inside_file_must_match_file_name(self, tmp_path):
        write_yaml(tmp_path, "r1", "name: r2\n")
        with pytest.raises(ValueError, match="r1"):
            load_config("r1", tmp_path)

    def test_missing_config_lists_available_ones(self, tmp_path):
        write_yaml(tmp_path, "r0", "name: r0\n")
        with pytest.raises(FileNotFoundError, match="r0"):
            load_config("r9", tmp_path)

    def test_name_with_path_separator_is_rejected(self, tmp_path):
        with pytest.raises(ValueError):
            load_config("../secret", tmp_path)


def test_shipped_configs_load():
    assert load_config("r0").chunker == "fixed"
    assert load_config("r1").chunker == "heading"
