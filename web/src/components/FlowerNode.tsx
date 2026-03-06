import { motion } from "motion/react"
import { type Service } from "@/hooks/useHealth"

const CATEGORY_COLORS: Record<string, string> = {
  search: "#6B8DAE",
  creative: "#9B8EC2",
  finance: "#C5A862",
  weather: "#7BA787",
  knowledge: "#87A878",
  default: "#B87333",
}

function getCategory(serviceId: string): string {
  if (serviceId.includes("exa") || serviceId.includes("search")) return "search"
  if (serviceId.includes("claude") || serviceId.includes("nano") || serviceId.includes("gemini")) return "creative"
  if (serviceId.includes("frank") || serviceId.includes("fx")) return "finance"
  if (serviceId.includes("meteo") || serviceId.includes("weather") || serviceId.includes("geo")) return "weather"
  if (serviceId.includes("hackathon")) return "knowledge"
  return "default"
}

function getColor(serviceId: string): string {
  return CATEGORY_COLORS[getCategory(serviceId)] ?? CATEGORY_COLORS.default
}

interface FlowerNodeProps {
  service: Service
  x: number
  y: number
}

export function FlowerNode({ service, x, y }: FlowerNodeProps) {
  const color = getColor(service.service_id)
  const surge = service.surge_multiplier ?? 1
  const calls = service.call_count ?? 0
  const demandPressure = service.surge_signals?.demand_pressure ?? 1.0
  const highDemand = demandPressure > 1.5
  const petalCount = 6
  const baseRadius = 50
  const petalLength = baseRadius + Math.min(calls * 4, 40)
  const openness = 0.3 + Math.min(surge - 1, 1) * 0.7

  // Surge shifts color warmer
  const surgeColor = surge > 1.5 ? "#C47A7A" : surge > 1.2 ? "#C5A862" : color

  return (
    <motion.g
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
    >
      {/* Petals */}
      {Array.from({ length: petalCount }).map((_, i) => {
        const angle = (i / petalCount) * Math.PI * 2
        const px = x + Math.cos(angle) * petalLength * openness
        const py = y + Math.sin(angle) * petalLength * openness
        return (
          <motion.ellipse
            key={i}
            cx={px}
            cy={py}
            rx={petalLength * 0.4}
            ry={petalLength * 0.15}
            transform={`rotate(${(angle * 180) / Math.PI}, ${px}, ${py})`}
            fill={surgeColor}
            fillOpacity={0.15}
            stroke={surgeColor}
            strokeWidth={1}
            strokeOpacity={0.6}
            animate={{
              rx: petalLength * 0.4 * (0.95 + Math.sin(Date.now() / 1000 + i) * 0.05),
            }}
            transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
          />
        )
      })}

      {/* Center */}
      <motion.circle
        cx={x}
        cy={y}
        r={12}
        fill={surgeColor}
        fillOpacity={0.3}
        stroke={surgeColor}
        strokeWidth={1.5}
      />

      {/* Surge pulse */}
      {surge > 1.2 && (
        <motion.circle
          cx={x}
          cy={y}
          r={petalLength}
          fill="none"
          stroke={surgeColor}
          strokeWidth={1}
          initial={{ opacity: 0.4, scale: 0.8 }}
          animate={{ opacity: 0, scale: 1.3 }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeOut" }}
        />
      )}

      {/* Demand pressure ring — searches but no buys: people are looking */}
      {highDemand && (
        <circle
          cx={x}
          cy={y}
          r={petalLength + 10}
          fill="none"
          stroke={color}
          strokeWidth={1.5}
          strokeOpacity={0.5}
          strokeDasharray="4 6"
        />
      )}

      {/* Label */}
      <text
        x={x}
        y={y + petalLength + 24}
        textAnchor="middle"
        className="fill-stone font-sans"
        fontSize={18}
      >
        {service.name}
      </text>
      <text
        x={x}
        y={y + petalLength + 44}
        textAnchor="middle"
        className="fill-copper font-mono"
        fontSize={16}
      >
        {service.price_credits}cr
      </text>
    </motion.g>
  )
}
