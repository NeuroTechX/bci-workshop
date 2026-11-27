#!/usr/bin/env python3
"""Replay a recorded EEG file (.fif, .edf, or .csv) over LSL for hardware-free workshops.

Uses `mne-lsl`'s `PlayerLSL` when installed, and falls back to `mne` / `numpy` + `pylsl`
so chapters can replay any pre-recorded session identically to live hardware.
"""

from __future__ import annotations

import argparse
import pathlib
import time
import uuid

import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock


def load_recording(path: pathlib.Path, default_sfreq: float = 256.0) -> tuple[np.ndarray, list[str], float]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
        raw_arr = np.loadtxt(path, delimiter=",", skiprows=1, dtype=np.float32)
        if raw_arr.ndim == 1:
            raw_arr = raw_arr[:, np.newaxis]
        # Drop leading timestamp column if detected
        if header and header[0].strip().lower() in ("time", "timestamp", "timestamps"):
            ch_names = [c.strip() for c in header[1:]]
            diffs = np.diff(raw_arr[: min(500, len(raw_arr)), 0])
            median_dt = float(np.median(diffs[diffs > 0])) if np.any(diffs > 0) else (1.0 / default_sfreq)
            sfreq = round(1.0 / median_dt) if median_dt > 0 else default_sfreq
            data = raw_arr[:, 1:]
        else:
            ch_names = [c.strip() for c in header] if len(header) == raw_arr.shape[1] else [
                f"Ch{i+1}" for i in range(raw_arr.shape[1])
            ]
            sfreq = default_sfreq
            data = raw_arr
        return data, ch_names, float(sfreq)

    import mne

    raw = mne.io.read_raw(str(path), preload=True, verbose="ERROR")
    raw.pick("eeg")
    # Convert Volts -> microvolts for consistent workshop visualization
    data_uv = (raw.get_data().T * 1e6).astype(np.float32)
    return data_uv, list(raw.ch_names), float(raw.info["sfreq"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=pathlib.Path, help="Path to .fif, .edf, .bdf, .vhdr, or .csv EEG file")
    parser.add_argument("--name", default="NTX-ReplayEEG", help="LSL stream name")
    parser.add_argument("--sfreq", type=float, default=256.0, help="Fallback sampling rate for headerless CSVs")
    parser.add_argument("--no-loop", action="store_true", help="Exit at end of file instead of looping")
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"File not found: {args.file}")

    # Prefer mne_lsl.player.PlayerLSL for MNE formats when installed and looping
    if args.file.suffix.lower() != ".csv" and not args.no_loop:
        try:
            from mne_lsl.player import PlayerLSL  # type: ignore[import-not-found]

            print(f"[NTX Replay] Starting mne-lsl PlayerLSL for {args.file.name} as '{args.name}'...")
            with PlayerLSL(str(args.file), chunk_size=16, name=args.name):
                print("[NTX Replay] Streaming live. Press Ctrl+C to stop.")
                while True:
                    time.sleep(0.5)
        except ImportError:
            pass
        except KeyboardInterrupt:
            print("\n[NTX Replay] Stopped.")
            return

    data, ch_names, sfreq = load_recording(args.file, default_sfreq=args.sfreq)
    info = StreamInfo(
        name=args.name,
        type="EEG",
        channel_count=len(ch_names),
        nominal_srate=sfreq,
        channel_format="float32",
        source_id=f"ntx-replay-{uuid.uuid4().hex[:8]}",
    )
    chns = info.desc().append_child("channels")
    for label in ch_names:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("unit", "microvolts")
        ch.append_child_value("type", "EEG")
    outlet = StreamOutlet(info, chunk_size=16, max_buffered=60)

    chunk_len = max(4, int(round(sfreq * 0.04)))
    print(f"[NTX Replay] Streaming '{args.name}' from {args.file.name} ({len(ch_names)} ch @ {sfreq:.0f} Hz)")
    cursor = 0
    t0 = time.monotonic()
    sent = 0
    try:
        while True:
            elapsed = time.monotonic() - t0
            if int(elapsed * sfreq) - sent < chunk_len:
                time.sleep(0.01)
                continue
            end = cursor + chunk_len
            if end <= len(data):
                chunk = data[cursor:end]
                cursor = end
            elif args.no_loop:
                break
            else:
                part1 = data[cursor:]
                rem = chunk_len - len(part1)
                chunk = np.vstack([part1, data[:rem]])
                cursor = rem
            outlet.push_chunk(chunk.tolist(), local_clock())
            sent += len(chunk)
    except KeyboardInterrupt:
        print("\n[NTX Replay] Stopped.")


if __name__ == "__main__":
    main()
