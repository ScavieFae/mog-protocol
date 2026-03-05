# Scout: Initial API Discovery

**Type:** scout
**Model:** sonnet

## Goal

Discover 3-5 APIs worth wrapping and selling through our gateway. Focus on APIs that are:
- Free or very cheap per call
- Useful to AI agents at a hackathon (practical tools, not toys)
- Have clean documentation or OpenAPI specs
- Not already in our catalog (we have: exa_search, exa_get_contents, claude_summarize)

## Tasks

1. Use Exa to search for free APIs useful to AI agents. Try queries like:
   - "free REST API for AI agents"
   - "OpenAPI specification free tier"
   - "API for data extraction text parsing"
   - "free weather API" "free translation API" "free code execution API"
   Write results to `.loop-backoffice/knowledge/scout-001-results.md`

2. Evaluate the top 3 most promising APIs. For each, write a structured evaluation to `.loop-backoffice/knowledge/api-eval-{name}.md` with:
   - upstream_cost (free tier limits, pricing)
   - spec_quality (OpenAPI spec? docs-only?)
   - spec_url (direct link)
   - auth_model (API key? OAuth? none?)
   - endpoint_count (total vs useful subset)
   - estimated_demand (would hackathon agents pay for this?)
   - competition (anyone else selling this?)
   - margin (upstream cost vs what we'd charge)
   - recommendation: wrap / skip / defer (with reasoning)

3. Update `.loop-backoffice/knowledge/portfolio.json` demand_signals with any unmet needs discovered.

## Success Criteria
- At least 3 api-eval files written with honest assessments
- At least 1 with recommendation "wrap"
- scout-001-results.md with raw search results for reference
