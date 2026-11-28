#!/usr/bin/env python3
"""Stream & pack a compact 1-subject Alljoined-1.6M `.npz` shard (~15-35 MB) for Exercise 05.

Instead of downloading ~6 GB (`preprocessed_eeg_training_flat.npy` 4.26 GB +
`preprocessed_eeg_test_flat.npy` 1.04 GB + `stimuli.zip` 661 MB), this helper uses
HTTP Range requests against `Alljoined/Alljoined-1.6M` on Hugging Face (or reads a local
clone via `--local-dir`) to fetch ONLY the requested slice of trials (~80-160 MB over the
wire), resample `250 Hz -> 120 Hz` (matching 2026 Challenge Track 01), compute target
embeddings (`clip-text`, `dinov2`, `clip-image`, or zero-PyTorch `category-svd`), and write
a self-contained `.npz` shard ready for `exercises/05_eeg_to_image_retrieval.py --npz`.

License & Terms Reminder:
  `Alljoined/Alljoined-1.6M` (NEMAR `nm000134`) is released under **CC BY-NC-SA 4.0**
  and Alljoined's Terms of Access (strictly non-commercial research & educational use;
  see https://huggingface.co/datasets/Alljoined/Alljoined-1.6M). Pass `--accept-nc-terms`
  to confirm compliance, and do not redistribute raw/derived shards commercially.

Examples:
  # 1. Fast workshop shard (~100 MB network transfer, CLIP semantic embeddings, no stimuli.zip):
  uv pip install pyarrow pandas transformers torch
  uv run python streams/prepare_alljoined_shard.py \\
    --subject sub-01 --train-trials 1200 --test-trials 1000 \\
    --embedder clip-text --accept-nc-terms

  # 2. Exact 2026 Challenge Track 01 vision embeddings (streams only needed JPGs from stimuli.zip):
  uv run python streams/prepare_alljoined_shard.py \\
    --subject sub-01 --embedder dinov2 --model-id facebook/dinov2-small --accept-nc-terms

  # 3. Zero-PyTorch / CPU-only lightweight shard (only needs pandas + pyarrow + scikit-learn):
  uv run python streams/prepare_alljoined_shard.py \\
    --subject sub-01 --embedder category-svd --accept-nc-terms
"""

from __future__ import annotations

import argparse
import io
import os
import pathlib
import struct
import sys
import urllib.request
import zipfile
import zlib
from typing import Any

import numpy as np
from scipy.signal import resample
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from bci_workshop.retrieval import l2_normalize  # noqa: E402

HF_BASE = "https://huggingface.co/datasets/Alljoined/Alljoined-1.6M/resolve/main"
ALLJOINED_32_CHANNELS = [
    "Cz", "FCz", "AFz", "Fp1", "F5", "F1", "CP5", "CP3",
    "CP1", "P1", "P3", "P5", "P7", "PO7", "PO3", "O1",
    "Pz", "POz", "Oz", "O2", "PO4", "PO8", "P8", "P6",
    "P4", "P2", "CP2", "CP4", "CP6", "F2", "F6", "Fp2",
]
NATIVE_SFREQ = 250.0
NATIVE_SAMPLES = 250


def _http_headers(byte_range: str | None = None) -> dict[str, str]:
    headers = {"User-Agent": "ntx-bci-workshop/2.0"}
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if byte_range:
        headers["Range"] = byte_range
    return headers


def fetch_bytes(url: str, start: int | None = None, end_inclusive: int | None = None) -> bytes:
    byte_range = f"bytes={start}-{end_inclusive}" if start is not None and end_inclusive is not None else None
    req = urllib.request.Request(url, headers=_http_headers(byte_range))
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def fetch_content_length(url: str) -> int:
    # Request a 1-byte range to read total size from Content-Range: bytes 0-0/<total>
    req = urllib.request.Request(url, headers=_http_headers("bytes=0-0"))
    with urllib.request.urlopen(req, timeout=30) as resp:
        cr = resp.headers.get("Content-Range", "")
        if "/" in cr:
            return int(cr.split("/")[-1])
        return int(resp.headers["Content-Length"])


def parse_pickle5_binbytes8_header(
    prefix: bytes,
    expected_rows: int,
    n_channels: int = 32,
    n_times: int = 250,
) -> tuple[int, int]:
    """Locate the contiguous C-order float64 buffer inside Alljoined's pickled dict `.npy`.

    Returns ``(data_start_offset, total_buffer_bytes)`` after verifying exact row alignment.
    """
    if b"preprocessed_eeg_data" not in prefix or b"_frombuffer" not in prefix:
        raise ValueError("Unexpected file header: missing 'preprocessed_eeg_data' / '_frombuffer'.")
    idx_fb = prefix.index(b"_frombuffer")
    idx96 = prefix.index(b"\x96", idx_fb)  # Pickle Protocol 5 BINBYTES8 opcode
    n_bytes_total = int.from_bytes(prefix[idx96 + 1 : idx96 + 9], "little")
    data_start = idx96 + 9

    bytes_per_trial = n_channels * n_times * 8  # float64
    expected_bytes = expected_rows * bytes_per_trial
    if n_bytes_total != expected_bytes:
        raise ValueError(
            f"Row count mismatch: metadata has {expected_rows} non-dropped trials "
            f"({expected_bytes} B), but binary buffer has {n_bytes_total} B."
        )
    return data_start, n_bytes_total


def stream_eeg_slice(
    url_or_path: str,
    expected_total_rows: int,
    n_trials: int,
    local_mode: bool = False,
    n_channels: int = 32,
    n_times: int = 250,
    chunk_trials: int = 250,
) -> np.ndarray:
    """Load only the first ``n_trials`` epochs ``(n_trials, 32, 250)`` via HTTP Range or local file."""
    n_take = min(int(n_trials), int(expected_total_rows))
    if local_mode:
        obj = np.load(url_or_path, allow_pickle=True)
        if not isinstance(obj, dict):
            obj = obj.item()
        arr = np.asarray(obj["preprocessed_eeg_data"][:n_take], dtype=np.float32)
        ch_names = list(obj.get("ch_names", ALLJOINED_32_CHANNELS))
        if ch_names != ALLJOINED_32_CHANNELS:
            idx = [ch_names.index(ch) for ch in ALLJOINED_32_CHANNELS]
            arr = arr[:, idx, :]
        return arr

    prefix = fetch_bytes(url_or_path, 0, 511)
    data_start, _ = parse_pickle5_binbytes8_header(
        prefix, expected_rows=expected_total_rows, n_channels=n_channels, n_times=n_times
    )
    bytes_per_trial = n_channels * n_times * 8
    out = np.empty((n_take, n_channels, n_times), dtype=np.float32)

    loaded = 0
    while loaded < n_take:
        batch = min(chunk_trials, n_take - loaded)
        b_start = data_start + loaded * bytes_per_trial
        b_end = b_start + batch * bytes_per_trial - 1
        raw = fetch_bytes(url_or_path, b_start, b_end)
        block_f64 = np.frombuffer(raw, dtype="<f8").reshape(batch, n_channels, n_times)
        out[loaded : loaded + batch] = block_f64.astype(np.float32)
        loaded += batch
        mb_done = (loaded * bytes_per_trial) / (1024 * 1024)
        mb_tot = (n_take * bytes_per_trial) / (1024 * 1024)
        print(f"    Streamed {loaded:5d}/{n_take} trials ({mb_done:5.1f} / {mb_tot:5.1f} MiB)...", end="\r")
    print()
    return out


class RemoteHttpZipIndex:
    """Minimal HTTP Range ZIP reader so we fetch ~10 MB of JPGs instead of 661 MB `stimuli.zip`."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.total_size = fetch_content_length(url)
        tail_len = min(65558, self.total_size)
        tail = fetch_bytes(url, self.total_size - tail_len, self.total_size - 1)
        eocd_pos = tail.rfind(b"PK\x05\x06")
        if eocd_pos < 0:
            raise RuntimeError("Could not locate ZIP End-of-Central-Directory in stimuli.zip.")
        cd_size, cd_offset = struct.unpack_from("<II", tail, eocd_pos + 12)
        cd_bytes = fetch_bytes(url, cd_offset, cd_offset + cd_size - 1)

        self.entries_by_basename: dict[str, tuple[int, int, int]] = {}
        pos = 0
        while pos + 46 <= len(cd_bytes) and cd_bytes[pos : pos + 4] == b"PK\x01\x02":
            comp_method = struct.unpack_from("<H", cd_bytes, pos + 10)[0]
            comp_size, _, fname_len, extra_len, comment_len = struct.unpack_from("<IIHHH", cd_bytes, pos + 20)
            local_hdr_offset = struct.unpack_from("<I", cd_bytes, pos + 42)[0]
            fname = cd_bytes[pos + 46 : pos + 46 + fname_len].decode("utf-8", errors="replace")
            if not fname.endswith("/"):
                base = pathlib.PurePosixPath(fname).name
                self.entries_by_basename[base] = (local_hdr_offset, comp_size, comp_method)
            pos += 46 + fname_len + extra_len + comment_len

    def read_by_basename(self, basename: str) -> bytes:
        if basename not in self.entries_by_basename:
            raise KeyError(f"Stimulus '{basename}' not found in stimuli.zip central directory.")
        lh_off, comp_size, comp_method = self.entries_by_basename[basename]
        # Fetch 30-byte local header + up to 256 bytes of filename/extra + compressed payload
        blob = fetch_bytes(self.url, lh_off, lh_off + 30 + 256 + comp_size - 1)
        if blob[:4] != b"PK\x03\x04":
            raise RuntimeError(f"Invalid local ZIP header for {basename}.")
        fname_len, extra_len = struct.unpack_from("<HH", blob, 26)
        data_off = 30 + fname_len + extra_len
        if data_off + comp_size > len(blob):
            payload = fetch_bytes(self.url, lh_off + data_off, lh_off + data_off + comp_size - 1)
        else:
            payload = blob[data_off : data_off + comp_size]
        if comp_method == 0:
            return payload
        if comp_method == 8:
            return zlib.decompress(payload, -zlib.MAX_WBITS)
        raise RuntimeError(f"Unsupported ZIP compression method {comp_method} for {basename}.")


def build_category_svd_embeddings(
    unique_items: list[tuple[str, str, str]],
    embed_dim: int = 48,
    seed: int = 42,
) -> dict[str, np.ndarray]:
    """Zero-PyTorch semantic embeddings from THINGS `super_category` + `category_name`."""
    docs = []
    for _, cat_name, super_cat in unique_items:
        clean_cat = str(cat_name).replace("_", " ")
        clean_sup = str(super_cat).replace("_", " ")
        docs.append(f"{clean_sup} {clean_sup} {clean_sup} {clean_cat}")
    tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
    mat = tfidf.fit_transform(docs)
    n_comp = min(embed_dim, max(2, min(mat.shape) - 1))
    svd = TruncatedSVD(n_components=n_comp, random_state=seed)
    base_vecs = l2_normalize(svd.fit_transform(mat)).astype(np.float32)
    out: dict[str, np.ndarray] = {}
    for i, (img_key, _, _) in enumerate(unique_items):
        rng = np.random.default_rng(abs(hash(img_key)) % (2**31))
        jittered = base_vecs[i] + 0.02 * rng.normal(size=base_vecs[i].shape).astype(np.float32)
        out[img_key] = l2_normalize(jittered[None, :])[0].astype(np.float32)
    return out


def build_neural_embeddings(
    unique_items: list[tuple[str, str, str]],
    embedder: str,
    model_id: str | None,
    local_dir: pathlib.Path | None,
) -> dict[str, np.ndarray]:
    """Compute real CLIP-text, CLIP-image, or DINOv2 embeddings via HuggingFace `transformers`."""
    try:
        import torch
        from PIL import Image
        from transformers import AutoImageProcessor, AutoModel, CLIPModel, CLIPProcessor
    except ImportError as exc:
        raise SystemExit(
            f"Embedder '{embedder}' requires PyTorch, Pillow, and transformers.\n"
            "Install with: uv pip install torch transformers pillow\n"
            "Or run with `--embedder category-svd` for a zero-PyTorch lightweight run."
        ) from exc

    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

    if embedder == "clip-text":
        mid = model_id or "openai/clip-vit-base-patch32"
        print(f"[Embedder] Loading CLIP text encoder '{mid}' on {device}...")
        proc = CLIPProcessor.from_pretrained(mid)
        model = CLIPModel.from_pretrained(mid).to(device).eval()

        unique_cats = sorted({cat for _, cat, _ in unique_items})
        cat_vecs: dict[str, np.ndarray] = {}
        batch_size = 128
        with torch.inference_mode():
            for i in range(0, len(unique_cats), batch_size):
                batch_cats = unique_cats[i : i + batch_size]
                prompts = [f"a photo of a {c.replace('_', ' ')}" for c in batch_cats]
                inputs = proc(text=prompts, return_tensors="pt", padding=True, truncation=True).to(device)
                feats = model.get_text_features(**inputs)
                if not isinstance(feats, torch.Tensor):
                    feats = feats.pooler_output
                arr = l2_normalize(feats.detach().cpu().numpy()).astype(np.float32)
                for c_name, vec in zip(batch_cats, arr):
                    cat_vecs[c_name] = vec
        # Add tiny deterministic per-image jitter so distinct images in the same category stay distinguishable
        out: dict[str, np.ndarray] = {}
        for img_key, cat_name, _ in unique_items:
            rng = np.random.default_rng(abs(hash(img_key)) % (2**31))
            vec = cat_vecs[cat_name] + 0.02 * rng.normal(size=cat_vecs[cat_name].shape).astype(np.float32)
            out[img_key] = l2_normalize(vec[None, :])[0].astype(np.float32)
        return out

    # Image-based embedders (`dinov2` or `clip-image`) fetch actual JPGs from `stimuli.zip`
    local_zip = (local_dir / "stimuli.zip") if local_dir is not None else None
    zf = zipfile.ZipFile(local_zip, "r") if (local_zip and local_zip.exists()) else None
    local_name_map = {pathlib.PurePosixPath(n).name: n for n in zf.namelist()} if zf is not None else {}
    remote_zip = None if zf is not None else RemoteHttpZipIndex(f"{HF_BASE}/stimuli.zip")

    def _load_pil(img_key: str) -> Any:
        base = pathlib.PurePosixPath(img_key).name
        raw = zf.read(local_name_map[base]) if zf is not None else remote_zip.read_by_basename(base)  # type: ignore[union-attr]
        return Image.open(io.BytesIO(raw)).convert("RGB")

    if embedder == "clip-image":
        mid = model_id or "openai/clip-vit-base-patch32"
        print(f"[Embedder] Loading CLIP vision encoder '{mid}' on {device}...")
        proc = CLIPProcessor.from_pretrained(mid)
        model = CLIPModel.from_pretrained(mid).to(device).eval()
    else:
        mid = model_id or "facebook/dinov2-small"
        print(f"[Embedder] Loading DINOv2 vision encoder '{mid}' on {device} (Track 01 uses dinov2-giant)...")
        proc = AutoImageProcessor.from_pretrained(mid)
        model = AutoModel.from_pretrained(mid).to(device).eval()

    out_img: dict[str, np.ndarray] = {}
    batch_size = 32
    with torch.inference_mode():
        for i in range(0, len(unique_items), batch_size):
            batch_items = unique_items[i : i + batch_size]
            pil_imgs = [_load_pil(k) for k, _, _ in batch_items]
            if embedder == "clip-image":
                inputs = proc(images=pil_imgs, return_tensors="pt").to(device)
                feats = model.get_image_features(**inputs)
                if not isinstance(feats, torch.Tensor):
                    feats = feats.pooler_output
            else:
                inputs = proc(images=pil_imgs, return_tensors="pt").to(device)
                outputs = model(**inputs)
                feats = outputs.last_hidden_state[:, 0]  # CLS token
            vecs = l2_normalize(feats.detach().cpu().numpy()).astype(np.float32)
            for (img_key, _, _), vec in zip(batch_items, vecs):
                out_img[img_key] = vec
            print(f"    Embedded {min(i + batch_size, len(unique_items)):4d}/{len(unique_items)} unique images...", end="\r")
    print()
    if zf is not None:
        zf.close()
    return out_img


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--subject", default="sub-01", help="Participant ID (`sub-01` .. `sub-20`)")
    parser.add_argument("--train-trials", type=int, default=1200, help="Number of training EEG trials to stream")
    parser.add_argument("--test-trials", type=int, default=1000, help="Number of unseen test EEG trials to stream")
    parser.add_argument("--target-sfreq", type=float, default=120.0, help="Target resampled sfreq in Hz (Track 01 = 120 Hz)")
    parser.add_argument(
        "--embedder",
        default="clip-text",
        choices=["clip-text", "dinov2", "clip-image", "category-svd"],
        help="Target representation (`clip-text` needs no stimuli.zip; `dinov2` matches Track 01)",
    )
    parser.add_argument("--model-id", default=None, help="Optional HuggingFace model override (e.g. facebook/dinov2-giant)")
    parser.add_argument("--local-dir", type=pathlib.Path, default=None, help="Optional local clone of Alljoined-1.6M")
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=ROOT / "data" / "alljoined_sub01_shard.npz",
        help="Output `.npz` path",
    )
    parser.add_argument(
        "--accept-nc-terms",
        action="store_true",
        help="Acknowledge Alljoined-1.6M CC BY-NC-SA 4.0 & non-commercial educational/research Terms of Use",
    )
    args = parser.parse_args()

    if not args.accept_nc_terms:
        raise SystemExit(
            "Alljoined-1.6M is licensed under CC BY-NC-SA 4.0 for non-commercial research and educational use.\n"
            "Review https://huggingface.co/datasets/Alljoined/Alljoined-1.6M and re-run with `--accept-nc-terms`.\n"
            "(If your Hugging Face account requires gated access, also set `export HF_TOKEN=...`.)"
        )

    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit("Install pandas & pyarrow first: `uv pip install pandas pyarrow`") from exc

    subj = args.subject
    print(f"[Alljoined Shard] Loading metadata for {subj} (CC BY-NC-SA 4.0, non-commercial educational use)...")
    if args.local_dir is not None:
        pq_path = args.local_dir / "preprocessed_eeg" / subj / "experiment_metadata_categories.parquet"
        df_all = pd.read_parquet(pq_path)
    else:
        pq_url = f"{HF_BASE}/preprocessed_eeg/{subj}/experiment_metadata_categories.parquet"
        pq_bytes = fetch_bytes(pq_url)
        df_all = pd.read_parquet(io.BytesIO(pq_bytes))

    df_train_full = df_all[(df_all["partition"] == "stim_train") & (~df_all["dropped"])].reset_index(drop=True)
    df_test_full = df_all[(df_all["partition"] == "stim_test") & (~df_all["dropped"])].reset_index(drop=True)

    df_tr = df_train_full.iloc[: min(args.train_trials, len(df_train_full))].copy()
    df_te = df_test_full.iloc[: min(args.test_trials, len(df_test_full))].copy()

    print(f"[Alljoined Shard] Streaming {len(df_tr)}/{len(df_train_full)} train trials for {subj}...")
    tr_src = (
        str(args.local_dir / "preprocessed_eeg" / subj / "preprocessed_eeg_training_flat.npy")
        if args.local_dir is not None
        else f"{HF_BASE}/preprocessed_eeg/{subj}/preprocessed_eeg_training_flat.npy"
    )
    X_tr_raw = stream_eeg_slice(tr_src, len(df_train_full), len(df_tr), local_mode=args.local_dir is not None)

    print(f"[Alljoined Shard] Streaming {len(df_te)}/{len(df_test_full)} unseen test trials for {subj}...")
    te_src = (
        str(args.local_dir / "preprocessed_eeg" / subj / "preprocessed_eeg_test_flat.npy")
        if args.local_dir is not None
        else f"{HF_BASE}/preprocessed_eeg/{subj}/preprocessed_eeg_test_flat.npy"
    )
    X_te_raw = stream_eeg_slice(te_src, len(df_test_full), len(df_te), local_mode=args.local_dir is not None)

    target_samples = int(round((NATIVE_SAMPLES / NATIVE_SFREQ) * args.target_sfreq))
    if target_samples != NATIVE_SAMPLES:
        print(f"[Alljoined Shard] Resampling 32-ch epochs {NATIVE_SFREQ:.0f} Hz -> {args.target_sfreq:.0f} Hz ({target_samples} samples)...")
        X_tr = resample(X_tr_raw, target_samples, axis=-1).astype(np.float32)
        X_te = resample(X_te_raw, target_samples, axis=-1).astype(np.float32)
    else:
        X_tr, X_te = X_tr_raw, X_te_raw

    # Collect unique images across selected train + unseen test trials
    combined = pd.concat([df_tr, df_te], ignore_index=True)
    unique_rows = combined.drop_duplicates(subset=["image_path"])[
        ["image_path", "category_name", "super_category"]
    ]
    unique_items = [
        (str(r.image_path), str(r.category_name), str(r.super_category))
        for r in unique_rows.itertuples(index=False)
    ]
    img_to_id = {img_key: idx for idx, (img_key, _, _) in enumerate(unique_items)}

    if args.embedder == "category-svd":
        print(f"[Embedder] Building zero-PyTorch THINGS category SVD embeddings ({len(unique_items)} unique stimuli)...")
        emb_map = build_category_svd_embeddings(unique_items)
    else:
        emb_map = build_neural_embeddings(unique_items, args.embedder, args.model_id, args.local_dir)

    Y_tr = np.stack([emb_map[str(p)] for p in df_tr["image_path"]], axis=0)
    ids_tr = np.array([img_to_id[str(p)] for p in df_tr["image_path"]], dtype=np.int32)

    Y_te = np.stack([emb_map[str(p)] for p in df_te["image_path"]], axis=0)
    ids_te = np.array([img_to_id[str(p)] for p in df_te["image_path"]], dtype=np.int32)

    # Unseen candidate gallery = unique images in `stim_test` slice
    te_unique = df_te.drop_duplicates(subset=["image_path"]).sort_values("image_path")
    gal_ids = np.array([img_to_id[str(p)] for p in te_unique["image_path"]], dtype=np.int32)
    gal_emb = np.stack([emb_map[str(p)] for p in te_unique["image_path"]], axis=0)
    gal_labels = np.array([str(c) for c in te_unique["category_name"]], dtype="U48")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        train_epochs=X_tr.astype(np.float16),
        train_embeddings=Y_tr.astype(np.float32),
        train_image_ids=ids_tr,
        test_epochs=X_te.astype(np.float16),
        test_embeddings=Y_te.astype(np.float32),
        test_image_ids=ids_te,
        gallery_embeddings=gal_emb.astype(np.float32),
        gallery_image_ids=gal_ids,
        gallery_labels=gal_labels,
        ch_names=np.array(ALLJOINED_32_CHANNELS, dtype="U8"),
        sfreq=np.array([args.target_sfreq], dtype=np.float32),
        subject=np.array([subj], dtype="U16"),
        embedder=np.array([args.embedder], dtype="U24"),
        license=np.array(["CC-BY-NC-SA-4.0 (Alljoined-1.6M non-commercial educational/research use)"], dtype="U96"),
    )
    size_mb = args.out.stat().st_size / (1024 * 1024)
    print(f"[Alljoined Shard] Wrote {args.out} ({size_mb:.1f} MiB, {len(gal_ids)} unseen gallery images).")
    print(f"  Run next: uv run python exercises/05_eeg_to_image_retrieval.py --npz {args.out}")


if __name__ == "__main__":
    main()
