"use client";

import { useState } from "react";
import { Send, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import TimestampVerificationModal from "./TimestampVerificationModal";

interface Moment {
  id: string;
  start: number;
  duration: number;
  transcript_snippet?: string;
  energy_score?: number;
}

interface OpusTimestampSenderProps {
  videoId: string;
  moments: Moment[];
  uploadComplete: boolean;
  isYoutube?: boolean;
  disabled?: boolean;
  onMomentSent?: (momentId: string, projectId: string) => void;
  onAllSent?: (count: number) => void;
}

export default function OpusTimestampSender({
  videoId,
  moments,
  uploadComplete,
  isYoutube = false,
  disabled = false,
  onMomentSent,
  onAllSent,
}: OpusTimestampSenderProps) {
  const [sendingStates, setSendingStates] = useState<Record<string, "idle" | "sending" | "sent" | "error">>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedMoment, setSelectedMoment] = useState<Moment | null>(null);
  const [projectIds, setProjectIds] = useState<Record<string, string>>({});
  const [errorMessages, setErrorMessages] = useState<Record<string, string>>({});

  const canSend = uploadComplete && !disabled;

  const handleSendIndividual = (moment: Moment) => {
    setSelectedMoment(moment);
    setModalOpen(true);
  };

  const handleConfirmSend = async (momentId: string) => {
    setModalOpen(false);

    const momentToSend = moments.find(m => m.id === momentId);
    if (!momentToSend) return;

    setSendingStates(prev => ({ ...prev, [momentId]: "sending" }));

    try {
      const res = await fetch("/api/opus/send-moments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoId,
          use_youtube: isYoutube,
          moments: [{
            id: momentToSend.id,
            start: momentToSend.start,
            duration: momentToSend.duration,
          }],
        }),
      });

      if (!res.ok) throw new Error("Falha ao enviar momento");

      const { project_id } = await res.json();
      setProjectIds(prev => ({ ...prev, [momentId]: project_id }));
      setSendingStates(prev => ({ ...prev, [momentId]: "sent" }));
      onMomentSent?.(momentId, project_id);
    } catch (err) {
      setSendingStates(prev => ({ ...prev, [momentId]: "error" }));
      setErrorMessages(prev => ({ ...prev, [momentId]: "Erro ao enviar para Opus" }));
    }
  };

  const handleSendAll = async () => {
    const unsentMoments = moments.filter(m => sendingStates[m.id] !== "sent");
    if (unsentMoments.length === 0) return;

    for (const moment of unsentMoments) {
      setSendingStates(prev => ({ ...prev, [moment.id]: "sending" }));
    }

    try {
      const res = await fetch("/api/opus/send-moments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoId,
          use_youtube: isYoutube,
          moments: unsentMoments.map(m => ({
            id: m.id,
            start: m.start,
            duration: m.duration,
          })),
        }),
      });

      if (!res.ok) throw new Error("Falha ao enviar momentos");

      const { project_id } = await res.json();

      for (const moment of unsentMoments) {
        setProjectIds(prev => ({ ...prev, [moment.id]: project_id }));
        setSendingStates(prev => ({ ...prev, [moment.id]: "sent" }));
      }

      onAllSent?.(unsentMoments.length);
    } catch (err) {
      for (const moment of unsentMoments) {
        setSendingStates(prev => ({ ...prev, [moment.id]: "error" }));
        setErrorMessages(prev => ({ ...prev, [moment.id]: "Erro ao enviar para Opus" }));
      }
    }
  };

  const getStatusIcon = (state: string) => {
    switch (state) {
      case "sent": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "sending": return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case "error": return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Send className="w-4 h-4 text-gray-400" />;
    }
  };

  if (moments.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p className="text-lg font-medium">Nenhum momento selecionado</p>
        <p className="text-sm mt-1">Selecione momentos na lista acima para enviar ao Opus</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Bulk send button */}
      <div className="flex gap-3">
        <button
          onClick={handleSendAll}
          disabled={!canSend || moments.every(m => sendingStates[m.id] === "sent")}
          className={`
            flex-1 px-4 py-2 rounded-lg font-medium flex items-center justify-center gap-2
            transition-colors
            ${!canSend ? "bg-gray-600 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-500"}
            ${moments.every(m => sendingStates[m.id] === "sent") ? "bg-green-600" : ""}
          `}
        >
          <Send className="w-4 h-4" />
          Enviar todos
        </button>
      </div>

      {/* Per-moment send list */}
      <div className="space-y-2">
        {moments.map(moment => (
          <div
            key={moment.id}
            className="flex items-center justify-between p-3 bg-gray-800 rounded-lg"
          >
            <div className="flex items-center gap-3">
              {getStatusIcon(sendingStates[moment.id] || "idle")}
              <div>
                <span className="text-white font-mono">
                  {Math.floor(moment.start / 60)}:{String(Math.floor(moment.start % 60)).padStart(2, "0")}
                </span>
                <span className="text-gray-400 ml-2 text-sm">{moment.duration}s</span>
              </div>
            </div>

            {sendingStates[moment.id] !== "sent" ? (
              <button
                onClick={() => handleSendIndividual(moment)}
                disabled={!canSend}
                className={`
                  px-3 py-1 rounded text-sm
                  ${canSend ? "bg-gray-700 hover:bg-gray-600 text-gray-200" : "bg-gray-800 text-gray-500 cursor-not-allowed"}
                `}
              >
                Enviar pro Opus
              </button>
            ) : (
              <span className="text-green-400 text-sm">
                Enviado {projectIds[moment.id] ? `(Project: ${projectIds[moment.id].slice(0, 8)}...)` : ""}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Verification Modal */}
      <TimestampVerificationModal
        isOpen={modalOpen}
        moment={selectedMoment}
        onConfirm={handleConfirmSend}
        onCancel={() => setModalOpen(false)}
      />
    </div>
  );
}