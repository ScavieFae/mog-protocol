import { motion } from "motion/react"
import type { HealthData } from "@/hooks/useHealth"

interface TimelineProps {
  data: HealthData
}

interface TimelineEvent {
  time: string
  title: string
  detail: string
  color: string
  icon: string
}

function buildTimeline(data: HealthData): TimelineEvent[] {
  const events: TimelineEvent[] = []

  // Hardcoded milestone events (the story)
  events.push(
    {
      time: "12:36",
      title: "First paid transaction",
      detail: "Exa search, 1 credit burned, tx 0xe5a5d1bc…",
      color: "#87A878",
      icon: "◆",
    },
    {
      time: "13:30",
      title: "Vertical slice complete",
      detail: "find_service → buy_and_call → real API result → credits burned",
      color: "#B87333",
      icon: "●",
    },
    {
      time: "15:08",
      title: "Agent autonomously wrapped Open-Meteo",
      detail: "Discovered via web search → evaluated ROI → wrote handler → tested → live",
      color: "#9B8EC2",
      icon: "★",
    },
    {
      time: "16:10",
      title: "External subscribers arrived",
      detail: "4 unknown wallets subscribed — real teams finding us on the portal",
      color: "#C5A862",
      icon: "↗",
    },
    {
      time: "18:00",
      title: "First USDC transaction",
      detail: "1 USDC paid, credit burned, Exa search returned — settled on Base Sepolia",
      color: "#87A878",
      icon: "◆",
    },
    {
      time: "18:15",
      title: "Cross-team trade with Trust Net",
      detail: "Subscribed to their plan, called list_agents — real cross-team commerce",
      color: "#6B8DAE",
      icon: "⇄",
    },
  )

  // Dynamic events from live data
  const agentServices = data.services.filter(s => s.provider === "mog-agent")
  if (agentServices.length > 0) {
    events.push({
      time: "now",
      title: `${agentServices.length} agent-built service${agentServices.length > 1 ? "s" : ""} live`,
      detail: agentServices.map(s => s.name).join(", "),
      color: "#9B8EC2",
      icon: "●",
    })
  }

  const totalCalls = data.services.reduce((sum, s) => sum + (s.stats?.total_calls ?? 0), 0)
  if (totalCalls > 0) {
    events.push({
      time: "now",
      title: `${totalCalls} total API calls served`,
      detail: `${data.services_count} services, ${data.portfolio?.total_earned ?? 0}cr earned`,
      color: "#87A878",
      icon: "↑",
    })
  }

  if (data.colony?.running) {
    events.push({
      time: "now",
      title: "Colony is live",
      detail: `${data.colony.agents.length} agents running — scout, worker, supervisor, debugger`,
      color: "#B87333",
      icon: "▶",
    })
  }

  return events
}

export function Timeline({ data }: TimelineProps) {
  const events = buildTimeline(data)

  return (
    <div className="px-8 py-5 border-t border-charcoal/5">
      <h3 className="font-sans text-xs uppercase tracking-wider text-stone/40 mb-3">
        Timeline — Key Moments
      </h3>
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
        {events.map((ev, i) => (
          <motion.div
            key={i}
            className="flex-shrink-0 w-52 rounded-lg border border-charcoal/5 bg-white/50 px-3 py-2.5 hover:bg-white/80 transition-colors"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <div className="flex items-center gap-2 mb-1">
              <span style={{ color: ev.color }} className="text-sm">{ev.icon}</span>
              <span className="font-mono text-[10px] text-stone/40">
                {ev.time === "now" ? (
                  <span className="text-sage font-medium">live</span>
                ) : (
                  ev.time
                )}
              </span>
            </div>
            <p className="font-sans text-[13px] font-medium text-charcoal leading-snug">
              {ev.title}
            </p>
            <p className="font-sans text-[11px] text-stone/50 mt-0.5 leading-snug">
              {ev.detail}
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
