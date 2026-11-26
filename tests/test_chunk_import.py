"""The live server only reads chunks; it must not need the tokenizer vocabulary (a download) at import time."""

import importlib
import sys

import tiktoken


def test_importing_the_chunk_module_does_not_load_the_tokenizer(monkeypatch):
    def forbidden(name):
        raise AssertionError("tokenizer loaded at import time")

    monkeypatch.setattr(tiktoken, "get_encoding", forbidden)
    monkeypatch.delitem(sys.modules, "rag.chunk")
    importlib.import_module("rag.chunk")


def test_counting_tokens_still_works():
    from rag.chunk import count_tokens

    assert count_tokens("hello world") == 2
