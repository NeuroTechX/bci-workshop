"""Causal online filtering, Welch PSD bandpower extraction, and epoch slicing."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, iirnotch, sosfilt, sosfilt_zi, tf2sos, welch

BANDS: dict[str, tuple[float, float]] = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 12.0),
    "beta": (12.0, 30.0),
    "gamma": (30.0, 45.0),
}


class OnlineFilterBank:
    """Stateful causal notch + bandpass filter for real-time multi-channel EEG."""

    def __init__(
        self,
        sfreq: float,
        n_channels: int,
        mains_hz: float | None = 60.0,
        bandpass_hz: tuple[float, float] | None = (1.0, 45.0),
        order: int = 4,
    ) -> None:
        if sfreq <= 0:
            raise ValueError(f"Sampling rate must be positive, got {sfreq}")
        self.sfreq = float(sfreq)
        self.n_channels = int(n_channels)
        nyq = 0.5 * self.sfreq

        sos_sections: list[np.ndarray] = []
        if mains_hz is not None and 0 < mains_hz < nyq - 1.0:
            b_notch, a_notch = iirnotch(w0=mains_hz, Q=30.0, fs=self.sfreq)
            sos_sections.append(tf2sos(b_notch, a_notch))

        if bandpass_hz is not None:
            low, high = bandpass_hz
            high = min(high, nyq * 0.92)
            if 0 < low < high:
                sos_bp = butter(order, [low, high], btype="bandpass", fs=self.sfreq, output="sos")
                sos_sections.append(sos_bp)

        self.sos = np.vstack(sos_sections) if sos_sections else None
        self._zi: np.ndarray | None = None

    def reset(self) -> None:
        self._zi = None

    def transform(self, chunk: np.ndarray) -> np.ndarray:
        """Filter chunk of shape (n_samples, n_channels), preserving filter state."""
        arr = np.asarray(chunk, dtype=np.float64)
        if arr.ndim == 1:
            arr = arr[:, np.newaxis]
        if arr.shape[0] == 0 or self.sos is None:
            return arr.copy()
        if arr.shape[1] != self.n_channels:
            raise ValueError(f"Expected {self.n_channels} channels, got {arr.shape[1]}")

        if self._zi is None:
            zi_unit = sosfilt_zi(self.sos)  # (n_sections, 2)
            self._zi = zi_unit[:, :, np.newaxis] * arr[0:1, :]

        filtered, self._zi = sosfilt(self.sos, arr, axis=0, zi=self._zi)
        return filtered


def compute_bandpowers(
    epoch: np.ndarray,
    sfreq: float,
    bands: dict[str, tuple[float, float]] | None = None,
    relative: bool = False,
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Compute Welch PSD bandpowers for an epoch of shape (n_samples, n_channels).

    Returns
    -------
    band_powers : dict[str, np.ndarray]
        If `relative=False`, log10 bandpower (dB-like log10 uV^2) per channel.
        If `relative=True`, fraction of total power in [1, 45] Hz per channel.
    freqs : np.ndarray
        Welch frequency bins (Hz).
    psd : np.ndarray
        Power spectral density of shape (n_freqs, n_channels).
    """
    use_bands = bands or BANDS
    data = np.asarray(epoch, dtype=np.float64)
    if data.ndim == 1:
        data = data[:, np.newaxis]
    n_samples = data.shape[0]
    if n_samples < 16:
        raise ValueError(f"Epoch too short ({n_samples} samples) for spectral estimation.")

    nperseg = min(n_samples, int(round(sfreq)))
    nperseg = max(16, nperseg)
    freqs, psd = welch(
        data,
        fs=sfreq,
        window="hann",
        nperseg=nperseg,
        noverlap=nperseg // 2,
        detrend="constant",
        axis=0,
    )
    df = float(freqs[1] - freqs[0]) if len(freqs) > 1 else 1.0
    eps = 1e-12

    total_mask = (freqs >= 1.0) & (freqs <= min(45.0, 0.5 * sfreq))
    total_power = np.maximum(np.sum(psd[total_mask], axis=0) * df, eps)

    out: dict[str, np.ndarray] = {}
    for name, (fmin, fmax) in use_bands.items():
        mask = (freqs >= fmin) & (freqs < fmax)
        if not np.any(mask):
            idx = int(np.argmin(np.abs(freqs - 0.5 * (fmin + fmax))))
            raw_power = psd[idx] * df
        else:
            raw_power = np.sum(psd[mask], axis=0) * df
        if relative:
            out[name] = np.maximum(raw_power, 0.0) / total_power
        else:
            out[name] = np.log10(np.maximum(raw_power, eps))

    return out, freqs, psd


def extract_epoch_features(
    epoch: np.ndarray,
    sfreq: float,
    bands: dict[str, tuple[float, float]] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Extract concatenated log-bandpower + alpha/theta & alpha/beta ratios per channel."""
    use_bands = bands or BANDS
    log_bp, _, _ = compute_bandpowers(epoch, sfreq=sfreq, bands=use_bands, relative=False)
    n_channels = epoch.shape[1] if epoch.ndim == 2 else 1

    feats: list[np.ndarray] = []
    names: list[str] = []
    for band_name in use_bands:
        vals = log_bp[band_name]
        feats.append(vals)
        names.extend([f"{band_name}_ch{ch}" for ch in range(n_channels)])

    if "alpha" in log_bp and "theta" in log_bp:
        feats.append(log_bp["alpha"] - log_bp["theta"])
        names.extend([f"log_alpha_over_theta_ch{ch}" for ch in range(n_channels)])
    if "alpha" in log_bp and "beta" in log_bp:
        feats.append(log_bp["alpha"] - log_bp["beta"])
        names.extend([f"log_alpha_over_beta_ch{ch}" for ch in range(n_channels)])

    return np.concatenate(feats, axis=0), names


def slice_epochs(
    signal: np.ndarray,
    sfreq: float,
    epoch_sec: float = 1.0,
    step_sec: float = 0.25,
) -> np.ndarray:
    """Slice continuous (n_samples, n_channels) signal into (n_epochs, n_channels, n_win)."""
    arr = np.asarray(signal, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    n_win = int(round(epoch_sec * sfreq))
    n_step = max(1, int(round(step_sec * sfreq)))
    if arr.shape[0] < n_win:
        raise ValueError(
            f"Signal has {arr.shape[0]} samples, fewer than one {epoch_sec}s epoch ({n_win} samples)."
        )

    starts = range(0, arr.shape[0] - n_win + 1, n_step)
    epochs = np.stack([arr[s : s + n_win, :].T for s in starts], axis=0)
    return epochs
