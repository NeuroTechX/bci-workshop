#!/usr/bin/env python3
"""Exercise 02: Calibrated Live Binary Brain-Computer Interface.

Records two mental/physiological states over LSL (e.g., Eyes Open vs. Eyes Closed, or
Left vs. Right Motor Imagery on multi-channel caps), trains a leak-free decoder:
  - `lda` (Welch PSD + Ledoit-Wolf Shrinkage LDA — default)
  - `logreg` / `svm`
  - `riemann-mdm` / `riemann-ts` (OAS Spatial Covariance + Riemannian Geometry via pyRiemann)

Prints BOTH honest contiguous-block accuracy and naive overlapping-window accuracy so
participants see why proper temporal splitting matters, then streams smoothed live
probabilities onto LSL (`BCI_Decisions`) and UDP JSON (`127.0.0.1:5005`).
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import socket
import sys
import time
import uuid

import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bci_workshop.audio import play_cue  # noqa: E402
from bci_workshop.classifier import evaluate_bci_dataset  # noqa: E402
from bci_workshop.lsl_buffer import EEGStreamBuffer  # noqa: E402


def prompt_or_auto(label: str, auto: bool, delay: float = 0.5) -> None:
    if auto:
        print(f"\n[Auto-Calibration] Starting '{label}' in {delay:.1f}s...")
        time.sleep(delay)
    else:
        input(f"\n>>> Press ENTER when ready to record {label} <<< ")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clf",
        default="lda",
        choices=["lda", "logreg", "svm", "riemann-mdm", "riemann-ts"],
        help="Decoding pipeline (default: lda; try riemann-mdm with 4+ channels!)",
    )
    parser.add_argument("--stream-name", default=None, help="Specific LSL stream name")
    parser.add_argument("--mains", type=float, default=60.0, choices=[50.0, 60.0], help="Mains notch frequency (Hz)")
    parser.add_argument("--cal-seconds", type=float, default=16.0, help="Calibration duration per class (seconds)")
    parser.add_argument("--epoch-sec", type=float, default=1.0, help="Decoding epoch length (seconds)")
    parser.add_argument("--step-sec", type=float, default=0.2, help="Online step interval (seconds)")
    parser.add_argument("--smooth", type=int, default=5, help="Moving-average smoothing over N predictions")
    parser.add_argument("--udp-port", type=int, default=5005, help="Local UDP JSON output port (0 to disable)")
    parser.add_argument("--live-seconds", type=float, default=0.0, help="Stop live loop after N seconds (0 = infinite)")
    parser.add_argument("--auto-cue", action="store_true", help="Skip interactive Enter prompts (for mock/CI runs)")
    parser.add_argument("--mute", action="store_true", help="Silence audio cue tones")
    args = parser.parse_args()

    buf = EEGStreamBuffer(stream_name=args.stream_name, mains_hz=args.mains)
    print(f"[BCI v2.0] Connected to '{buf.stream_name}' ({buf.n_channels} ch {buf.ch_names} @ {buf.sfreq:.0f} Hz)")
    print(f"[BCI v2.0] Selected pipeline: {args.clf}")

    try:
        # Warm up causal filter state
        time.sleep(0.4)
        buf.pull()

        prompt_or_auto(f"CLASS 0 (Baseline / Eyes Open, {args.cal_seconds:.0f}s)", auto=args.auto_cue)
        play_cue(freq_hz=520.0, mute=args.mute)
        print(f"  Recording Class 0 for {args.cal_seconds:.1f}s...")
        rec_c0 = buf.record_segment(args.cal_seconds, filtered=True)
        play_cue(freq_hz=440.0, mute=args.mute)
        print(f"  Captured {len(rec_c0)} samples ({len(rec_c0)/buf.sfreq:.1f}s).")

        prompt_or_auto(f"CLASS 1 (Task / Eyes Closed Alpha, {args.cal_seconds:.0f}s)", auto=args.auto_cue, delay=1.0)
        play_cue(freq_hz=780.0, mute=args.mute)
        print(f"  Recording Class 1 for {args.cal_seconds:.1f}s...")
        rec_c1 = buf.record_segment(args.cal_seconds, filtered=True)
        play_cue(freq_hz=440.0, mute=args.mute)
        print(f"  Captured {len(rec_c1)} samples ({len(rec_c1)/buf.sfreq:.1f}s).")

        pipeline, summary = evaluate_bci_dataset(
            rec_c0,
            rec_c1,
            sfreq=buf.sfreq,
            kind=args.clf,
            epoch_sec=args.epoch_sec,
            step_sec=args.step_sec,
        )

        print("\n=== Calibration & Leakage Audit ===")
        print(f"  Total epochs trained          : {summary.n_epochs_total}")
        print(f"  Training resubstitution score : {summary.train_resubstitution_acc * 100:5.1f}%  (legacy 2017 metric — optimistic!)")
        print(f"  Naive random CV (80% overlap) : {summary.naive_overlap_random_acc * 100:5.1f}%  (inflated by window bleed)")
        print(f"  Contiguous temporal block CV  : {summary.contiguous_block_acc * 100:5.1f}%  <-- Honest generalization estimate")

        # Set up LSL + UDP output buses for downstream hackathon apps
        out_info = StreamInfo(
            name="BCI_Decisions",
            type="Markers",
            channel_count=2,
            nominal_srate=1.0 / args.step_sec,
            channel_format="float32",
            source_id=f"ntx-bci-out-{uuid.uuid4().hex[:6]}",
        )
        lsl_out = StreamOutlet(out_info)
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if args.udp_port > 0 else None

        prob_hist: collections.deque[float] = collections.deque(maxlen=max(1, args.smooth))
        print(
            f"\n=== Live BCI Decoding (LSL 'BCI_Decisions' + UDP 127.0.0.1:{args.udp_port}) ===\n"
            "Press Ctrl+C to stop."
        )

        buf.flush()
        t_live = time.monotonic()
        while True:
            if args.live_seconds > 0 and (time.monotonic() - t_live) >= args.live_seconds:
                break
            time.sleep(args.step_sec)
            buf.pull()
            epoch = buf.get_latest_window(args.epoch_sec, filtered=True)
            X_live = epoch.T[np.newaxis, :, :]  # (1, n_ch, n_times)

            if hasattr(pipeline, "predict_proba"):
                p1 = float(pipeline.predict_proba(X_live)[0, 1])
            else:
                p1 = float(pipeline.predict(X_live)[0])

            prob_hist.append(p1)
            p_smooth = float(np.mean(prob_hist))
            pred_cls = int(p_smooth >= 0.5)

            lsl_out.push_sample([float(pred_cls), p_smooth], local_clock())
            if udp_sock is not None:
                payload = json.dumps(
                    {"class": pred_cls, "prob_class1": round(p_smooth, 4), "clf": args.clf, "ts": time.time()}
                ).encode("utf-8")
                udp_sock.sendto(payload, ("127.0.0.1", args.udp_port))

            gauge_pos = int(round(p_smooth * 24))
            meter = "".join("|" if i == 12 else ("#" if i < gauge_pos else ".") for i in range(25))
            label_str = "CLASS 1 (Active)" if pred_cls == 1 else "CLASS 0 (Rest)  "
            print(f"  [{meter}] P(Class 1)={p_smooth:5.2f} -> {label_str}")
    except KeyboardInterrupt:
        print("\n[BCI v2.0] Live session ended.")
    finally:
        buf.close()


if __name__ == "__main__":
    main()
