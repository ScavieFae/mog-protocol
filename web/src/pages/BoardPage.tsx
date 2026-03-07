import { useState, useMemo } from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "motion/react"
import { useHealth, type SupervisorEvaluation } from "@/hooks/useHealth"
import { ServiceCard } from "@/components/ServiceCard"
import { HivePanel } from "@/components/HivePanel"
import { EventTicker } from "@/components/EventTicker"
import { HeroSection } from "@/components/HeroSection"
import { Timeline } from "@/components/Timeline"

function TransactionStream({ transactions }: { transactions: ReturnType<typeof useHealth>["data"] extends infer T ? T extends { recent_transactions: infer R } ? R : never : never }) {
  if (!transactions || transactions.length === 0) return null
  return (
    <div className="border-t border-sage/15 bg-white/30 px-6 py-2 flex items-center gap-3 overflow-x-auto">
      <span className="font-sans text-[10px] uppercase tracking-wider text-stone/40 shrink-0">live</span>
      <AnimatePresence mode="popLayout">
        {transactions.slice(0, 12).map((tx, i) => (
          <motion.span
            key={`${tx.service_id}-${tx.timestamp}-${i}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className={`font-mono text-xs whitespace-nowrap ${tx.success ? "text-stone/60" : "text-rose/60"}`}
          >
            <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1 ${tx.success ? "bg-sage" : "bg-rose/40"}`} />
            {tx.service_id.replace(/_/g, " ")} {tx.credits_charged}cr
          </motion.span>
        ))}
      </AnimatePresence>
    </div>
  )
}

export function BoardPage() {
  const { data, error, loading } = useHealth(5000)
  const [hiveExpanded, setHiveExpanded] = useState(false)
  const navigate = useNavigate()

  // Build evaluation lookup from supervisor data
  const evaluationMap = useMemo(() => {
    const map = new Map<string, SupervisorEvaluation>()
    if (data?.supervisor?.evaluations) {
      for (const ev of data.supervisor.evaluations) {
        map.set(ev.service_id, ev)
      }
    }
    return map
  }, [data])

  // Sort services: earning first, then by revenue, then alphabetical
  const sortedServices = useMemo(() => {
    if (!data) return []
    return [...data.services].sort((a, b) => {
      const ra = a.stats?.revenue_credits ?? 0
      const rb = b.stats?.revenue_credits ?? 0
      if (ra !== rb) return rb - ra
      return (b.stats?.total_calls ?? 0) - (a.stats?.total_calls ?? 0)
    })
  }, [data])

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <p className="text-lg font-sans text-stone">loading board...</p>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <p className="text-lg font-sans text-rose">{error}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen bg-linen flex flex-col">
      {/* Event ticker — notable happenings */}
      <EventTicker
        services={data.services}
        transactions={data.recent_transactions}
        graveyard={data.graveyard}
      />

      {/* Hero — tagline, stats, how it works */}
      <HeroSection data={data} />

      {/* Nav */}
      <div className="px-8 pb-2 flex items-center gap-4 border-b border-charcoal/5">
        <span className="font-sans text-sm font-medium text-charcoal border-b-2 border-copper pb-1">Board</span>
        <Link to="/garden" className="font-sans text-sm text-stone/50 hover:text-charcoal transition-colors pb-1">Garden</Link>
        <Link to="/colony" className="font-sans text-sm text-stone/50 hover:text-charcoal transition-colors pb-1">Colony</Link>
        <Link to="/connect" className="font-sans text-sm text-stone/50 hover:text-charcoal transition-colors pb-1">Connect</Link>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Service cards grid */}
        <div className="flex-1 px-8 pb-6 overflow-y-auto">
          <h3 className="font-sans text-xs uppercase tracking-wider text-stone/40 mb-3">
            Services — {data.services_count} live
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 stagger-children">
            {sortedServices.map((service) => (
              <ServiceCard
                key={service.service_id}
                service={service}
                evaluation={evaluationMap.get(service.service_id)}
                onClick={() => navigate(`/service/${service.service_id}`)}
              />
            ))}
          </div>

          {/* Demand whispers zone */}
          {data.demand_signals && data.demand_signals.length > 0 && (
            <div className="mt-6 pt-4 border-t border-sage/10">
              <h3 className="font-sans text-xs uppercase tracking-wider text-stone/40 mb-3">
                Unmet Demand — Scout is watching
              </h3>
              <div className="flex flex-wrap gap-2">
                {data.demand_signals.slice(0, 8).map((signal, i) => (
                  <motion.span
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.1 }}
                    className="font-sans text-sm italic text-purple/60 bg-purple/5 px-3 py-1 rounded-full"
                  >
                    "{signal.query}"
                  </motion.span>
                ))}
              </div>
            </div>
          )}

          {/* Service graveyard */}
          {data.graveyard && data.graveyard.length > 0 && (
            <div className="mt-6 pt-4 border-t border-rose/10">
              <h3 className="font-sans text-xs uppercase tracking-wider text-stone/40 mb-3">
                Graveyard — {data.graveyard.length} killed
              </h3>
              <div className="flex flex-wrap gap-2">
                {data.graveyard.map((g) => (
                  <div
                    key={g.service_id}
                    className="rounded-lg px-3 py-2 border border-rose/15 bg-rose/5 opacity-50"
                    title={g.reason}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-rose/60 text-xs">&#x2717;</span>
                      <span className="font-mono text-xs text-stone/50 line-through">{g.name}</span>
                      <span className="font-mono text-[10px] text-stone/30">{g.provider}</span>
                    </div>
                    <p className="font-mono text-[10px] text-stone/40 mt-0.5 max-w-[200px] truncate">
                      {g.reason}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Hive panel */}
        <HivePanel
          colony={data.colony}
          expanded={hiveExpanded}
          onToggle={() => setHiveExpanded(!hiveExpanded)}
        />
      </div>

      {/* Timeline — the story */}
      <Timeline data={data} />

      {/* Live transaction stream */}
      <TransactionStream transactions={data.recent_transactions} />
    </div>
  )
}
