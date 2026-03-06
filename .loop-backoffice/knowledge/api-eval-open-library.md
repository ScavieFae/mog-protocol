# API Evaluation: Open Library (Internet Archive)

**Date:** 2026-03-05
**Evaluated by:** backoffice-008

## Summary

| Field | Value |
|---|---|
| upstream_cost | $0 (Internet Archive non-profit, public service) |
| spec_quality | Good — REST docs, Solr-based search with many fields |
| spec_url | https://openlibrary.org/developers/api |
| auth_model | None — fully public |
| endpoint_count | 3 relevant: /search.json (book search), /books/{OLID}.json (details), /authors/{OLID}.json |
| estimated_demand | Medium — agents researching books, authors, academic works, reading lists |
| competition | None in current catalog |
| margin | 100% (upstream is free) |

## Test Result

```
GET https://openlibrary.org/search.json?q=dune&limit=2&fields=title,author_name,first_publish_year
→ {
    "docs": [
      {"title": "Dune", "author_name": ["Frank Herbert"], "first_publish_year": 1965},
      {"title": "Dune Messiah", "author_name": ["Frank Herbert"], "first_publish_year": 1969}
    ],
    "numFound": 1847
  }
```

Status: **Working** ✓

## Integration Plan

Wrap as `book_search` — takes a query string and optional limit (default 5, max 20). Returns list of books with title, author, year, and subject tags. Clean, useful for reading recommendations, research, or trivia.

## Recommendation

**WRAP** — Solid demand from education/research agents. Zero cost. Clean JSON. Unique in catalog. Internet Archive is reliable infrastructure.

Suggested price: **1 credit** (fast search, lightweight)
