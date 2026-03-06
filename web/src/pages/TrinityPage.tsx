import { useState, useCallback } from "react"
import { Link } from "react-router-dom"
import { useTrinity } from "@/hooks/useTrinity"
import { AgentCard } from "@/components/trinity/AgentCard"
import { ChatHistory } from "@/components/trinity/ChatHistory"
import { AgentNetwork } from "@/components/trinity/AgentNetwork"

export function TrinityPage() {
  const { agents, error, loading, sendMessage } = useTrinity(8000)
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)

  const selected = agents.find((a) => a.agent.name === selectedAgent) ?? null

  const handleSend = useCallback(
    async (message: string) => {
      if (!selectedAgent) return
      await sendMessage(selectedAgent, message)
    },
    [selectedAgent, sendMessage]
  )

  if (loading && agents.length === 0) {
    return (
      <div className="min-h-screen bg-linen flex items-center justify-center">
        <p className="text-lg font-sans text-stone">connecting to colony...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-linen flex flex-col">
      {/* Header */}
      <div className="border-b border-sage/20 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="text-sm font-mono text-stone/50 hover:text-copper transition-colors"
          >
            &larr; garden
          </Link>
          <h1 className="text-2xl font-sans font-medium text-charcoal">
            Colony
          </h1>
          <span className="text-sm font-mono text-stone/50">
            {agents.length} agents
          </span>
        </div>

        {error && (
          <span className="text-sm font-mono text-rose">{error}</span>
        )}
      </div>

      {/* Network visualization */}
      <div className="border-b border-sage/10 py-6 flex justify-center bg-white/30">
        <AgentNetwork agents={agents} />
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Agent list */}
        <div className="w-[420px] border-r border-sage/20 p-5 space-y-3 overflow-y-auto">
          {agents.map((a) => (
            <AgentCard
              key={a.agent.name}
              data={a}
              selected={selectedAgent === a.agent.name}
              onSelect={() => setSelectedAgent(a.agent.name)}
            />
          ))}
        </div>

        {/* Chat panel */}
        <div className="flex-1">
          {selected ? (
            <ChatHistory data={selected} onSendMessage={handleSend} />
          ) : (
            <div className="h-full flex items-center justify-center">
              <p className="text-lg font-sans text-stone/40 italic">
                Select an agent to view its activity
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
