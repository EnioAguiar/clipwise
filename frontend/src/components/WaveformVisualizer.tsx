'use client'

import { cn } from '@/lib/utils'

interface EnergyPoint {
  time: number
  score: number
  isPeak: boolean
}

interface WaveformVisualizerProps {
  energyData: EnergyPoint[]
  peakTimes: number[]
  duration: number
  onSeek: (time: number) => void
}

export function WaveformVisualizer({ energyData, peakTimes, duration, onSeek }: WaveformVisualizerProps) {
  if (!energyData || energyData.length === 0) {
    return (
      <div className="h-16 bg-gray-800 rounded flex items-center justify-center text-gray-500 text-sm">
        Waveform visualization unavailable
      </div>
    )
  }

  const maxScore = Math.max(...energyData.map(e => e.score))
  const barWidth = 100 / energyData.length

  return (
    <div className="relative h-16 bg-gray-800/50 rounded overflow-hidden">
      {/* Energy bars */}
      <div className="flex items-end h-full">
        {energyData.map((point, i) => {
          const heightPercent = (point.score / maxScore) * 100
          const isPeak = peakTimes.some(pt => Math.abs(pt - point.time) < 1)
          return (
            <div
              key={i}
              className={cn(
                'flex-1 transition-opacity cursor-pointer hover:opacity-100',
                isPeak ? 'bg-blue-500' : 'bg-blue-500/30'
              )}
              style={{
                height: `${heightPercent}%`,
                width: `${barWidth}%`
              }}
              onClick={() => onSeek(point.time)}
              title={`${point.time.toFixed(1)}s - Score: ${point.score.toFixed(1)}`}
            />
          )
        })}
      </div>

      {/* Peak markers */}
      {peakTimes.map((peakTime, i) => {
        const leftPercent = (peakTime / duration) * 100
        return (
          <div
            key={i}
            className="absolute top-0 bottom-0 w-0.5 bg-yellow-400"
            style={{ left: `${leftPercent}%` }}
          />
        )
      })}
    </div>
  )
}