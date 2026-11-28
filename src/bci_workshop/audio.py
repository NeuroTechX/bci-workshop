"""Cross-platform RIFF WAV audio cue generator (fixes legacy Issue #13)."""

from __future__ import annotations

import math
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import wave


def generate_beep_wav(
    path: str | pathlib.Path | None = None,
    freq_hz: float = 660.0,
    duration_sec: float = 0.22,
    sample_rate: int = 44100,
    amplitude: float = 0.35,
) -> pathlib.Path:
    """Write a valid 16-bit PCM mono RIFF WAV sine tone with smooth fade-in/out."""
    out_path = (
        pathlib.Path(path)
        if path is not None
        else pathlib.Path(tempfile.gettempdir()) / f"ntx_bci_cue_{int(freq_hz)}hz.wav"
    )
    n_samples = max(1, int(round(duration_sec * sample_rate)))
    fade = max(1, min(int(0.015 * sample_rate), n_samples // 4))

    frames = bytearray()
    for i in range(n_samples):
        env = 1.0
        if i < fade:
            env = i / fade
        elif i >= n_samples - fade:
            env = (n_samples - 1 - i) / fade
        sample = amplitude * env * math.sin(2.0 * math.pi * freq_hz * (i / sample_rate))
        pcm = max(-32767, min(32767, int(round(sample * 32767.0))))
        frames.extend(struct.pack("<h", pcm))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))

    return out_path


def play_cue(freq_hz: float = 660.0, duration_sec: float = 0.22, mute: bool = False) -> None:
    """Play a short non-blocking cue tone across macOS, Linux, and Windows without shell=True."""
    if mute:
        return
    wav_path = generate_beep_wav(freq_hz=freq_hz, duration_sec=duration_sec)
    try:
        if sys.platform == "darwin" and shutil.which("afplay"):
            subprocess.Popen(
                ["afplay", str(wav_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        if sys.platform.startswith("linux"):
            for player in ("pw-play", "paplay", "aplay"):
                if shutil.which(player):
                    subprocess.Popen(
                        [player, str(wav_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
        if sys.platform == "win32":
            import winsound  # type: ignore[import-not-found]

            winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
    except Exception:
        pass
    # Safe terminal bell fallback
    sys.stdout.write("\a")
    sys.stdout.flush()
