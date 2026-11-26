import string

import pytest

from rag.chunk import (
    MAX_CHUNK_TOKENS,
    Chunk,
    chunk_by_heading,
    chunk_fixed,
    count_broken_code_blocks,
    count_tokens,
)
from rag.ingest import Page


def make_page(text: str, title: str = "Layouts") -> Page:
    return Page(url="https://docs.flutter.dev/ui/layout", title=title, section="ui", text=text)


def distinct_text(n: int) -> str:
    """n characters where every 200-char window is unique (so overlap checks are meaningful)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(alphabet[i % len(alphabet)] + chr(0x4E00 + i // len(alphabet)) for i in range(n))[:n]


class TestChunkFixed:
    def test_empty_text_gives_no_chunks(self):
        assert chunk_fixed(make_page("")) == []

    def test_short_text_gives_single_chunk_with_full_text(self):
        chunks = chunk_fixed(make_page("hello world"))
        assert [c.text for c in chunks] == ["hello world"]

    def test_text_of_exactly_size_gives_one_chunk(self):
        assert len(chunk_fixed(make_page("a" * 1000), size=1000, overlap=200)) == 1

    def test_text_one_char_over_size_gives_two_chunks(self):
        assert len(chunk_fixed(make_page("a" * 1001), size=1000, overlap=200)) == 2

    def test_no_chunk_exceeds_size(self):
        chunks = chunk_fixed(make_page(distinct_text(5000)), size=1000, overlap=200)
        assert all(len(c.text) <= 1000 for c in chunks)

    def test_consecutive_chunks_overlap_by_exact_amount(self):
        chunks = chunk_fixed(make_page(distinct_text(3000)), size=1000, overlap=200)
        assert len(chunks) >= 3
        for prev, nxt in zip(chunks, chunks[1:]):
            assert nxt.text[:200] == prev.text[-200:]

    def test_chunks_cover_the_whole_text(self):
        text = distinct_text(3500)
        chunks = chunk_fixed(make_page(text), size=1000, overlap=200)
        assert chunks[0].text == text[:1000]
        assert chunks[-1].text.endswith(text[-50:])

    def test_small_custom_size_and_overlap(self):
        chunks = chunk_fixed(make_page("abcdefghij"), size=4, overlap=1)
        assert [c.text for c in chunks] == ["abcd", "defg", "ghij"]

    def test_metadata_is_copied_and_heading_is_empty(self):
        chunk = chunk_fixed(make_page("hello"))[0]
        assert (chunk.url, chunk.title, chunk.section, chunk.heading) == (
            "https://docs.flutter.dev/ui/layout", "Layouts", "ui", "",
        )


class TestChunkByHeading:
    def test_empty_text_gives_no_chunks(self):
        assert chunk_by_heading(make_page("")) == []

    def test_splits_on_h2_and_prefixes_page_and_heading(self):
        text = "## Row\nRows lay out children.\n\n## Column\nColumns stack children."
        chunks = chunk_by_heading(make_page(text))
        assert [c.heading for c in chunks] == ["Row", "Column"]
        assert chunks[0].text.startswith("Layouts > Row\n\n")
        assert "Rows lay out children." in chunks[0].text
        assert "Columns" not in chunks[0].text

    def test_h3_is_its_own_chunk(self):
        text = "## Row\nintro\n\n### Expanded\nFills space."
        chunks = chunk_by_heading(make_page(text))
        assert [c.heading for c in chunks] == ["Row", "Expanded"]
        assert chunks[1].text.startswith("Layouts > Expanded\n\n")

    def test_intro_before_first_heading_gets_title_only_prefix(self):
        chunks = chunk_by_heading(make_page("Intro text.\n\n## Row\nbody"))
        assert chunks[0].heading == ""
        assert chunks[0].text.startswith("Layouts\n\nIntro text.")

    def test_heading_inside_code_fence_is_not_a_split_point(self):
        text = "## Shell\n```bash\n## not a heading\necho hi\n```\n"
        chunks = chunk_by_heading(make_page(text))
        assert len(chunks) == 1
        assert "## not a heading" in chunks[0].text

    def test_heading_with_empty_body_produces_no_chunk(self):
        chunks = chunk_by_heading(make_page("## Empty\n\n## Real\nbody"))
        assert [c.heading for c in chunks] == ["Real"]

    def test_long_section_is_split_under_token_limit(self):
        paragraph = "Flutter widgets compose into layouts. " * 12
        text = "## Big\n" + "\n\n".join([paragraph] * 20)
        chunks = chunk_by_heading(make_page(text))
        assert len(chunks) > 1
        assert all(count_tokens(c.text) <= MAX_CHUNK_TOKENS for c in chunks)
        assert all(c.text.startswith("Layouts > Big\n\n") for c in chunks)

    def test_fitting_code_block_is_never_cut(self):
        paragraph = "Flutter widgets compose into layouts. " * 12
        code = "```dart\n" + "\n".join(f"final a{i} = Text('{i}');" for i in range(8)) + "\n```"
        text = "## Big\n" + "\n\n".join([paragraph] * 4 + [code] + [paragraph] * 4)
        chunks = chunk_by_heading(make_page(text))
        assert len(chunks) > 1
        assert count_broken_code_blocks(chunks) == 0

    def test_metadata_is_copied(self):
        chunk = chunk_by_heading(make_page("## Row\nbody"))[0]
        assert (chunk.url, chunk.title, chunk.section) == (
            "https://docs.flutter.dev/ui/layout", "Layouts", "ui",
        )


class TestHelpers:
    def test_count_tokens_is_positive_and_monotonic(self):
        assert 0 < count_tokens("Expanded") < count_tokens("Expanded widget in a Row")

    @pytest.mark.parametrize("text,expected", [("```\ncode\n```", 0), ("```\ncode", 1)])
    def test_count_broken_code_blocks(self, text, expected):
        chunk = Chunk(url="u", title="t", section="s", heading="", text=text)
        assert count_broken_code_blocks([chunk]) == expected
