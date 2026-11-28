---
marp: true
theme: default
paginate: true
backgroundColor: "#F7F5F0"
color: "#1D2229"
style: |
  section {
    font-family: "Public Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding: 48px 64px;
  }
  h1, h2, h3 {
    font-family: "EB Garamond", Palatino, Georgia, serif;
    color: #1D2229;
  }
  h3 {
    font-family: "Public Sans", sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #0B6B70;
    margin-bottom: 0.25rem;
  }
  a { color: #0B6B70; }
  code { background: #EDE9E0; padding: 2px 6px; border-radius: 4px; }
  pre { background: #EDE9E0; border: 1px solid #CFC8BA; border-radius: 6px; }
---

### NEUROTECHX · HANDS-ON WORKSHOP KIT · v2.0

# Introduction to Brain–Computer Interfaces

From live EEG signals and artifacts to leak-free machine learning and real-time applications.

*Customize this Markdown deck for your local chapter or student club with [Marp](https://marp.app/) or compile `slides/workshop_slides.tex` with Tectonic.*

**NeuroTechX** · [neurotechx.org](https://neurotechx.org) · [github.com/NeuroTechX/bci-workshop](https://github.com/NeuroTechX/bci-workshop)

---

### DEFINITION

## What is a Brain–Computer Interface?

> "A system that measures central nervous system (CNS) activity and converts it into artificial output that replaces, restores, enhances, supplements, or improves natural CNS output."
> — Wolpaw & Wolpaw (2012), *Brain–Computer Interfaces: Principles and Practice*

* **Acquire** ($\mu\text{V}$ scalp EEG over LSL) $\rightarrow$ **Preprocess** (causal 50/60 Hz notch + bandpass) $\rightarrow$ **Extract Features** (Welch PSD or spatial covariance) $\rightarrow$ **Classify & Feedback** (LDA / Riemannian MDM $\rightarrow$ LSL / UDP / Web UI)

---

### TODAY'S SESSION

## Workshop Roadmap (2.5 Hours)

1. **Signals, Hardware & Safety (25m):** Cortical EEG (`5–30 µV`) vs. blinks & EMG (`100+ µV`), electrical isolation, and informed consent.
2. **Exercise 00 & 01 — Live Neurofeedback (45m):** Stream via Lab Streaming Layer (LSL), inspect artifacts, and observe the Eyes-Closed **8–12 Hz Berger alpha** effect.
3. **Exercise 02 — Calibrated Live Binary BCI (45m):** Train Shrinkage LDA & `pyRiemann` MDM decoders and audit overlapping-window leakage vs. contiguous-block CV.
4. **Exercise 03 & Timeflux — Hackathon Outputs (30m):** Drive live UDP JSON receivers or launch `Timeflux` browser dashboards.

---

### MANDATORY SAFETY & ETHICS CHECK

## Unplug AC Wall Chargers on Wired / DIY Boards

* Using **PiEEG, BioAmp EXG Pill, OpenBCI USB, FreeEEG32, or icibici**? **Unplug your laptop's wall charger** (run strictly on battery or a medical-grade USB isolator).
* **Explicit consent:** Never pressure anyone to wear a headset; delete raw calibration data after the workshop unless agreed otherwise.
* **Non-clinical scope:** Educational exploration only — see [neurotechx.org/safety-and-ethics](https://neurotechx.org/safety-and-ethics).

---

### HANDS-ON · EXERCISE 00 & 01

## Stream EEG & Measure the Berger Alpha Rhythm

```bash
# Self-test your laptop in 10 seconds
uv run python exercises/00_check_setup.py --self-test

# Terminal 1: Start mock stream (or muselsl / brainflow_to_lsl.py)
uv run python streams/mock_eeg_stream.py

# Terminal 2: Launch real-time Welch PSD neurofeedback (--mains 50 in 50 Hz regions)
uv run python exercises/01_neurofeedback.py
```

* **Try 3 things:** (1) Double eye blink, (2) Gentle 2s jaw clench (watch broadband EMG!), (3) Sit still & close your eyes for 12s (watch `8–12 Hz` alpha climb!).

---

### HANDS-ON · EXERCISE 02 & 03

## Train, Audit Leakage & Stream Live Predictions

```bash
# Terminal 2: Calibrate Class 0 vs. Class 1 (Shrinkage LDA or Riemannian MDM)
uv run python exercises/02_basic_bci.py --clf lda
uv run python exercises/02_basic_bci.py --clf riemann-mdm

# Terminal 3: Receive live BCI JSON packets on udp://127.0.0.1:5005
uv run python exercises/03_udp_output_demo.py
```

* **Evaluation rule:** Slicing 20s into 80%-overlapping 1s windows leaks correlated neighbors into random CV splits (`95%+` on pure drift!). Always trust **contiguous temporal block CV** & **Balanced Accuracy** (and deepen your `Pipeline` + non-i.i.d. CV skills via the free [Inria/Probabl scikit-learn MOOC](https://inria.github.io/scikit-learn-mooc/) & [Probabl Certification](https://certification.probabl.ai/)).

---

### BONUS TRACK · EXERCISE 05 & 2026 CHALLENGE

## EEG-to-Image Retrieval & 2026 Foundation Challenge

```bash
# CPU-fast zero-shot visual embedding retrieval (Mean-Ridge vs. Spatiotemporal-ERP-Ridge)
uv run python exercises/05_eeg_to_image_retrieval.py
```

* **Track 01 (`EEG -> Image`, Alljoined-1.6M + Meta FAIR):** Maps `1.0s` visual-evoked epochs (`-0.2..+0.8s` @ `120 Hz` on 32-ch Emotiv, `CC BY-NC-SA 4.0`) onto `DINOv2`/`CLIP` embeddings for **Top-5 unseen-image retrieval**; GPU teams can extend to [`Alljoined/ENIGMA`](https://github.com/Alljoined/ENIGMA) (`MIT`, CLIP + SDXL Turbo, averaging ~80 repeats of *viewed* images).
* **Tracks 02–04 ([neural-interfaces26.github.io](https://neural-interfaces26.github.io/)):** Causal `B=1` zero-calibration recentering (`--online-adapt` in `02_basic_bci.py`, `PROTEUS`), **4-ch Muse** sleep-onset regression (`W-bMAE`), and 16-ch wrist **EMG2Pose**.

---

### GOING FURTHER

## The Wider NeuroTechX Open-Source Stack

* **Declarative Real-Time & Browser UI:** [`timeflux/`](../timeflux/README.md) & [`github.com/timeflux/demos`](https://github.com/timeflux/demos) (Oddball, P300, dry-EEG `c-VEP` Speller, EMG Roshambo)
* **Stimulus-Locked ERPs (P300, N170, SSVEP):** [`NeuroTechX/EEG-ExPy`](https://github.com/NeuroTechX/EEG-ExPy)
* **Reproducible Multi-Dataset Benchmarks:** [`NeuroTechX/moabb`](https://github.com/NeuroTechX/moabb) & `exercises/04_moabb_pseudoonline.py`
* **Deep & Geometric Learning + Benchmarks:** [`Braindecode`](https://braindecode.org), [`SPD Learn`](https://spdlearn.org), [`EEGDash`](https://eegdash.org), and [`neurotechx.org/learn`](https://neurotechx.org/learn)
