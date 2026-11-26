from pathlib import Path

import pytest

from rag.ingest import (
    clean_text,
    ingest,
    is_included,
    parse_frontmatter,
    path_to_url,
)


class TestParseFrontmatter:
    def test_extracts_title_and_description_and_strips_block(self):
        raw = "---\ntitle: Layouts\ndescription: >-\n  Learn layout.\n---\n\n## Overview\nBody"
        meta, body = parse_frontmatter(raw)
        assert meta["title"] == "Layouts"
        assert meta["description"] == "Learn layout."
        assert "title:" not in body
        assert body.lstrip().startswith("## Overview")

    def test_tolerates_trailing_space_after_opening_fence(self):
        meta, body = parse_frontmatter("--- \ntitle: T\n---\nBody")
        assert meta["title"] == "T"
        assert body == "Body"

    def test_returns_empty_meta_when_no_frontmatter(self):
        meta, body = parse_frontmatter("Just text\n")
        assert meta == {}
        assert body == "Just text\n"

    def test_horizontal_rule_later_in_body_is_not_frontmatter(self):
        raw = "---\ntitle: T\n---\nA\n\n---\n\nB"
        _, body = parse_frontmatter(raw)
        assert "A" in body and "B" in body


class TestCleanText:
    def test_removes_inline_template_tags(self):
        assert "render" not in clean_text('Before {% render "x.md" %} after')

    def test_removes_multiline_template_tags(self):
        text = 'a\n{% render "docs/x.md",\n  os: "mac"\n%}\nb'
        out = clean_text(text)
        assert "render" not in out and "os:" not in out
        assert "a" in out and "b" in out

    def test_removes_variable_expressions(self):
        assert "{{" not in clean_text("See {{site.api}}/flutter/widgets here")

    def test_keeps_content_between_raw_tags(self):
        out = clean_text("{% raw %}\nvar x = {{y}};\n{% endraw %}")
        assert "var x = {{y}};" in out
        assert "raw" not in out

    def test_raw_tags_without_spaces_are_handled(self):
        out = clean_text("{%raw%}style={{ a: 1 }}{%endraw%} and {{site.api}}")
        assert "style={{ a: 1 }}" in out
        assert "site.api" not in out

    def test_drops_comment_blocks_with_content(self):
        out = clean_text("keep\n{% comment %}\nhidden note\n{% endcomment %}\nkeep2")
        assert "hidden note" not in out
        assert "keep" in out and "keep2" in out

    def test_preserves_code_blocks(self):
        code = "```dart\nExpanded(child: Text('hi'))\n```"
        assert code in clean_text(f"Intro\n\n{code}\n\nOutro")

    def test_removes_code_excerpt_processing_instruction(self):
        out = clean_text('<?code-excerpt path-base="x/"?>\n\nText')
        assert "code-excerpt" not in out
        assert "Text" in out

    def test_removes_admonition_fences_but_keeps_content(self):
        out = clean_text(":::note\nUse http package.\n:::\n")
        assert ":::" not in out
        assert "Use http package." in out

    def test_collapses_excess_blank_lines(self):
        assert "\n\n\n" not in clean_text("a\n\n\n\n\nb")


class TestPathToUrl:
    def test_index_file_maps_to_directory_url(self):
        assert path_to_url(Path("ui/layout/index.md")) == "https://docs.flutter.dev/ui/layout"

    def test_regular_file_drops_extension(self):
        assert (
            path_to_url(Path("cookbook/networking/fetch-data.md"))
            == "https://docs.flutter.dev/cookbook/networking/fetch-data"
        )

    def test_top_level_section_index(self):
        assert path_to_url(Path("ui/index.md")) == "https://docs.flutter.dev/ui"


class TestIsIncluded:
    @pytest.mark.parametrize("rel", ["ui/layout/index.md", "cookbook/a.md", "learn/x/y.md"])
    def test_included_sections(self, rel):
        assert is_included(Path(rel))

    @pytest.mark.parametrize(
        "rel",
        ["release/notes.md", "contribute/x.md", "jobs/a.md", "tos/index.md", "index.md"],
    )
    def test_excluded_sections_and_root(self, rel):
        assert not is_included(Path(rel))

    def test_underscore_partials_are_excluded(self):
        assert not is_included(Path("add-to-app/android/_initial-route.md"))


class TestIngest:
    def _write(self, root: Path, rel: str, content: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def test_builds_pages_for_included_files_only(self, tmp_path):
        self._write(tmp_path, "ui/layout/index.md", "---\ntitle: Layout\n---\n## Hi\nExpanded")
        self._write(tmp_path, "ui/_partial.md", "partial")
        self._write(tmp_path, "release/notes.md", "---\ntitle: N\n---\nx")
        pages = ingest(tmp_path)
        assert [p.url for p in pages] == ["https://docs.flutter.dev/ui/layout"]
        assert pages[0].title == "Layout"
        assert pages[0].section == "ui"
        assert "Expanded" in pages[0].text

    def test_output_is_sorted_by_url_for_reproducibility(self, tmp_path):
        self._write(tmp_path, "ui/b.md", "---\ntitle: B\n---\nb")
        self._write(tmp_path, "ui/a.md", "---\ntitle: A\n---\na")
        assert [p.title for p in ingest(tmp_path)] == ["A", "B"]

    def test_page_without_title_is_rejected_loudly(self, tmp_path):
        self._write(tmp_path, "ui/x.md", "no frontmatter at all")
        with pytest.raises(ValueError, match="ui/x.md"):
            ingest(tmp_path)
