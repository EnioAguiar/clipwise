"use client";

import { useState } from "react";
import { Upload, CheckCircle, AlertCircle } from "lucide-react";

interface OpusUploadButtonProps {
  videoId: string;
  videoFilename?: string;
  isYoutube?: boolean;
  youtubeUrl?: string;
  onUploadComplete?: (uploadId: string) => void;
  disabled?: boolean;
}

export default function OpusUploadButton({
  videoId,
  videoFilename,
  isYoutube = false,
  youtubeUrl,
  onUploadComplete,
  disabled = false,
}: OpusUploadButtonProps) {
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");

  const handleUpload = async () => {
    if (isYoutube && youtubeUrl) {
      setStatus("uploading");
      try {
        await fetch("/api/opus/store-youtube", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_id: videoId, youtube_url: youtubeUrl }),
        });
        setStatus("success");
        onUploadComplete?.("youtube");
      } catch (err) {
        setStatus("error");
        setErrorMessage("Erro ao configurar vídeo do YouTube");
      }
      return;
    }

    if (!videoFilename) return;

    setStatus("uploading");
    setProgress(0);

    try {
      // Step 1: Get upload link
      const linkRes = await fetch("/api/opus/upload-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_id: videoId, filename: videoFilename }),
      });

      if (!linkRes.ok) throw new Error("Falha ao obter link de upload");

      const { upload_id, url } = await linkRes.json();

      // Step 2: Initiate resumable upload
      const startRes = await fetch(url, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${process.env.NEXT_PUBLIC_OPUS_API_KEY}`,
          "X-Goog-Resumable": "start",
        },
      });

      const location = startRes.headers.get("Location");
      if (!location) throw new Error("Não foi possível iniciar upload");

      // Step 3: Upload video in chunks with progress
      const videoRes = await fetch(`/api/video/${videoId}`);
      const videoBlob = await videoRes.blob();

      const chunkSize = 5 * 1024 * 1024;
      const totalChunks = Math.ceil(videoBlob.size / chunkSize);
      let uploaded = 0;

      for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, videoBlob.size);
        const chunk = videoBlob.slice(start, end);

        await fetch(location, {
          method: "PUT",
          headers: {
            "Content-Range": `bytes ${start}-${end - 1}/${videoBlob.size}`,
            "Content-Length": String(end - start),
          },
          body: chunk,
        });

        uploaded++;
        setProgress((uploaded / totalChunks) * 100);
      }

      // Step 4: Confirm upload complete
      await fetch("/api/opus/upload-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_id: videoId, upload_id }),
      });

      setStatus("success");
      onUploadComplete?.(upload_id);
    } catch (err) {
      setStatus("error");
      setErrorMessage("Erro ao enviar vídeo para o Opus. Verifique sua chave de API.");
    }
  };

  if (status === "success") {
    return (
      <div className="flex items-center gap-2 p-4 rounded-lg bg-green-900/20 border border-green-700">
        <CheckCircle className="w-5 h-5 text-green-500" />
        <span className="text-green-400">Vídeo enviado! Agora você pode enviar os momentos.</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <button
        onClick={handleUpload}
        disabled={disabled || status === "uploading"}
        className={`
          w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium
          transition-colors
          ${disabled ? "bg-gray-600 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-500"}
          ${status === "uploading" ? "bg-blue-700" : ""}
        `}
      >
        {status === "uploading" ? (
          <>
            <Upload className="w-4 h-4 animate-spin" />
            Enviando vídeo para o Opus...
          </>
        ) : (
          <>
            <Upload className="w-4 h-4" />
            Subir vídeo para Opus
          </>
        )}
      </button>

      {status === "uploading" && (
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {status === "error" && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-900/20 border border-red-700">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-red-400 text-sm">{errorMessage}</span>
        </div>
      )}

      <p className="text-xs text-gray-400 text-center">
        {isYoutube ? "Vídeo do YouTube - upload será ignorado" : "O envio pode demorar dependendo do tamanho do arquivo"}
      </p>
    </div>
  );
}