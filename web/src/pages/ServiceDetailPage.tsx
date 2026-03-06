import { useParams, Link } from "react-router-dom"
import { useHealth, type Service } from "@/hooks/useHealth"
import { FlowerNode } from "@/components/FlowerNode"

function formatUptime(firstSeen?: string): string {
  if (!firstSeen) return "--"
  const ms = Date.now() - new Date(firstSeen).getTime()
  const hours = Math.floor(ms / 3600000)
  const mins = Math.floor((ms % 3600000) / 60000)
  if (hours >= 24) {
    const days = Math.floor(hours / 24)
    return `${days}d ${hours % 24}h`
  }
  return `${hours}h ${mins}m`
}

function StatCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-white/50 rounded-lg p-4 border border-sage/10">
      <div className="text-sm font-sans text-stone/70 mb-1">{label}</div>
      <div className={`text-xl font-mono ${color ?? "text-copper"}`}>{value}</div>
    </div>
  )
}

function rateColor(rate: number): string {
  if (rate >= 0.95) return "text-sage"
  if (rate >= 0.8) return "text-gold"
  return "text-rose"
}

export function ServiceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, loading } = useHealth(5000)

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <p className="text-lg font-sans text-stone">loading...</p>
      </div>
    )
  }

  const service: Service | undefined = data?.services.find((s) => s.service_id === id)

  if (!service) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-sans text-stone">service not found: {id}</p>
          <Link to="/" className="font-mono text-copper hover:text-copper/80 mt-4 inline-block">
            &larr; back to garden
          </Link>
        </div>
      </div>
    )
  }

  const stats = service.stats
  const surge = service.surge_multiplier ?? 1
  const currentPrice = service.current_price ?? service.price_credits

  return (
    <div className="min-h-screen bg-linen">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Back link */}
        <Link to="/" className="font-mono text-sm text-copper/60 hover:text-copper transition-colors">
          &larr; back to garden
        </Link>

        {/* Header */}
        <div className="flex items-center justify-between mt-6 mb-8">
          <h1 className="text-2xl font-sans text-charcoal">{service.name}</h1>
          <span className="font-mono text-sm text-stone/60">{service.provider ?? "mog-protocol"}</span>
        </div>

        {/* Flower hero */}
        <div className="flex justify-center mb-8">
          <svg viewBox="0 0 300 260" className="w-64 h-56">
            <FlowerNode service={service} x={150} y={110} />
          </svg>
        </div>

        {/* Description */}
        <div className="bg-white/50 rounded-lg p-5 border border-sage/10 mb-6">
          <p className="font-sans text-stone leading-relaxed">{service.description ?? "No description available."}</p>
          {service.example_params && Object.keys(service.example_params).length > 0 && (
            <pre className="mt-4 font-mono text-sm text-stone/80 bg-linen rounded p-3 overflow-x-auto">
              {JSON.stringify(service.example_params, null, 2)}
            </pre>
          )}
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <StatCard
            label="Uptime"
            value={formatUptime(stats?.first_seen)}
          />
          <StatCard
            label="Total Calls"
            value={stats ? `${stats.total_calls}` : "0"}
          />
          <StatCard
            label="Success Rate"
            value={stats ? `${(stats.success_rate * 100).toFixed(1)}%` : "--"}
            color={stats ? rateColor(stats.success_rate) : undefined}
          />
          <StatCard
            label="Revenue"
            value={stats ? `${stats.revenue_credits}cr` : "0cr"}
            color="text-gold"
          />
          <StatCard
            label="Avg Latency"
            value={stats ? `${stats.avg_latency_ms}ms` : "--"}
          />
          <StatCard
            label="Current Price"
            value={`${currentPrice}cr${surge > 1 ? ` (${surge.toFixed(1)}x)` : ""}`}
            color={surge > 1.2 ? "text-rose" : undefined}
          />
        </div>

        {/* Pricing */}
        <div className="bg-white/50 rounded-lg p-5 border border-sage/10 mb-6">
          <h2 className="font-sans text-sm text-stone/70 mb-2">Pricing</h2>
          <p className="font-mono text-stone">
            Base price: {service.price_credits}cr
          </p>
          {surge > 1 ? (
            <p className="font-mono text-rose mt-1">
              Surge: {surge.toFixed(2)}x
              {service.surge_signals?.demand_pressure && service.surge_signals.demand_pressure > 1
                ? ` (demand pressure: ${service.surge_signals.demand_pressure.toFixed(1)})`
                : ""}
            </p>
          ) : (
            <p className="font-mono text-sage mt-1">No surge — stable pricing</p>
          )}
        </div>

        {/* How to buy */}
        <div className="bg-white/50 rounded-lg p-5 border border-sage/10">
          <h2 className="font-sans text-sm text-stone/70 mb-2">How to buy</h2>
          <pre className="font-mono text-sm text-stone/80 bg-linen rounded p-3 overflow-x-auto">
{JSON.stringify({
  method: "tools/call",
  params: {
    name: "buy_and_call",
    arguments: {
      service_id: service.service_id,
      params: service.example_params ?? {},
    },
  },
}, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}
