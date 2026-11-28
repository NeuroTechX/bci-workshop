#!/usr/bin/env python3
"""Exercise 05: EEG-to-Image Zero-Shot Retrieval (2026 Challenge Track 01 & Alljoined).

Hands-on CPU-friendly lab inspired by Track 01 (Visual Image Decoding) of the 2026
EEG/EMG Foundation Challenge (`neural-interfaces26/2026-competition`, Alljoined-1.6M +
Meta FAIR Brain & AI).

What participants learn in <5 seconds on any laptop (zero GPU required):
  1. Retrieval vs. "Mind Reading": Visual EEG decoding maps stimulus-locked 1.0s epochs
     (`-0.2s` to `+0.8s` @ `120 Hz`, e.g., 32-ch Emotiv `Alljoined-1.6M`) onto vision-model
     embeddings (`DINOv2-giant` in Track 01; `CLIP` in `Alljoined/ENIGMA`) and ranks an
     UNSEEN candidate image gallery via cosine similarity (`Top-1` / `Top-5`).
  2. Why ERP timing matters: Comparing Track 01's `Mean-Ridge` starter (collapsing time)
     against `Spatiotemporal-ERP-Ridge` (preserving P100 / N170 / P300 latency bins).
  3. The Repeat-Averaging SNR Law (`K = 1, 4, 8, 16` repeats): Why single-trial EEG visual
     retrieval is modest, why averaging repeated presentations boosts Top-5 dramatically,
     and why generative reconstructions (`Alljoined/ENIGMA`, arXiv:2602.10361, Appendix A.1)
     average ~80 stimulus repetitions of *viewed* images!

Usage:
  # Run instant synthetic 32-ch @ 120 Hz benchmark (default):
  uv run python exercises/05_eeg_to_image_retrieval.py

  # Or run on a pre-extracted `.npz` shard from Alljoined-1.6M / THINGS-EEG2:
  uv run python exercises/05_eeg_to_image_retrieval.py --npz path/to/alljoined_shard.npz
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bci_workshop.retrieval import (  # noqa: E402
    evaluate_gallery_retrieval,
    extract_visual_eeg_features,
    fit_ridge_image_decoder,
    simulate_visual_erp_dataset,
)


def load_or_simulate(npz_path: str | None, test_repeats: int, seed: int) -> dict[str, np.ndarray]:
    if npz_path is None:
        return simulate_visual_erp_dataset(test_repeats=test_repeats, seed=seed)
    data = dict(np.load(npz_path, allow_pickle=False))
    required = {
        "train_epochs",
        "train_embeddings",
        "test_epochs",
        "test_image_ids",
        "gallery_embeddings",
        "gallery_image_ids",
    }
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"NPZ file {npz_path} is missing required arrays: {sorted(missing)}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--npz",
        default=None,
        help="Optional .npz shard with Alljoined-1.6M / THINGS-EEG2 epochs & DINOv2/CLIP embeddings",
    )
    parser.add_argument("--test-repeats", type=int, default=16, help="Max repeats simulated per unseen test image")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    ds = load_or_simulate(args.npz, test_repeats=args.test_repeats, seed=args.seed)
    X_tr = ds["train_epochs"]
    Y_tr = ds["train_embeddings"]
    X_te = ds["test_epochs"]
    ids_te = ds["test_image_ids"]
    gal_emb = ds["gallery_embeddings"]
    gal_ids = ds["gallery_image_ids"]

    source_desc = args.npz if args.npz else "Synthetic 32-ch @ 120 Hz Visual-ERP Benchmark (Alljoined geometry)"
    chance_top1 = 100.0 / len(gal_ids)
    chance_top5 = min(100.0, 500.0 / len(gal_ids))

    print(f"[EEG->Image] Source       : {source_desc}")
    print(f"[EEG->Image] Train trials : {X_tr.shape} -> target latents {Y_tr.shape}")
    print(
        f"[EEG->Image] Unseen test  : {X_te.shape[0]} trials across {len(gal_ids)} held-out gallery images "
        f"(Chance Top-1: {chance_top1:.1f}%, Top-5: {chance_top5:.1f}%)"
    )

    # 1. Compare Track 01 Mean-Ridge vs. Spatiotemporal ERP Ridge
    mean_model = fit_ridge_image_decoder(X_tr, Y_tr, mode="mean")
    erp_model = fit_ridge_image_decoder(X_tr, Y_tr, mode="spatiotemporal")

    pred_mean = mean_model.predict(extract_visual_eeg_features(X_te, mode="mean"))
    pred_erp = erp_model.predict(extract_visual_eeg_features(X_te, mode="spatiotemporal"))

    m_mean = evaluate_gallery_retrieval(pred_mean, ids_te, gal_emb, gal_ids, max_repeats=args.test_repeats)
    m_erp = evaluate_gallery_retrieval(pred_erp, ids_te, gal_emb, gal_ids, max_repeats=args.test_repeats)

    print("\n=== 1. Feature Representation Comparison (Zero-Shot Unseen Images) ===")
    print(
        f"  Mean-Ridge (Track 01 channel-mean starter) : "
        f"Top-1 = {m_mean.top1_acc * 100:5.1f}% | Top-5 = {m_mean.top5_acc * 100:5.1f}% | Mean Rank = {m_mean.mean_rank:5.1f}/{m_mean.gallery_size}"
    )
    print(
        f"  Spatiotemporal-ERP-Ridge (12 latency bins) : "
        f"Top-1 = {m_erp.top1_acc * 100:5.1f}% | Top-5 = {m_erp.top5_acc * 100:5.1f}% | Mean Rank = {m_erp.mean_rank:5.1f}/{m_erp.gallery_size}"
    )

    # 2. Repeat-averaging SNR curve (single-trial vs multi-repeat pooling)
    print("\n=== 2. Repeat-Averaging SNR Scaling (Spatiotemporal-ERP-Ridge) ===")
    repeat_grid = sorted({k for k in (1, 2, 4, 8, 16, args.test_repeats) if 1 <= k <= args.test_repeats})
    for k in repeat_grid:
        mk = evaluate_gallery_retrieval(pred_erp, ids_te, gal_emb, gal_ids, max_repeats=k, rng_seed=args.seed)
        print(
            f"  K = {k:2d} repeat(s)/image -> Top-1 = {mk.top1_acc * 100:5.1f}% | "
            f"Top-5 = {mk.top5_acc * 100:5.1f}% | Mean Rank = {mk.mean_rank:5.1f}/{mk.gallery_size}"
        )

    print(
        "\n=== Going Further with Real Data & Generative Reconstruction ===\n"
        "  * 2026 Challenge Track 01 (DINOv2-giant Top-5 retrieval on 32-ch Emotiv): https://neural-interfaces26.github.io/\n"
        "  * Alljoined-1.6M Dataset (1.6M+ trials, 20 subjects, NEMAR nm000134 — CC BY-NC-SA 4.0): https://huggingface.co/datasets/Alljoined/Alljoined-1.6M\n"
        "  * Alljoined/ENIGMA (MIT code, CLIP + SDXL Turbo reconstruction; note ~80-repeat averaging in Appendix A.1): https://github.com/Alljoined/ENIGMA"
    )


if __name__ == "__main__":
    main()
