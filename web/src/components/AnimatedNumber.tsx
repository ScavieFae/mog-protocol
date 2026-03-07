import { useEffect, useRef, useState } from "react"

interface AnimatedNumberProps {
  value: number
  duration?: number
  className?: string
  suffix?: string
  prefix?: string
  decimals?: number
}

export function AnimatedNumber({
  value,
  duration = 800,
  className = "",
  suffix = "",
  prefix = "",
  decimals = 0,
}: AnimatedNumberProps) {
  const [display, setDisplay] = useState(value)
  const prevRef = useRef(value)
  const frameRef = useRef<number>(0)

  useEffect(() => {
    const from = prevRef.current
    const to = value
    if (from === to) return

    const start = performance.now()
    const diff = to - from

    function tick(now: number) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(from + diff * eased)

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick)
      } else {
        prevRef.current = to
      }
    }

    frameRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frameRef.current)
  }, [value, duration])

  const formatted = decimals > 0 ? display.toFixed(decimals) : Math.round(display).toString()

  // Determine flash direction
  const direction = value > prevRef.current ? "up" : value < prevRef.current ? "down" : null

  return (
    <span
      className={`${className} transition-colors duration-500 ${
        direction === "up" ? "text-sage" : direction === "down" ? "text-rose" : ""
      }`}
    >
      {prefix}{formatted}{suffix}
    </span>
  )
}
