'use client'

import { useState, useCallback, useRef } from 'react'
import { Upload, Settings, Play, Download, X, AlertCircle, CheckCircle2, Copy } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ConfigPanel, DEFAULT_CONFIG, type ProcessingConfig } from '@/components/ConfigPanel'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { MomentCard } from '@/components/MomentCard'
import { WaveformVisualizer } from '@/components/WaveformVisualizer'

interface EnergyPoint {
  time: number
  score: number
  isPeak: boolean
}

interface Moment {
  start: number
  end: number
  duration: number
  total_score: number
  scores: { hook: number; standalone: number; relevance: number; quotability: number }
  transcript_snippet: string
  segments: { start: number; end: number }[]
  content_type: string
  selected?: boolean
}

type ProcessingState = 'idle' | 'uploading' | 'downloading' | 'transcribing' | 'analyzing' | 'complete' | 'error'

interface LogEntry {
  timestamp: string
  message: string
  type: 'info' | 'success' | 'error'
}

const STEPS = [
  { key: 'downloading', label: 'Baixando YouTube...' },
  { key: 'transcribing', label: 'Transcrevendo...' },
  { key: 'analyzing', label: 'Extraindo energia...' },
] as const

const API_BASE = 'http://localhost:8000'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'arquivo' | 'youtube'>('arquivo')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [processingState, setProcessingState] = useState<ProcessingState>('idle')
  const [currentStep, setCurrentStep] = useState<string>('')
  const [progress, setProgress] = useState(0)
  const [config, setConfig] = useState<ProcessingConfig>(DEFAULT_CONFIG)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [error, setError] = useState<string | null>(null)
  const [moments, setMoments] = useState<Moment[]>([])
  const [videoId, setVideoId] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [selectedMoments, setSelectedMoments] = useState<Set<number>>(new Set())
  const [topN, setTopN] = useState(10)
  const [videoSrc, setVideoSrc] = useState<string | null>(null)
  const [energyData, setEnergyData] = useState<EnergyPoint[]>([])
  const [videoDuration, setVideoDuration] = useState<number>(0)
  const [extractionComplete, setExtractionComplete] = useState(false)
  const [opusStatus, setOpusStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle')
  const [opusJobId, setOpusJobId] = useState<string | null>(null)

  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    const timestamp = new Date().toLocaleTimeString('pt-BR')
    setLogs(prev => [...prev, { timestamp, message, type }])
  }, [])

  const handleConfigChange = (newConfig: ProcessingConfig) => {
    setConfig(newConfig)
    localStorage.setItem('clipwise-config', JSON.stringify(newConfig))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const formatTimestamp = (start: number, end: number) => {
    const fmt = (s: number) => {
      const h = Math.floor(s / 3600)
      const m = Math.floor((s % 3600) / 60)
      const sec = Math.floor(s % 60)
      return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
    }
    return `${fmt(start)}-${fmt(end)}`
  }

  const copyTimestamps = async () => {
    const selected = moments.filter(m => m.selected)
    if (selected.length === 0) {
      setError('Selecione pelo menos um momento')
      return
    }
    const text = selected.map(m => formatTimestamp(m.start, m.end)).join('\n')
    await navigator.clipboard.writeText(text)
    addLog(`${selected.length} timestamps copiados!`, 'success')
  }

  const exportJSON = () => {
    const selected = moments.filter(m => m.selected)
    const blob = new Blob([JSON.stringify({ moments: selected }, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'moments.json'
    a.click()
    URL.revokeObjectURL(url)
    addLog('JSON exportado!', 'success')
  }

  const sendToOpus = async () => {
    if (selectedMoments.size === 0) {
      setError('Selecione pelo menos um momento')
      return
    }

    setOpusStatus('sending')
    setError(null)
    addLog('Enviando para o Opus Clip...')

    try {
      const momentsToSend = moments
        .filter((_, i) => selectedMoments.has(i))
        .map(m => ({ start: m.start, end: m.end }))

      const API_BASE = 'http://localhost:8000'

        const res = await fetch(`${API_BASE}/opus/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: videoId,
          moments: momentsToSend
        })
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Opus API error')
      }

      const data = await res.json()
      setOpusJobId(data.job_id)
      setOpusStatus('success')
      addLog(`Enviado! Job ID: ${data.job_id}`, 'success')
      addLog(`${data.moments_count} momentos enviados para processamento.`, 'info')

    } catch (err) {
      setOpusStatus('error')
      const msg = err instanceof Error ? err.message : 'Erro desconhecido'
      setError(msg)
      addLog(`Erro ao enviar para Opus: ${msg}`, 'error')
    }
  }

  const jumpToTimestamp = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time
      videoRef.current.play()
    }
  }

  const toggleMoment = (index: number) => {
    setSelectedMoments(prev => {
      const newSet = new Set(prev)
      if (newSet.has(index)) {
        newSet.delete(index)
      } else {
        newSet.add(index)
      }
      return newSet
    })
  }

  const processVideo = async () => {
    setError(null)
    setLogs([])
    setProcessingState('idle')
    setProgress(0)
    setMoments([])
    setOpusStatus('idle')
    setOpusJobId(null)
    setSelectedMoments(new Set())

    const inputSource = activeTab === 'youtube' ? youtubeUrl : file?.name || 'arquivo'

    try {
      let videoId: string

      // Step 1: Upload or YouTube download
      if (activeTab === 'youtube') {
        setProcessingState('downloading')
        setCurrentStep('Baixando YouTube...')
        addLog(`Iniciando processamento: ${inputSource}`)
        setProgress(5)

        const ytRes = await fetch(`${API_BASE}/youtube`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: youtubeUrl })
        })
        if (!ytRes.ok) throw new Error('YouTube download failed')
        const ytData = await ytRes.json()
        videoId = ytData.file_id
        addLog('YouTube baixado com sucesso', 'success')
        setProgress(20)
      } else {
        setProcessingState('uploading')
        setCurrentStep('Enviando arquivo...')
        addLog(`Iniciando processamento: ${inputSource}`)
        setProgress(5)

        const formData = new FormData()
        if (file) formData.append('file', file)
        const uploadRes = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData })
        console.log('[DEBUG] uploadRes status:', uploadRes.status)
        const uploadData = await uploadRes.json()
        console.log('[DEBUG] uploadData:', uploadData)
        if (!uploadRes.ok) throw new Error('Upload failed')
        if (!uploadData.file_id) throw new Error('Upload returned no video_id')
        videoId = uploadData.file_id
        addLog('Arquivo enviado com sucesso', 'success')
        setProgress(20)
      }
      setVideoId(videoId)

      // Step 2: Extract (transcribe + energy)
      setProcessingState('transcribing')
      setCurrentStep('Transcrevendo...')
      setProgress(30)
      addLog('Iniciando transcrição...')

      const extractRes = await fetch(`${API_BASE}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: activeTab === 'youtube' ? 'youtube' : 'upload',
          file_id: videoId,
          youtube_url: activeTab === 'youtube' ? youtubeUrl : '',
        })
      })

      // Update UI to show energy extraction phase (backend is doing this now)
      setCurrentStep('Extraindo energia...')
      setProgress(40)
      addLog('Extraindo energia...', 'info')

      if (!extractRes.ok) throw new Error('Extraction failed')
      setVideoId(videoId)
      setExtractionComplete(true)

      // Brief pause to show energy extraction completing
      setProgress(45)
      addLog('Finalizando...', 'info')

      setTimeout(() => {
        setProgress(50)
        addLog('Extração completa! Ajuste as configurações.', 'success')
      }, 300)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      addLog(`Erro: ${msg}`, 'error')
      setError(msg)
      setProcessingState('error')
    }
  }

  const rankMoments = async () => {
    console.log('[RANK] videoId:', videoId, 'config:', config)
    if (!videoId) { console.log('[RANK] early return - no videoId'); return }
    setError(null)
    setProcessingState('analyzing')
    setCurrentStep('Processando...')
    setProgress(60)
    addLog('Analisando momentos com IA...')

    try {
      const processRes = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: activeTab === 'youtube' ? 'youtube' : 'upload',
          file_id: videoId,
          youtube_url: activeTab === 'youtube' ? youtubeUrl : '',
          config: config
        })
      })
      console.log('[DEBUG] processRes status:', processRes.status)
      if (!processRes.ok) throw new Error('Processing failed')
      const processData = await processRes.json()
      setProgress(85)

      // Step 3: Fetch moments
      setCurrentStep('Carregando momentos...')
      const momentsRes = await fetch(`${API_BASE}/moments/${videoId}`)
      if (!momentsRes.ok) throw new Error('Failed to load moments')
      const momentsData = await momentsRes.json()
      setMoments(momentsData.moments || [])

      // Step 4: Set video source for player
      setVideoSrc(`${API_BASE}/video/${videoId}`)
      setProcessingState('complete')
      setCurrentStep('Completo')
      setProgress(100)
      addLog('Processamento completo!', 'success')
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      addLog(`Erro: ${msg}`, 'error')
      setError(msg)
      setProcessingState('error')
    }
  }

  const showConfigPanel = processingState === 'transcribing'

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold">ClipWise</h1>
          <p className="text-gray-400">Detector de momentos para lives</p>
        </header>

        {/* Tabs */}
        <div className="flex border-b border-gray-700 mb-6">
          <button
            onClick={() => setActiveTab('arquivo')}
            className={cn(
              'px-4 py-2 font-medium transition-colors',
              activeTab === 'arquivo'
                ? 'text-blue-500 border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-gray-200'
            )}
          >
            Arquivo
          </button>
          <button
            onClick={() => setActiveTab('youtube')}
            className={cn(
              'px-4 py-2 font-medium transition-colors',
              activeTab === 'youtube'
                ? 'text-blue-500 border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-gray-200'
            )}
          >
            YouTube
          </button>
        </div>

        <div className="grid gap-6">
          {/* Upload/URL Section */}
          <section className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Upload da Live
            </h2>

            {activeTab === 'arquivo' ? (
              <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-gray-400 transition-colors cursor-pointer relative">
                <input
                  type="file"
                  accept="video/*,audio/*"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-gray-400">
                  {file ? file.name : 'Arraste o arquivo aqui ou clique para selecionar'}
                </p>
                <p className="text-sm text-gray-500 mt-2">MP4, MKV, WAV</p>
              </div>
            ) : (
              <div className="space-y-2">
                <input
                  type="url"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="mt-4 p-3 bg-red-900/30 border border-red-800 rounded-lg flex items-center gap-2 text-red-400">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}

            {/* Transcribe Button */}
            <div className="mt-6 flex justify-end">
              <Button
                onClick={processVideo}
                disabled={processingState !== 'idle' && processingState !== 'complete'}
                className="flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Transcrever
              </Button>
            </div>
          </section>

          {/* Progress Section - shown during processing */}
          {(processingState !== 'idle' && processingState !== 'complete') && (
            <section className="border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Play className="w-5 h-5" />
                Processando
              </h2>

              {/* Progress bar + percentage */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-400 mb-2">
                  <span>{currentStep}</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Step list */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                {STEPS.map((step) => {
                  const stepIndex = STEPS.findIndex(s => s.key === step.key)
                  const currentIndex = STEPS.findIndex(s => s.key === processingState)
                  const isComplete = stepIndex < currentIndex
                  const isCurrent = step.key === processingState

                  return (
                    <div
                      key={step.key}
                      className={cn(
                        'p-2 rounded text-center text-sm',
                        isComplete && 'bg-green-900/30 text-green-400',
                        isCurrent && 'bg-blue-900/30 text-blue-400',
                        !isComplete && !isCurrent && 'bg-gray-800 text-gray-500'
                      )}
                    >
                      {step.label}
                    </div>
                  )
                })}
              </div>

              {/* Log window */}
              <div className="bg-black/50 border border-gray-700 rounded-lg p-4 h-40 overflow-y-auto font-mono text-sm space-y-1">
                {logs.length === 0 ? (
                  <p className="text-gray-500">Aguardando...</p>
                ) : (
                  logs.map((log, i) => (
                    <p key={i} className={cn(
                      log.type === 'error' && 'text-red-400',
                      log.type === 'success' && 'text-green-400',
                      log.type === 'info' && 'text-gray-400'
                    )}>
                      <span className="text-gray-600">[{log.timestamp}]</span> {log.message}
                    </p>
                  ))
                )}
              </div>
            </section>
          )}

          {/* Video Player */}
          {processingState === 'complete' && videoSrc && (
            <section className="border rounded-lg p-4">
              <video
                ref={videoRef}
                src={videoSrc}
                controls
                className="w-full rounded-lg"
                onLoadedMetadata={(e) => setVideoDuration(e.currentTarget.duration)}
              />
            </section>
          )}

          {/* Energy Waveform Visualization */}
          {processingState === 'complete' && energyData.length > 0 && videoDuration > 0 && (
            <WaveformVisualizer
              energyData={energyData}
              peakTimes={energyData.filter(e => e.isPeak).map(e => e.time)}
              duration={videoDuration}
              onSeek={jumpToTimestamp}
            />
          )}

          {/* Dashboard: Top N Slider + Export */}
          {processingState === 'complete' && moments.length > 0 && (
            <section className="border rounded-lg p-6 space-y-4">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium">Top {topN} momentos</span>
                <Slider
                  value={[topN]}
                  onValueChange={(v) => setTopN(v[0])}
                  min={3}
                  max={Math.min(20, moments.length)}
                  step={1}
                  className="flex-1"
                />
                <span className="text-sm text-gray-400 w-12">{topN}/{moments.length}</span>
              </div>
              <Button
                onClick={sendToOpus}
                disabled={selectedMoments.size === 0 || opusStatus === 'sending'}
                className="w-full flex items-center gap-2"
              >
                {opusStatus === 'sending' ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Enviando...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Enviar pro Opus Clip ({selectedMoments.size} selecionados)
                  </>
                )}
              </Button>
              {opusStatus === 'success' && (
                <div className="mt-2 p-3 bg-green-900/30 border border-green-800 rounded-lg text-green-400 text-sm">
                  ✓ Momentos enviados! Job ID: {opusJobId}
                  <br />
                  <span className="text-gray-400">O Opus Clip processará seus clips em breve.</span>
                </div>
              )}
              {opusStatus === 'error' && (
                <div className="mt-2 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
                  ✗ Erro ao conectar com o Opus Clip
                  <br />
                  <span className="text-gray-400">Verifique sua chave de API e tente novamente.</span>
                </div>
              )}
            </section>
          )}

          {/* Moments List */}
          {processingState === 'complete' && moments.length > 0 && (
            <section className="space-y-3">
              {moments.slice(0, topN).map((moment, index) => (
                <MomentCard
                  key={index}
                  moment={moment}
                  rank={index + 1}
                  isSelected={selectedMoments.has(index)}
                  onToggle={() => toggleMoment(index)}
                  onPlay={jumpToTimestamp}
                />
              ))}
            </section>
          )}

          {/* Config Panel - shown when no moments but config is needed */}
          {showConfigPanel && (
            <section className="space-y-4">
              <ConfigPanel
                config={config}
                onConfigChange={handleConfigChange}
              />
              <div className="flex justify-end">
                <Button
                  onClick={() => { console.log('[CLICK] Processar com IA clicked, extractionComplete=', extractionComplete); rankMoments(); }}
                  disabled={!extractionComplete}
                  className="flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Processar com IA
                </Button>
              </div>
            </section>
          )}

          {/* Complete State - no moments yet */}
          {processingState === 'complete' && !showConfigPanel && moments.length === 0 && (
            <section className="border rounded-lg p-6 border-green-800 bg-green-900/10">
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle2 className="w-6 h-6" />
                <span className="text-lg font-semibold">Processamento completo!</span>
              </div>
              <p className="text-gray-400 mt-2">Configure os parâmetros abaixo para gerar seus clips.</p>
            </section>
          )}
        </div>
      </div>
    </main>
  )
}