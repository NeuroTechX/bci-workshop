#!/usr/bin/env python3
"""Exercise 01: Real-Time Spectral Neurofeedback (Berger Alpha & Artifact Lab).

Connects to any LSL EEG stream (mock_eeg_stream, replay_eeg_stream, muselsl, BrainFlow,
PiEEG, OpenBCI, etc.), applies causal mains notch + 1-45 Hz bandpass filtering, and plots:
  1. Multi-channel filtered EEG traces (observe eye blinks & jaw clench EMG vs. clean EEG)
  2. Live 5-band Welch PSD relative bandpower bars (Delta, Theta, Alpha, Beta, Gamma)
  3. Rolling 30-second Relative Alpha (8-12 Hz) neurofeedback curve (Eyes Open vs. Closed)
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bci_workshop.dsp import BANDS, compute_bandpowers  # noqa: E402
from bci_workshop.lsl_buffer import EEGStreamBuffer  # noqa: E402


def select_alpha_indices(ch_names: list[str]) -> list[int]:
    preferred = {"TP9", "TP10", "O1", "O2", "OZ", "PO7", "PO8", "PO3", "PO4", "P7", "P8", "PZ", "TP7", "TP8"}
    hits = [i for i, name in enumerate(ch_names) if name.upper() in preferred]
    return hits if hits else list(range(len(ch_names)))


def run_headless(buf: EEGStreamBuffer, window_sec: float, duration_sec: float, alpha_idx: list[int]) -> None:
    print(
        f"[Neurofeedback Headless] Stream='{buf.stream_name}' ({buf.n_channels} ch @ {buf.sfreq:.0f} Hz), "
        f"alpha channels={[buf.ch_names[i] for i in alpha_idx]}"
    )
    t_start = time.monotonic()
    while time.monotonic() - t_start < duration_sec:
        time.sleep(0.25)
        buf.pull()
        if buf.total_samples_seen < int(window_sec * buf.sfreq):
            continue
        epoch = buf.get_latest_window(window_sec, filtered=True)
        rel_bp, _, _ = compute_bandpowers(epoch, sfreq=buf.sfreq, relative=True)
        alpha_pct = 100.0 * float(np.mean(rel_bp["alpha"][alpha_idx]))
        theta_pct = 100.0 * float(np.mean(rel_bp["theta"][alpha_idx]))
        beta_pct = 100.0 * float(np.mean(rel_bp["beta"][alpha_idx]))
        bar = "#" * min(30, int(round(alpha_pct * 0.6)))
        elapsed = time.monotonic() - t_start
        print(
            f"  [{elapsed:5.1f}s] Rel Alpha (8-12 Hz): {alpha_pct:5.1f}% | Theta: {theta_pct:4.1f}% | "
            f"Beta: {beta_pct:4.1f}%  {bar}"
        )


def run_gui(buf: EEGStreamBuffer, window_sec: float, duration_sec: float, alpha_idx: list[int]) -> None:
    import matplotlib.pyplot as plt

    plt.rcParams["toolbar"] = "None"
    fig = plt.figure(figsize=(12, 6.5), facecolor="#F7F5F0")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.45, 1.0], hspace=0.36, wspace=0.25)
    ax_eeg = fig.add_subplot(gs[:, 0], facecolor="#FFFFFF")
    ax_bars = fig.add_subplot(gs[0, 1], facecolor="#FFFFFF")
    ax_nf = fig.add_subplot(gs[1, 1], facecolor="#FFFFFF")

    trace_sec = 5.0
    n_trace = int(round(trace_sec * buf.sfreq))
    t_axis = np.linspace(-trace_sec, 0.0, n_trace)
    spacing_uv = 80.0
    n_show = min(buf.n_channels, 8)

    lines = []
    offsets = np.arange(n_show)[::-1] * spacing_uv
    for ch_i in range(n_show):
        (ln,) = ax_eeg.plot(t_axis, np.zeros(n_trace) + offsets[ch_i], lw=1.0, color="#1D2229")
        lines.append(ln)
    ax_eeg.set_yticks(offsets)
    ax_eeg.set_yticklabels(buf.ch_names[:n_show])
    ax_eeg.set_xlim(-trace_sec, 0.0)
    ax_eeg.set_ylim(-spacing_uv, offsets[0] + spacing_uv)
    ax_eeg.set_xlabel("Time (s)")
    ax_eeg.set_title(f"Filtered Live EEG ({buf.stream_name}, {buf.sfreq:.0f} Hz)", fontweight="bold")

    band_names = list(BANDS.keys())
    bar_colors = ["#8E9AAF", "#535C67", "#0B6B70", "#2A9D8F", "#CFC8BA"]
    bars = ax_bars.bar(band_names, [0.2] * len(band_names), color=bar_colors)
    ax_bars.set_ylim(0.0, 0.75)
    ax_bars.set_ylabel("Relative Power")
    ax_bars.set_title(f"Welch Bandpower ({', '.join(buf.ch_names[i] for i in alpha_idx)})", fontweight="bold")

    history_len = 150  # ~30s @ 5 Hz UI refresh
    alpha_hist: collections.deque[float] = collections.deque([0.0] * history_len, maxlen=history_len)
    x_hist = np.linspace(-30.0, 0.0, history_len)
    (nf_line,) = ax_nf.plot(x_hist, list(alpha_hist), lw=2.0, color="#0B6B70")
    thresh_line = ax_nf.axhline(25.0, ls="--", lw=1.0, color="#535C67", label="Baseline median")
    ax_nf.set_xlim(-30.0, 0.0)
    ax_nf.set_ylim(0.0, 75.0)
    ax_nf.set_xlabel("Time (s)")
    ax_nf.set_ylabel("Rel. Alpha (%)")
    ax_nf.set_title("Neurofeedback Metric: Eyes-Closed 8-12 Hz Alpha", fontweight="bold")
    ax_nf.legend(loc="upper left", frameon=False, fontsize=8)

    plt.ion()
    plt.show(block=False)
    print("[Exercise 01] Try blinking, clenching your jaw, then closing your eyes for 10s! Close window or Ctrl+C to exit.")

    t_start = time.monotonic()
    try:
        while plt.fignum_exists(fig.number):
            if duration_sec > 0 and (time.monotonic() - t_start) >= duration_sec:
                break
            buf.pull()
            if buf.total_samples_seen >= int(window_sec * buf.sfreq):
                trace = buf.get_latest_window(trace_sec, filtered=True)
                if len(trace) == n_trace:
                    for ch_i in range(n_show):
                        lines[ch_i].set_ydata(trace[:, ch_i] + offsets[ch_i])

                epoch = buf.get_latest_window(window_sec, filtered=True)
                rel_bp, _, _ = compute_bandpowers(epoch, sfreq=buf.sfreq, relative=True)
                for b_rect, b_name in zip(bars, band_names):
                    b_rect.set_height(float(np.mean(rel_bp[b_name][alpha_idx])))

                alpha_pct = 100.0 * float(np.mean(rel_bp["alpha"][alpha_idx]))
                alpha_hist.append(alpha_pct)
                nf_line.set_ydata(list(alpha_hist))
                nonzero = [v for v in alpha_hist if v > 0.0]
                if len(nonzero) >= 10:
                    thresh_line.set_ydata([float(np.median(nonzero))] * 2)

            fig.canvas.draw_idle()
            plt.pause(0.18)
    except KeyboardInterrupt:
        pass
    finally:
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream-name", default=None, help="Connect to a specific LSL stream name")
    parser.add_argument("--mains", type=float, default=60.0, choices=[50.0, 60.0], help="Power-line notch Hz (50 or 60)")
    parser.add_argument("--window", type=float, default=2.0, help="Welch PSD sliding window length in seconds")
    parser.add_argument("--duration", type=float, default=0.0, help="Stop after N seconds (0 = until closed)")
    parser.add_argument("--headless", action="store_true", help="Print live bandpower meter in terminal without GUI")
    args = parser.parse_args()

    buf = EEGStreamBuffer(stream_name=args.stream_name, mains_hz=args.mains)
    alpha_idx = select_alpha_indices(buf.ch_names)
    try:
        if args.headless:
            run_headless(buf, window_sec=args.window, duration_sec=args.duration or 12.0, alpha_idx=alpha_idx)
        else:
            run_gui(buf, window_sec=args.window, duration_sec=args.duration, alpha_idx=alpha_idx)
    finally:
        buf.close()


if __name__ == "__main__":
    main()
