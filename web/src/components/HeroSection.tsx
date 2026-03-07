import { motion } from "motion/react"
import { AnimatedNumber } from "@/components/AnimatedNumber"
import type { HealthData } from "@/hooks/useHealth"

interface HeroProps {
  data: HealthData
}

const LOOP_STEPS = [
  { label: "Scout", desc: "discover APIs", color: "#6B8DAE" },
  { label: "Evaluate", desc: "score ROI", color: "#9B8EC2" },
  { label: "Wrap", desc: "create handler", color: "#B87333" },
  { label: "Price", desc: "dynamic surge", color: "#C5A862" },
  { label: "Sell", desc: "serve buyers", color: "#87A878" },
]

export function HeroSection({ data }: HeroProps) {
  // Offset: 19 calls happened before current gateway restart (leaderboard counts all on-chain txns)
  const totalCalls = 19 + data.services.reduce((sum, s) => sum + (s.stats?.total_calls ?? 0), 0)
  const totalRevenue = data.portfolio?.total_earned ?? 0
  const agentBuilt = data.services.filter(s => s.provider === "mog-agent").length

  return (
    <div className="px-8 pt-8 pb-6">
      {/* Tagline */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className="font-sans text-3xl font-semibold text-charcoal tracking-tight">
          Autonomous API Proving Ground
        </h1>
        <p className="font-sans text-base text-stone/70 mt-1.5 max-w-xl">
          Agents discover APIs, evaluate ROI, wrap them as paid services, price dynamically, and sell to other agents — no humans in the loop.
        </p>
      </motion.div>

      {/* Stats row */}
      <motion.div
        className="flex items-end gap-10 mt-6"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15 }}
      >
        <StatBlock
          value={data.services_count}
          label="services live"
          color="#B87333"
        />
        <StatBlock
          value={totalCalls}
          label="total calls"
          color="#87A878"
        />
        <StatBlock
          value={totalRevenue}
          label="credits earned"
          suffix="cr"
          color="#C5A862"
        />
        {agentBuilt > 0 && (
          <StatBlock
            value={agentBuilt}
            label="agent-built"
            color="#9B8EC2"
          />
        )}
        <StatBlock
          value={data.portfolio?.balance ?? 0}
          label="balance"
          suffix="cr"
          color="#78716C"
        />

        {/* How it works — the loop */}
        <div className="ml-auto flex items-center gap-1">
          {LOOP_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center">
              <motion.div
                className="flex flex-col items-center"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + i * 0.08 }}
              >
                <span
                  className="font-mono text-[11px] font-semibold px-2 py-1 rounded-md"
                  style={{ backgroundColor: `${step.color}15`, color: step.color }}
                >
                  {step.label}
                </span>
                <span className="font-sans text-[9px] text-stone/40 mt-0.5">{step.desc}</span>
              </motion.div>
              {i < LOOP_STEPS.length - 1 && (
                <span className="text-stone/20 mx-0.5 text-xs">→</span>
              )}
            </div>
          ))}
          <span className="text-stone/20 mx-0.5 text-xs">↺</span>
        </div>
      </motion.div>
    </div>
  )
}

function StatBlock({
  value,
  label,
  color,
  suffix = "",
}: {
  value: number
  label: string
  color: string
  suffix?: string
}) {
  return (
    <div className="flex flex-col">
      <AnimatedNumber
        value={value}
        suffix={suffix}
        className="font-mono text-2xl font-semibold tabular-nums"
        duration={1000}
      />
      <span className="font-sans text-[11px] mt-0.5" style={{ color }}>
        {label}
      </span>
    </div>
  )
}
