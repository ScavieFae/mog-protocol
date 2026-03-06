import { motion } from "motion/react"
import { type AgentWithHistory } from "@/hooks/useTrinity"

const AGENT_POSITIONS: Record<string, { x: number; y: number }> = {
  "mog-scout": { x: 200, y: 60 },
  "mog-worker": { x: 400, y: 60 },
  "mog-dashboard": { x: 300, y: 200 },
}

const ROLE_META: Record<string, { color: string; label: string }> = {
  "mog-scout": { color: "#6B8DAE", label: "Scout" },
  "mog-worker": { color: "#87A878", label: "Worker" },
  "mog-dashboard": { color: "#C5A862", label: "Dashboard" },
}

const CONNECTIONS = [
  { from: "mog-scout", to: "mog-worker", label: "wrap briefs" },
  { from: "mog-worker", to: "mog-scout", label: "status reports" },
  { from: "mog-dashboard", to: "mog-scout", label: "demand signals" },
  { from: "mog-dashboard", to: "mog-worker", label: "health alerts" },
]

interface AgentNetworkProps {
  agents: AgentWithHistory[]
}

export function AgentNetwork({ agents }: AgentNetworkProps) {
  return (
    <svg viewBox="0 0 600 280" className="w-full max-w-2xl">
      {/* Connection lines */}
      {CONNECTIONS.map((conn, i) => {
        const from = AGENT_POSITIONS[conn.from]
        const to = AGENT_POSITIONS[conn.to]
        if (!from || !to) return null

        const midX = (from.x + to.x) / 2
        const midY = (from.y + to.y) / 2
        const offset = i % 2 === 0 ? -20 : 20

        return (
          <g key={`${conn.from}-${conn.to}`}>
            <path
              d={`M ${from.x} ${from.y} Q ${midX} ${midY + offset} ${to.x} ${to.y}`}
              fill="none"
              stroke="#87A878"
              strokeWidth={1}
              strokeOpacity={0.3}
              strokeDasharray="4 4"
            />
            <text
              x={midX}
              y={midY + offset - 6}
              textAnchor="middle"
              className="fill-stone/40 font-mono"
              fontSize={10}
            >
              {conn.label}
            </text>
          </g>
        )
      })}

      {/* Agent nodes */}
      {agents.map((a) => {
        const pos = AGENT_POSITIONS[a.agent.name]
        const meta = ROLE_META[a.agent.name]
        if (!pos || !meta) return null
        const isRunning = a.agent.status === "running"

        return (
          <motion.g
            key={a.agent.name}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
          >
            {/* Pulse ring for running agents */}
            {isRunning && (
              <motion.circle
                cx={pos.x}
                cy={pos.y}
                r={32}
                fill="none"
                stroke={meta.color}
                strokeWidth={0.5}
                initial={{ opacity: 0.3, scale: 0.9 }}
                animate={{ opacity: 0, scale: 1.4 }}
                transition={{ repeat: Infinity, duration: 3, ease: "easeOut" }}
              />
            )}

            <circle
              cx={pos.x}
              cy={pos.y}
              r={28}
              fill={meta.color}
              fillOpacity={0.12}
              stroke={meta.color}
              strokeWidth={1.5}
            />

            <text
              x={pos.x}
              y={pos.y + 5}
              textAnchor="middle"
              className="font-mono font-bold"
              fontSize={14}
              fill={meta.color}
            >
              {meta.label}
            </text>

            {/* Status dot */}
            <circle
              cx={pos.x + 22}
              cy={pos.y - 22}
              r={5}
              fill={isRunning ? "#87A878" : "#78716C"}
            />

            {/* Message count */}
            <text
              x={pos.x}
              y={pos.y + 50}
              textAnchor="middle"
              className="fill-stone/50 font-mono"
              fontSize={11}
            >
              {a.history.length} msgs
            </text>
          </motion.g>
        )
      })}
    </svg>
  )
}
