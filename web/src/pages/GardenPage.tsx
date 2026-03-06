import { Link } from "react-router-dom"
import { useHealth } from "@/hooks/useHealth"
import { Ticker } from "@/components/Ticker"
import { Garden } from "@/components/Garden"
import { TransactionFeed } from "@/components/TransactionFeed"
import { DemandWhispers } from "@/components/DemandWhispers"

export function GardenPage() {
  const { data, error, loading } = useHealth(5000)

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <div className="text-center">
          <svg viewBox="0 0 60 60" className="w-20 h-20 mx-auto mb-4">
            <circle cx="30" cy="30" r="4" fill="none" stroke="#87A878" strokeWidth="1" />
            {[0, 1, 2, 3, 4, 5].map((i) => {
              const a = (i / 6) * Math.PI * 2
              return (
                <ellipse
                  key={i}
                  cx={30 + Math.cos(a) * 14}
                  cy={30 + Math.sin(a) * 14}
                  rx={6}
                  ry={2.5}
                  transform={`rotate(${(a * 180) / Math.PI}, ${30 + Math.cos(a) * 14}, ${30 + Math.sin(a) * 14})`}
                  fill="none"
                  stroke="#87A878"
                  strokeWidth="0.75"
                  opacity={0.4}
                />
              )
            })}
          </svg>
          <p className="text-lg font-sans text-stone">seeding garden...</p>
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-sans text-rose">{error}</p>
          <p className="text-base font-sans text-stone mt-2">gateway unreachable</p>
        </div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen bg-linen flex flex-col">
      {/* Top Ticker */}
      <Ticker services={data.services} />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Transaction Feed */}
        <TransactionFeed transactions={data.recent_transactions} />

        {/* Center: Garden */}
        <Garden services={data.services} />

        {/* Right: Demand Whispers */}
        <DemandWhispers signals={data.demand_signals} />
      </div>

      {/* Bottom Status Bar with Colony link */}
      <div className="border-t border-sage/20 bg-linen/80 backdrop-blur-sm px-6 py-3 flex items-center gap-8 text-base">
        <span className="font-sans text-stone">
          <span className="inline-block w-3 h-3 rounded-full bg-sage mr-2.5 align-middle" />
          {data.status}
        </span>
        <span className="font-mono text-copper">
          {data.services_count} services
        </span>
        <span className="font-mono text-stone">
          {data.recent_transactions.length} txns
        </span>
        {data.total_revenue_credits !== undefined && (
          <span className="font-mono text-gold">
            {data.total_revenue_credits} credits earned
          </span>
        )}
        <span className="font-mono text-stone/50 ml-auto">
          mog protocol
        </span>
        <Link
          to="/connect"
          className="font-mono text-sage/60 hover:text-sage transition-colors"
        >
          connect &rarr;
        </Link>
        <Link
          to="/colony"
          className="font-mono text-copper/60 hover:text-copper transition-colors"
        >
          colony &rarr;
        </Link>
      </div>
    </div>
  )
}
