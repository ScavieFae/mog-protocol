import { useState, useEffect, useCallback, useRef } from "react"

const TRINITY_URL = "/trinity"

export interface TrinityAgent {
  name: string
  type: string
  status: string
  port: number
  created: string
  runtime: string
  container_id: string
  autonomy_enabled: boolean
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  timestamp: string
}

export interface AgentWithHistory {
  agent: TrinityAgent
  history: ChatMessage[]
}

async function getToken(): Promise<string> {
  const res = await fetch(`${TRINITY_URL}/api/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: "username=admin&password=mogprotocol2026",
  })
  if (!res.ok) throw new Error(`Auth: HTTP ${res.status}`)
  const data = await res.json()
  return data.access_token
}

export function useTrinity(intervalMs = 8000) {
  const [agents, setAgents] = useState<AgentWithHistory[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const tokenRef = useRef<string | null>(null)

  const authHeaders = useCallback(async (): Promise<Record<string, string>> => {
    if (!tokenRef.current) {
      tokenRef.current = await getToken()
    }
    return {
      Authorization: `Bearer ${tokenRef.current}`,
      "Content-Type": "application/json",
    }
  }, [])

  const fetchAll = useCallback(async () => {
    try {
      const hdrs = await authHeaders()
      const agentRes = await fetch(`${TRINITY_URL}/api/agents`, { headers: hdrs })

      if (agentRes.status === 401) {
        tokenRef.current = null
        const retryHdrs = await authHeaders()
        const retry = await fetch(`${TRINITY_URL}/api/agents`, { headers: retryHdrs })
        if (!retry.ok) throw new Error(`Agents: HTTP ${retry.status}`)
        const agentList: TrinityAgent[] = await retry.json()
        return agentList
      }

      if (!agentRes.ok) throw new Error(`Agents: HTTP ${agentRes.status}`)
      const agentList: TrinityAgent[] = await agentRes.json()

      const mogAgents = agentList.filter((a) => a.name.startsWith("mog-"))

      const withHistory = await Promise.all(
        mogAgents.map(async (agent) => {
          try {
            const histRes = await fetch(
              `${TRINITY_URL}/api/agents/${agent.name}/chat/history`,
              { headers: hdrs }
            )
            const history: ChatMessage[] = histRes.ok ? await histRes.json() : []
            return { agent, history }
          } catch {
            return { agent, history: [] }
          }
        })
      )

      setAgents(withHistory)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [authHeaders])

  const sendMessage = useCallback(async (agentName: string, message: string) => {
    const hdrs = await authHeaders()
    const res = await fetch(`${TRINITY_URL}/api/agents/${agentName}/chat`, {
      method: "POST",
      headers: hdrs,
      body: JSON.stringify({ message }),
    })
    if (!res.ok) throw new Error(`Chat: HTTP ${res.status}`)
    const data = await res.json()
    fetchAll()
    return data
  }, [authHeaders, fetchAll])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, intervalMs)
    return () => clearInterval(id)
  }, [fetchAll, intervalMs])

  return { agents, error, loading, sendMessage, refresh: fetchAll }
}
