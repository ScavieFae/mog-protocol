import { type HealthData } from "@/hooks/useHealth"

interface StatusBarProps {
  data: HealthData
}

export function StatusBar({ data }: StatusBarProps) {
  const uptime = data.uptime_seconds
    ? `${Math.floor(data.uptime_seconds / 3600)}h ${Math.floor((data.uptime_seconds % 3600) / 60)}m`
    : "---"

  return (
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
        uptime {uptime}
      </span>
      <span className="font-mono text-stone/50">
        mog protocol
      </span>
    </div>
  )
}
