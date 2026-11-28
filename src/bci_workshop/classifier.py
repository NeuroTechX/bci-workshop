"""Leak-free BCI classification pipelines (Shrinkage LDA, LogReg, SVM, and pyRiemann)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .dsp import extract_epoch_features, slice_epochs


class CausalSessionAdapter:
    """Label-free causal running feature/epoch recenterer (`reset_state()` per session).

    Mirrors the zero-calibration streaming adaptation contract of Track 02 (`PROTEUS`)
    in `neural-interfaces26/2026-competition` (`benchmark_utils/streaming.py`): each live
    window ``X_t`` is centered using ONLY current and past unlabeled windows in the session,
    mitigating slow baseline/impedance drift across sessions without peeking ahead.
    """

    def __init__(self, momentum: float = 0.05) -> None:
        self.momentum = float(momentum)
        self._running_mean: np.ndarray | None = None
        self._n_seen: int = 0

    def reset_state(self) -> None:
        self._running_mean = None
        self._n_seen = 0

    def update_and_center(self, x: np.ndarray) -> np.ndarray:
        arr = np.asarray(x, dtype=np.float64)
        sample_mean = arr.mean(axis=0, keepdims=True)
        self._n_seen += len(arr)
        if self._running_mean is None:
            self._running_mean = sample_mean.copy()
        else:
            alpha = max(self.momentum, 1.0 / self._n_seen)
            self._running_mean = (1.0 - alpha) * self._running_mean + alpha * sample_mean
        return arr - self._running_mean


class SpectralFeatureTransformer(BaseEstimator, TransformerMixin):
    """Scikit-learn transformer turning (n_epochs, n_channels, n_times) into Welch PSD features."""

    def __init__(self, sfreq: float = 256.0) -> None:
        self.sfreq = sfreq

    def fit(self, X: np.ndarray, y: Any = None) -> SpectralFeatureTransformer:
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        arr = np.asarray(X, dtype=np.float64)
        rows = [extract_epoch_features(ep.T, sfreq=self.sfreq)[0] for ep in arr]
        return np.vstack(rows)


def build_bci_pipeline(kind: str = "lda", sfreq: float = 256.0) -> Pipeline:
    """Build a calibrated binary/multi-class BCI pipeline operating on (n_epochs, n_ch, n_times).

    Supported `kind`:
      - `lda`: Welch log-bandpower + Ledoit-Wolf shrinkage LDA (Lotte et al. 2018 baseline)
      - `logreg`: Welch log-bandpower + L2 Logistic Regression
      - `svm`: Welch log-bandpower + RBF Support Vector Machine (probability=True)
      - `riemann-mdm`: OAS regularized spatial covariance + Riemannian Minimum Distance to Mean
      - `riemann-ts`: OAS regularized spatial covariance + Riemannian Tangent Space + Logistic Regression
    """
    key = kind.lower().strip()
    if key == "lda":
        return Pipeline(
            [
                ("psd", SpectralFeatureTransformer(sfreq=sfreq)),
                ("scaler", StandardScaler()),
                ("clf", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
            ]
        )
    if key == "logreg":
        return Pipeline(
            [
                ("psd", SpectralFeatureTransformer(sfreq=sfreq)),
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(C=1.0, max_iter=500)),
            ]
        )
    if key == "svm":
        return Pipeline(
            [
                ("psd", SpectralFeatureTransformer(sfreq=sfreq)),
                ("scaler", StandardScaler()),
                ("clf", SVC(kernel="rbf", C=1.0, probability=True)),
            ]
        )
    if key in ("riemann-mdm", "riemann-ts"):
        try:
            from pyriemann.classification import MDM
            from pyriemann.estimation import Covariances
            from pyriemann.tangentspace import TangentSpace
        except ImportError as exc:
            raise ImportError(
                f"Pipeline '{kind}' requires pyRiemann (`uv pip install pyriemann`)."
            ) from exc

        if key == "riemann-mdm":
            return Pipeline([("cov", Covariances(estimator="oas")), ("mdm", MDM(metric="riemann"))])
        return Pipeline(
            [
                ("cov", Covariances(estimator="oas")),
                ("ts", TangentSpace(metric="riemann")),
                ("clf", LogisticRegression(C=1.0, max_iter=500)),
            ]
        )

    raise ValueError(
        f"Unknown classifier '{kind}'. Choose from: lda, logreg, svm, riemann-mdm, riemann-ts."
    )


@dataclass(frozen=True)
class EvaluationSummary:
    contiguous_block_acc: float
    contiguous_block_bal_acc: float
    naive_overlap_random_acc: float
    train_resubstitution_acc: float
    n_epochs_total: int


def evaluate_bci_dataset(
    class0_signal: np.ndarray,
    class1_signal: np.ndarray,
    sfreq: float,
    kind: str = "lda",
    epoch_sec: float = 1.0,
    step_sec: float = 0.2,
    n_blocks: int = 4,
) -> tuple[Pipeline, EvaluationSummary]:
    """Evaluate BCI pipeline with leak-free contiguous temporal blocks vs. naive random CV.

    Why both numbers are returned:
    In the 2015-2018 workshop, `clf.score(X, y)` was evaluated on 80%-overlapping 1s windows,
    producing 95-100% accuracy even on pure 1/f drift due to window overlap leakage. Here we:
      1. Split each continuous recording into `n_blocks` disjoint temporal segments BEFORE
         slicing overlapping epochs inside each segment (preventing boundary bleed),
      2. Compute honest held-out block accuracy (`contiguous_block_acc`), AND
      3. Show naive random-split accuracy (`naive_overlap_random_acc`) + resubstitution accuracy
         so students see the leakage difference firsthand.
    """
    c0 = np.asarray(class0_signal, dtype=np.float64)
    c1 = np.asarray(class1_signal, dtype=np.float64)
    min_samples_per_block = max(16, int(round(epoch_sec * sfreq)))
    max_valid_blocks = min(len(c0), len(c1)) // min_samples_per_block
    if max_valid_blocks < 2:
        raise ValueError(
            f"Calibration too short ({min(len(c0), len(c1))/sfreq:.1f}s); need at least {2 * epoch_sec:.1f}s per class."
        )
    n_blocks = min(n_blocks, max_valid_blocks)

    # 1. Leak-free contiguous block split (slice windows INSIDE each temporal block)
    c0_chunks = np.array_split(c0, n_blocks, axis=0)
    c1_chunks = np.array_split(c1, n_blocks, axis=0)

    block_scores: list[float] = []
    block_bal_scores: list[float] = []
    for fold in range(n_blocks):
        train_epochs_list: list[np.ndarray] = []
        train_labels_list: list[np.ndarray] = []
        test_epochs_list: list[np.ndarray] = []
        test_labels_list: list[np.ndarray] = []

        for b_idx in range(n_blocks):
            ep0 = slice_epochs(c0_chunks[b_idx], sfreq=sfreq, epoch_sec=epoch_sec, step_sec=step_sec)
            ep1 = slice_epochs(c1_chunks[b_idx], sfreq=sfreq, epoch_sec=epoch_sec, step_sec=step_sec)
            if b_idx == fold:
                test_epochs_list.extend([ep0, ep1])
                test_labels_list.extend([np.zeros(len(ep0), dtype=int), np.ones(len(ep1), dtype=int)])
            else:
                train_epochs_list.extend([ep0, ep1])
                train_labels_list.extend([np.zeros(len(ep0), dtype=int), np.ones(len(ep1), dtype=int)])

        X_tr = np.concatenate(train_epochs_list, axis=0)
        y_tr = np.concatenate(train_labels_list, axis=0)
        X_te = np.concatenate(test_epochs_list, axis=0)
        y_te = np.concatenate(test_labels_list, axis=0)

        fold_pipe = build_bci_pipeline(kind=kind, sfreq=sfreq)
        fold_pipe.fit(X_tr, y_tr)
        y_pred = fold_pipe.predict(X_te)
        block_scores.append(float(np.mean(y_pred == y_te)))
        block_bal_scores.append(float(balanced_accuracy_score(y_te, y_pred)))

    # 2. Full overlapping dataset for final live decoder + naive comparison
    ep0_all = slice_epochs(c0, sfreq=sfreq, epoch_sec=epoch_sec, step_sec=step_sec)
    ep1_all = slice_epochs(c1, sfreq=sfreq, epoch_sec=epoch_sec, step_sec=step_sec)
    X_all = np.concatenate([ep0_all, ep1_all], axis=0)
    y_all = np.concatenate([np.zeros(len(ep0_all), dtype=int), np.ones(len(ep1_all), dtype=int)])

    naive_cv = StratifiedKFold(n_splits=n_blocks, shuffle=True, random_state=42)
    naive_scores = cross_val_score(build_bci_pipeline(kind=kind, sfreq=sfreq), X_all, y_all, cv=naive_cv)

    final_pipe = build_bci_pipeline(kind=kind, sfreq=sfreq)
    final_pipe.fit(X_all, y_all)
    resub_acc = float(final_pipe.score(X_all, y_all))

    summary = EvaluationSummary(
        contiguous_block_acc=float(np.mean(block_scores)),
        contiguous_block_bal_acc=float(np.mean(block_bal_scores)),
        naive_overlap_random_acc=float(np.mean(naive_scores)),
        train_resubstitution_acc=resub_acc,
        n_epochs_total=int(len(y_all)),
    )
    return final_pipe, summary
