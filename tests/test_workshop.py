"""Automated unit and live-LSL integration tests for NeuroTechX bci-workshop v2.0."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import time
import wave

import numpy as np
import pytest

from bci_workshop.audio import generate_beep_wav
from bci_workshop.classifier import build_bci_pipeline, evaluate_bci_dataset
from bci_workshop.dsp import OnlineFilterBank, compute_bandpowers, extract_epoch_features, slice_epochs
from bci_workshop.lsl_buffer import EEGStreamBuffer
from bci_workshop.profiles import DEVICE_PROFILES, get_profile

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
        epochs = slice_epochs(c1[:500], sfreq=sfreq, epoch_sec=1.0, step_sec=0.5)
        probs = pipe.predict_proba(epochs)
        assert probs.shape == (len(epochs), 2)

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
