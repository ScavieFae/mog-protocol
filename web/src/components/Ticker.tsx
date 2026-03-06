import { type Service } from "@/hooks/useHealth"
import { motion } from "motion/react"

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
          return (
            <span key={`${s.service_id}-${i}`} className="inline-flex items-center gap-3 text-lg">
              <span className="font-sans text-stone">{s.name}</span>
              <span className="font-mono text-copper font-medium text-xl">
                {s.current_price != null
                  ? `${s.current_price}cr`
                  : s.surge_multiplier && s.surge_multiplier > 1
                  ? `${Math.round(s.price_credits * s.surge_multiplier)}cr`
                  : `${s.price_credits}cr`}
              </span>
              {s.surge_multiplier && s.surge_multiplier > 1 && (
                <span className="font-mono text-rose text-base">
                  {s.surge_multiplier.toFixed(1)}x
                </span>
              )}
              {trend === "rising" && (
                <span className="text-rose text-base leading-none" title="rising">↑</span>
              )}
              {trend === "falling" && (
                <span className="text-sage text-base leading-none" title="falling">↓</span>
              )}
              <span className="text-stone/30 text-xl">|</span>
            </span>
          )
        })}
      </motion.div>
    </div>
  )
}
