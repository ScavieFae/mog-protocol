import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { type AgentWithHistory } from "@/hooks/useTrinity"

const ROLE_META: Record<string, { color: string }> = {
  "mog-scout": { color: "#6B8DAE" },
  "mog-worker": { color: "#87A878" },
  "mog-dashboard": { color: "#C5A862" },
}

interface ChatHistoryProps {
  data: AgentWithHistory
  onSendMessage: (message: string) => Promise<void>
}

export function ChatHistory({ data, onSendMessage }: ChatHistoryProps) {
  const { agent, history } = data
  const meta = ROLE_META[agent.name] ?? { color: "#B87333" }
  const [input, setInput] = useState("")
  const [sending, setSending] = useState(false)

  async function handleSend() {
    if (!input.trim() || sending) return
    setSending(true)
    try {
      await onSendMessage(input.trim())
      setInput("")
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-sage/20">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-full"
            style={{ backgroundColor: meta.color, opacity: 0.3 }}
          />
          <div>
            <h2 className="text-xl font-sans font-medium text-charcoal">
              {agent.name}
            </h2>
            <span className="text-sm font-mono text-stone/50">
              {agent.status} · {history.length} messages
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {history.length === 0 && (
          <div className="text-center text-stone/40 text-base italic py-12">
            No conversation yet. Send a message to wake this agent.
          </div>
        )}

        <AnimatePresence initial={false}>
          {history.map((msg, i) => (
            <motion.div
              key={`${msg.timestamp}-${i}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] rounded-lg px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-copper/10 border border-copper/20"
                    : "bg-white border border-sage/20"
                }`}
              >
                <div className="text-xs font-mono text-stone/40 mb-1">
                  {msg.role === "user" ? "you" : agent.name}
                  {" · "}
                  {new Date(msg.timestamp).toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: false,
                  })}
                </div>
                <div className="text-base font-sans text-charcoal whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Input */}
      <div className="border-t border-sage/20 p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={`Message ${agent.name}...`}
            disabled={sending}
            className="flex-1 px-4 py-3 rounded-lg border border-sage/30 bg-white text-base font-sans text-charcoal placeholder:text-stone/40 focus:outline-none focus:border-copper/50 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={sending || !input.trim()}
            className="px-6 py-3 rounded-lg bg-copper text-white font-sans font-medium text-base hover:bg-copper-light transition-colors disabled:opacity-40"
          >
            {sending ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  )
}
