'use client'

import { Settings, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'

export interface ProcessingConfig {
  minDuration: number    // seconds, range 20-180, default 30
  maxDuration: number    // seconds, range 30-300, default 60
  targetClips: number    // range 3-20, default 10
  format: 'vertical' | 'square'  // 9:16 or 1:1
  mode: 'auto' | 'manual'        // auto = top moments, manual = user reviews
  extractEnergy: boolean         // extract audio energy data (for fallback)
}

interface ConfigPanelProps {
  config: ProcessingConfig
  onConfigChange: (config: ProcessingConfig) => void
  disabled?: boolean
}

const DEFAULT_CONFIG: ProcessingConfig = {
  minDuration: 30,
  maxDuration: 60,
  targetClips: 10,
  format: 'vertical',
  mode: 'auto',
  extractEnergy: true,
}

export function ConfigPanel({ config, onConfigChange, disabled }: ConfigPanelProps) {
  // Enforce min < max constraint
  const effectiveMaxDuration = Math.max(config.maxDuration, config.minDuration + 1)

  const updateConfig = <K extends keyof ProcessingConfig>(
    key: K,
    value: ProcessingConfig[K]
  ) => {
    onConfigChange({ ...config, [key]: value })
  }

  return (
    <div className={cn('border rounded-lg p-6 space-y-6', disabled && 'opacity-50 pointer-events-none')}>
      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Configurações
        </h2>
      </div>

      {/* Min Duration */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-sm text-gray-400">Duração mínima (s)</label>
          <span className="text-lg font-bold">{config.minDuration}s</span>
        </div>
        <Slider
          value={[config.minDuration]}
          min={20}
          max={180}
          step={1}
          onValueChange={([value]) => updateConfig('minDuration', value)}
          disabled={disabled}
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>20s</span>
          <span>180s</span>
        </div>
      </div>

      {/* Max Duration */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-sm text-gray-400">Duração máxima (s)</label>
          <span className="text-lg font-bold">{config.maxDuration}s</span>
        </div>
        <Slider
          value={[config.maxDuration]}
          min={30}
          max={300}
          step={1}
          onValueChange={([value]) => updateConfig('maxDuration', value)}
          disabled={disabled}
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>30s</span>
          <span>300s</span>
        </div>
      </div>

      {/* Target Clips */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-sm text-gray-400">Número de clips</label>
          <span className="text-lg font-bold">{config.targetClips}</span>
        </div>
        <Slider
          value={[config.targetClips]}
          min={3}
          max={20}
          step={1}
          onValueChange={([value]) => updateConfig('targetClips', value)}
          disabled={disabled}
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>3</span>
          <span>20</span>
        </div>
      </div>

      {/* Format Toggle */}
      <div className="space-y-2">
        <label className="text-sm text-gray-400">Formato</label>
        <div className="flex gap-2">
          <Button
            variant={config.format === 'vertical' ? 'default' : 'outline'}
            onClick={() => updateConfig('format', 'vertical')}
            disabled={disabled}
            className="flex-1"
          >
            Vertical (9:16)
          </Button>
          <Button
            variant={config.format === 'square' ? 'default' : 'outline'}
            onClick={() => updateConfig('format', 'square')}
            disabled={disabled}
            className="flex-1"
          >
            Square (1:1)
          </Button>
        </div>
      </div>

      {/* Mode Toggle */}
      <div className="space-y-2">
        <label className="text-sm text-gray-400">Modo</label>
        <div className="flex gap-2">
          <Button
            variant={config.mode === 'auto' ? 'default' : 'outline'}
            onClick={() => updateConfig('mode', 'auto')}
            disabled={disabled}
            className="flex-1"
          >
            Auto
          </Button>
          <Button
            variant={config.mode === 'manual' ? 'default' : 'outline'}
            onClick={() => updateConfig('mode', 'manual')}
            disabled={disabled}
            className="flex-1"
          >
            Manual
          </Button>
        </div>
        <p className="text-xs text-gray-500">
          {config.mode === 'auto' ? 'Melhores momentos são selecionados automaticamente' : 'Você revisa cada clip antes de processar'}
        </p>
      </div>
    </div>
  )
}

export { DEFAULT_CONFIG }