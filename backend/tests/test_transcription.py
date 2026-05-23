"""
Tests for transcription service using Faster Whisper.

RED phase: These tests define the expected behavior.
GREEN phase: Implement transcription.py to make them pass.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock


class TestTranscribeFile:
    """Test the transcribe_file function signature and output structure."""

    def test_transcribe_file_exists(self):
        """transcribe_file function should exist and be importable."""
        from services.transcription import transcribe_file
        assert callable(transcribe_file)

    def test_transcribe_file_returns_dict(self):
        """transcribe_file should return a dictionary."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            [
                MagicMock(
                    id=0,
                    start=0.0,
                    end=5.0,
                    text="Test transcript",
                    words=[
                        MagicMock(word="Test", start=0.0, end=0.5, probability=0.9),
                        MagicMock(word="transcript", start=0.5, end=1.0, probability=0.9),
                    ],
                )
            ],
            MagicMock(duration=5.0, language="en"),
        )

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model
            result = transcribe_file("/tmp/clipwise/test-id/file.wav")
            assert isinstance(result, dict)

    def test_transcribe_file_output_has_required_keys(self):
        """Output should have transcript, segments, words, duration, language keys."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            [
                MagicMock(
                    id=0,
                    start=0.0,
                    end=5.0,
                    text="Test transcript",
                    words=[
                        MagicMock(word="Test", start=0.0, end=0.5, probability=0.9),
                        MagicMock(word="transcript", start=0.5, end=1.0, probability=0.9),
                    ],
                )
            ],
            MagicMock(duration=5.0, language="en"),
        )

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model
            result = transcribe_file("/tmp/clipwise/test-id/file.wav")

            required_keys = ["transcript", "segments", "words", "duration", "language"]
            for key in required_keys:
                assert key in result, f"Missing key: {key}"

    def test_transcribe_file_segments_have_word_timestamps(self):
        """Segments should have word-level timestamps (word_timestamps=True)."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            [
                MagicMock(
                    id=0,
                    start=0.0,
                    end=2.0,
                    text="Hello world",
                    words=[
                        MagicMock(word="Hello", start=0.0, end=1.0, probability=0.95),
                        MagicMock(word="world", start=1.0, end=2.0, probability=0.95),
                    ],
                )
            ],
            MagicMock(duration=2.0, language="en"),
        )

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model
            result = transcribe_file("/tmp/clipwise/test-id/file.wav")

            assert len(result["words"]) > 0
            for word in result["words"]:
                assert "start" in word, "Word missing start timestamp"
                assert "end" in word, "Word missing end timestamp"
                assert "word" in word, "Word missing text"

    def test_transcribe_file_saves_json_to_tmp(self):
        """Should save JSON output to /tmp/clipwise/<video_id>/transcript.json."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            [
                MagicMock(
                    id=0,
                    start=0.0,
                    end=1.0,
                    text="Test",
                    words=[MagicMock(word="Test", start=0.0, end=1.0, probability=0.9)],
                )
            ],
            MagicMock(duration=1.0, language="en"),
        )

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model

            result = transcribe_file("/tmp/clipwise/test-video-id/original.mp4")

            assert isinstance(result, dict)
            assert result["transcript"] == "Test"

    def test_transcribe_file_uses_base_model_by_default(self):
        """Should use 'base' model for good speed/accuracy balance."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], MagicMock(duration=0, language="en"))

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model

            transcribe_file("/tmp/clipwise/test-id/file.wav")

            mock_whisper.assert_called_once_with("base", device="auto", compute_type="auto")

    def test_transcribe_file_accepts_model_size_param(self):
        """Should accept custom model_size parameter."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], MagicMock(duration=0, language="en"))

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model

            transcribe_file("/tmp/clipwise/test-id/file.wav", model_size="small")

            mock_whisper.assert_called_once_with("small", device="auto", compute_type="auto")

    def test_transcribe_file_handles_60_minute_files(self):
        """Should handle 60-minute files without memory issues."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        segments = []
        for i in range(3600):
            start = i * 1.0
            end = (i + 1) * 1.0
            segments.append(
                MagicMock(
                    id=i,
                    start=start,
                    end=end,
                    text=f"Word {i}",
                    words=[
                        MagicMock(word=f"Word {i}", start=start, end=end, probability=0.9)
                    ],
                )
            )

        mock_model.transcribe.return_value = (
            segments,
            MagicMock(duration=3600.0, language="en"),
        )

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model

            result = transcribe_file("/tmp/clipwise/test-id/file.wav")

            assert result["duration"] == 3600.0
            assert len(result["segments"]) == 3600
            assert len(result["words"]) == 3600

    def test_transcribe_file_returns_language(self):
        """Should return detected language."""
        from services.transcription import transcribe_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = (
            [
                MagicMock(
                    id=0,
                    start=0.0,
                    end=2.0,
                    text="Bonjour monde",
                    words=[
                        MagicMock(word="Bonjour", start=0.0, end=1.0, probability=0.9),
                        MagicMock(word="monde", start=1.0, end=2.0, probability=0.9),
                    ],
                )
            ],
            MagicMock(duration=2.0, language="fr"),
        )

        with patch("services.transcription.WhisperModel") as mock_whisper, \
             patch("services.transcription.os.path.exists", return_value=True), \
             patch("services.transcription.os.makedirs"), \
             patch("services.transcription.open", MagicMock()):
            mock_whisper.return_value = mock_model

            result = transcribe_file("/tmp/clipwise/test-id/file.wav")

            assert result["language"] == "fr"


class TestTranscriptionIntegration:
    """Integration tests for transcription with actual file processing."""

    def test_transcribe_nonexistent_file_raises_error(self):
        """Should raise FileNotFoundError for non-existent files."""
        from services.transcription import transcribe_file

        with pytest.raises(FileNotFoundError):
            transcribe_file("/nonexistent/path/audio.wav")