# Phase 1 Discussion Log

**Date:** 2025-05-23

## Areas Discussed

### 1. Video Source Handling
**Options presented:**
- Stream audio to whisper
- Download first, then transcribe

**Decision:** Download first, then transcribe

**Notes:** Backend handles everything (yt-dlp + transcription + energy extraction)

---

### 2. Upload Methods
**Options presented:**
- Both: arquivo + YouTube URL
- Apenas arquivo (MP4, MKV, WAV)

**Decision:** Both — file upload AND YouTube URL

---

### 3. UI Layout for Upload
**Options presented:**
- UI única com ambas opções
- Tabs: Arquivo | YouTube

**Decision:** Tabs: Arquivo | YouTube

---

### 4. UI Component Style
**Options presented:**
- Um box com toggle File/YouTube
- Dropzone e campo URL separados

**Decision:** Um box com toggle File/YouTube

---

### 5. YouTube Flow
**Options presented:**
- Download completo, depois processa
- Stream direto

**Decision:** Download completo, depois processa

---

### 6. Transcription Responsibility
**Question:** Backend faz tudo ou Frontend baixa e manda?

**Clarification:** Explicado que para YouTube, backend precisa da URL para yt-dlp funcionar. Recomendação: Backend faz tudo.

**Decision:** Backend faz tudo

---

### 7. Whisper Model
**Options presented:**
- tiny (~1GB RAM)
- base (~1GB RAM)
- small (~2GB RAM)

**Decision:** base (~1GB RAM)

---

### 8. Audio Energy Method
**Options presented:**
- FFmpeg astats + Z-score (podcli-style)
- Janela deslizante 0.5s

**Decision:** FFmpeg astats + Z-score (podcli-style)

---

### 9. Transcription Trigger
**Options presented:**
- Automático após upload
- Botão manual
- Confirmação antes

**Decision:** Botão manual

---

### 10. Data Storage Format
**Question:** JSON único ou dois arquivos separados? Referência ao podcli.

**Clarification:** Explained podcli's `pack_transcript` approach — creates markdown with transcript + energy peaks combined.

**Decision:** Follow podcli pattern — transcript.json + energy.json + combined.md (markdown for LLM)

---

### 11. Configuration UI Location
**Options presented:**
- Antes do processamento
- Na mesma tela do upload
- Após processamento

**Decision:** Após processamento

---

### 12. Progress Display
**Options presented:**
- Tela única, mostra tudo: upload → processing → config → done
- Wizard com steps

**Decision:** Tela única (everything on same page)

---

### 13. Progress Type
**Options presented:**
- Progress bar com %
- Lista de steps

**Decision:** Both — progress bar AND step list shown simultaneously

---

### 14. Error Handling
**Question:** Toast notification or log window?

**Clarification:** User clarified: log window showing each step, with details if problems occur.

**Decision:** Log window with retry option (not toast)

---

## Summary

Phase 1 context captured with 14 decisions covering:
- Input methods (file + YouTube URL)
- UI layout (tabs with toggle)
- Processing flow (backend does everything)
- Whisper model (base)
- Energy extraction (FFmpeg astats + Z-score, podcli-style)
- Data format (follow podcli: JSON + combined markdown)
- UI behavior (single page, manual trigger, progress bar + steps, log window for errors)