import { useState, useEffect, useMemo } from "react"
import { Link } from "react-router-dom"
import { motion } from "motion/react"

const GATEWAY_URL = "/gateway"
const TRUSTNET_URL = "/trustnet/api/agents"

interface TrustNetAgent {
  agent_id: string
  team_name: string
  name: string
  description: string
  category: string
  marketplace_ready: boolean
  endpoint_url: string
  trust_score: string
  tier: string
  review_count: number
  total_orders: string
  unique_buyers: string
  repeat_buyers: string
  total_revenue_usdc: string
  plan_count: string
}

interface ColonyActivity {
  agent: string
  tool: string
  args: string
  result: string
  timestamp: string
  is_nvm: boolean
  is_scout?: boolean
}

export function IntelPage() {
  const [trustNetAgents, setTrustNetAgents] = useState<TrustNetAgent[]>([])
  const [colonyFeed, setColonyFeed] = useState<ColonyActivity[]>([])
  const [ourServices, setOurServices] = useState<string[]>([])
  const [filter, setFilter] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch Trust-Net data
    fetch(TRUSTNET_URL)
      .then((r) => r.json())
      .then((data) => {
        setTrustNetAgents(data.items ?? data ?? [])
      })
      .catch(() => {})

    // Fetch our health data for colony activity + service list
    fetch(`${GATEWAY_URL}/health`)
      .then((r) => r.json())
      .then((data) => {
        setOurServices(data.services?.map((s: { service_id: string }) => s.service_id) ?? [])
        setColonyFeed(data.colony?.activity_feed ?? [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Sort by revenue
  const sortedAgents = useMemo(() => {
    return [...trustNetAgents].sort(
      (a, b) => parseFloat(b.total_revenue_usdc || "0") - parseFloat(a.total_revenue_usdc || "0"),
    )
  }, [trustNetAgents])

  // Filter
  const filtered = useMemo(() => {
    if (!filter) return sortedAgents
    const q = filter.toLowerCase()
    return sortedAgents.filter(
      (a) =>
        a.team_name?.toLowerCase().includes(q) ||
        a.name?.toLowerCase().includes(q) ||
        a.category?.toLowerCase().includes(q),
    )
  }, [sortedAgents, filter])

  // Find our interactions with a specific team
  function getTeamInteractions(teamName: string): ColonyActivity[] {
    const q = teamName.toLowerCase()
    return colonyFeed.filter((a) => {
      const args = a.args?.toLowerCase() ?? ""
      const result = a.result?.toLowerCase() ?? ""
      return args.includes(q) || result.includes(q)
    })
  }

  // Our entries
  const ourEntries = useMemo(() => {
    return trustNetAgents.filter((a) => a.team_name?.toLowerCase().includes("mog"))
  }, [trustNetAgents])

  if (loading) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <p className="text-lg font-sans text-stone">loading intel...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-linen">
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link to="/" className="font-mono text-sm text-copper/60 hover:text-copper transition-colors">
              &larr; board
            </Link>
            <h1 className="text-2xl font-sans text-charcoal mt-2">Marketplace Intelligence</h1>
            <p className="font-mono text-sm text-stone/50 mt-1">
              {trustNetAgents.length} participants scanned via Trust-Net &middot; {ourServices.length} services in our
              catalog
            </p>
          </div>
          <div className="text-right">
            <div className="font-mono text-xs text-stone/40">data sources</div>
            <div className="font-mono text-xs text-stone/60 mt-1">
              Trust-Net &middot; Nevermined Discovery &middot; Colony Telemetry
            </div>
          </div>
        </div>

        {/* Our position */}
        {ourEntries.length > 0 && (
          <div className="bg-copper/5 border border-copper/20 rounded-xl p-5 mb-6">
            <h2 className="font-sans text-sm font-medium text-copper mb-3">Our Position (Mog Markets)</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {ourEntries.map((e) => (
                <div key={e.agent_id} className="bg-white/60 rounded-lg p-3">
                  <div className="font-mono text-xs text-stone/50 truncate">{e.name}</div>
                  <div className="font-mono text-sm text-charcoal mt-1">
                    trust: {e.trust_score} &middot; {e.tier}
                  </div>
                  <div className="font-mono text-xs text-stone/40 mt-0.5">
                    {e.total_orders} orders &middot; ${e.total_revenue_usdc} rev
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder='Search teams... (e.g. "aibizbrain", "switchboard")'
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-white/60 border border-sage/20 rounded-lg px-4 py-2.5 font-mono text-sm text-charcoal placeholder:text-stone/30 focus:outline-none focus:border-copper/40"
          />
        </div>

        {/* Leaderboard */}
        <div className="space-y-2">
          {filtered.map((agent, i) => {
            const isMog = agent.team_name?.toLowerCase().includes("mog")
            const interactions = getTeamInteractions(agent.team_name)
            const revenue = parseFloat(agent.total_revenue_usdc || "0")
            const orders = parseInt(agent.total_orders || "0")

            return (
              <motion.div
                key={agent.agent_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.02 }}
                className={`rounded-xl border p-4 ${
                  isMog
                    ? "bg-copper/5 border-copper/20"
                    : interactions.length > 0
                      ? "bg-sage/5 border-sage/20"
                      : "bg-white/60 border-sage/10"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-sans text-sm font-medium text-charcoal">{agent.name}</span>
                      <span className="font-mono text-[10px] text-stone/40">{agent.team_name}</span>
                      {agent.marketplace_ready && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-sage/15 text-sage">
                          live
                        </span>
                      )}
                      {isMog && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-copper/15 text-copper">
                          us
                        </span>
                      )}
                    </div>
                    <p className="font-mono text-xs text-stone/50 mt-0.5 truncate max-w-lg">
                      {agent.description?.slice(0, 120)}
                    </p>
                  </div>

                  <div className="flex items-center gap-4 text-right flex-shrink-0 ml-4">
                    <div>
                      <div className="font-mono text-sm text-charcoal">${revenue.toFixed(0)}</div>
                      <div className="font-mono text-[10px] text-stone/40">revenue</div>
                    </div>
                    <div>
                      <div className="font-mono text-sm text-charcoal">{orders}</div>
                      <div className="font-mono text-[10px] text-stone/40">orders</div>
                    </div>
                    <div>
                      <div
                        className={`font-mono text-sm ${
                          parseInt(agent.trust_score) >= 80
                            ? "text-sage"
                            : parseInt(agent.trust_score) >= 50
                              ? "text-gold"
                              : "text-stone/50"
                        }`}
                      >
                        {agent.trust_score}
                      </div>
                      <div className="font-mono text-[10px] text-stone/40">trust</div>
                    </div>
                    <div>
                      <div className="font-mono text-sm text-stone/60">{agent.tier}</div>
                      <div className="font-mono text-[10px] text-stone/40">tier</div>
                    </div>
                  </div>
                </div>

                {/* Interactions with this team */}
                {interactions.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-sage/10">
                    <div className="font-mono text-[10px] text-sage/60 uppercase tracking-wider mb-1">
                      Our agent interactions ({interactions.length})
                    </div>
                    <div className="space-y-0.5">
                      {interactions.slice(0, 5).map((act, j) => (
                        <div key={j} className="flex items-center gap-2 font-mono text-[11px] text-stone/60">
                          <span className="text-stone/40">{act.agent.replace("mog-", "")}</span>
                          <span
                            className="px-1 py-0 rounded text-[9px]"
                            style={{ backgroundColor: act.is_nvm ? "#87A87818" : "#78716C18" }}
                          >
                            {act.tool}
                          </span>
                          <span className="truncate">{act.result?.slice(0, 80)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Endpoint info */}
                {agent.endpoint_url && !isMog && (
                  <div className="mt-2 font-mono text-[10px] text-stone/30 truncate">
                    {agent.endpoint_url}
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* Stats footer */}
        <div className="mt-8 pt-4 border-t border-sage/10 flex items-center gap-6 font-mono text-xs text-stone/40">
          <span>{trustNetAgents.length} total participants</span>
          <span>{trustNetAgents.filter((a) => a.marketplace_ready).length} marketplace ready</span>
          <span>
            {trustNetAgents.filter((a) => parseInt(a.total_orders || "0") > 0).length} with transactions
          </span>
          <span>
            $
            {trustNetAgents
              .reduce((sum, a) => sum + parseFloat(a.total_revenue_usdc || "0"), 0)
              .toFixed(0)}{" "}
            total ecosystem revenue
          </span>
        </div>
      </div>
    </div>
  )
}
