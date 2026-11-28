"""EEG-to-Image zero-shot embedding retrieval utilities (2026 Track 01 / Alljoined style).

Implements the core paradigm from Track 01 of the 2026 EEG/EMG Foundation Challenge
(`neural-interfaces26/2026-competition`, Alljoined-1.6M + Meta FAIR Brain & AI):

  1. Stimulus-locked visual EEG epochs ``X`` of shape ``(n_trials, n_channels, n_times)``
     (conventionally ``-0.2s`` to ``+0.8s`` @ ``120 Hz`` -> ``120`` samples on 32-ch Emotiv
     for ``Alljoined-1.6M`` or 63-ch ``THINGS-EEG2``).
  2. Target vision-backbone embeddings ``Y`` of shape ``(n_trials, embed_dim)``
     (e.g., 1536-D ``DINOv2-giant`` in Track 01, or ``CLIP`` in ``Alljoined/ENIGMA``).
  3. Linear Ridge probes (Track 01 ``Mean-Ridge`` baseline vs. time-resolved
     ``Spatiotemporal-ERP-Ridge``) trained strictly on SEEN training images, then evaluated
     via cosine similarity against a held-out gallery of UNSEEN test images (`Top-1` / `Top-5`),
     demonstrating the effect of averaging ``K`` stimulus repetitions on SNR.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler


def l2_normalize(vecs: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Row-wise L2 normalization for cosine-similarity retrieval."""
    arr = np.asarray(vecs, dtype=np.float64)
    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    return arr / np.maximum(norms, eps)


def extract_visual_eeg_features(
    epochs: np.ndarray,
    mode: str = "spatiotemporal",
    n_time_bins: int = 12,
) -> np.ndarray:
    """Convert ``(n_trials, n_ch, n_times)`` visual epochs into 2D tabular features.

    Modes:
      - ``mean``: Collapses time to channel means ``(n_trials, n_ch)`` — reproduces the
        exact `Mean-Ridge` reference baseline from `neural-interfaces26` Track 01.
      - ``spatiotemporal``: Averages into ``n_time_bins`` contiguous ERP windows
        (capturing P100 / N170 / P300 latency structure) -> ``(n_trials, n_ch * n_time_bins)``.
    """
    X = np.asarray(epochs, dtype=np.float64)
    if X.ndim != 3:
        raise ValueError(f"Expected 3D epochs (n_trials, n_ch, n_times), got shape {X.shape}")

    key = mode.lower().strip()
    if key == "mean":
        return X.mean(axis=-1)
    if key == "spatiotemporal":
        chunks = np.array_split(X, n_time_bins, axis=-1)
        binned = np.stack([c.mean(axis=-1) for c in chunks], axis=-1)  # (B, C, n_bins)
        return binned.reshape(len(X), -1)
    raise ValueError(f"Unknown feature mode '{mode}'. Choose 'mean' or 'spatiotemporal'.")


def fit_ridge_image_decoder(
    train_epochs: np.ndarray,
    train_embeddings: np.ndarray,
    mode: str = "spatiotemporal",
    alphas: tuple[float, ...] = (1.0, 10.0, 100.0, 1000.0, 5000.0),
) -> Pipeline:
    """Fit a leak-free ``StandardScaler -> RidgeCV`` probe from EEG epochs to image latents."""
    X_feat = extract_visual_eeg_features(train_epochs, mode=mode)
    Y_norm = l2_normalize(train_embeddings)
    model = make_pipeline(StandardScaler(), RidgeCV(alphas=alphas))
    model.fit(X_feat, Y_norm)
    return model


@dataclass(frozen=True)
class RetrievalMetrics:
    top1_acc: float
    top5_acc: float
    mean_rank: float
    gallery_size: int
    n_queries: int


def evaluate_gallery_retrieval(
    pred_trial_embeddings: np.ndarray,
    trial_image_ids: np.ndarray,
    gallery_embeddings: np.ndarray,
    gallery_image_ids: np.ndarray,
    max_repeats: int | None = None,
    rng_seed: int = 0,
) -> RetrievalMetrics:
    """Score zero-shot image retrieval via cosine similarity against a candidate gallery.

    Mirrors the 2026 Track 01 evaluation protocol:
      1. Group predicted embeddings across up to ``max_repeats`` presentations of the same
         unseen test image and average them BEFORE L2-normalizing.
      2. Rank all ``gallery_embeddings`` by cosine similarity (`pred_norm @ gallery_norm.T`).
      3. Report Top-1 accuracy, Top-5 accuracy, and mean true-image rank.
    """
    preds = np.asarray(pred_trial_embeddings, dtype=np.float64)
    img_ids = np.asarray(trial_image_ids)
    gal_emb = l2_normalize(gallery_embeddings)
    gal_ids = np.asarray(gallery_image_ids)
    id_to_gal_idx = {int(gid): idx for idx, gid in enumerate(gal_ids)}

    rng = np.random.default_rng(rng_seed)
    unique_query_ids = np.unique(img_ids)

    pooled_preds: list[np.ndarray] = []
    target_gal_indices: list[int] = []

    for qid in unique_query_ids:
        if int(qid) not in id_to_gal_idx:
            continue
        trial_idx = np.flatnonzero(img_ids == qid)
        if max_repeats is not None and len(trial_idx) > max_repeats:
            trial_idx = rng.choice(trial_idx, size=max_repeats, replace=False)
        pooled_preds.append(preds[trial_idx].mean(axis=0))
        target_gal_indices.append(id_to_gal_idx[int(qid)])

    query_norm = l2_normalize(np.vstack(pooled_preds))
    sims = query_norm @ gal_emb.T  # (n_queries, gallery_size)
    # Descending rank of each gallery item
    order = np.argsort(-sims, axis=1)
    targets = np.asarray(target_gal_indices)[:, None]
    ranks = np.argmax(order == targets, axis=1) + 1  # 1-indexed rank

    return RetrievalMetrics(
        top1_acc=float(np.mean(ranks <= 1)),
        top5_acc=float(np.mean(ranks <= min(5, len(gal_ids)))),
        mean_rank=float(np.mean(ranks)),
        gallery_size=int(len(gal_ids)),
        n_queries=int(len(ranks)),
    )


def simulate_visual_erp_dataset(
    n_train_images: int = 240,
    n_test_images: int = 100,
    train_repeats: int = 4,
    test_repeats: int = 16,
    n_channels: int = 32,
    sfreq: float = 120.0,
    embed_dim: int = 128,
    single_trial_snr: float = 0.11,
    seed: int = 42,
) -> dict[str, np.ndarray]:
    """Generate a realistic synthetic visual-ERP -> image-embedding benchmark (`Alljoined` geometry).

    Why time-resolved features beat channel-means here (just as in real visual EEG):
    Visual semantic information emerges in zero-mean biphasic P100 (`+100 ms`), N170 (`+170 ms`),
    and P250/P300 (`+260 ms`) occipital-temporal waveforms over a ``-0.2s .. +0.8s`` window
    (`120` samples @ `120 Hz`, `32` channels). Averaging across the whole 1s window cancels
    biphasic deflections, whereas spatiotemporal binning preserves them—and averaging ``K``
    repeated presentations scales amplitude SNR by ``sqrt(K)``.
    """
    rng = np.random.default_rng(seed)
    n_times = int(round(1.0 * sfreq))  # -0.2s to +0.8s (120 samples @ 120 Hz)
    t = np.linspace(-0.2, 0.8, n_times, endpoint=False)

    # Low-dimensional visual semantic factors driving both image embeddings and visual cortex ERPs
    n_latents = 12
    W_img = rng.normal(0.0, 1.0, size=(n_latents, embed_dim))

    # Biphasic zero-mean temporal kernels (P100/N170, N170/P250, P300-like) so naive time-mean washes out
    temporal_basis = np.zeros((n_latents, n_times), dtype=np.float64)
    centers = np.linspace(0.09, 0.38, n_latents)
    for k, c_sec in enumerate(centers):
        pos = np.exp(-0.5 * ((t - c_sec) / 0.028) ** 2)
        neg = np.exp(-0.5 * ((t - (c_sec + 0.055)) / 0.028) ** 2)
        wave = pos - neg
        temporal_basis[k] = wave - wave.mean()

    spatial_leadfield = rng.normal(0.0, 1.0, size=(n_latents, n_channels))
    # Boost posterior/occipital channels (last 12 channels)
    spatial_leadfield[:, -12:] *= 2.2

    # Full-rank ongoing cortical background sources (n_bg_sources > n_channels -> no noise-free nullspace!)
    n_bg_sources = 64
    bg_leadfield = rng.normal(0.0, 1.0, size=(n_bg_sources, n_channels))
    smooth_kernel = np.exp(-0.5 * (np.linspace(-2.0, 2.0, 9) ** 2))
    smooth_kernel /= np.linalg.norm(smooth_kernel)

    # First 2 latents carry a slow sustained offset (decodable by Mean-Ridge above chance);
    # remaining 10 semantic latents live strictly in zero-mean biphasic P100/N170/P250 waves.
    temporal_kernels = temporal_basis.copy()
    temporal_kernels[:2] += 0.35 * np.exp(-0.5 * ((t - 0.30) / 0.16) ** 2)[None, :]

    def _make_split(
        img_id_offset: int, n_imgs: int, repeats: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        z_img = rng.normal(0.0, 1.0, size=(n_imgs, n_latents))
        gallery_emb = l2_normalize(z_img @ W_img + 0.15 * rng.normal(size=(n_imgs, embed_dim)))
        gallery_ids = np.arange(img_id_offset, img_id_offset + n_imgs, dtype=int)

        clean_erp = np.einsum("il,lc,lt->ict", z_img, spatial_leadfield, temporal_kernels)
        clean_erp /= np.std(clean_erp) + 1e-8

        trial_img_idx = np.repeat(np.arange(n_imgs), repeats)
        n_trials = len(trial_img_idx)

        raw_src = rng.normal(0.0, 1.0, size=(n_trials, n_bg_sources, n_times + 8))
        corr_src = np.apply_along_axis(lambda v: np.convolve(v, smooth_kernel, mode="valid"), -1, raw_src)
        bg_eeg = np.einsum("bst,sc->bct", corr_src, bg_leadfield)
        sensor_noise = 0.65 * rng.normal(0.0, 1.0, size=(n_trials, n_channels, n_times))
        noise = bg_eeg + sensor_noise
        noise /= np.std(noise) + 1e-8

        epochs = single_trial_snr * clean_erp[trial_img_idx] + noise
        trial_emb = gallery_emb[trial_img_idx]
        trial_ids = gallery_ids[trial_img_idx]
        return epochs.astype(np.float32), trial_emb.astype(np.float32), trial_ids, gallery_emb.astype(np.float32)

    X_tr, Y_tr, ids_tr, _ = _make_split(0, n_train_images, train_repeats)
    X_te, Y_te, ids_te, gal_te = _make_split(n_train_images, n_test_images, test_repeats)
    gal_ids_te = np.arange(n_train_images, n_train_images + n_test_images, dtype=int)

    return {
        "train_epochs": X_tr,
        "train_embeddings": Y_tr,
        "train_image_ids": ids_tr,
        "test_epochs": X_te,
        "test_embeddings": Y_te,
        "test_image_ids": ids_te,
        "gallery_embeddings": gal_te,
        "gallery_image_ids": gal_ids_te,
    }
