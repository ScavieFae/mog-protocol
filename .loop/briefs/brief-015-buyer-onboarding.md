# Brief: Buyer Onboarding — Website + CLI

**Branch:** brief-015-buyer-onboarding
**Model:** sonnet

## Goal

Make it dead simple for two audiences to connect to Mog Markets:
1. **Agents/developers** finding us via CLI or GitHub — copy-paste commands, instant connection
2. **Humans** visiting the website — see what's available, see how to install, one-click copy

Both paths end at the same place: an agent with `find_service` + `buy_and_call` connected.

## Context

Read these before starting:
- `README.md` — current landing page for GitHub visitors
- `docs/guides/quick-connect.md` — detailed subscribe + connect guide
- `docs/buy-from-mog.md` — simpler version of the same
- `onboard.py` — one-command onboard script
- `web/src/App.tsx` — current routes
- `web/src/pages/GardenPage.tsx` — layout/style reference
- `trinity/design-book.md` — design language

## Tasks

### 1. Website `/connect` page

Create `web/src/pages/ConnectPage.tsx`. Route: `/connect`. This is the "how to buy" page a human lands on from the garden.

**Layout** (botanical aesthetic, linen bg):

**Hero** — short pitch, one sentence:
> "Two tools. Any service. Pay per call."

**Step 1: Get a key** — link to nevermined.app, one line explaining "create account, generate API key with all 4 permissions enabled"

**Step 2: Run the onboard script** — the fastest path. Show as a copyable code block:
```bash
pip install payments-py httpx
git clone https://github.com/ScavieFae/mog-protocol.git
cd mog-protocol
python onboard.py YOUR_NVM_API_KEY
```
Add a "copy" button (clipboard icon, copies the block). Below it: "This subscribes you (free, 100 credits), prints your token, and gives you the MCP config."

**Step 3: Or configure manually** — collapsible/accordion section with the MCP JSON config block:
```json
{
  "mcpServers": {
    "mog-marketplace": {
      "type": "http",
      "url": "https://beneficial-essence-production-99c7.up.railway.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```
With note: "Paste into your `.mcp.json` (Claude Code) or agent's MCP config."

**Step 4: What you get** — the service table from the garden data (pull from /health, reuse the service list). Show service name, credits, one-line description. Link each to `/service/:id` if that page exists (brief-014).

**Pricing cards** — 3 cards for Starter/Standard/Pro packs. Show price, credits, $/call. Simple, not flashy.

**Footer link** — "Full docs on GitHub" linking to the repo.

**Nav** — Add a "connect" link in the bottom status bar of GardenPage (next to "colony →"). Format: `connect →`

### 2. Add route in App.tsx

```tsx
<Route path="/connect" element={<ConnectPage />} />
```

### 3. Copy-to-clipboard utility

Create a small `CopyBlock` component that wraps a `<pre>` block with a copy button. Used on the connect page for code snippets. Keeps it DRY if we reuse on the service detail page too.

Style: monospace (JetBrains Mono), subtle border, sage copy icon that turns to a checkmark for 2s after click.

### 4. Update GardenPage status bar

Add a "connect →" link next to "colony →" in the bottom bar:
```tsx
<Link to="/connect" className="font-mono text-sage/60 hover:text-sage transition-colors">
  connect &rarr;
</Link>
```

## Completion Criteria

- [ ] `/connect` route exists and renders
- [ ] Page has: hero pitch, onboard script block, MCP config block, service table, pricing cards
- [ ] Code blocks have copy-to-clipboard
- [ ] Service table pulls from /health data (live, not hardcoded)
- [ ] GardenPage has "connect →" link in status bar
- [ ] Visual style matches design book (linen, sage/copper, Inter + JetBrains Mono)
- [ ] Links to GitHub repo for full docs

## Verification

- Navigate to `/connect` — page renders with all sections
- Click "copy" on code blocks — copies to clipboard
- Service table shows live services from gateway
- "connect →" in garden footer navigates correctly
- Page looks good on mobile (responsive, nothing overflows)
