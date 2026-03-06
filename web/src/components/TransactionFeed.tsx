import { motion, AnimatePresence } from "motion/react"
import { type Transaction } from "@/hooks/useHealth"

interface TransactionFeedProps {
  transactions: Transaction[]
}

export function TransactionFeed({ transactions }: TransactionFeedProps) {
  const recent = transactions.slice(0, 20)

  return (
    <div className="w-96 border-r border-sage/20 p-6 overflow-y-auto">
      <h3 className="text-base font-sans text-stone uppercase tracking-widest mb-5">
        Transactions
      </h3>
      <div className="space-y-4">
        <AnimatePresence initial={false}>
          {recent.map((tx, i) => {
            const isSuccess = tx.success
            const time = new Date(tx.timestamp).toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
              hour12: false,
            })

            return (
              <motion.div
                key={`${tx.timestamp}-${tx.service_id}-${i}`}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="flex items-center gap-3"
              >
                <div
                  className={`w-3 h-3 rounded-full flex-shrink-0 ${
                    isSuccess ? "bg-sage" : "bg-stone/40"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-base font-sans text-charcoal truncate">
                    {tx.service_id}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-mono text-copper">
                      {tx.credits_charged}cr
                    </span>
                    <span className="text-sm font-mono text-stone/50">
                      {tx.latency_ms}ms
                    </span>
                  </div>
                </div>
                <span className="text-sm font-mono text-stone/40">{time}</span>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}
