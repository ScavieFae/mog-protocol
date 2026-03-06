import { motion, AnimatePresence } from "motion/react"
import { useState, useEffect } from "react"
import { type Service, type SupervisorEvaluation } from "@/hooks/useHealth"
import { getServiceIcon } from "@/components/HivePanel"

const CATEGORY_COLORS: Record<string, string> = {
  search: "#6B8DAE",
  creative: "#9B8EC2",
  finance: "#C5A862",
  weather: "#7BA787",
  knowledge: "#87A878",
  toolkit: "#B87333",
  default: "#78716C",
}

function getCategory(id: string): string {
  if (id.includes("exa") || id.includes("search") || id.includes("social")) return "search"
  if (id.includes("claude") || id.includes("nano") || id.includes("gemini")) return "creative"
  if (id.includes("frank") || id.includes("fx") || id.includes("circle")) return "finance"
  if (id.includes("meteo") || id.includes("weather") || id.includes("geo")) return "weather"
  if (id.includes("hackathon") || id.includes("news") || id.includes("archive")) return "knowledge"
  if (id.includes("browser") || id.includes("email") || id.includes("debug")) return "toolkit"
  return "default"
}

const VALUE_ADD_LABELS: Record<string, { label: string; color: string }> = {
  signup_bypass: { label: "Signup Bypass", color: "#9B8EC2" },
  micro_paid: { label: "Micro Paid", color: "#C5A862" },
  api_bypass: { label: "API Bypass", color: "#6B8DAE" },
}

const SUPERVISOR_BADGES: Record<string, { label: string; color: string; icon: string }> = {
  greenlit: { label: "Greenlit", color: "#87A878", icon: "●" },
  under_review: { label: "Under Review", color: "#C5A862", icon: "◐" },
  killed: { label: "Killed", color: "#C47A7A", icon: "✕" },
  pending: { label: "Pending", color: "#78716C", icon: "○" },
}

interface ServiceCardProps {
  service: Service
  evaluation?: SupervisorEvaluation
  onClick?: () => void
}

function isNew(stats?: { first_seen?: string }): boolean {
  if (!stats?.first_seen) return true // no calls = brand new
  const age = Date.now() - new Date(stats.first_seen).getTime()
  return age < 60 * 60 * 1000 // less than 1 hour old
}

export function ServiceCard({ service, evaluation, onClick }: ServiceCardProps) {
  const cat = getCategory(service.service_id)
  const color = CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.default
  const surge = service.surge_multiplier ?? 1
  const stats = service.stats
  const totalCalls = stats?.total_calls ?? 0
  const fresh = isNew(stats)
  const revenue = stats?.revenue_credits ?? 0
  const [flash, setFlash] = useState(false)
  const [prevCalls, setPrevCalls] = useState(totalCalls)

  // Flash when a new sale happens
  useEffect(() => {
    if (totalCalls > prevCalls) {
      setFlash(true)
      const t = setTimeout(() => setFlash(false), 1200)
      setPrevCalls(totalCalls)
      return () => clearTimeout(t)
    }
    setPrevCalls(totalCalls)
  }, [totalCalls, prevCalls])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="relative cursor-pointer group"
      onClick={onClick}
    >
      {/* Sale flash */}
      <AnimatePresence>
        {flash && (
          <motion.div
            initial={{ opacity: 0.6, scale: 0.95 }}
            animate={{ opacity: 0, scale: 1.05 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1.2 }}
            className="absolute inset-0 rounded-xl"
            style={{ border: `2px solid ${color}`, boxShadow: `0 0 20px ${color}40` }}
          />
        )}
      </AnimatePresence>

      <div
        className={`rounded-xl p-4 border hover:bg-white/80 transition-all ${flash ? "animate-shimmer" : ""} ${surge > 1.5 ? "bg-rose/5" : surge > 1.1 ? "bg-gold/5" : "bg-white/60"}`}
        style={{
          borderColor: surge > 1.5 ? "#C47A7A50" : surge > 1.1 ? "#C5A86240" : `${color}30`,
          boxShadow: surge > 1.5 ? "0 0 12px #C47A7A20" : surge > 1.1 ? "0 0 8px #C5A86215" : undefined,
        }}
      >
        {/* Header: name + badges */}
        <div className="flex items-start justify-between mb-1.5">
          <div className="flex items-center gap-2">
            {(() => {
              const icon = getServiceIcon(service.service_id)
              return icon ? (
                <img src={icon} alt="" className={`w-4 h-4 rounded-sm flex-shrink-0 ${totalCalls > 0 ? "animate-breathe" : "opacity-60"}`} loading="lazy" />
              ) : (
                <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${totalCalls > 0 ? "animate-breathe" : ""}`} style={{ backgroundColor: color }} />
              )
            })()}
            <span className="font-sans text-sm font-medium text-charcoal truncate max-w-[140px]">
              {service.name}
            </span>
          </div>
          <div className="flex items-center gap-1">
            {fresh && (
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-sage/15 text-sage animate-fade-up">
                NEW
              </span>
            )}
            {evaluation && (() => {
              const badge = SUPERVISOR_BADGES[evaluation.status]
              if (!badge) return null
              return (
                <span
                  className="font-mono text-[9px] px-1.5 py-0.5 rounded-full"
                  style={{ backgroundColor: `${badge.color}15`, color: badge.color }}
                  title={evaluation.reason}
                >
                  {badge.icon}
                </span>
              )
            })()}
          </div>
        </div>

        {/* Hero stats: calls + revenue + health */}
        <div className="flex items-baseline gap-2 mb-2">
          {totalCalls > 0 ? (
            <>
              <span className="font-mono text-lg font-medium text-charcoal">{totalCalls}</span>
              <span className="font-mono text-xs text-stone/50">calls</span>
              {revenue > 0 && (
                <>
                  <span className="font-mono text-lg font-medium text-sage">{revenue}</span>
                  <span className="font-mono text-xs text-stone/50">earned</span>
                </>
              )}
            </>
          ) : (
            <span className="font-mono text-sm text-stone/40 italic">awaiting first buyer</span>
          )}
        </div>

        {/* Health bar + price + surge */}
        <div className="flex items-center gap-2">
          {/* Success rate bar */}
          {stats?.success_rate != null && totalCalls > 0 && (
            <div className="flex items-center gap-1.5 flex-1 min-w-0">
              <div className="flex-1 h-1.5 rounded-full bg-stone/10 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.round(stats.success_rate * 100)}%`,
                    backgroundColor: stats.success_rate > 0.9 ? "#87A878" : stats.success_rate > 0.6 ? "#C5A862" : "#C47A7A",
                  }}
                />
              </div>
              <span className={`font-mono text-[10px] ${stats.success_rate > 0.9 ? "text-sage" : stats.success_rate > 0.6 ? "text-gold" : "text-rose"}`}>
                {(stats.success_rate * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {/* Price (small, right-aligned) */}
          <span className={`font-mono text-xs ml-auto flex-shrink-0 ${surge > 1.5 ? "text-rose font-bold" : surge > 1.1 ? "text-gold font-medium" : "text-stone/50"}`}>
            {service.current_price ?? service.price_credits}cr
          </span>

          {/* Surge badge */}
          {surge > 1.1 && (
            <motion.span
              className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded-full animate-pulse-copper flex-shrink-0"
              style={{
                backgroundColor: surge > 1.5 ? "#C47A7A30" : "#C5A86230",
                color: surge > 1.5 ? "#C47A7A" : "#C5A862",
              }}
              animate={{ scale: [1, 1.08, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              {surge.toFixed(1)}x
            </motion.span>
          )}
        </div>

        {/* Provider + latency */}
        <div className="flex items-center gap-2 mt-2 text-[10px] font-mono text-stone/40">
          <span>{service.provider ?? "mog"}</span>
          {stats?.avg_latency_ms != null && stats.avg_latency_ms > 0 && (
            <span>{stats.avg_latency_ms}ms</span>
          )}
        </div>

        {/* Value-add badges */}
        {service.value_adds && service.value_adds.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {service.value_adds.map((va) => {
              const cfg = VALUE_ADD_LABELS[va]
              if (!cfg) return null
              return (
                <span
                  key={va}
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded-full"
                  style={{ backgroundColor: `${cfg.color}15`, color: cfg.color }}
                >
                  {cfg.label}
                </span>
              )
            })}
          </div>
        )}

        {/* Ad-supported badge */}
        {service.ad_supported && (
          <div className="mt-2">
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-sage/10 text-sage">
              Ad-Supported Free
            </span>
          </div>
        )}
      </div>
    </motion.div>
  )
}
