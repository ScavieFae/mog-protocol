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

interface TxEntry {
  event_type?: string
  service_id?: string
  service_name?: string
  success?: boolean
  credits_charged?: number
  timestamp?: string
  params?: Record<string, unknown>
  result?: string
  error?: string
  latency_ms?: number
  surge_multiplier?: number
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
  const [transactions, setTransactions] = useState<TxEntry[]>([])
  const [colonyActivity, setColonyActivity] = useState<ColonyActivity[]>([])
  const [filter, setFilter] = useState("")
  const [loading, setLoading] = useState(true)
  const [expandedTeam, setExpandedTeam] = useState<string | null>(null)

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [trustRes, txRes] = await Promise.allSettled([
          fetch(TRUSTNET_URL).then((r) => r.json()),
          fetch(`${GATEWAY_URL}/txlog`).then((r) => r.json()),
        ])

        if (trustRes.status === "fulfilled") {
          setTrustNetAgents(trustRes.value.items ?? trustRes.value ?? [])
        }
        if (txRes.status === "fulfilled") {
          setTransactions(txRes.value.transactions ?? [])
          setColonyActivity(txRes.value.colony_activity ?? [])
        }
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [])

  // Sort by revenue
  const sortedAgents = useMemo(() => {
    return [...trustNetAgents].sort(
      (a, b) => parseFloat(b.total_revenue_usdc || "0") - parseFloat(a.total_revenue_usdc || "0"),
    )
  }, [trustNetAgents])

  // Filter (hide our own zero-activity registrations from the list)
  const filtered = useMemo(() => {
    const base = sortedAgents.filter((a) => {
      const isMog = a.team_name?.toLowerCase().includes("mog")
      if (isMog && parseInt(a.total_orders || "0") === 0) return false
      return true
    })
    if (!filter) return base
    const q = filter.toLowerCase()
    return base.filter(
      (a) =>
        a.team_name?.toLowerCase().includes(q) ||
        a.name?.toLowerCase().includes(q) ||
        a.category?.toLowerCase().includes(q),
    )
  }, [sortedAgents, filter])

  // Find colony interactions referencing a team
  function getColonyInteractions(teamName: string): ColonyActivity[] {
    const q = teamName.toLowerCase()
    return colonyActivity.filter((a) => {
      const args = a.args?.toLowerCase() ?? ""
      const result = a.result?.toLowerCase() ?? ""
      const tool = a.tool?.toLowerCase() ?? ""
      return (
        (tool === "explore_seller" || tool === "discover_sellers" || tool === "scout_trustnet") &&
        (args.includes(q) || result.includes(q))
      )
    })
  }

  // Find gateway transactions referencing a service (for sell-side)
  function getTransactionsForService(serviceId: string): TxEntry[] {
    return transactions.filter((t) => t.service_id === serviceId && t.event_type === "buy_and_call")
  }

  // Our entries in Trust-Net (only show if they have real activity)
  const ourEntries = useMemo(() => {
    return trustNetAgents.filter(
      (a) => a.team_name?.toLowerCase().includes("mog") && parseInt(a.total_orders || "0") > 0,
    )
  }, [trustNetAgents])

  // Summary stats from our txlog
  const txStats = useMemo(() => {
    const buys = transactions.filter((t) => t.event_type === "buy_and_call")
    const successful = buys.filter((t) => t.success)
    const revenue = buys.reduce((sum, t) => sum + (t.credits_charged || 0), 0)
    const uniqueServices = new Set(buys.map((t) => t.service_id)).size
    const nvmActivity = colonyActivity.filter((a) => a.is_nvm)
    const scoutActivity = colonyActivity.filter((a) => a.is_scout)
    return { total: buys.length, successful: successful.length, revenue, uniqueServices, nvmActivity: nvmActivity.length, scoutActivity: scoutActivity.length }
  }, [transactions, colonyActivity])

  // Explore_seller calls grouped by team
  const explorations = useMemo(() => {
    const map = new Map<string, ColonyActivity[]>()
    for (const a of colonyActivity) {
      if (a.tool === "explore_seller" || a.tool === "discover_sellers") {
        // Try to extract team name from args
        const teamMatch = a.args?.match(/team_name=([^,]+)/i)
        const key = teamMatch ? teamMatch[1].trim() : "discovery"
        const list = map.get(key) || []
        list.push(a)
        map.set(key, list)
      }
    }
    return map
  }, [colonyActivity])

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
              {trustNetAgents.length} participants via Trust-Net &middot; {txStats.total} gateway transactions &middot;{" "}
              {txStats.nvmActivity} agent NVM calls &middot; {txStats.scoutActivity} scout operations
            </p>
          </div>
          <div className="text-right">
            <div className="font-mono text-xs text-stone/40">data sources</div>
            <div className="font-mono text-xs text-stone/60 mt-1">
              Trust-Net &middot; txlog.jsonl &middot; Colony Telemetry
            </div>
          </div>
        </div>

        {/* Our transaction summary */}
        <div className="bg-copper/5 border border-copper/20 rounded-xl p-5 mb-6">
          <h2 className="font-sans text-sm font-medium text-copper mb-3">Our Activity Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white/60 rounded-lg p-3">
              <div className="font-mono text-2xl text-charcoal">{txStats.total}</div>
              <div className="font-mono text-[10px] text-stone/40">total transactions</div>
            </div>
            <div className="bg-white/60 rounded-lg p-3">
              <div className="font-mono text-2xl text-charcoal">{txStats.successful}</div>
              <div className="font-mono text-[10px] text-stone/40">successful</div>
            </div>
            <div className="bg-white/60 rounded-lg p-3">
              <div className="font-mono text-2xl text-charcoal">{txStats.revenue}</div>
              <div className="font-mono text-[10px] text-stone/40">credits earned</div>
            </div>
            <div className="bg-white/60 rounded-lg p-3">
              <div className="font-mono text-2xl text-charcoal">{txStats.uniqueServices}</div>
              <div className="font-mono text-[10px] text-stone/40">services transacted</div>
            </div>
          </div>

          {/* Our Trust-Net position */}
          {ourEntries.length > 0 && (
            <>
              <h3 className="font-mono text-[10px] text-copper/60 uppercase tracking-wider mb-2">Trust-Net Position</h3>
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
            </>
          )}
        </div>

        {/* Our buy-side explorations */}
        {explorations.size > 0 && (
          <div className="bg-sage/5 border border-sage/20 rounded-xl p-5 mb-6">
            <h2 className="font-sans text-sm font-medium text-sage mb-3">
              Buy-Side Activity — Teams We Explored ({explorations.size})
            </h2>
            <div className="space-y-2">
              {[...explorations.entries()].map(([team, acts]) => (
                <div key={team} className="bg-white/60 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-sans text-sm font-medium text-charcoal">{team}</span>
                      <span className="font-mono text-[10px] text-sage px-1.5 py-0.5 rounded-full bg-sage/10">
                        {acts.length} interaction{acts.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <span className="font-mono text-[10px] text-stone/40">
                      {acts[0]?.timestamp?.slice(0, 16)?.replace("T", " ")}
                    </span>
                  </div>
                  <div className="mt-2 space-y-1">
                    {acts.slice(0, 5).map((act, j) => (
                      <div key={j} className="flex items-start gap-2 font-mono text-[11px] text-stone/60">
                        <span className="text-stone/40 shrink-0">{act.agent.replace("mog-", "")}</span>
                        <span
                          className="px-1 py-0 rounded text-[9px] shrink-0"
                          style={{ backgroundColor: act.is_nvm ? "#87A87818" : "#78716C18" }}
                        >
                          {act.tool}
                        </span>
                        <span className="truncate">{act.result?.slice(0, 120)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent transaction log */}
        {transactions.length > 0 && (
          <div className="bg-white/40 border border-sage/10 rounded-xl p-5 mb-6">
            <h2 className="font-sans text-sm font-medium text-charcoal mb-3">
              Transaction Log ({transactions.length} entries)
            </h2>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {transactions
                .slice()
                .reverse()
                .slice(0, 50)
                .map((tx, i) => (
                  <div
                    key={i}
                    className={`flex items-center gap-2 font-mono text-[11px] px-2 py-1 rounded ${
                      tx.success ? "text-stone/70" : "text-rose/60 bg-rose/5"
                    }`}
                  >
                    <span
                      className={`inline-block w-1.5 h-1.5 rounded-full shrink-0 ${tx.success ? "bg-sage" : "bg-rose/40"}`}
                    />
                    <span className="text-stone/40 shrink-0 w-28">
                      {tx.timestamp?.slice(11, 19) ?? ""}
                    </span>
                    <span className="font-medium shrink-0">{tx.service_id}</span>
                    {tx.credits_charged ? (
                      <span className="text-copper shrink-0">{tx.credits_charged}cr</span>
                    ) : null}
                    {tx.surge_multiplier && tx.surge_multiplier > 1 ? (
                      <span className="text-gold text-[9px] shrink-0">{tx.surge_multiplier}x surge</span>
                    ) : null}
                    {tx.latency_ms ? (
                      <span className="text-stone/30 shrink-0">{tx.latency_ms}ms</span>
                    ) : null}
                    {tx.error ? (
                      <span className="truncate text-rose/50">{tx.error.slice(0, 80)}</span>
                    ) : null}
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
            const interactions = getColonyInteractions(agent.team_name)
            const revenue = parseFloat(agent.total_revenue_usdc || "0")
            const orders = parseInt(agent.total_orders || "0")
            const isExpanded = expandedTeam === agent.agent_id

            return (
              <motion.div
                key={agent.agent_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.02 }}
                className={`rounded-xl border p-4 cursor-pointer transition-colors ${
                  isMog
                    ? "bg-copper/5 border-copper/20"
                    : interactions.length > 0
                      ? "bg-sage/5 border-sage/20"
                      : "bg-white/60 border-sage/10 hover:border-sage/20"
                }`}
                onClick={() => setExpandedTeam(isExpanded ? null : agent.agent_id)}
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
                      {interactions.length > 0 && !isMog && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-sage/15 text-sage">
                          {interactions.length} interaction{interactions.length !== 1 ? "s" : ""}
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

                {/* Expanded: show our specific interactions */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-sage/10 space-y-3">
                    {/* Colony agent interactions */}
                    {interactions.length > 0 && (
                      <div>
                        <div className="font-mono text-[10px] text-sage/60 uppercase tracking-wider mb-1">
                          Agent Interactions ({interactions.length})
                        </div>
                        <div className="space-y-1">
                          {interactions.slice(0, 10).map((act, j) => (
                            <div key={j} className="flex items-start gap-2 font-mono text-[11px] text-stone/60">
                              <span className="text-stone/40 shrink-0 w-24">
                                {act.timestamp?.slice(11, 19) ?? ""}
                              </span>
                              <span className="text-stone/50 shrink-0">{act.agent.replace("mog-", "")}</span>
                              <span
                                className="px-1 py-0 rounded text-[9px] shrink-0"
                                style={{ backgroundColor: act.is_nvm ? "#87A87818" : "#78716C18" }}
                              >
                                {act.tool}
                              </span>
                              <span className="truncate">{act.result?.slice(0, 150)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Endpoint info */}
                    {agent.endpoint_url && !isMog && (
                      <div className="font-mono text-[10px] text-stone/30 truncate">
                        endpoint: {agent.endpoint_url}
                      </div>
                    )}

                    {interactions.length === 0 && (
                      <div className="font-mono text-[11px] text-stone/30 italic">
                        No recorded interactions with this team yet
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* Stats footer */}
        <div className="mt-8 pt-4 border-t border-sage/10 flex flex-wrap items-center gap-6 font-mono text-xs text-stone/40">
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
          <span>{explorations.size} teams explored by our agents</span>
        </div>
      </div>
    </div>
  )
}
