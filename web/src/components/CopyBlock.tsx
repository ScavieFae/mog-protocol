import { useState } from "react"

interface CopyBlockProps {
  code: string
  language?: string
}

export function CopyBlock({ code }: CopyBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      <pre className="font-mono text-sm text-stone/80 bg-linen rounded-lg p-4 overflow-x-auto border border-sage/10">
        {code}
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1.5 rounded bg-white/60 hover:bg-white border border-sage/20 transition-colors"
        title="Copy to clipboard"
      >
        {copied ? (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#87A878" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3.5 8.5 6.5 11.5 12.5 4.5" />
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#87A878" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="5" y="5" width="8" height="8" rx="1" />
            <path d="M3 11V3a1 1 0 0 1 1-1h8" />
          </svg>
        )}
      </button>
    </div>
  )
}
