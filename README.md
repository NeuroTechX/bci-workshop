# NeuroTechX BCI Workshop (`v2.0`)

A turnkey, device-agnostic **2.5-hour hands-on Brain–Computer Interface (BCI) workshop** built for **NeuroTechX city chapters, university student clubs, and hacknights**—usable with **zero hardware** (built-in realistic LSL simulator & file replay) or with **18+ consumer and open-hardware EEG/biosignal boards**.

* **Slides:** [`workshop_slides.pdf`](workshop_slides.pdf) · Editable sources: [`slides/workshop_slides.tex`](slides/workshop_slides.tex) (2026–27 NeuroTechX Beamer theme) & [`slides/workshop_slides.md`](slides/workshop_slides.md) (Marp/Markdown)
* **Participant Step-by-Step Guide:** [`INSTRUCTIONS.md`](INSTRUCTIONS.md)
* **Supported Hardware & Safety Matrix (22 Targets):** [`docs/TARGETS.md`](docs/TARGETS.md)
* **Chapter & Student Club Facilitator Guide:** [`docs/CHAPTER_ORGANIZER_GUIDE.md`](docs/CHAPTER_ORGANIZER_GUIDE.md)
* **2015 → 2026 Lineage & Legacy Git Tags:** [`HISTORY.md`](HISTORY.md)

---

## 60-Second Quickstart (No Headset Needed!)

We recommend **[uv](https://docs.astral.sh/uv/)** (standard `python -m venv` + `pip` works identically; see [`INSTRUCTIONS.md`](INSTRUCTIONS.md)):

```bash
git clone https://github.com/NeuroTechX/bci-workshop.git
cd bci-workshop

# 1. Create environment & install core + Riemannian geometry extras
uv venv && uv pip install -e ".[riemann,dev]"

# 2. Verify Python packages, audio cues, and LSL streaming in one command
uv run python exercises/00_check_setup.py --self-test
```

Now open **two terminals**:

```bash
# Terminal 1 — Start an EEG stream (built-in simulator, or see docs/TARGETS.md for Muse/OpenBCI/PiEEG)
uv run python streams/mock_eeg_stream.py
```

```bash
# Terminal 2 — Run Exercise 01 (Neurofeedback) and Exercise 02 (Calibrated Live BCI)
uv run python exercises/01_neurofeedback.py
uv run python exercises/02_basic_bci.py --clf lda          # or --clf riemann-mdm --online-adapt
uv run python exercises/03_udp_output_demo.py              # in a 3rd terminal to receive live BCI JSON!

# Bonus — CPU-fast EEG-to-Image zero-shot retrieval lab (2026 Challenge Track 01 / Alljoined style)
uv run python exercises/05_eeg_to_image_retrieval.py
```

*(In 50 Hz mains regions such as Europe, Asia, Africa, and Australia, pass `--mains 50`.)*

### Recommended Machine-Learning Brush-Up (Optional)

Because BCI evaluation fails silently whenever preprocessing or overlapping time windows leak across train/test splits, we recommend the free **[Inria / Probabl scikit-learn MOOC](https://inria.github.io/scikit-learn-mooc/)** (especially the modules on `Pipeline` composition and non-i.i.d. `GroupKFold` / `TimeSeriesSplit` validation) and **[Probabl's official scikit-learn Certification](https://certification.probabl.ai/)** (*Associate* & *Professional Practitioner*).

---

## Two Parallel Real-Time Paths + 2026 Challenge Tracks

1. **Path A — Transparent Python (`exercises/` + `src/bci_workshop/`):**
   Inspectable scripts teaching non-lagging LSL ring buffers, causal IIR notch/bandpass filtering, Welch PSD bandpower neurofeedback (**Berger 8–12 Hz alpha effect**), Shrinkage LDA vs. **Riemannian Geometry (`pyRiemann` MDM / Tangent Space)**, **temporal leakage auditing & Balanced Accuracy**, **causal label-free session adaptation (`--online-adapt`)**, and live LSL/UDP outputs.
2. **Path B — Declarative Graphs & Browser UI (`timeflux/`):**
   Ready-to-run YAML pipelines for **[Timeflux](https://timeflux.io)** serving live browser dashboards (`http://localhost:8000`) and connecting directly into [`timeflux/demos`](https://github.com/timeflux/demos) (Oddball, EMG Roshambo, P300 Speller, and dry-EEG `c-VEP` Speller). See [`timeflux/README.md`](timeflux/README.md).
3. **2026 EEG/EMG Foundation Challenge Bridge ([`neural-interfaces26`](https://neural-interfaces26.github.io/)):**
   * **Track 01 (`EEG -> Image`):** [`exercises/05_eeg_to_image_retrieval.py`](exercises/05_eeg_to_image_retrieval.py) implements CPU-friendly zero-shot visual embedding retrieval (`RidgeCV` onto `DINOv2`/`CLIP` latents, comparing single-trial vs. multi-repeat SNR) and links directly to **[`Alljoined/Alljoined-1.6M`](https://huggingface.co/datasets/Alljoined/Alljoined-1.6M)** (`32-ch` Emotiv, NEMAR `nm000134`, `CC BY-NC-SA 4.0`) and **[`Alljoined/ENIGMA`](https://github.com/Alljoined/ENIGMA)** (`MIT`, CLIP + SDXL Turbo reconstruction of *viewed* images).
   * **Track 02 (`Cross-Session BCI`, `PROTEUS` `nm000290`):** Causal `B=1` streaming (`reset_state()`), label-free running recentering (`--online-adapt` in `02_basic_bci.py`), and 3-class mental commands (motor imagery, mental subtraction, word generation).
   * **Track 03 (`4-ch Muse Home EEG Regression`, `nm000287`):** Continuous time-to-sleep-onset (`0–600 s`) regression on 4-channel Muse headbands with domain-weighted error (`W-bMAE`).
   * **Track 04 (`EMG -> Pose`, `EMG2Pose`):** 16-ch wrist surface EMG to continuous 20-joint hand pose angles.

---

## Where to Go Next in the NeuroTechX Ecosystem

* **Stimulus-locked ERP / VEP experiments (P300, N170, SSVEP):** [`NeuroTechX/EEG-ExPy`](https://github.com/NeuroTechX/EEG-ExPy)
* **Reproducible multi-dataset BCI benchmarking (36+ datasets):** [`NeuroTechX/moabb`](https://github.com/NeuroTechX/moabb), [`sylvchev/moabb_minischool`](https://github.com/sylvchev/moabb_minischool), and [`exercises/04_moabb_pseudoonline.py`](exercises/04_moabb_pseudoonline.py)
* **Deep learning, geometric DL & foundation-model benchmarks:** [`Braindecode`](https://braindecode.org), [`SPD Learn`](https://spdlearn.org), [`EEGDash`](https://eegdash.org), [`ComputationalReviewDLEEG`](https://github.com/NeuroTechX/ComputationalReviewDLEEG), and [`neurotechx.org/learn`](https://neurotechx.org/learn)
* **Safety, ethics & neural data privacy:** [`neurotechx.org/safety-and-ethics`](https://neurotechx.org/safety-and-ethics)

---

## Credits & License

Originally created in May 2015 by **Raymundo Cassani** and **Hubert Banville** (BCI Montréal @ District 3, Concordia University), refreshed in 2017–2018 with **Dano Morrison**, **Sydney Swaine-Simon**, and NeuroTechX contributors, and modernized in 2026 for global chapters and student clubs alongside the wider NeuroTechX open-source ecosystem (see [`HISTORY.md`](HISTORY.md)). Released under the [MIT License](LICENSE.txt).
