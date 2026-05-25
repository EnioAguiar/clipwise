"use client";

import { useState } from "react";
import { X, Play, CheckCircle } from "lucide-react";

interface TimestampVerificationModalProps {
  isOpen: boolean;
  moment: {
    id: string;
    start: number;
    duration: number;
    transcript_snippet?: string;
    energy_score?: number;
  } | null;
  videoUrl?: string;
  onConfirm: (momentId: string) => void;
  onCancel: () => void;
}

export default function TimestampVerificationModal({
  isOpen,
  moment,
  videoUrl,
  onConfirm,
  onCancel,
}: TimestampVerificationModalProps) {
  if (!isOpen || !moment) return null;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-gray-800 rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Verificar momento</h3>
          <button onClick={onCancel} className="p-1 hover:bg-gray-700 rounded">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Video preview at timestamp */}
        {videoUrl && (
          <div className="mb-4 rounded-lg overflow-hidden bg-black">
            <video
              src={videoUrl}
              controls
              className="w-full"
              style={{ maxHeight: "200px" }}
            />
          </div>
        )}

        {/* Moment details */}
        <div className="bg-gray-900 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Início:</span>
              <span className="ml-2 text-white font-mono">{formatTime(moment.start)}</span>
            </div>
            <div>
              <span className="text-gray-400">Duração:</span>
              <span className="ml-2 text-white font-mono">{moment.duration}s</span>
            </div>
            {moment.energy_score !== undefined && (
              <div>
                <span className="text-gray-400">Score:</span>
                <span className="ml-2 text-blue-400 font-mono">{moment.energy_score.toFixed(1)}</span>
              </div>
            )}
          </div>
          
          {moment.transcript_snippet && (
            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-gray-300 text-sm italic">"{moment.transcript_snippet}"</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700"
          >
            Cancelar
          </button>
          <button
            onClick={() => onConfirm(moment.id)}
            className="flex-1 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 flex items-center justify-center gap-2"
          >
            <CheckCircle className="w-4 h-4" />
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
}