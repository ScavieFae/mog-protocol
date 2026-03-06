# API Evaluation: Hacker News

**Date:** 2026-03-05
**Evaluated by:** backoffice-008

## Summary

| Field | Value |
|---|---|
| upstream_cost | $0 (completely free, no rate limits documented) |
| spec_quality | High — Firebase REST docs, predictable JSON schema |
| spec_url | https://github.com/HackerNews/API |
| auth_model | None — fully public |
| endpoint_count | ~8 (topstories, newstories, beststories, askstories, showstories, jobstories, item/{id}, user/{id}) |
| estimated_demand | High — agents frequently need tech news and current events |
| competition | Exa search can surface HN content, but HN API gives structured data (scores, comment counts, author) that Exa doesn't |
| margin | 100% (upstream is free) |

## Test Result

```
GET https://hacker-news.firebaseio.com/v0/topstories.json
→ [47249387, 47265045, ...] (500 story IDs)

GET https://hacker-news.firebaseio.com/v0/item/47249387.json
→ {"title": "CBP tapped into the online advertising ecosystem...", "url": "...", "score": 358, "by": "ece", "descendants": 151}
```

Status: **Working** ✓

## Integration Plan

Wrap two capabilities:
1. `hacker_news_top` — returns top N stories with title/url/score
2. Could add more (new stories, ask HN) later, but top stories is the money feature

Service fetches top story IDs, then fetches item details for first N (default 5, max 20). Returns structured JSON.

No API key needed. No rate limits documented (Firebase hosting is Google-backed).

## Recommendation

**WRAP** — High demand, zero cost, unique structured data complement to Exa search. Quick to implement. Agents covering "what's happening in tech" will use this repeatedly.

Suggested price: **2 credits** (returns multiple items, slightly more work than a single lookup)
