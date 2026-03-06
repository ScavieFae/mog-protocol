import { useRef, useMemo } from "react"
import { useNavigate } from "react-router-dom"
import { type Service } from "@/hooks/useHealth"
import { FlowerNode } from "./FlowerNode"

interface GardenProps {
  services: Service[]
}

function layoutFlowers(services: Service[], width: number, height: number) {
  const cx = width / 2
  const cy = height / 2
  const count = services.length

  if (count === 0) return []

  const positions: { service: Service; x: number; y: number }[] = []

  if (count === 1) {
    positions.push({ service: services[0], x: cx, y: cy })
    return positions
  }

  // Center the highest-revenue service
  const sorted = [...services].sort(
    (a, b) => (b.revenue_credits ?? 0) - (a.revenue_credits ?? 0)
  )

  positions.push({ service: sorted[0], x: cx, y: cy })

  const remaining = sorted.slice(1)
  const ringCapacities = [6, 12, 18]
  let ringIdx = 0
  let placed = 0

  while (placed < remaining.length && ringIdx < ringCapacities.length) {
    const ringSize = Math.min(ringCapacities[ringIdx], remaining.length - placed)
    const radius = 220 + ringIdx * 200
    for (let i = 0; i < ringSize; i++) {
      const angle = (i / ringSize) * Math.PI * 2 - Math.PI / 2
      positions.push({
        service: remaining[placed + i],
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
      })
    }
    placed += ringSize
    ringIdx++
  }

  return positions
}

export function Garden({ services }: GardenProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const width = 1400
  const height = 1000

  const flowers = useMemo(() => layoutFlowers(services, width, height), [services])

  const cx = width / 2
  const cy = height / 2

  return (
    <div ref={containerRef} className="flex-1 flex items-center justify-center p-4">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
        {/* Stems */}
        {flowers.slice(1).map(({ service, x, y }, i) => {
          const seed = (i * 137.508) % 1
          const midX = (cx + x) / 2 + (seed - 0.5) * 60
          const midY = (cy + y) / 2 + ((seed * 2.3) % 1 - 0.5) * 60
          return (
            <path
              key={`stem-${service.service_id}`}
              d={`M ${cx} ${cy} Q ${midX} ${midY} ${x} ${y}`}
              fill="none"
              stroke="#87A878"
              strokeWidth={1}
              strokeOpacity={0.3}
            />
          )
        })}

        {/* Flowers */}
        {flowers.map(({ service, x, y }) => (
          <g
            key={service.service_id}
            style={{ cursor: "pointer" }}
            onClick={() => navigate(`/service/${service.service_id}`)}
          >
            <FlowerNode service={service} x={x} y={y} />
          </g>
        ))}
      </svg>
    </div>
  )
}
