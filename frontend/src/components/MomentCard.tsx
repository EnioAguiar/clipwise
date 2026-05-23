'use client'

import { useState } from 'react'
import { Play, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MomentScores {
  hook: number
  standalone: number
  relevance: number
  quotability: number
}

export interface Moment {
  start: number
  end: number
  duration: number
  total_score: number
  scores: MomentScores
  transcript_snippet: string
  segments: { start: number; end: number }[]
  content_type: string
  selected?: boolean
}

interface MomentCardProps {
  moment: Moment
  rank: number
  isSelected: boolean
  onToggle: () => void
  onPlay: (start: number) => void
}

const CONTENT_TYPE_LABELS: Record<string, string> = {
  guest_story: 'Guest Story',
  technical_insight: 'Technical Insight',
  hot_take: 'Hot Take',
  market_landscape: 'Market Landscape',
  business_strategy: 'Business Strategy',
}

const formatTimestamp = (seconds: number): string => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const getScoreColor = (score: number): string => {
  if (score >= 70) return 'text-green-400 bg-green-400/20'
  if (score >= 40) return 'text-yellow-400 bg-yellow-400/20'
  return 'text-red-400 bg-red-400/20'
}

export function MomentCard({ moment, rank, isSelected, onToggle, onPlay }: MomentCardProps) {
  return (
    <div
      className={cn(
        'border rounded-lg p-4 transition-colors cursor-pointer',
        isSelected ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-500'
      )}
      onClick={onToggle}
    >
      <div className="flex items-start gap-3">
        {/* Rank number */}
        <div className="text-2xl font-bold text-gray-500 w-8 text-center">
          {rank}
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Top row: timestamps, duration, score badge */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-sm">
              {formatTimestamp(moment.start)} - {formatTimestamp(moment.end)}
            </span>
            <span className="text-sm text-gray-400">{moment.duration}s</span>
            <span className={cn('px-2 py-0.5 rounded text-sm font-medium', getScoreColor(moment.total_score))}>
              Score: {moment.total_score}
            </span>
            <span className="px-2 py-0.5 rounded text-sm bg-gray-700 text-gray-300">
              {CONTENT_TYPE_LABELS[moment.content_type] || moment.content_type}
            </span>
          </div>

          {/* Transcript snippet */}
          <p className="text-gray-300 mt-2 text-sm line-clamp-2">
            "{moment.transcript_snippet}"
          </p>

          {/* Action row */}
          <div className="flex items-center gap-2 mt-3">
            <button
              onClick={(e) => { e.stopPropagation(); onPlay(moment.start) }}
              className={cn(
                'flex items-center gap-1 px-3 py-1.5 rounded text-sm transition-colors',
                'bg-blue-600 hover:bg-blue-500 text-white'
              )}
            >
              <Play className="w-4 h-4" />
              Play
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                const text = `${formatTimestamp(moment.start)}-${formatTimestamp(moment.end)}`
                navigator.clipboard.writeText(text)
              }}
              className="flex items-center gap-1 px-3 py-1.5 rounded text-sm border border-gray-600 hover:border-gray-400 text-gray-300 transition-colors"
            >
              <Copy className="w-4 h-4" />
              Copy
            </button>
            <div className="flex items-center gap-2 ml-auto">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => { e.stopPropagation(); onToggle() }}
                className="w-4 h-4 accent-blue-500"
              />
              <span className="text-sm text-gray-400">Selecionar</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}