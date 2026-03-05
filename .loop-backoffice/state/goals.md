# Back-Office Goals

## Active Priority

1. **Scout for wrappable APIs** — Find 3-5 APIs that agents at the hackathon would pay for. Focus on: free/cheap upstream, clean docs, high demand.

2. **Wrap profitable APIs** — For each API with recommendation "wrap", generate the handler, register in catalog, self-test.

3. **Monitor portfolio** — Track revenue per service, kill underperformers, adjust pricing.

## Constraints

- We have API keys for: Exa, Anthropic, ZeroClick. Other APIs need key acquisition (escalate to Mattie).
- Budget is limited. Don't scout endlessly — evaluate quickly, wrap or skip.
- The gateway picks up new services automatically via catalog registration in `src/services.py`.

## What Agents Need

Think about what other hackathon teams' agents commonly need:
- Web search (we have this: exa_search)
- Text summarization (we have this: claude_summarize)
- Full page content (we have this: exa_get_contents)
- Weather data
- PDF/document parsing
- Code execution
- Image generation/analysis
- Translation
- Data extraction from URLs
- News/current events
