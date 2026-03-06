import { useState, useMemo } from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "motion/react"
import { useHealth, type SupervisorEvaluation } from "@/hooks/useHealth"
import { ServiceCard } from "@/components/ServiceCard"
import { HivePanel } from "@/components/HivePanel"
import { Ticker } from "@/components/Ticker"

function PortfolioBar({ data }: { data: ReturnType<typeof useHealth>["data"] }) {
  if (!data) return null
  const p = data.portfolio
  return (
    <div className="border-b border-sage/15 bg-white/40 px-6 py-2.5 flex items-center gap-6 text-sm">
      <span className="font-sans text-stone/60">
        <span className={`inline-block w-2 h-2 rounded-full mr-2 align-middle ${data.colony?.running ? "bg-sage animate-pulse-sage" : "bg-stone/30"}`} />
        {data.colony?.running ? "colony live" : data.status}
      </span>
      <span className="font-mono text-copper">{data.services_count} services</span>
      <span className="font-mono text-gold">{p?.total_earned ?? 0}cr earned</span>
      <span className="font-mono text-stone/50">{p?.balance ?? 0}cr balance</span>
      {data.supervisor && (
        <span className="font-mono text-xs text-stone/40">
          {data.supervisor.counts?.greenlit ?? 0} greenlit
          {(data.supervisor.counts?.under_review ?? 0) > 0 && ` · ${data.supervisor.counts.under_review} reviewing`}
          {(data.supervisor.counts?.killed ?? 0) > 0 && ` · ${data.supervisor.counts.killed} killed`}
        </span>
      )}
      <div className="ml-auto flex gap-4">
        <Link to="/colony" className="font-mono text-xs text-sage/60 hover:text-sage transition-colors">
          colony &rarr;
        </Link>
        <Link to="/connect" className="font-mono text-xs text-stone/40 hover:text-stone transition-colors">
          connect &rarr;
        </Link>
      </div>
    </div>
  )
}

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
  const [hiveExpanded, setHiveExpanded] = useState(true)
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
      return (a.stats?.total_calls ?? 0) - (b.stats?.total_calls ?? 0)
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
      <Ticker services={data.services} />
      <PortfolioBar data={data} />

      <div className="flex flex-1 overflow-hidden">
        {/* Service cards grid */}
        <div className="flex-1 p-6 overflow-y-auto">
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

        </div>

        {/* Hive panel */}
        <HivePanel
          colony={data.colony}
          expanded={hiveExpanded}
          onToggle={() => setHiveExpanded(!hiveExpanded)}
        />
      </div>

      <TransactionStream transactions={data.recent_transactions} />
    </div>
  )
}
