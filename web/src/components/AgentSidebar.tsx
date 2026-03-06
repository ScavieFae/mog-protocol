import { motion } from "motion/react"

export interface AgentState {
  name: string
  role: string
  status: "working" | "scouting" | "evaluating" | "idle"
  currentTask?: string
  currentService?: string
  tools: string[]  // exa, browserbase, apify, etc.
  recentActions: string[]
}

const TOOL_ICONS: Record<string, { label: string; color: string }> = {
  exa: { label: "Exa", color: "#6B8DAE" },
  browserbase: { label: "BB", color: "#9B8EC2" },
  apify: { label: "Ap", color: "#C5A862" },
  anthropic: { label: "An", color: "#B87333" },
  agentmail: { label: "AM", color: "#7BA787" },
  nevermined: { label: "NM", color: "#87A878" },
}

const STATUS_COLORS: Record<string, string> = {
  working: "#87A878",
  scouting: "#6B8DAE",
  evaluating: "#C5A862",
  idle: "#78716C",
}

interface AgentSidebarProps {
  agents: AgentState[]
  selectedAgent?: string
  onSelectAgent?: (name: string) => void
}

export function AgentSidebar({ agents, selectedAgent, onSelectAgent }: AgentSidebarProps) {
  return (
    <div className="w-72 border-l border-sage/15 bg-white/30 p-4 overflow-y-auto">
      <h2 className="font-sans text-xs uppercase tracking-wider text-stone/50 mb-4">Agents</h2>
      <div className="space-y-3">
        {agents.map((agent) => (
          <motion.div
            key={agent.name}
            layout
            className={`rounded-lg p-3 border cursor-pointer transition-colors ${
              selectedAgent === agent.name
                ? "bg-white/80 border-copper/30"
                : "bg-white/40 border-sage/10 hover:bg-white/60"
            }`}
            onClick={() => onSelectAgent?.(agent.name)}
          >
            {/* Agent header */}
            <div className="flex items-center gap-2 mb-1.5">
              <motion.div
                className={`w-2 h-2 rounded-full ${agent.status === "working" ? "animate-pulse-sage" : agent.status === "scouting" ? "animate-pulse-gold" : ""}`}
                style={{ backgroundColor: STATUS_COLORS[agent.status] }}
                animate={agent.status !== "idle" ? { scale: [1, 1.3, 1] } : {}}
                transition={{ repeat: Infinity, duration: 2 }}
              />
              <span className="font-mono text-sm text-charcoal font-medium">{agent.name}</span>
              <span className="font-sans text-[10px] text-stone/50 ml-auto">{agent.role}</span>
            </div>

            {/* Current task */}
            <p className="font-sans text-xs text-stone/70 mb-2 line-clamp-2">
              {agent.currentTask ?? "idle"}
            </p>

            {/* Tool icons */}
            {agent.tools.length > 0 && (
              <div className="flex gap-1">
                {agent.tools.map((tool) => {
                  const cfg = TOOL_ICONS[tool]
                  if (!cfg) return null
                  return (
                    <span
                      key={tool}
                      className="text-[9px] font-mono px-1.5 py-0.5 rounded"
                      style={{ backgroundColor: `${cfg.color}15`, color: cfg.color }}
                      title={tool}
                    >
                      {cfg.label}
                    </span>
                  )
                })}
              </div>
            )}

            {/* Recent actions (expanded) */}
            {selectedAgent === agent.name && agent.recentActions.length > 0 && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                className="mt-3 pt-2 border-t border-sage/10"
              >
                <p className="font-sans text-[10px] uppercase tracking-wider text-stone/40 mb-1">Recent</p>
                <div className="space-y-1 stagger-children">
                  {agent.recentActions.slice(0, 5).map((action, i) => (
                    <p key={i} className="font-mono text-[11px] text-stone/60 leading-tight animate-slide-in">
                      {action}
                    </p>
                  ))}
                </div>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
