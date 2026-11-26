"""Two chunking strategies: fixed-size (r0 baseline) and heading-based (r1)."""

import functools
import logging
import statistics
from collections.abc import Callable
from dataclasses import dataclass

import tiktoken
from pydantic import BaseModel, ConfigDict

from rag.ingest import DEFAULT_OUTPUT, Page, load_pages

logger = logging.getLogger(__name__)

TOKENIZER_NAME = "cl100k_base"
FIXED_SIZE_CHARS = 1000
FIXED_OVERLAP_CHARS = 200
MAX_CHUNK_TOKENS = 400
CODE_FENCE = "```"
HEADING_PREFIXES = ("## ", "### ")
BLOCK_SEPARATOR = "\n\n"


@functools.cache
def _encoder() -> tiktoken.Encoding:
    """Loaded on first use: it downloads a vocabulary, which a server that only reads chunks never needs."""
    return tiktoken.get_encoding(TOKENIZER_NAME)


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str
    title: str
    section: str
    heading: str
    text: str


def count_tokens(text: str) -> int:
    return len(_encoder().encode(text))


def chunk_fixed(
    page: Page,
    size: int = FIXED_SIZE_CHARS,
    overlap: int = FIXED_OVERLAP_CHARS,
) -> list[Chunk]:
    """Cut page.text into windows of `size` characters; consecutive windows
    share `overlap` characters. Empty text -> no chunks. `heading` is "".
    Stops at the window that reaches the end, so no redundant tail chunk.
    """
    if not page.text:
        return []

    step = size - overlap
    if step <= 0:
        raise ValueError("size must be greater than overlap")

    chunks = []
    for start in range(0, len(page.text), step):
        end = start + size
        chunks.append(
            Chunk(
                text=page.text[start:end],
                url=page.url,
                title=page.title,
                section=page.section,
                heading="",
            )
        )
        if end >= len(page.text):
            break

    return chunks


# --- heading-based chunking -------------------------------------------------


@dataclass(frozen=True)
class _Budget:
    """Token budget for one section: knows how a body is prefixed and measured."""

    title: str
    heading: str
    max_tokens: int

    def wrap(self, body: str) -> str:
        prefix = f"{self.title} > {self.heading}" if self.heading else self.title
        return f"{prefix}{BLOCK_SEPARATOR}{body}"

    def fits(self, body: str) -> bool:
        return count_tokens(self.wrap(body)) <= self.max_tokens


def _is_fence(line: str) -> bool:
    return line.strip().startswith(CODE_FENCE)


def _append_section(sections: list[tuple[str, str]], heading: str, lines: list[str]) -> None:
    body = "\n".join(lines).strip()
    if body:
        sections.append((heading, body))


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split at `##`/`###` lines (ignoring those inside code fences).
    Returns (heading, body) pairs; text before the first heading has heading "".
    """
    sections: list[tuple[str, str]] = []
    heading, lines, in_code = "", [], False

    for line in text.splitlines():
        if _is_fence(line):
            in_code = not in_code
            lines.append(line)
        elif not in_code and line.strip().startswith(HEADING_PREFIXES):
            _append_section(sections, heading, lines)
            heading, lines = line.strip().lstrip("#").strip(), []
        else:
            lines.append(line)

    _append_section(sections, heading, lines)
    return sections


def _split_units(body: str) -> list[tuple[str, bool]]:
    """Break a section body into paragraphs and whole code blocks.
    Returns (text, is_code) pairs.
    """
    units: list[tuple[str, bool]] = []
    paragraph: list[str] = []
    code: list[str] | None = None

    def flush_paragraph() -> None:
        if paragraph:
            units.append(("\n".join(paragraph), False))
            paragraph.clear()

    for line in body.splitlines():
        if code is not None:
            code.append(line)
            if _is_fence(line):
                units.append(("\n".join(code), True))
                code = None
        elif _is_fence(line):
            flush_paragraph()
            code = [line]
        elif not line.strip():
            flush_paragraph()
        else:
            paragraph.append(line)

    if code is not None:  # unclosed fence: keep what we have
        units.append(("\n".join(code), True))
    flush_paragraph()
    return units


def _split_long_line(line: str, budget: _Budget) -> list[str]:
    """Binary-search the longest prefix that fits, repeatedly."""
    pieces, remaining = [], line
    while remaining:
        low, high, best = 1, len(remaining), 0
        while low <= high:
            mid = (low + high) // 2
            if budget.fits(remaining[:mid]):
                best, low = mid, mid + 1
            else:
                high = mid - 1
        if best == 0:
            raise ValueError("Cannot split line within token limit")
        pieces.append(remaining[:best])
        remaining = remaining[best:]
    return pieces


def _split_code_block(block: str, budget: _Budget) -> list[str]:
    """Split an oversized code block on line boundaries; every piece is
    re-wrapped in its own fences so no piece has an unbalanced fence.
    """
    lines = block.splitlines()
    opening = lines[0]
    has_closing = len(lines) >= 2 and _is_fence(lines[-1])
    content = lines[1:-1] if has_closing else lines[1:]

    def wrap(code_lines: list[str]) -> str:
        return "\n".join([opening, *code_lines, CODE_FENCE])

    pieces: list[str] = []
    current: list[str] = []
    for line in content:
        if budget.fits(wrap([*current, line])):
            current.append(line)
            continue
        if current:
            pieces.append(wrap(current))
            current = []
        if budget.fits(wrap([line])):
            current.append(line)
        else:
            pieces.extend(wrap([part]) for part in _split_long_line(line, budget))

    if current:
        pieces.append(wrap(current))
    return pieces or [block]


def _split_paragraph(paragraph: str, budget: _Budget) -> list[str]:
    """Pack words greedily into pieces that fit. Newlines inside the paragraph
    are collapsed to single spaces.
    """
    pieces: list[str] = []
    current = ""
    for word in paragraph.split():
        candidate = f"{current} {word}".strip()
        if budget.fits(candidate):
            current = candidate
            continue
        if current:
            pieces.append(current)
            current = ""
        if budget.fits(word):
            current = word
        else:
            pieces.extend(_split_long_line(word, budget))
    if current:
        pieces.append(current)
    return pieces


def _pack_section(units: list[tuple[str, bool]], budget: _Budget) -> list[str]:
    """Greedily pack units into bodies that fit the token budget.

    A unit that fits alone is never split. An oversized code block is split on
    line boundaries (re-fenced); an oversized paragraph is split on words.
    """
    bodies: list[str] = []
    current: list[str] = []

    for unit, is_code in units:
        if budget.fits(BLOCK_SEPARATOR.join([*current, unit])):
            current.append(unit)
            continue
        if current:
            bodies.append(BLOCK_SEPARATOR.join(current))
            current = []
        if budget.fits(unit):
            current = [unit]
        elif is_code:
            bodies.extend(_split_code_block(unit, budget))
        else:
            pieces = _split_paragraph(unit, budget)
            bodies.extend(pieces[:-1])
            current = pieces[-1:]

    if current:
        bodies.append(BLOCK_SEPARATOR.join(current))
    return bodies


def chunk_by_heading(page: Page, max_tokens: int = MAX_CHUNK_TOKENS) -> list[Chunk]:
    """Split page.text at `##`/`###` headings; each chunk is
    "<page title> > <heading>\\n\\n<body>" and never exceeds `max_tokens`.

    Sections that are too long are packed paragraph by paragraph. A code block
    that fits is kept whole; one that alone exceeds `max_tokens` is split on
    line boundaries and each piece is re-fenced (so it is never cut mid-fence,
    but the code itself is no longer contiguous).
    """
    if not page.text:
        return []
    if max_tokens <= 0:
        raise ValueError("max_tokens must be greater than zero")

    chunks = []
    for heading, body in _split_sections(page.text):
        budget = _Budget(page.title, heading, max_tokens)
        for piece in _pack_section(_split_units(body), budget):
            text = budget.wrap(piece)
            if count_tokens(text) > max_tokens:
                raise ValueError(f"Chunk exceeds {max_tokens} tokens: {page.url} > {heading}")
            chunks.append(
                Chunk(
                    text=text,
                    url=page.url,
                    title=page.title,
                    section=page.section,
                    heading=heading,
                )
            )
    return chunks


# --- helpers and CLI --------------------------------------------------------


def count_broken_code_blocks(chunks: list[Chunk]) -> int:
    """Chunks with an odd number of ``` fences were cut inside a code block."""
    return sum(1 for c in chunks if c.text.count(CODE_FENCE) % 2 == 1)


def chunk_pages(pages: list[Page], strategy: Callable[[Page], list[Chunk]]) -> list[Chunk]:
    return [chunk for page in pages for chunk in strategy(page)]


def _log_stats(name: str, chunks: list[Chunk]) -> None:
    sizes = [count_tokens(c.text) for c in chunks]
    logger.info(
        "%-10s chunks=%d  avg_tokens=%.0f  max_tokens=%d  over_%d=%d  broken_code_blocks=%d",
        name,
        len(chunks),
        statistics.mean(sizes),
        max(sizes),
        MAX_CHUNK_TOKENS,
        sum(1 for s in sizes if s > MAX_CHUNK_TOKENS),
        count_broken_code_blocks(chunks),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    pages = load_pages(DEFAULT_OUTPUT)
    _log_stats("fixed", chunk_pages(pages, chunk_fixed))
    _log_stats("heading", chunk_pages(pages, chunk_by_heading))


if __name__ == "__main__":
    main()
