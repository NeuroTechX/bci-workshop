#!/usr/bin/env python3
"""Universal BrainFlow -> Lab Streaming Layer (LSL) bridge for NeuroTechX workshops.

Unlocks 10+ EEG boards with the exact same workshop exercises:
  - brainflow-synthetic (zero hardware test)
  - muse2, museS, museS-athena (native OS BLE, no BLED112 dongle needed!)
  - ganglion, cyton, cyton-daisy (OpenBCI)
  - freeeeg32 (32-ch open hardware)
  - crown (Neurosity), brainbit, unicorn (g.tec)

Example:
    python streams/brainflow_to_lsl.py --profile muse2
    python streams/brainflow_to_lsl.py --profile cyton --serial-port /dev/cu.usbserial-DM00XXXX
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import time
import uuid

from pylsl import StreamInfo, StreamOutlet, local_clock

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bci_workshop.profiles import DEVICE_PROFILES, get_profile  # noqa: E402


def main() -> None:
    bf_keys = sorted(k for k, p in DEVICE_PROFILES.items() if p.brainflow_board)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="brainflow-synthetic", choices=bf_keys, help="Hardware profile")
    parser.add_argument("--serial-port", default="", help="Serial port (Cyton, FreeEEG32, BLED112)")
    parser.add_argument("--mac-address", default="", help="Optional BLE MAC address")
    parser.add_argument("--serial-number", default="", help="Optional device serial number (Unicorn/BrainBit)")
    parser.add_argument("--name", default="", help="Override LSL stream name")
    args = parser.parse_args()

    try:
        from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit(
            "BrainFlow is not installed. Install hardware extras with:\n  uv pip install 'brainflow>=5.12'"
        ) from exc

    profile = get_profile(args.profile)
    assert profile.brainflow_board is not None
    if not hasattr(BoardIds, profile.brainflow_board):
        raise SystemExit(
            f"Your installed BrainFlow version does not yet include BoardIds.{profile.brainflow_board}. "
            "Upgrade with: uv pip install -U brainflow"
        )

    board_id = getattr(BoardIds, profile.brainflow_board).value
    params = BrainFlowInputParams()
    if args.serial_port:
        params.serial_port = args.serial_port
    if args.mac_address:
        params.mac_address = args.mac_address
    if args.serial_number:
        params.serial_number = args.serial_number

    eeg_channels = BoardShim.get_eeg_channels(board_id)
    sfreq = float(BoardShim.get_sampling_rate(board_id))
    try:
        ch_names = BoardShim.get_eeg_names(board_id)
    except Exception:
        ch_names = list(profile.channels[: len(eeg_channels)])

    stream_name = args.name or f"NTX-{profile.key}"
    info = StreamInfo(
        name=stream_name,
        type="EEG",
        channel_count=len(eeg_channels),
        nominal_srate=sfreq,
        channel_format="float32",
        source_id=f"ntx-bf-{profile.key}-{uuid.uuid4().hex[:6]}",
    )
    chns = info.desc().append_child("channels")
    for label in ch_names:
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("unit", "microvolts")
        ch.append_child_value("type", "EEG")
    outlet = StreamOutlet(info, chunk_size=16, max_buffered=60)

    BoardShim.enable_dev_board_logger()
    board = BoardShim(board_id, params)
    print(f"[BrainFlow -> LSL] Preparing {profile.name} (board_id={board_id})...")
    board.prepare_session()
    board.start_stream(45000)
    print(f"[BrainFlow -> LSL] Streaming '{stream_name}' ({len(eeg_channels)} ch @ {sfreq:.0f} Hz). Ctrl+C to stop.")

    try:
        while True:
            data = board.get_board_data()  # drains all new samples since last call
            if data.shape[1] > 0:
                eeg_chunk = data[eeg_channels, :].T.astype("float32")
                outlet.push_chunk(eeg_chunk.tolist(), local_clock())
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\n[BrainFlow -> LSL] Stopping session...")
    finally:
        try:
            board.stop_stream()
            board.release_session()
        except Exception:
            pass


if __name__ == "__main__":
    main()
