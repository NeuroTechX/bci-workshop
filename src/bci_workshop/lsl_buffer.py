"""Non-lagging real-time LSL ring buffer supporting both mne-lsl and pylsl."""

from __future__ import annotations

import time
import numpy as np

from .dsp import OnlineFilterBank


class EEGStreamBuffer:
    """Real-time LSL EEG ring buffer that drains all available samples per poll.

    Fixes two critical bugs from the 2017-2018 workshop:
      1. Cumulative display lag (Issue #14): legacy code pulled at most `0.2s` per loop,
         falling behind whenever Matplotlib took >200ms to render. Here `pull()` drains up
         to 16,384 pending samples per tick into a fixed-length circular buffer.
      2. Calibration bleed: `flush()` discards buffered pre-cue samples, and
         `record_segment(duration_sec)` uses `time.monotonic()` to collect an exact-duration
         segment without returning early on already-buffered samples.
    """

    def __init__(
        self,
        stream_type: str = "EEG",
        stream_name: str | None = None,
        bufsize_sec: float = 15.0,
        mains_hz: float | None = 60.0,
        bandpass_hz: tuple[float, float] | None = (1.0, 45.0),
        timeout_sec: float = 5.0,
    ) -> None:
        from pylsl import StreamInlet, resolve_byprop

        if stream_name:
            streams = resolve_byprop("name", stream_name, timeout=timeout_sec)
        else:
            streams = resolve_byprop("type", stream_type, timeout=timeout_sec)

        if not streams:
            target = f"name='{stream_name}'" if stream_name else f"type='{stream_type}'"
            raise RuntimeError(
                f"No LSL stream found matching {target} after {timeout_sec:.1f}s.\n"
                "Tip: No headset? Start the built-in simulator in another terminal:\n"
                "  python streams/mock_eeg_stream.py"
            )

        self._inlet = StreamInlet(streams[0], max_buflen=max(30, int(bufsize_sec * 2)), max_chunklen=0)
        info = self._inlet.info()
        self.stream_name = info.name()
        self.sfreq = float(info.nominal_srate())
        if self.sfreq <= 0:
            raise RuntimeError(f"LSL stream '{self.stream_name}' has irregular srate ({self.sfreq}).")
        self.n_channels = int(info.channel_count())
        self.ch_names = self._parse_channel_names(info, self.n_channels)

        self.buf_samples = max(64, int(round(bufsize_sec * self.sfreq)))
        self.raw_buffer = np.zeros((self.buf_samples, self.n_channels), dtype=np.float64)
        self.filtered_buffer = np.zeros((self.buf_samples, self.n_channels), dtype=np.float64)
        self.timestamps = np.zeros(self.buf_samples, dtype=np.float64)
        self.total_samples_seen = 0

        self.filter_bank = OnlineFilterBank(
            sfreq=self.sfreq,
            n_channels=self.n_channels,
            mains_hz=mains_hz,
            bandpass_hz=bandpass_hz,
        )
        # Initialize LSL time-offset estimation
        try:
            self._inlet.time_correction(timeout=1.0)
        except Exception:
            pass

    @staticmethod
    def _parse_channel_names(info: object, n_channels: int) -> list[str]:
        """Parse channel labels from LSL XML metadata without the legacy off-by-one bug."""
        names: list[str] = []
        try:
            ch = info.desc().child("channels").first_child()  # type: ignore[attr-defined]
            for _ in range(n_channels):
                if ch.empty():
                    break
                label = ch.child_value("label") or ch.child_value("name")
                names.append(label if label else f"Ch{len(names) + 1}")
                ch = ch.next_sibling()
        except Exception:
            pass
        while len(names) < n_channels:
            names.append(f"Ch{len(names) + 1}")
        return names[:n_channels]

    def flush(self) -> None:
        """Drain and discard any stale samples sitting in the LSL inlet queue."""
        while True:
            chunk, _ = self._inlet.pull_chunk(timeout=0.0, max_samples=16384)
            if not chunk:
                break

    def pull(self, timeout: float = 0.0) -> int:
        """Drain all currently available LSL samples into the ring buffer; returns count read."""
        total_new = 0
        first = True
        while True:
            wait = timeout if first else 0.0
            first = False
            chunk, ts = self._inlet.pull_chunk(timeout=wait, max_samples=16384)
            if not chunk:
                break
            raw = np.asarray(chunk, dtype=np.float64)
            if raw.ndim == 1:
                raw = raw[:, np.newaxis]
            # Handle Muse AUX5 extra column if nominal channels differ
            raw = raw[:, : self.n_channels]
            filt = self.filter_bank.transform(raw)
            ts_arr = np.asarray(ts, dtype=np.float64)

            n = raw.shape[0]
            total_new += n
            self.total_samples_seen += n
            if n >= self.buf_samples:
                self.raw_buffer[:] = raw[-self.buf_samples :]
                self.filtered_buffer[:] = filt[-self.buf_samples :]
                self.timestamps[:] = ts_arr[-self.buf_samples :]
            else:
                self.raw_buffer = np.roll(self.raw_buffer, -n, axis=0)
                self.filtered_buffer = np.roll(self.filtered_buffer, -n, axis=0)
                self.timestamps = np.roll(self.timestamps, -n, axis=0)
                self.raw_buffer[-n:] = raw
                self.filtered_buffer[-n:] = filt
                self.timestamps[-n:] = ts_arr
            if n < 1024:
                break
        return total_new

    def get_latest_window(self, window_sec: float, filtered: bool = True) -> np.ndarray:
        """Return most recent (n_win, n_channels) samples from the ring buffer."""
        n_win = min(self.buf_samples, max(1, int(round(window_sec * self.sfreq))))
        src = self.filtered_buffer if filtered else self.raw_buffer
        return src[-n_win:].copy()

    def record_segment(self, duration_sec: float, filtered: bool = True) -> np.ndarray:
        """Flush stale samples and record a fresh continuous segment of `duration_sec` seconds."""
        target_samples = max(16, int(round(duration_sec * self.sfreq)))
        self.flush()
        collected: list[np.ndarray] = []
        n_collected = 0
        deadline = time.monotonic() + duration_sec + 3.0

        while n_collected < target_samples and time.monotonic() < deadline:
            chunk, _ = self._inlet.pull_chunk(timeout=0.05, max_samples=4096)
            if not chunk:
                continue
            raw = np.asarray(chunk, dtype=np.float64)
            if raw.ndim == 1:
                raw = raw[:, np.newaxis]
            raw = raw[:, : self.n_channels]
            filt = self.filter_bank.transform(raw)
            collected.append(filt if filtered else raw)
            n_collected += raw.shape[0]

        if not collected:
            raise RuntimeError("No EEG samples received during calibration window.")
        full = np.concatenate(collected, axis=0)
        return full[:target_samples]

    def close(self) -> None:
        try:
            self._inlet.close_stream()
        except Exception:
            pass
