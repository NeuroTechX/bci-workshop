# History & Lineage of `NeuroTechX/bci-workshop` (2015 – 2026)

`NeuroTechX/bci-workshop` is one of NeuroTechX's earliest open-source educational deliverables—originally created in **May 2015** for **BCI Montréal** at District 3 (Concordia University), right at the birth of NeuroTechX (*Société BCI Montréal*). Over eleven years, its branches and successor community workshops trace how accessible Brain–Computer Interfacing evolved across hardware, transport protocols, and machine learning.

All historical iterations in this repository are preserved as immutable annotated Git tags so nothing from the 2015–2018 eras is lost.

---

## 1. Chronological Iterations in This Repository

| Tag / Branch | Date & Venue | Authors & Contributors | Software Stack & Languages | Hardware & Transport Targets |
| :--- | :--- | :--- | :--- | :--- |
| **`v0.1-mules-2015`**<br/>(`origin/mules-version`) | **May 2015**<br/>BCI Montréal @ District 3, Concordia University | Raymundo Cassani, Hubert Banville | **Python 2/3**, **MATLAB**, and **GNU Octave** (with compiled C/MEX `libsvm` & `tone.c` audio cues) | **MuLES** (*MuSAE Lab EEG Server*, TCP on Windows) driving **Muse 2014** (`220 Hz`), **EMOTIV EPOC+**, **NeuroSky MindWave**, **Neuroelectrics ENOBIO**, and **OpenBCI V3**. |
| **`v0.2-museio-2016`**<br/>(`origin/muse-io-version`,<br/>`origin/IPython-Notebook-Muse-io`) | **Late 2015 – 2016**<br/>Montreal & early NTX chapters | Hubert Banville, `twuilliam`, BCI Montréal contributors | **Python 2.7** scripts + first **IPython / Jupyter Notebooks** (`NeuroTechX-GettingStarted.ipynb`, `NeuroTechX-Exercise1.ipynb`) | Cross-platform InteraXon **`muse-io`** SDK streaming **OSC** (`pyOSC`) and **ZeroMQ** (`pyZMQ`) on Windows, macOS, and Linux for **Muse 2014**. |
| **`v1.0-lsl-2018`**<br/>(`origin/master` @ `2ce12f3`) | **2017 – April 2018**<br/>NeuroTechTO & chapter hacknights | Hubert Banville, Dano Morrison, Sydney Swaine-Simon, `jdpigeon`, `micuat` | **Python 3.6** (Anaconda / Spyder), `numpy`, `scipy`, `scikit-learn` (`SVC`), `matplotlib` | **Lab Streaming Layer (`pylsl`)** + vendored snapshot of Alexandre Barachant's **`muse-lsl`** (`pygatt` + Bluegiga **BLED112** USB dongle for **Muse 2016 BLE** @ `256 Hz`). |
| **`v2.0.0`**<br/>(`main`, 2026) | **2026**<br/>Global NeuroTechX Chapters & Student Clubs | NeuroTechX Community (building on Cassani, Banville, Barachant, Griffiths, Chevallier, Clisson, Aristimunha, Guetschel, Carrara) | **Python 3.10–3.13** (`pyproject.toml` / `uv`), **Path A:** `pylsl` / `mne-lsl` + `scipy.signal.welch` + `scikit-learn` (Shrinkage LDA) + `pyRiemann` (`MDM` / `TangentSpace`); **Path B:** **`Timeflux`** YAML + Browser UI (`timeflux_ui`) | **Zero-hardware simulation & file replay** (`mock_eeg_stream.py`, `replay_eeg_stream.py`, `SYNTHETIC_BOARD`) + **18 EEG/biosignal profiles** via `muselsl` (native OS `bleak` BLE), `BrainFlow`, and `Timeflux` (Muse 2/S/Athena, OpenBCI Ganglion/Cyton/Daisy, PiEEG, FreeEEG32, HackEEG, BITalino, BioAmp EXG Pill, Crown, BrainBit, Unicorn, OctaFlow). |

To inspect or check out any historical version locally:

```bash
git checkout v0.1-mules-2015   # 2015 MATLAB/Octave + Python + MuLES edition
git checkout v0.2-museio-2016  # 2016 Muse-IO OSC + IPython Notebook edition
git checkout v1.0-lsl-2018     # 2018 Python 3.6 + pylsl + pygatt edition
```

---

## 2. Wider NeuroTechX & Community Workshop Lineage (2017 – 2026)

After `bci-workshop`'s last commit in 2018, the NeuroTechX open-source community—particularly **Alexandre Barachant**, **John Griffiths**, **Yannick Roy**, **Sylvain Chevallier**, **Pierre Clisson**, **Bruno Aristimunha**, **Pierre Guetschel**, **Igor Carrara**, **Raphaëlle Bertrand-Lalo**, **Sébastien Velut**, and **Marie-Constance Corsi**—developed specialized open-source toolkits and international workshops that directly inform `v2.0`:

* **2017–2024 — Stimulus-Locked Experiments (`EEG-ExPy`, formerly `eeg-notebooks`):** Initiated by Alexandre Barachant (`muse-lsl`) and led by John Griffiths with Andrey Parfenov's `BrainFlow` device layer (`NeuroTechX/EEG-ExPy`), bringing P300, N170, and SSVEP experiments to affordable headsets.
* **2018–2019 & 2026 — Deep Learning for EEG (`dl-eeg-playground` & Roy et al., *JNE* 2019):** Montreal hacknight deep-learning tutorials and systematic review (Yannick Roy, Hubert Banville, Isabela Albuquerque, Alexandre Gramfort, Tiago H. Falk, Jocelyn Faubert), followed by the 2026 `ComputationalReviewDLEEG` and `dl-eeg-playground` rebuild (*train → benchmark → audit*).
* **2019–2024 — Reproducible Benchmarking (`NeuroTechX/moabb` & `moabb_minischool`):** Pedro L. C. Rodrigues and Sylvain Chevallier's Graz 2019 MOABB workshop, CuttingGardens 2023 / 2024 `sylvchev/moabb_minischool` (with Pierre Guetschel), and the 36-dataset / 30-pipeline reproducibility benchmark (Chevallier, Carrara, Aristimunha, Guetschel et al., 2024), including Igor Carrara's pseudo-online sliding-window evaluation (`plot_pseudoonline.py`).
* **2021–2026 — Real-Time Reactive Pipelines (`Timeflux` & NTX Hackathons):** Pierre Clisson, Sylvain Chevallier, and Raphaëlle Bertrand-Lalo's NTX Hackathon @ 42 Paris masterclass (`timeflux/hackathon`), `timeflux/workshops` (`bci_thursdays_2021`, `tuni_2023`), `timeflux/ntx_data_challenge_2023`, and `timeflux/demos` (bandpower neurofeedback, oddball, EMG roshambo, P300 speller, and fast-calibration dry-EEG burst/`c-VEP` spellers).
* **2021–2024 — International BCI Meeting, Graz BCI & Neuroergonomics Workshops:**
  * Int. BCI Meeting 2021 Riemannian Geometry Workshop (`lkorczowski/BCI-2021-Riemannian-Geometry-workshop`)
  * Int. BCI Meeting 2023 W5 (*Offline & Online Open-Source Tools*: `HappyFeat`, `pyRiemann`, `Timeflux`, `MOABB` — `mccorsi/BCI-2023-Open-Source-Tool-workshop`) & W6 (*Learning from Small Datasets* — `MTangermann/BCI-2023-Workshop_Learning-from-small-datasets`)
  * 9th Graz BCI Conference 2024 & Neuroergonomics 2024 (*Designing BCIs from Theory to Real-Life Scenarios* — `Inria-NERV/Graz24-DesigningBCITools-Workshop` & `NEC24-DesigningBCI-Workshop`, co-organized by Corsi, Desbois, Clisson, Aristimunha, Guetschel, Dehais, and Velut).
* **2025–2026 — Istanbul MLSP 2025, Geometric Deep Learning (`SPD Learn`), `EEGDash` & NeurIPS Foundation Challenges:**
  * **IEEE MLSP 2025 (Istanbul, Aug 31 – Sept 3, 2025):** Special Session *Decoding the Brain Time Series* (`mlsp2025-decoding-brain.github.io`), co-organized by Bruno Aristimunha, Florian Yger, Marie-Constance Corsi, and Sylvain Chevallier—featuring **Hubert Banville** (co-creator of the original May 2015 `bci-workshop`) as keynote speaker (*"EEG Decoding in the Age of Deep Learning"*).
  * **NeurIPS 2025 & 2026 EEG/EMG Foundation Challenges** (`eeg2025/startkit`, `neural-interfaces26/2026-competition`), **`Braindecode` / `OpenEEGBench`**, **`SPD Learn`** (`spdlearn/spd_learn`), and **`EEGDash`** (`eegdash/EEGDash`).

---

## 3. What Changed Between `v1.0-lsl-2018` and `v2.0.0` (File Migration Map)

| `v1.0-lsl-2018` File | Fate in `v2.0.0` | Reason |
| :--- | :--- | :--- |
| `python/muse/muse.py` & `python/muse-lsl.py` | **Removed** (preserved on tag `v1.0-lsl-2018`) | Vendored 2017 `pygatt` snapshot required a discontinued BLED112 dongle and Muse 2016 BLE handles. Replaced by `streams/mock_eeg_stream.py`, `streams/replay_eeg_stream.py`, `streams/brainflow_to_lsl.py`, and OS-native `muselsl` (`bleak`). |
| `python/lsl-viewer.py` | **Replaced** by `exercises/01_neurofeedback.py`, `mne-lsl viewer`, and `timeflux_ui` | Background-thread `fig.canvas.draw()` crashed macOS Cocoa/Qt backends (Issue #21) and had an off-by-one XML channel parser bug. |
| `python/bci_workshop_tools.py` | **Refactored** into `src/bci_workshop/` (`dsp.py`, `lsl_buffer.py`, `classifier.py`, `audio.py`, `profiles.py`) | Fixed hardcoded `256 Hz` / `60 Hz` notch, headerless `beep.wav` + `shell=True` bug (Issue #13), empty-chunk `IndexError`, and training-set resubstitution leakage on 80%-overlapping windows. |
| `python/exercise_01.py` & `exercise_01_multichannel.py` | **Unified** into `exercises/01_neurofeedback.py` + `timeflux/neurofeedback_lsl.yaml` | Ring buffer drains up to 16,384 pending samples per tick, eliminating cumulative Matplotlib lag (Issue #14), and works across 1–32 channels automatically. |
| `python/exercise_02.py` | **Upgraded** into `exercises/02_basic_bci.py` + `exercises/03_udp_output_demo.py` + `timeflux/bci_riemann_lsl.yaml` | Uses `time.monotonic()` + inlet flush for exact calibration windows, adds Shrinkage LDA and `pyRiemann` MDM/TangentSpace, reports honest contiguous-block CV alongside naive overlap CV, and outputs LSL + UDP JSON. |
| `python/compute_feature_vector_advanced.py` | **Integrated** into `src/bci_workshop/dsp.py` | Fixed Python 2 float-slice `TypeError` (`NFFT/2`) and MuLES last-column deletion; replaced raw FFT bins with `scipy.signal.welch` log-bandpowers and band ratios. |
| `workshop_slides.pdf` | **Rebuilt** from `slides/workshop_slides.tex` (+ editable `slides/workshop_slides.md`) | Updated from 2015 Windows/MuLES slides to the 2026–27 NeuroTechX Beamer design (`beamerthemeNeuroTechX.sty`) covering LSL, multi-board safety, leakage-free evaluation, Timeflux, MOABB, and foundation-model benchmarks. |
