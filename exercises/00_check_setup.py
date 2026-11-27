#!/usr/bin/env python3
"""Exercise 00: 30-second pre-workshop setup, audio, DSP, and LSL stream health check."""

from __future__ import annotations

import argparse
import importlib
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bci_workshop.audio import generate_beep_wav  # noqa: E402
from bci_workshop.lsl_buffer import EEGStreamBuffer  # noqa: E402
from bci_workshop.profiles import DEVICE_PROFILES  # noqa: E402


def check_packages() -> None:
    core = ["numpy", "scipy", "sklearn", "matplotlib", "pylsl"]
    optional = ["pyriemann", "mne", "mne_lsl", "brainflow", "muselsl", "timeflux"]

    print("=== 1. Python Environment ===")
    print(f"  Python: {sys.version.split()[0]} ({sys.executable})")
    missing_core: list[str] = []
    for mod in core:
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "installed")
            print(f"  [OK] {mod:<12} {ver}")
        except ImportError:
            print(f"  [MISSING] {mod}")
            missing_core.append(mod)

    print("\n=== 2. Optional Ecosystem Modules ===")
    for mod in optional:
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "installed")
            print(f"  [OK] {mod:<12} {ver}")
        except ImportError:
            print(f"  [--] {mod:<12} (optional)")

    if missing_core:
        raise SystemExit(f"\nMissing core packages: {', '.join(missing_core)}. Run `uv sync` or `pip install -e .`.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Spawn a temporary local mock EEG LSL stream if none is currently running",
    )
    parser.add_argument("--list-targets", action="store_true", help="List all 18 built-in EEG/biosignal profiles")
    args = parser.parse_args()

    if args.list_targets:
        print(f"{'Profile':<20} {'Rate':<8} {'Ch':<4} {'Tier & Name'}")
        print("-" * 78)
        for key, prof in DEVICE_PROFILES.items():
            print(f"{key:<20} {prof.sfreq:>5.0f} Hz {len(prof.channels):>3}  [{prof.tier}] {prof.name}")
        return

    check_packages()

    wav_path = generate_beep_wav()
    print(f"\n=== 3. Audio Cue Generator ===\n  [OK] Valid RIFF WAV cue written to {wav_path}")

    print("\n=== 4. Lab Streaming Layer (LSL) Discovery ===")
    mock_proc: subprocess.Popen[bytes] | None = None
    try:
        from pylsl import resolve_byprop

        streams = resolve_byprop("type", "EEG", timeout=2.0)
        if not streams and args.self_test:
            print("  No external EEG stream detected; launching temporary mock_eeg_stream.py for self-test...")
            mock_proc = subprocess.Popen(
                [sys.executable, str(ROOT / "streams" / "mock_eeg_stream.py"), "--duration", "6"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.2)

        buf = EEGStreamBuffer(timeout_sec=3.0)
        time.sleep(0.5)
        n_read = buf.pull(timeout=0.5)
        print(
            f"  [OK] Connected to '{buf.stream_name}' | {buf.n_channels} ch {buf.ch_names} @ {buf.sfreq:.0f} Hz "
            f"(pulled {n_read} live samples)"
        )
        buf.close()
    except RuntimeError as exc:
        print(f"  [INFO] {exc}")
        if args.self_test:
            raise SystemExit(1) from exc
    finally:
        if mock_proc is not None:
            mock_proc.terminate()
            mock_proc.wait(timeout=3)

    print(
        "\n=== 5. Electrical Safety & Consent Check ===\n"
        "  * If using DIY / wired boards (PiEEG, BioAmp, OpenBCI USB, FreeEEG32, icibici),\n"
        "    UNPLUG your laptop's AC wall charger (run strictly on battery or medical USB isolator).\n"
        "  * Never record another participant's brain/muscle signals without explicit consent.\n"
        "  * Full guide: https://neurotechx.org/safety-and-ethics\n\n"
        "Ready for Exercise 01 (`python exercises/01_neurofeedback.py`)!"
    )


if __name__ == "__main__":
    main()
