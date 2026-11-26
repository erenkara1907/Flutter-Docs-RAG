"""RunConfig: which parts of the pipeline are switched on for one ablation step."""

import re
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

CONFIG_DIR = Path("configs")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class RunConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    chunker: Literal["fixed", "heading"] = "fixed"
    embedding: Literal["minilm", "bge-small", "gemini", "bm25"] = "minilm"  # bm25: keywords only, no vectors
    hybrid: bool = False  # add BM25 and merge with RRF
    rewrite: bool = False  # LLM turns the question into a short English search query
    rerank: bool = False  # LLM picks the best top_k out of `candidates`
    top_k: int = 5
    candidates: int = 20  # how many chunks retrieval fetches before rerank/fusion

    @model_validator(mode="after")
    def _hybrid_needs_vectors(self) -> Self:
        if self.embedding == "bm25" and self.hybrid:
            raise ValueError("hybrid merges vectors with BM25; embedding 'bm25' has no vectors")
        return self

    @model_validator(mode="after")
    def _rerank_has_something_to_choose_from(self) -> Self:
        if self.rerank and self.candidates <= self.top_k:
            raise ValueError("rerank needs candidates > top_k")
        return self


def load_config(name: str, directory: Path = CONFIG_DIR) -> RunConfig:
    if not _SAFE_NAME.match(name):
        raise ValueError(f"invalid config name {name!r}")
    path = Path(directory) / f"{name}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in Path(directory).glob("*.yaml"))
        raise FileNotFoundError(f"no config {name!r}; available: {available}")
    config = RunConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if config.name != name:
        raise ValueError(f"{path} declares name {config.name!r}, expected {name!r}")
    return config
