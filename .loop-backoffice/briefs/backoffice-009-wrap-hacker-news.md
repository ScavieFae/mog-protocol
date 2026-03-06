# Wrap: Hacker News

**Type:** wrap
**Model:** sonnet

## Goal

Add Hacker News top stories as a paid service in the gateway catalog.

## Context

API evaluation: `.loop-backoffice/knowledge/api-eval-hacker-news.md`

## API Details

- **Base URL:** `https://hacker-news.firebaseio.com/v0/`
- **Top stories:** GET `/topstories.json` returns array of up to 500 story IDs
- **Item details:** GET `/item/{id}.json` returns `{title, url, score, by, descendants, time, type}`
- **Auth:** None (fully public)
- **Rate limits:** None documented (Google Firebase infrastructure)

## Tasks

1. Read the API evaluation at `.loop-backoffice/knowledge/api-eval-hacker-news.md`
2. Read `src/services.py` to understand the existing handler pattern
3. Write handler function `_hacker_news_top` in `src/services.py`:
   - Accept `count` parameter (default 5, max 20)
   - Fetch top story IDs from `/topstories.json`
   - Fetch item details for the first `count` IDs (use asyncio or concurrent requests)
   - Return JSON with list of `{title, url, score, author, comments, time_ago}`
   - Handle errors gracefully (return error JSON, don't crash)
4. Add `catalog.register(...)` call:
   - `service_id`: `"hacker_news_top"`
   - `name`: `"Hacker News Top Stories"`
   - `description`: `"Get the current top stories from Hacker News with title, URL, score, author, and comment count"`
   - `price_credits`: `2`
   - `handler`: `_hacker_news_top`
   - `tags`: `["news", "tech", "current events", "hacker news"]`
5. Self-test: import and call the handler, verify it returns valid JSON with story data
6. Update `.loop-backoffice/knowledge/portfolio.json`: add `hacker_news_top` entry with source `backoffice-009`, upstream_cost 0, price 2 credits, wrapping_cost 3

## Constraints

- Follow the exact pattern in src/services.py
- Handler must return JSON string
- Use `httpx` or `urllib` for HTTP requests (check what existing handlers use)
- Keep response concise — agents don't need full article text, just metadata
- Handle network errors gracefully
