import { type Service } from "@/hooks/useHealth"
import { motion } from "motion/react"
import { getServiceIcon } from "@/components/HivePanel"

interface TickerProps {
  services: Service[]
}

export function Ticker({ services }: TickerProps) {
  const items = [...services, ...services]

  return (
    <div className="border-b border-sage/30 bg-linen/80 backdrop-blur-sm overflow-hidden h-16 flex items-center px-4">
      <motion.div
        className="flex gap-12 whitespace-nowrap"
        animate={{ x: ["0%", "-50%"] }}
        transition={{
          x: {
            repeat: Infinity,
            repeatType: "loop",
            duration: services.length * 3,
            ease: "linear",
          },
        }}
      >
        {items.map((s, i) => {
          const trend = s.surge_signals?.trend
          const surging = s.surge_multiplier && s.surge_multiplier > 1
          const hotSurge = s.surge_multiplier && s.surge_multiplier > 1.5
          return (
            <span
              key={`${s.service_id}-${i}`}
              className={`inline-flex items-center gap-3 text-lg ${surging ? "px-3 py-1 rounded-lg" : ""}`}
              style={surging ? {
                backgroundColor: hotSurge ? "#C47A7A12" : "#C5A86210",
              } : undefined}
            >
              {(() => {
                const icon = getServiceIcon(s.service_id)
                return icon ? <img src={icon} alt="" className="w-4 h-4 rounded-sm" loading="lazy" /> : null
              })()}
              <span className={`font-sans ${surging ? "text-charcoal font-medium" : "text-stone"}`}>{s.name}</span>
              <span className={`font-mono font-medium text-xl ${hotSurge ? "text-rose" : surging ? "text-gold" : "text-copper"}`}>
                {s.current_price != null
                  ? `${s.current_price}cr`
                  : surging
                  ? `${Math.round(s.price_credits * s.surge_multiplier!)}cr`
                  : `${s.price_credits}cr`}
              </span>
              {surging && (
                <span className={`font-mono font-bold text-base animate-pulse-copper ${hotSurge ? "text-rose" : "text-gold"}`}>
                  {s.surge_multiplier!.toFixed(1)}x
                </span>
              )}
              {trend === "rising" && (
                <span className="text-rose text-lg font-bold leading-none" title="rising">↑</span>
              )}
              {trend === "falling" && (
                <span className="text-sage text-lg leading-none" title="falling">↓</span>
              )}
              <span className="text-stone/30 text-xl">|</span>
            </span>
          )
        })}
      </motion.div>
    </div>
  )
}
