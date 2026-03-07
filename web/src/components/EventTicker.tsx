import { useMemo } from "react"
import { motion } from "motion/react"
import type { Service, Transaction, GraveyardEntry } from "@/hooks/useHealth"

interface EventTickerProps {
  services: Service[]
  transactions: Transaction[]
  graveyard?: GraveyardEntry[]
}

interface TickerEvent {
  text: string
  color: string
  icon: string
}

export function EventTicker({ services, transactions, graveyard }: EventTickerProps) {
  const events = useMemo(() => {
    const items: TickerEvent[] = []

    // Surge events
    for (const s of services) {
      if (s.surge_multiplier && s.surge_multiplier > 1.3) {
        items.push({
          text: `${s.name} surging at ${s.surge_multiplier.toFixed(1)}x`,
          color: s.surge_multiplier > 1.5 ? "#C47A7A" : "#C5A862",
          icon: "↑",
        })
      }
    }

    // Top earners
    const earners = [...services]
      .filter(s => (s.stats?.revenue_credits ?? 0) > 0)
      .sort((a, b) => (b.stats?.revenue_credits ?? 0) - (a.stats?.revenue_credits ?? 0))
    if (earners.length > 0) {
      items.push({
        text: `${earners[0].name} leads with ${earners[0].stats?.revenue_credits}cr earned`,
        color: "#87A878",
        icon: "★",
      })
    }

    // High call count milestones
    for (const s of services) {
      const calls = s.stats?.total_calls ?? 0
      if (calls >= 10) {
        items.push({
          text: `${s.name} hit ${calls} calls`,
          color: "#B87333",
          icon: "●",
        })
      }
    }

    // Recent transaction activity
    const recentTx = transactions.slice(0, 5)
    for (const tx of recentTx) {
      if (tx.success) {
        items.push({
          text: `${tx.service_id.replace(/_/g, " ")} sold for ${tx.credits_charged}cr`,
          color: "#87A878",
          icon: "→",
        })
      } else {
        items.push({
          text: `${tx.service_id.replace(/_/g, " ")} call failed`,
          color: "#C47A7A",
          icon: "✕",
        })
      }
    }

    // Killed services
    if (graveyard) {
      for (const g of graveyard) {
        items.push({
          text: `${g.name} killed — ${g.reason}`,
          color: "#C47A7A",
          icon: "☠",
        })
      }
    }

    // Low success rate warnings
    for (const s of services) {
      if (s.stats && s.stats.total_calls >= 3 && s.stats.success_rate < 0.5) {
        items.push({
          text: `${s.name} struggling — ${(s.stats.success_rate * 100).toFixed(0)}% success`,
          color: "#C5A862",
          icon: "⚠",
        })
      }
    }

    // Pad with service count if we need more
    if (items.length < 3) {
      items.push({
        text: `${services.length} services live on the proving ground`,
        color: "#78716C",
        icon: "◆",
      })
    }

    return items
  }, [services, transactions, graveyard])

  const items = [...events, ...events] // duplicate for seamless loop

  return (
    <div className="border-b border-charcoal/8 bg-charcoal/[0.03] overflow-hidden h-10 flex items-center">
      <motion.div
        className="flex gap-10 whitespace-nowrap px-4"
        animate={{ x: ["0%", "-50%"] }}
        transition={{
          x: {
            repeat: Infinity,
            repeatType: "loop",
            duration: Math.max(events.length * 5, 20),
            ease: "linear",
          },
        }}
      >
        {items.map((ev, i) => (
          <span key={i} className="inline-flex items-center gap-2 text-sm">
            <span style={{ color: ev.color }} className="text-xs">{ev.icon}</span>
            <span className="font-sans text-stone/70">{ev.text}</span>
            <span className="text-stone/15 ml-2">|</span>
          </span>
        ))}
      </motion.div>
    </div>
  )
}
