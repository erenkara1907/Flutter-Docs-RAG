"""Markdown docs (flutter/website repo) -> data/pages.jsonl."""

import logging
import re
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

BASE_URL = "https://docs.flutter.dev"
DEFAULT_CONTENT_DIR = Path("data/raw/flutter-website/sites/docs/src/content")
DEFAULT_OUTPUT = Path("data/pages.jsonl")

INCLUDED_SECTIONS = frozenset(
    {
        "ui", "cookbook", "tools", "platform-integration", "testing", "perf",
        "data-and-backend", "app-architecture", "add-to-app", "deployment",
        "packages-and-plugins", "learn", "install", "ai", "interop",
        "flutter-for", "reference", "resources", "security", "embedded",
    }
)

_FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
_RAW_BLOCK = re.compile(r"\{%-?\s*raw\s*-?%\}(.*?)\{%-?\s*endraw\s*-?%\}", re.DOTALL)
_COMMENT_BLOCK =re.compile(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", re.DOTALL)
_TEMPLATE_TAG = re.compile(r"\{%.*?%\}", re.DOTALL)
_VARIABLE = re.compile(r"\{\{[^{}\n]*\}\}")
_CODE_EXCERPT = re.compile(r"<\?code-excerpt.*?\?>", re.DOTALL)
_ADMONITION_FENCE = re.compile(r"^[ \t]*:::.*$", re.MULTILINE)
_BLANK_RUNS = re.compile(r"\n{3,}")


class Page(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str
    title: str
    section: str
    text: str
    description: str = ""


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    match = _FRONTMATTER.match(raw)
    if match is None:
        return {}, raw
    meta = yaml.safe_load(match.group(1))
    if not isinstance(meta, dict):
        meta = {}
    return meta, raw[match.end():]


def _strip_template_syntax(segment: str) -> str:
    text = _COMMENT_BLOCK.sub("", segment)
    text = _TEMPLATE_TAG.sub("", text)
    return _VARIABLE.sub("", text)


def clean_text(body: str) -> str:
    # re.split with one capture group: odd items are raw-block contents,
    # which are literal code and must not be template-stripped.
    segments = _RAW_BLOCK.split(body)
    text = "".join(
        segment if is_raw else _strip_template_syntax(segment)
        for is_raw, segment in ((i % 2 == 1, s) for i, s in enumerate(segments))
    )
    text = _CODE_EXCERPT.sub("", text)
    text = _ADMONITION_FENCE.sub("", text)
    return _BLANK_RUNS.sub("\n\n", text).strip()


def path_to_url(rel_path: Path) -> str:
    parts = list(rel_path.with_suffix("").parts)
    if parts and parts[-1] == "index":
        parts = parts[:-1]
    return "/".join([BASE_URL, *parts])


def is_included(rel_path: Path) -> bool:
    if len(rel_path.parts) < 2:
        return False
    if rel_path.name.startswith("_"):
        return False
    return rel_path.parts[0] in INCLUDED_SECTIONS


def _build_page(content_dir: Path, rel_path: Path) -> Page:
    raw = (content_dir / rel_path).read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    title = meta.get("title")
    if not title:
        raise ValueError(f"Missing title in frontmatter: {rel_path}")
    return Page(
        url=path_to_url(rel_path),
        title=str(title).strip(),
        section=rel_path.parts[0],
        text=clean_text(body),
        description=" ".join(str(meta.get("description", "")).split()),
    )


def ingest(content_dir: Path) -> list[Page]:
    rel_paths = (p.relative_to(content_dir) for p in content_dir.rglob("*.md"))
    pages = [_build_page(content_dir, p) for p in rel_paths if is_included(p)]
    return sorted(pages, key=lambda page: page.url)


def write_jsonl(pages: list[Page], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for page in pages:
            f.write(page.model_dump_json() + "\n")


def load_pages(path: Path) -> list[Page]:
    with path.open(encoding="utf-8") as f:
        return [Page.model_validate_json(line) for line in f if line.strip()]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    content_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONTENT_DIR
    pages = ingest(content_dir)
    write_jsonl(pages, DEFAULT_OUTPUT)
    logger.info("Wrote %d pages to %s", len(pages), DEFAULT_OUTPUT)


if __name__ == "__main__":
    main()
