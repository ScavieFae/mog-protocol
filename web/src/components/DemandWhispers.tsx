import { motion, AnimatePresence } from "motion/react"
import { type DemandSignal } from "@/hooks/useHealth"

interface DemandWhispersProps {
  signals: DemandSignal[]
}

export function DemandWhispers({ signals }: DemandWhispersProps) {
  const recent = signals.slice(0, 15)

  return (
    <div className="w-80 border-l border-sage/20 p-6 overflow-y-auto">
      <h3 className="text-base font-sans text-stone uppercase tracking-widest mb-5">
        Demand Signals
      </h3>
      <div className="space-y-4">
        <AnimatePresence initial={false}>
          {recent.map((signal, i) => (
            <motion.div
              key={`${signal.timestamp}-${i}`}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 0.8 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
              className="text-lg font-sans text-purple/80 italic"
            >
              "{signal.query}"
              <div className="text-sm font-mono text-stone/40 mt-1">
                {new Date(signal.timestamp).toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                  hour12: false,
                })}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {recent.length === 0 && (
          <div className="text-lg text-stone/40 italic">
            Listening for unmet demand...
          </div>
        )}
      </div>
    </div>
  )
}
