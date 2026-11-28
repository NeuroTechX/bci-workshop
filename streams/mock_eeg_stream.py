#!/usr/bin/env python3
"""Zero-hardware realistic LSL EEG simulator for NeuroTechX workshops.

Generates 4-channel (default: TP9, AF7, AF8, TP10 @ 256 Hz) or N-channel EEG with:
  - 1/f pink background activity (~10 uV RMS)
  - Alternating 'EYES_OPEN' (low posterior alpha) and 'EYES_CLOSED' (strong ~10 Hz Berger
    alpha on posterior/temporal channels TP9/TP10 + spatial covariance shift)
  - Occasional realistic frontal eye-blink deflections on AF7/AF8

Run in Terminal 1:
    python streams/mock_eeg_stream.py
Then run Exercise 00, 01, or 02 (or Timeflux) in Terminal 2!
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import time
import uuid

import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bci_workshop.profiles import get_profile  # noqa: E402


def create_eeg_outlet(
    stream_name: str,
    channels: tuple[str, ...],
    sfreq: float,
    source_id: str | None = None,
) -> StreamOutlet:
    info = StreamInfo(
        name=stream_name,
        type="EEG",
        channel_count=len(channels),
        nominal_srate=sfreq,
        channel_format="float32",
        source_id=source_id or f"ntx-mock-{uuid.uuid4().hex[:8]}",
    )
    chns = info.desc().append_child("channels")
    for label in channels:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("unit", "microvolts")
        ch.append_child_value("type", "EEG")
    return StreamOutlet(info, chunk_size=16, max_buffered=60)


def create_marker_outlet(stream_name: str = "NTX_Mock_Markers") -> StreamOutlet:
    info = StreamInfo(
        name=stream_name,
        type="Markers",
        channel_count=1,
        nominal_srate=0.0,
        channel_format="string",
        source_id=f"ntx-markers-{uuid.uuid4().hex[:8]}",
    )
    return StreamOutlet(info)


def synthesize_chunk(
    t_vec: np.ndarray,
    channels: tuple[str, ...],
    alpha_channels: tuple[str, ...],
    eyes_closed: bool,
    rng: np.random.Generator,
    pink_state: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate (n_samples, n_channels) microvolt EEG chunk with stateful AR(1) 1/f noise."""
    n_samples = len(t_vec)
    n_ch = len(channels)
    out = np.zeros((n_samples, n_ch), dtype=np.float32)

    # Stateful AR(1) approximation to 1/f drift + broadband cortical background
    for i in range(n_samples):
        pink_state[:] = 0.965 * pink_state + rng.normal(0.0, 3.2, size=n_ch)
        out[i] = pink_state

    # Shared cortical rhythms + posterior 10 Hz Berger alpha modulation
    alpha_amp = 22.0 if eyes_closed else 4.0
    beta_amp = 4.5 if not eyes_closed else 2.5
    theta_wave = 5.0 * np.sin(2.0 * np.pi * 6.0 * t_vec)
    alpha_wave = alpha_amp * np.sin(2.0 * np.pi * 10.2 * t_vec + 0.3)
    beta_wave = beta_amp * np.sin(2.0 * np.pi * 20.5 * t_vec + 1.1)

    for ch_idx, ch_name in enumerate(channels):
        is_alpha_site = ch_name in alpha_channels
        alpha_gain = 1.0 if is_alpha_site else 0.28
        beta_gain = 0.65 if is_alpha_site else 1.0
        out[:, ch_idx] += (theta_wave + alpha_gain * alpha_wave + beta_gain * beta_wave).astype(np.float32)

        # Occasional frontal eye blink on AF / Fp channels during eyes open
        if not eyes_closed and ch_name.upper().startswith(("AF", "FP")) and rng.random() < 0.015:
            peak = rng.integers(0, n_samples)
            width = max(3, n_samples // 2)
            idx = np.arange(n_samples)
            blink = 85.0 * np.exp(-0.5 * ((idx - peak) / width) ** 2)
            out[:, ch_idx] += blink.astype(np.float32)

    # Small 60 Hz mains hum so students can observe the online notch filter working
    mains_hum = 3.0 * np.sin(2.0 * np.pi * 60.0 * t_vec)[:, np.newaxis]
    out += mains_hum.astype(np.float32)
    return out, pink_state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="mock", help="Device channel profile to emulate (default: mock)")
    parser.add_argument("--name", default="NTX-MockEEG", help="LSL stream name")
    parser.add_argument(
        "--state-period",
        type=float,
        default=10.0,
        help="Seconds per alternating EYES_OPEN / EYES_CLOSED state (default: 10s)",
    )
    parser.add_argument("--duration", type=float, default=0.0, help="Stop after N seconds (0 = run until Ctrl+C)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    profile = get_profile(args.profile)
    outlet = create_eeg_outlet(args.name, profile.channels, profile.sfreq)
    marker_outlet = create_marker_outlet()

    rng = np.random.default_rng(args.seed)
    pink_state = np.zeros(len(profile.channels), dtype=np.float64)
    chunk_samples = max(4, int(round(profile.sfreq * 0.04)))  # ~25 chunks/sec
    dt = chunk_samples / profile.sfreq

    print(
        f"[NTX Mock EEG] Streaming '{args.name}' | {len(profile.channels)} ch {profile.channels} @ {profile.sfreq:.0f} Hz"
    )
    print(
        f"[NTX Mock EEG] Alternating EYES_OPEN / EYES_CLOSED every {args.state_period:.1f}s "
        f"(posterior alpha boost on {profile.alpha_channels}). Press Ctrl+C to stop."
    )

    t0 = time.monotonic()
    sample_cursor = 0
    last_state: bool | None = None

    try:
        while True:
            elapsed = time.monotonic() - t0
            if args.duration > 0 and elapsed >= args.duration:
                break

            target_samples = int(elapsed * profile.sfreq)
            if target_samples - sample_cursor < chunk_samples:
                time.sleep(max(0.002, dt * 0.5))
                continue

            phase = int(elapsed // max(1.0, args.state_period)) % 2
            eyes_closed = bool(phase == 1)
            if eyes_closed != last_state:
                label = "EYES_CLOSED (High 10 Hz Alpha)" if eyes_closed else "EYES_OPEN (Baseline)"
                marker_outlet.push_sample([label], local_clock())
                print(f"  [{elapsed:6.1f}s] State -> {label}")
                last_state = eyes_closed

            t_vec = (sample_cursor + np.arange(chunk_samples)) / profile.sfreq
            chunk, pink_state = synthesize_chunk(
                t_vec=t_vec,
                channels=profile.channels,
                alpha_channels=profile.alpha_channels,
                eyes_closed=eyes_closed,
                rng=rng,
                pink_state=pink_state,
            )
            outlet.push_chunk(chunk.tolist(), local_clock())
            sample_cursor += chunk_samples
    except KeyboardInterrupt:
        print("\n[NTX Mock EEG] Stopped cleanly.")


if __name__ == "__main__":
    main()
