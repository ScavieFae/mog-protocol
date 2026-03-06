import { useState, useMemo } from "react"
import { motion, AnimatePresence } from "motion/react"
import { type ColonyData, type ActivityEntry } from "@/hooks/useHealth"

// Tool → sponsor/category mapping for badges
const TOOL_META: Record<string, { label: string; color: string; sponsor?: string; bright?: boolean }> = {
  search_web: { label: "Exa", color: "#6B8DAE", sponsor: "exa" },
  scout_exa: { label: "SCOUT:EXA", color: "#4A90D9", sponsor: "exa", bright: true },
  scout_apify: { label: "SCOUT:APIFY", color: "#FF6B35", bright: true },
  scout_trustnet: { label: "SCOUT:TRUST", color: "#E056A0", bright: true },
  self_buy: { label: "NVM", color: "#87A878", sponsor: "nevermined" },
  explore_seller: { label: "NVM", color: "#87A878", sponsor: "nevermined" },
  discover_sellers: { label: "NVM", color: "#87A878", sponsor: "nevermined" },
  check_marketplace: { label: "MKT", color: "#78716C" },
  send_message: { label: "MSG", color: "#9B8EC2" },
  propose_service: { label: "NEW", color: "#C5A862" },
  register_service: { label: "REG", color: "#B87333" },
  test_service: { label: "TST", color: "#6B8DAE" },
  get_proposals: { label: "Q", color: "#78716C" },
  evaluate_service: { label: "EVL", color: "#C47A7A" },
  check_errors: { label: "ERR", color: "#C47A7A" },
  inspect_service: { label: "INS", color: "#C47A7A" },
  patch_service: { label: "FIX", color: "#87A878" },
}

const AGENT_COLORS: Record<string, string> = {
  "mog-scout": "#6B8DAE",
  "mog-worker": "#87A878",
  "mog-supervisor": "#C5A862",
  "mog-debugger": "#C47A7A",
}

function timeAgo(timestamp: string): string {
  if (!timestamp) return ""
  const diff = Date.now() - new Date(timestamp).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m`
  return `${Math.floor(minutes / 60)}h`
}

function summarizeResult(tool: string, result: string): string {
  // Parse JSON results into human-readable summaries
  try {
    const data = JSON.parse(result)
    if (data.error) return `error: ${data.error.slice(0, 60)}`
    if (tool === "search_web" && Array.isArray(data)) return `found ${data.length} results`
    if (tool === "scout_exa") return `${data.query} [${data.focus}] ${data.results?.length ?? 0} hits`
    if (tool === "scout_apify") return `${data.query} ${data.actors_found ?? 0} actors`
    if (tool === "scout_trustnet") return `${Array.isArray(data.trust_net_agents) ? data.trust_net_agents.length : "?"} participants vs ${data.our_service_count ?? "?"} ours`
    if (tool === "self_buy") return `${data.service_id} ${data.status === 200 ? "ok" : `status ${data.status}`}`
    if (tool === "explore_seller") return `${data.subscribed ?? "explored"} ${data.team ?? data.plan_id?.slice(0, 12) ?? ""}`
    if (tool === "discover_sellers" && Array.isArray(data)) return `${data.length} sellers found`
    if (tool === "register_service" && data.registered) return `${data.service_id} LIVE`
    if (tool === "test_service") return `${data.service_id} ${data.success ? "pass" : "fail"}`
    if (tool === "evaluate_service") return `${data.service_id} ${data.verdict}`
    if (tool === "propose_service" && data.proposed) return `${data.service_id} proposed`
    if (tool === "send_message" && data.sent) return `to ${data.to?.replace("mog-", "")}`
    if (tool === "check_marketplace") return `${data.services_count} services, ${data.stats?.total_revenue ?? 0}cr`
    if (tool === "get_proposals" && Array.isArray(data)) return `${data.length} pending`
  } catch {
    // not JSON
  }
  return result.slice(0, 60)
}

interface HivePanelProps {
  colony?: ColonyData
  expanded: boolean
  onToggle: () => void
}

export function HivePanel({ colony, expanded, onToggle }: HivePanelProps) {
  const [filterAgent, setFilterAgent] = useState<string | null>(null)

  const agents = colony?.agents ?? []
  const feed = colony?.activity_feed ?? []

  const filteredFeed = useMemo(() => {
    if (!filterAgent) return feed
    return feed.filter((a) => a.agent === filterAgent)
  }, [feed, filterAgent])

  // Stats
  const stats = useMemo(() => {
    const nvmCount = feed.filter((a) => a.is_nvm).length
    const exaCount = feed.filter((a) => a.tool === "search_web" || a.tool === "scout_exa").length
    const scoutCount = feed.filter((a) => a.is_scout).length
    const msgCount = feed.filter((a) => a.tool === "send_message").length
    return { nvmCount, exaCount, scoutCount, msgCount }
  }, [feed])

  // Collapsed rail
  if (!expanded) {
    return (
      <div className="w-12 border-l border-sage/15 bg-white/20 flex flex-col items-center py-3 gap-2">
        <button
          onClick={onToggle}
          className="w-8 h-8 rounded-full bg-copper/10 text-copper text-xs font-mono flex items-center justify-center hover:bg-copper/20 transition-colors"
          title="Open Hive"
        >
          H
        </button>
        {/* Agent dots */}
        {agents.map((a) => (
          <div
            key={a.name}
            className={`w-2.5 h-2.5 rounded-full ${a.status !== "idle" ? "animate-pulse-sage" : ""}`}
            style={{ backgroundColor: AGENT_COLORS[a.name] ?? "#78716C" }}
            title={`${a.name}: ${a.status}`}
          />
        ))}
        {colony?.running && (
          <div className="mt-auto text-[9px] font-mono text-sage/60 writing-mode-vertical" style={{ writingMode: "vertical-rl" }}>
            LIVE
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="w-96 border-l border-sage/15 bg-white/20 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-sage/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="font-sans text-sm font-medium text-charcoal">Hive</h2>
          {colony?.running && (
            <span className="inline-flex items-center gap-1 text-[10px] font-mono text-sage">
              <span className="w-1.5 h-1.5 rounded-full bg-sage animate-pulse-sage" />
              LIVE
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-2 text-[10px] font-mono text-stone/50">
            {stats.nvmCount > 0 && <span className="text-sage">{stats.nvmCount} nvm</span>}
            {stats.scoutCount > 0 && <span style={{ color: "#E056A0" }}>{stats.scoutCount} scout</span>}
            {stats.exaCount > 0 && <span className="text-blue-muted">{stats.exaCount} exa</span>}
            {stats.msgCount > 0 && <span className="text-purple">{stats.msgCount} msg</span>}
          </div>
          <button
            onClick={onToggle}
            className="text-stone/40 hover:text-stone transition-colors text-sm"
            title="Collapse"
          >
            &rsaquo;
          </button>
        </div>
      </div>

      {/* Agent pills */}
      <div className="px-4 py-2.5 border-b border-sage/10 flex gap-1.5 flex-wrap">
        <button
          onClick={() => setFilterAgent(null)}
          className={`text-[10px] font-mono px-2 py-1 rounded-full transition-colors ${
            filterAgent === null ? "bg-copper/15 text-copper" : "bg-stone/5 text-stone/50 hover:bg-stone/10"
          }`}
        >
          all
        </button>
        {agents.map((a) => {
          const color = AGENT_COLORS[a.name] ?? "#78716C"
          const isActive = a.status !== "idle"
          const isFiltered = filterAgent === a.name
          const shortName = a.name.replace("mog-", "")
          return (
            <button
              key={a.name}
              onClick={() => setFilterAgent(isFiltered ? null : a.name)}
              className={`inline-flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded-full transition-colors ${
                isFiltered ? "" : "hover:bg-stone/10"
              }`}
              style={{
                backgroundColor: isFiltered ? `${color}20` : undefined,
                color: isFiltered ? color : "#78716C",
                border: isFiltered ? `1px solid ${color}40` : "1px solid transparent",
              }}
              title={a.current_task ?? a.status}
            >
              <span
                className={`w-2 h-2 rounded-full flex-shrink-0 ${isActive ? "animate-pulse-sage" : ""}`}
                style={{ backgroundColor: isActive ? color : `${color}60` }}
              />
              {shortName}
              <span className="text-[9px] opacity-60">t{a.tick_count}</span>
            </button>
          )
        })}
      </div>

      {/* Activity stream */}
      <div className="flex-1 overflow-y-auto px-3 py-2">
        {filteredFeed.length === 0 && (
          <div className="text-center text-stone/30 text-sm italic py-8">
            {colony?.running ? "Waiting for first tick..." : "Colony not running"}
          </div>
        )}
        <div className="space-y-0.5">
          <AnimatePresence initial={false}>
            {filteredFeed.map((activity, i) => (
              <ActivityRow key={`${activity.timestamp}-${activity.tool}-${i}`} activity={activity} />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

function ActivityRow({ activity }: { activity: ActivityEntry }) {
  const meta = TOOL_META[activity.tool] ?? { label: activity.tool.slice(0, 3).toUpperCase(), color: "#78716C" }
  const agentColor = AGENT_COLORS[activity.agent] ?? "#78716C"
  const shortAgent = activity.agent.replace("mog-", "")
  const summary = summarizeResult(activity.tool, activity.result)
  const age = timeAgo(activity.timestamp)
  const isScout = activity.is_scout || meta.bright

  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-start gap-2 py-1.5 px-1 rounded transition-colors group ${
        isScout ? "bg-gradient-to-r from-transparent via-pink-50/40 to-transparent" : "hover:bg-white/40"
      }`}
      style={isScout ? { boxShadow: `inset 0 0 12px ${meta.color}15` } : undefined}
    >
      {/* Agent dot */}
      <span
        className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${isScout ? "animate-ping" : ""}`}
        style={{ backgroundColor: isScout ? meta.color : agentColor }}
      />

      <div className="flex-1 min-w-0">
        {/* Top line: agent + tool badge + time */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-mono font-medium" style={{ color: agentColor }}>
            {shortAgent}
          </span>
          <span
            className={`text-[9px] font-mono px-1.5 py-0 rounded-full font-bold ${
              isScout ? "animate-pulse" : activity.is_nvm ? "animate-pulse-sage" : ""
            }`}
            style={{
              backgroundColor: isScout ? `${meta.color}30` : `${meta.color}18`,
              color: meta.color,
              border: isScout ? `1px solid ${meta.color}50` : undefined,
            }}
          >
            {meta.label}
          </span>
          {activity.is_nvm && (
            <span className="text-[9px] font-mono text-sage/80">$</span>
          )}
          {isScout && (
            <span className="text-[9px] font-mono" style={{ color: meta.color }}>*</span>
          )}
          <span className="text-[9px] font-mono text-stone/30 ml-auto flex-shrink-0">{age}</span>
        </div>

        {/* Result summary */}
        <p className={`text-[11px] font-mono leading-tight truncate ${
          isScout ? "text-stone/80 font-medium" : "text-stone/60"
        }`}>
          {summary}
        </p>
      </div>
    </motion.div>
  )
}
