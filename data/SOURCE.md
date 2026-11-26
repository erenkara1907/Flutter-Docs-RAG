# Data source

- Repository: https://github.com/flutter/website
- Path: `sites/docs/src/content`
- Commit: `c1acb419c3c2b43be543d7c2eb0de0a6ba0e153b` (committed 2026-11-23)
- Downloaded: 2026-11-24
- Files under path: 716 `.md`; 453 pages after ingest filtering (`rag/ingest.py`)
- License: content CC BY 3.0, code samples BSD. Attribution: "Content: docs.flutter.dev, CC BY 3.0".

Reproduce:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/flutter/website.git data/raw/flutter-website
cd data/raw/flutter-website
git sparse-checkout set sites/docs/src/content
git checkout c1acb419c3c2b43be543d7c2eb0de0a6ba0e153b
cd ../../.. && uv run python -m rag.ingest
```
