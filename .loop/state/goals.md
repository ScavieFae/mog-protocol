# Goals

Autonomous API marketplace for the Nevermined Autonomous Business Hackathon.

## Current Priority

**First paid transaction by 8PM Thursday (March 5).**

Phase 1: Fork mcp-server-agent pattern, swap DuckDuckGo for Exa, register with Nevermined, get a self-buy working.

Read `docs/specs/04-wrapper-agent.md` for the three scoped briefs.
Read `docs/specs/06-nevermined-integration.md` for Nevermined SDK patterns.
Read `docs/research/hackathon-repo.md` for the reference implementation.

## Done Looks Like

- PaymentsMCP server running with Exa search tool (1 credit per call)
- Agent + plan registered on Nevermined sandbox
- Self-test client: subscriber orders plan, gets x402 token, calls exa_search, credits burn
- Listed in hackathon marketplace spreadsheet
