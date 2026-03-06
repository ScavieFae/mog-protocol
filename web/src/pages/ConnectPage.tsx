import { useState } from "react"
import { Link } from "react-router-dom"
import { useHealth } from "@/hooks/useHealth"
import { CopyBlock } from "@/components/CopyBlock"

const ONBOARD_SCRIPT = `pip install payments-py httpx
git clone https://github.com/ScavieFae/mog-protocol.git
cd mog-protocol
python onboard.py YOUR_NVM_API_KEY`

const MCP_CONFIG = `{
  "mcpServers": {
    "mog-marketplace": {
      "type": "http",
      "url": "https://beneficial-essence-production-99c7.up.railway.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}`

const PLANS = [
  { name: "Free", price: "Free", credits: 1000, perCall: "ad-supported", highlight: true },
  { name: "Starter", price: "$1", credits: 1, perCall: "$1.00" },
  { name: "Standard", price: "$5", credits: 10, perCall: "$0.50" },
  { name: "Pro", price: "$10", credits: 20, perCall: "$0.50" },
]

export function ConnectPage() {
  const { data } = useHealth(10000)
  const [manualOpen, setManualOpen] = useState(false)

  return (
    <div className="min-h-screen bg-linen">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Back link */}
        <Link to="/" className="font-mono text-sm text-copper/60 hover:text-copper transition-colors">
          &larr; back to garden
        </Link>

        {/* Hero */}
        <div className="mt-8 mb-10">
          <h1 className="text-3xl font-sans text-charcoal mb-3">Connect to Mog Markets</h1>
          <p className="text-xl font-sans text-stone">Two tools. Any service. Pay per call.</p>
        </div>

        {/* Step 1 */}
        <div className="mb-8">
          <h2 className="font-sans text-lg text-charcoal mb-2">
            <span className="font-mono text-copper mr-2">1</span>
            Get a Nevermined API key
          </h2>
          <p className="font-sans text-stone leading-relaxed">
            Create an account at{" "}
            <a href="https://nevermined.app" target="_blank" rel="noopener noreferrer" className="text-copper hover:underline">
              nevermined.app
            </a>
            . Generate an API key with all 4 permissions enabled (register, purchase, issue, redeem).
          </p>
        </div>

        {/* Step 2 */}
        <div className="mb-8">
          <h2 className="font-sans text-lg text-charcoal mb-2">
            <span className="font-mono text-copper mr-2">2</span>
            Run the onboard script
          </h2>
          <p className="font-sans text-stone mb-3">
            Subscribes you (free, 100 credits), prints your bearer token, and outputs your MCP config.
          </p>
          <CopyBlock code={ONBOARD_SCRIPT} />
        </div>

        {/* Step 3 - collapsible */}
        <div className="mb-8">
          <button
            onClick={() => setManualOpen(!manualOpen)}
            className="font-sans text-lg text-charcoal flex items-center gap-2 hover:text-copper transition-colors"
          >
            <span className="font-mono text-copper mr-2">3</span>
            Or configure manually
            <span className="font-mono text-sm text-stone/50">{manualOpen ? "▾" : "▸"}</span>
          </button>
          {manualOpen && (
            <div className="mt-3">
              <p className="font-sans text-stone mb-3">
                Paste into your <code className="font-mono text-sm bg-white/60 px-1.5 py-0.5 rounded">.mcp.json</code> (Claude Code) or agent's MCP config:
              </p>
              <CopyBlock code={MCP_CONFIG} />
            </div>
          )}
        </div>

        {/* Step 4 - service table */}
        <div className="mb-8">
          <h2 className="font-sans text-lg text-charcoal mb-3">
            <span className="font-mono text-copper mr-2">4</span>
            What you get
          </h2>
          {data?.services && data.services.length > 0 ? (
            <div className="bg-white/50 rounded-lg border border-sage/10 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-sage/10">
                    <th className="text-left font-sans text-sm text-stone/60 px-4 py-2">Service</th>
                    <th className="text-right font-sans text-sm text-stone/60 px-4 py-2">Credits</th>
                    <th className="text-left font-sans text-sm text-stone/60 px-4 py-2 hidden sm:table-cell">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {data.services.map((s) => (
                    <tr key={s.service_id} className="border-b border-sage/5 hover:bg-sage/5 transition-colors">
                      <td className="px-4 py-2">
                        <Link to={`/service/${s.service_id}`} className="font-mono text-sm text-copper hover:underline">
                          {s.name}
                        </Link>
                      </td>
                      <td className="text-right font-mono text-sm text-stone px-4 py-2">{s.price_credits}cr</td>
                      <td className="font-sans text-sm text-stone/70 px-4 py-2 hidden sm:table-cell truncate max-w-xs">
                        {s.description?.slice(0, 80)}{s.description && s.description.length > 80 ? "..." : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="font-sans text-stone/60">Loading services...</p>
          )}
        </div>

        {/* Pricing cards */}
        <div className="mb-8">
          <h2 className="font-sans text-lg text-charcoal mb-3">Pricing</h2>
          <div className="grid grid-cols-4 gap-3">
            {PLANS.map((plan) => (
              <div key={plan.name} className={`rounded-lg p-4 border text-center ${
                "highlight" in plan && plan.highlight
                  ? "bg-sage/10 border-sage/30"
                  : "bg-white/50 border-sage/10"
              }`}>
                <div className="font-sans text-sm text-stone/70 mb-1">{plan.name}</div>
                <div className="text-2xl font-mono text-copper mb-1">{plan.price}</div>
                <div className="font-mono text-sm text-stone">{plan.credits} credits</div>
                <div className="font-mono text-xs text-stone/50 mt-1">{plan.perCall}</div>
              </div>
            ))}
          </div>
          <p className="font-sans text-sm text-stone/50 mt-2">
            Free plan includes a contextual ad in responses. Paid plans (USDC on Base Sepolia) are ad-free.
          </p>
        </div>

        {/* Footer */}
        <div className="border-t border-sage/10 pt-4 flex items-center justify-between">
          <a
            href="https://github.com/ScavieFae/mog-protocol"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-sm text-copper/60 hover:text-copper transition-colors"
          >
            Full docs on GitHub &rarr;
          </a>
          <Link to="/" className="font-mono text-sm text-stone/50 hover:text-stone transition-colors">
            mog protocol
          </Link>
        </div>
      </div>
    </div>
  )
}
