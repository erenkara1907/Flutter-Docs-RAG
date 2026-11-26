"""Draft evaluation questions: show a local LLM one chunk, ask for a realistic question.

Output (eval/candidates.jsonl) is a DRAFT. A human reads every row before it
becomes part of the golden set.
"""

import logging
import random
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from rag.chunk import Chunk, chunk_by_heading, chunk_pages, count_tokens
from rag.ingest import DEFAULT_OUTPUT, load_pages
from rag.llm import Llm, ollama_llm, parse_json_object

logger = logging.getLogger(__name__)

OUTPUT_PATH = Path("eval/candidates.jsonl")
N_CANDIDATES = 60
POOL_SIZE = 90  # extra chunks to draw from when some generations fail
SEED = 42
MIN_TOKENS = 80
MAX_TOKENS = 400
MAX_CODE_RATIO = 0.6
MAX_ATTEMPTS = 2
TEMPERATURE = 0.7

_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_SOURCE_REFERENCE = re.compile(
    r"\b(the|this) (text|passage|document|section|article)\b", re.IGNORECASE
)
_WORD = re.compile(r"[a-z][a-z0-9_]{2,}")
_STOPWORDS = frozenset(
    "how what when where which who why the and for with can does did use using you your are "
    "that this from into should would could there not has have way get let make has its".split()
)


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str
    answer: str

    @field_validator("question", "answer")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class CandidateRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    url: str
    title: str
    section: str
    heading: str
    chunk_text: str
    question: str
    answer: str
    overlap: float


def _code_ratio(text: str) -> float:
    code_chars = sum(len(block) for block in _CODE_BLOCK.findall(text))
    return code_chars / len(text) if text else 0.0


def is_eligible(chunk: Chunk) -> bool:
    """Prose-heavy, medium-sized chunks from non-release-note pages."""
    if "/release-notes" in chunk.url:
        return False
    if not MIN_TOKENS <= count_tokens(chunk.text) <= MAX_TOKENS:
        return False
    return _code_ratio(chunk.text) <= MAX_CODE_RATIO


def sample_balanced(chunks: list[Chunk], n: int, seed: int) -> list[Chunk]:
    """Up to n chunks, one per page, taken round-robin across sections (seeded)."""
    rng = random.Random(seed)

    by_url: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        by_url.setdefault(chunk.url, []).append(chunk)

    by_section: dict[str, list[Chunk]] = {}
    for url in sorted(by_url):
        chosen = rng.choice(by_url[url])
        by_section.setdefault(chosen.section, []).append(chosen)
    for group in by_section.values():
        rng.shuffle(group)

    sections = sorted(by_section)
    rng.shuffle(sections)

    picked: list[Chunk] = []
    while len(picked) < n and any(by_section.values()):
        for section in sections:
            if by_section[section] and len(picked) < n:
                picked.append(by_section[section].pop())
    return picked


def build_prompt(chunk: Chunk) -> str:
    return (
        "You are helping build a test set for a Flutter documentation search engine.\n"
        f"Below is a passage from the Flutter docs (page: {chunk.title}).\n"
        "Write ONE question that a Flutter developer would realistically type into a "
        "search box, and that this passage answers.\n\n"
        "Rules:\n"
        "- Do NOT copy phrases from the passage. Use your own everyday wording, as a "
        "developer who has not read the page would.\n"
        '- The question must make sense on its own. Never say "the text", "the passage", '
        '"this section" or "the document".\n'
        "- The answer must be 1-2 sentences and based only on the passage.\n\n"
        'Reply with JSON only: {"question": "...", "answer": "..."}\n\n'
        f'Passage:\n"""\n{chunk.text}\n"""'
    )


def parse_candidate(raw: str) -> Candidate:
    """Validate a model reply. Raises ValueError for anything unusable."""
    candidate = Candidate.model_validate(parse_json_object(raw))
    if _SOURCE_REFERENCE.search(candidate.question):
        raise ValueError(f"question refers to the source text: {candidate.question!r}")
    return candidate


def _content_words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOPWORDS}


def lexical_overlap(question: str, chunk_text: str) -> float:
    """Share of the question's content words that also appear in the chunk.
    High values mean the question was copied from the passage (inflated scores).
    """
    question_words = _content_words(question)
    if not question_words:
        return 0.0
    return len(question_words & _content_words(chunk_text)) / len(question_words)


def _generate_one(chunk: Chunk, llm: Llm) -> Candidate | None:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return parse_candidate(llm(build_prompt(chunk)))
        except ValueError as error:
            logger.warning("attempt %d failed for %s: %s", attempt, chunk.url, error)
    return None


def generate_candidates(chunks: list[Chunk], llm: Llm, n: int) -> list[CandidateRow]:
    rows: list[CandidateRow] = []
    for chunk in chunks:
        if len(rows) >= n:
            break
        candidate = _generate_one(chunk, llm)
        if candidate is None:
            continue
        rows.append(
            CandidateRow(
                id=f"c{len(rows) + 1:03d}",
                url=chunk.url,
                title=chunk.title,
                section=chunk.section,
                heading=chunk.heading,
                chunk_text=chunk.text,
                question=candidate.question,
                answer=candidate.answer,
                overlap=round(lexical_overlap(candidate.question, chunk.text), 3),
            )
        )
        logger.info("%d/%d  %s", len(rows), n, candidate.question)
    return rows


def write_rows(rows: list[CandidateRow], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(row.model_dump_json() + "\n")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    chunks = chunk_pages(load_pages(DEFAULT_OUTPUT), chunk_by_heading)
    eligible = [c for c in chunks if is_eligible(c)]
    logger.info("%d chunks, %d eligible", len(chunks), len(eligible))

    pool = sample_balanced(eligible, POOL_SIZE, SEED)
    rows = generate_candidates(pool, ollama_llm(temperature=TEMPERATURE), N_CANDIDATES)
    write_rows(rows, OUTPUT_PATH)
    logger.info("wrote %d candidates to %s", len(rows), OUTPUT_PATH)


if __name__ == "__main__":
    main()
