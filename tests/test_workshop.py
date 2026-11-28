"""Automated unit and live-LSL integration tests for NeuroTechX bci-workshop v2.0."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import wave

import numpy as np
import pytest

from bci_workshop.audio import generate_beep_wav
from bci_workshop.classifier import CausalSessionAdapter, build_bci_pipeline, evaluate_bci_dataset
from bci_workshop.dsp import OnlineFilterBank, compute_bandpowers, extract_epoch_features, slice_epochs
from bci_workshop.lsl_buffer import EEGStreamBuffer
from bci_workshop.profiles import DEVICE_PROFILES, get_profile
from bci_workshop.retrieval import (
    evaluate_gallery_retrieval,
    extract_visual_eeg_features,
    fit_ridge_image_decoder,
    simulate_visual_erp_dataset,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_device_profiles_valid() -> None:
    assert len(DEVICE_PROFILES) >= 18
    muse = get_profile("muse2")
    assert muse.sfreq == 256.0
    assert "TP9" in muse.alpha_channels
    with pytest.raises(KeyError):
        get_profile("nonexistent-headset")


def test_beep_wav_header_and_pcm(tmp_path: pathlib.Path) -> None:
    wav_file = generate_beep_wav(tmp_path / "cue.wav", freq_hz=660.0, duration_sec=0.15)
    assert wav_file.exists()
    with wave.open(str(wav_file), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 44100
        assert wf.getnframes() == int(round(0.15 * 44100))


def test_online_filter_and_bandpower_berger_alpha() -> None:
    sfreq = 256.0
    t = np.arange(int(4 * sfreq)) / sfreq
    rng = np.random.default_rng(0)

    # Synthetic 4-channel signal: strong 10 Hz alpha + 60 Hz hum
    alpha = 25.0 * np.sin(2.0 * np.pi * 10.0 * t)[:, None]
    hum_60 = 20.0 * np.sin(2.0 * np.pi * 60.0 * t)[:, None]
    noise = rng.normal(0.0, 2.0, size=(len(t), 4))
    raw = alpha + hum_60 + noise

    fb = OnlineFilterBank(sfreq=sfreq, n_channels=4, mains_hz=60.0, bandpass_hz=(1.0, 45.0))
    # Feed in two chunks to verify state continuity
    f1 = fb.transform(raw[:512])
    f2 = fb.transform(raw[512:])
    filtered = np.vstack([f1, f2])

    rel_bp, _, _ = compute_bandpowers(filtered[256:], sfreq=sfreq, relative=True)
    # Alpha should dominate > 65% of relative power after 60 Hz hum removal
    assert float(np.mean(rel_bp["alpha"])) > 0.65

    vec, names = extract_epoch_features(filtered[256:512], sfreq=sfreq)
    assert len(vec) == len(names) == 4 * 7  # 5 bands + 2 ratios across 4 channels


def test_leakage_audit_and_classifiers() -> None:
    sfreq = 250.0
    rng = np.random.default_rng(7)
    t = np.arange(int(16 * sfreq)) / sfreq

    # Class 0: low alpha; Class 1: high 10 Hz alpha with spatial covariance difference
    c0 = rng.normal(0.0, 6.0, size=(len(t), 4))
    c1 = rng.normal(0.0, 6.0, size=(len(t), 4))
    c1[:, [0, 3]] += 18.0 * np.sin(2.0 * np.pi * 10.0 * t)[:, None]

    for kind in ("lda", "logreg", "svm"):
        pipe, summary = evaluate_bci_dataset(c0, c1, sfreq=sfreq, kind=kind, epoch_sec=1.0, step_sec=0.25)
        assert summary.contiguous_block_acc > 0.85
        assert summary.contiguous_block_bal_acc > 0.85
        epochs = slice_epochs(c1[:500], sfreq=sfreq, epoch_sec=1.0, step_sec=0.5)
        probs = pipe.predict_proba(epochs)
        assert probs.shape == (len(epochs), 2)

    adapter = CausalSessionAdapter()
    shifted = np.ones((8, 6)) * 12.0 + rng.normal(0.0, 0.5, size=(8, 6))
    centered = adapter.update_and_center(shifted)
    assert abs(float(centered[-1].mean())) < 1.0
    adapter.reset_state()

    # Also verify pyRiemann pipelines if installed in environment
    try:
        import pyriemann  # noqa: F401
    except ImportError:
        return
    for r_kind in ("riemann-mdm", "riemann-ts"):
        r_pipe = build_bci_pipeline(r_kind, sfreq=sfreq)
        X0 = slice_epochs(c0, sfreq=sfreq, epoch_sec=1.0, step_sec=0.5)
        X1 = slice_epochs(c1, sfreq=sfreq, epoch_sec=1.0, step_sec=0.5)
        X = np.concatenate([X0, X1], axis=0)
        y = np.array([0] * len(X0) + [1] * len(X1))
        r_pipe.fit(X, y)
        assert float(r_pipe.score(X, y)) > 0.85


def test_live_lsl_mock_to_ring_buffer_roundtrip() -> None:
    stream_name = "NTX-Pytest-EEG"
    proc = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "streams" / "mock_eeg_stream.py"),
            "--name",
            stream_name,
            "--state-period",
            "2.0",
            "--duration",
            "8.0",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        buf = EEGStreamBuffer(stream_name=stream_name, timeout_sec=5.0)
        assert buf.n_channels == 4
        assert buf.ch_names == ["TP9", "AF7", "AF8", "TP10"]
        seg = buf.record_segment(1.5, filtered=True)
        assert seg.shape == (int(round(1.5 * 256.0)), 4)
        assert np.std(seg) > 0.5
        buf.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_eeg_to_image_retrieval_and_repeat_snr_scaling() -> None:
    ds = simulate_visual_erp_dataset(
        n_train_images=160,
        n_test_images=80,
        train_repeats=4,
        test_repeats=16,
        n_channels=32,
        sfreq=120.0,
        embed_dim=64,
        single_trial_snr=0.11,
        seed=11,
    )
    mean_model = fit_ridge_image_decoder(ds["train_epochs"], ds["train_embeddings"], mode="mean")
    erp_model = fit_ridge_image_decoder(ds["train_epochs"], ds["train_embeddings"], mode="spatiotemporal")

    pred_mean = mean_model.predict(extract_visual_eeg_features(ds["test_epochs"], mode="mean"))
    pred_erp = erp_model.predict(extract_visual_eeg_features(ds["test_epochs"], mode="spatiotemporal"))

    m_mean = evaluate_gallery_retrieval(
        pred_mean, ds["test_image_ids"], ds["gallery_embeddings"], ds["gallery_image_ids"], max_repeats=16
    )
    m_erp_1 = evaluate_gallery_retrieval(
        pred_erp, ds["test_image_ids"], ds["gallery_embeddings"], ds["gallery_image_ids"], max_repeats=1
    )
    m_erp_16 = evaluate_gallery_retrieval(
        pred_erp, ds["test_image_ids"], ds["gallery_embeddings"], ds["gallery_image_ids"], max_repeats=16
    )

    # Time-resolved ERP bins must outperform collapsed channel means on biphasic ERPs,
    # and multi-repeat averaging must strongly beat single-trial Top-5 accuracy.
    assert m_erp_16.top5_acc > m_mean.top5_acc + 0.25
    assert m_erp_16.top5_acc > m_erp_1.top5_acc + 0.20
    assert m_erp_16.top5_acc > 0.65


def test_prepare_alljoined_shard_header_and_npz_roundtrip(tmp_path: pathlib.Path) -> None:
    import importlib.util
    import pickle

    spec = importlib.util.spec_from_file_location(
        "prepare_alljoined_shard", ROOT / "streams" / "prepare_alljoined_shard.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Verify Pickle-5 BINBYTES8 header parser & exact row-count guard
    fake_arr = np.zeros((5, 32, 250), dtype=np.float64)
    blob = pickle.dumps({"preprocessed_eeg_data": fake_arr, "ch_names": mod.ALLJOINED_32_CHANNELS}, protocol=5)
    offset, n_bytes = mod.parse_pickle5_binbytes8_header(blob[:256], expected_rows=5, n_channels=32, n_times=250)
    assert n_bytes == 5 * 32 * 250 * 8
    recovered = np.frombuffer(blob[offset : offset + n_bytes], dtype="<f8").reshape(5, 32, 250)
    assert np.allclose(recovered, fake_arr)
    with pytest.raises(ValueError):
        mod.parse_pickle5_binbytes8_header(blob[:256], expected_rows=6, n_channels=32, n_times=250)

    # Verify zero-PyTorch category-svd embedder & Exercise 05 `--npz` roundtrip with gallery_labels
    items = [
        ("a.jpg", "pug", "animals"),
        ("b.jpg", "bulldog", "animals"),
        ("c.jpg", "airplane", "vehicles"),
        ("d.jpg", "helicopter", "vehicles"),
        ("e.jpg", "broccoli", "foods_and_plants"),
        ("f.jpg", "jukebox", "household_items_and_furniture"),
    ]
    emb_map = mod.build_category_svd_embeddings(items, embed_dim=8)
    assert len(emb_map) == 6
    assert np.isclose(np.linalg.norm(emb_map["a.jpg"]), 1.0, atol=1e-5)

    ds = simulate_visual_erp_dataset(
        n_train_images=40, n_test_images=12, train_repeats=2, test_repeats=4, embed_dim=16, seed=3
    )
    npz_file = tmp_path / "mini_shard.npz"
    np.savez_compressed(
        npz_file,
        **ds,
        gallery_labels=np.array([f"concept_{i:02d}" for i in range(12)], dtype="U24"),
    )
    res = subprocess.run(
        [sys.executable, str(ROOT / "exercises" / "05_eeg_to_image_retrieval.py"), "--npz", str(npz_file)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Sample Zero-Shot Unseen Concept Retrievals" in res.stdout
    assert "concept_" in res.stdout
