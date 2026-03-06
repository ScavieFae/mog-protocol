import { useState, useEffect, useCallback } from "react"

const GATEWAY_URL = "/gateway"

export interface SurgeSignals {
  volume_15m: number
  velocity: number
  demand_pressure: number
  trend: "rising" | "falling" | "stable"
}

export interface Service {
  service_id: string
  name: string
  price_credits: number
  description?: string
  provider?: string
  call_count?: number
  revenue_credits?: number
  surge_multiplier?: number
  current_price?: number
  surge_signals?: SurgeSignals
}

export interface Transaction {
  type: string
  service_id: string
  credits_charged: number
  success: boolean
  latency_ms: number
  timestamp: string
}

export interface DemandSignal {
  query: string
  timestamp: string
}

export interface HealthData {
  status: string
  services_count: number
  services: Service[]
  recent_transactions: Transaction[]
  demand_signals: DemandSignal[]
  uptime_seconds?: number
  total_revenue_credits?: number
}

export function useHealth(intervalMs = 5000) {
  const [data, setData] = useState<HealthData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch(`${GATEWAY_URL}/health`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    const id = setInterval(fetchHealth, intervalMs)
    return () => clearInterval(id)
  }, [fetchHealth, intervalMs])

  return { data, error, loading }
}
