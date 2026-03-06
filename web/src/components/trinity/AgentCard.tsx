import { motion } from "motion/react"
import { type AgentWithHistory } from "@/hooks/useTrinity"

const ROLE_META: Record<string, { role: string; color: string; emoji: string }> = {
  "mog-scout": { role: "Chief Strategist", color: "#6B8DAE", emoji: "S" },
  "mog-worker": { role: "Engineering Lead", color: "#87A878", emoji: "W" },
  "mog-dashboard": { role: "Operations / COO", color: "#C5A862", emoji: "D" },
}

interface AgentCardProps {
  data: AgentWithHistory
  selected: boolean
  onSelect: () => void
}

export function AgentCard({ data, selected, onSelect }: AgentCardProps) {
  const { agent, history } = data
  const meta = ROLE_META[agent.name] ?? { role: "Agent", color: "#B87333", emoji: "?" }
  const lastMessage = history.length > 0 ? history[history.length - 1] : null
  const isRunning = agent.status === "running"

  return (
    <motion.button
      onClick={onSelect}
      className={`w-full text-left p-5 rounded-lg border transition-all ${
        selected
          ? "border-copper/60 bg-white shadow-sm"
          : "border-sage/20 bg-linen hover:border-sage/40"
      }`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center text-xl font-mono font-bold text-white flex-shrink-0"
          style={{ backgroundColor: meta.color }}
        >
          {meta.emoji}
        </div>

        <div className="flex-1 min-w-0">
          {/* Name + Status */}
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg font-sans font-medium text-charcoal">
              {agent.name}
            </span>
            <span
              className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                isRunning ? "bg-sage" : "bg-stone/30"
              }`}
            />
          </div>

          <div className="text-sm font-sans text-stone mb-2">
            {meta.role}
          </div>

          {/* Last activity */}
          {lastMessage && (
            <div className="text-sm font-sans text-stone/70 truncate">
              <span className="text-xs font-mono text-stone/40 mr-1">
                {lastMessage.role === "assistant" ? "responded" : "asked"}
              </span>
              {lastMessage.content.slice(0, 80)}
              {lastMessage.content.length > 80 ? "..." : ""}
            </div>
          )}

          {/* Stats */}
          <div className="flex items-center gap-4 mt-2 text-xs font-mono text-stone/50">
            <span>{history.length} messages</span>
            <span>port {agent.port}</span>
            <span>{agent.runtime}</span>
          </div>
        </div>
      </div>
    </motion.button>
  )
}
