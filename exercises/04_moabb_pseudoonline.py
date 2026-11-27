#!/usr/bin/env python3
"""Exercise 04: Reproducible Benchmarking with MOABB & pyRiemann (Going Further).

Bridges the live 2-state workshop directly into NeuroTechX's flagship benchmark framework
(`NeuroTechX/moabb`, Chevallier, Carrara, Aristimunha, Guetschel et al., 2024) and
`sylvchev/moabb_minischool`.

Compares two classic multi-channel Motor Imagery decoders on Subject 1 of BNCI2014-001:
  1. Riemannian Minimum Distance to Mean (`Covariances('oas') -> MDM`)
  2. Riemannian Tangent Space + Logistic Regression (`Covariances('oas') -> TangentSpace -> LR`)

Install optional dependencies first:
    uv pip install 'moabb>=1.1' 'pyriemann>=0.6'
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", type=int, default=1, help="BNCI2014-001 subject ID (1..9)")
    args = parser.parse_args()

    try:
        from moabb.datasets import BNCI2014_001  # type: ignore[import-not-found]
        from moabb.evaluations import WithinSessionEvaluation  # type: ignore[import-not-found]
        from moabb.paradigms import LeftRightImagery  # type: ignore[import-not-found]
        from pyriemann.classification import MDM
        from pyriemann.estimation import Covariances
        from pyriemann.tangentspace import TangentSpace
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
    except ImportError as exc:
        raise SystemExit(
            "MOABB and pyRiemann are required for Exercise 04.\n"
            "Install with: uv pip install 'moabb>=1.1' 'pyriemann>=0.6'\n"
            "See also: https://github.com/sylvchev/moabb_minischool"
        ) from exc

    dataset = BNCI2014_001()
    dataset.subject_list = [args.subject]
    paradigm = LeftRightImagery(fmin=8, fmax=32)

    pipelines = {
        "Riemann-MDM": make_pipeline(Covariances("oas"), MDM(metric="riemann")),
        "Riemann-TangentSpace-LR": make_pipeline(
            Covariances("oas"),
            TangentSpace(metric="riemann"),
            LogisticRegression(C=1.0, max_iter=500),
        ),
    }

    evaluation = WithinSessionEvaluation(
        paradigm=paradigm,
        datasets=[dataset],
        overwrite=True,
        hdf5_path=None,
    )
    results = evaluation.process(pipelines)
    print("\n=== MOABB Within-Session Motor Imagery Results (BNCI2014-001) ===")
    print(results[["pipeline", "subject", "session", "score", "time"]].to_string(index=False))


if __name__ == "__main__":
    main()
