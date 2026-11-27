# Supported Acquisition, Paradigm & Modality Targets

One goal of `bci-workshop` v2.0 is that **any NeuroTechX city chapter or university student club can run the workshop with whatever hardware they already have—including zero hardware at all**.

Run `python exercises/00_check_setup.py --list-targets` to inspect the 18 built-in EEG/biosignal profiles in [`src/bci_workshop/profiles.py`](../src/bci_workshop/profiles.py). Below is the complete 22-target inventory across the NeuroTechX ecosystem.

---

## 1. Electrical Isolation & Participant Consent (Read First!)

> **CRITICAL ELECTRICAL SAFETY RULE FOR DIY & WIRED BOARDS:**
> Whenever electrodes touch human skin using wired USB, GPIO, or audio-jack hardware (**PiEEG**, **Upside Down Labs BioAmp**, **FreeEEG32**, **HackEEG**, **OpenBCI USB**, **icibici**):
> 1. **Unplug your laptop's AC wall charger** — run strictly on battery power (or use a certified medical-grade USB isolator such as ADuM3160/ADuM4160, and power Raspberry Pi boards from a standalone USB battery bank). Mains ground loops or charger fault currents must never have a path to scalp/skin electrodes.
> 2. **Explicit informed consent:** Brain and muscle recordings are sensitive physiological data. Explain what is being recorded, never pressure a student to wear a headset, and delete calibration recordings after the session unless explicit written consent is obtained.
> 3. **Educational scope:** None of the hardware or scripts in this workshop are medical devices or clinical diagnostics. See **[neurotechx.org/safety-and-ethics](https://neurotechx.org/safety-and-ethics)**.

---

## 2. Tier 0 — Zero-Hardware Simulation & Replay Targets (100% of Laptops)

| # | Profile Key | Stream Source | Rate / Channels | How to Start |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `mock` | Interactive `1/f` + 10 Hz Berger alpha + blinks/EMG | `256 Hz`, 4 ch (`TP9, AF7, AF8, TP10`) | `python streams/mock_eeg_stream.py` *(or `--profile cyton` to emulate 8 ch!)* |
| 2 | `replay` | Pre-recorded `.fif`, `.edf`, or `.csv` EEG file | File-native (`mne-lsl` `PlayerLSL` or `pylsl`) | `python streams/replay_eeg_stream.py path/to/eeg.fif` |
| 3 | `brainflow-synthetic` | BrainFlow `SYNTHETIC_BOARD` (`board_id=-1`) | `250 Hz`, 16 ch (`10-20` montage) | `python streams/brainflow_to_lsl.py --profile brainflow-synthetic` |

---

## 3. Tier 1 — Chapter & Student Club Workhorse Headsets & Open Hardware

| # | Profile Key | Hardware Target | Rate / Channels | Setup Command / Bridge |
| :-: | :--- | :--- | :--- | :--- |
| 4 | `muse2` | **InteraXon Muse 2 / Muse 2016** | `256 Hz`, 4 ch | `muselsl stream` *(native OS Bleak BLE)* or `python streams/brainflow_to_lsl.py --profile muse2` *(BlueMuse on Windows)* |
| 5 | `museS` | **InteraXon Muse S (Gen 1 / 2)** | `256 Hz`, 4 ch | `muselsl stream` or `python streams/brainflow_to_lsl.py --profile museS` |
| 6 | `museS-athena` | **InteraXon Muse S "Athena" (Gen 3)** | `256 Hz`, 4 ch | `python streams/brainflow_to_lsl.py --profile museS-athena` *(BrainFlow 5.22+)* |
| 7 | `ganglion` | **OpenBCI Ganglion** | `200 Hz`, 4 ch | `python streams/brainflow_to_lsl.py --profile ganglion` |
| 8 | `cyton` | **OpenBCI Cyton** | `250 Hz`, 8 ch | `python streams/brainflow_to_lsl.py --profile cyton --serial-port <PORT>` *(or OpenBCI GUI LSL / Timeflux `cyton.yaml`)* |
| 9 | `cyton-daisy` | **OpenBCI Cyton + Daisy** | `125 Hz`, 16 ch | `python streams/brainflow_to_lsl.py --profile cyton-daisy --serial-port <PORT>` |
| 10 | `pieeg` | **PiEEG (Raspberry Pi 4/5 ADS1299 HAT)** | `250 Hz`, 8 ch | Battery-powered Pi publishing LSL (`timeflux/demos` `lsl_pieeg.yaml` ready) |
| 11 | `freeeeg32` | **FreeEEG32 (32-ch Open Hardware)** | `512 Hz`, 32 ch | `python streams/brainflow_to_lsl.py --profile freeeeg32 --serial-port <PORT>` *(with USB isolator)* |
| 12 | `hackeeg` | **Starcat HackEEG (Arduino Due ADS1299)** | `250+ Hz`, 8–32 ch | `timeflux_hackeeg` (`hackeeg.yaml` in `timeflux/demos`) |
| 13 | `bitalino` | **BITalino / PLUX (EEG / EMG / ECG)** | `100–1000 Hz`, 1–6 ch | `timeflux_bitalino` (`bitalino.yaml` in `timeflux/demos`) or OpenSignals LSL |
| 14 | `bioamp` | **Upside Down Labs BioAmp EXG Pill** | `250–500 Hz`, 1–2 ch | `timeflux_upsidedownlabs` or Arduino/ESP32 serial→LSL *(strictly battery-powered laptop!)* |

---

## 4. Tier 2 — Commercial LSL & BrainFlow Headsets

| # | Profile Key | Hardware Target | Rate / Channels | Setup Command / Bridge |
| :-: | :--- | :--- | :--- | :--- |
| 15 | `crown` | **Neurosity Crown / Notion 1 & 2** | `256 Hz`, 8 ch | Native Neurosity LSL stream or `python streams/brainflow_to_lsl.py --profile crown` |
| 16 | `brainbit` | **BrainBit Headband** | `250 Hz`, 4 ch (`T3, T4, O1, O2`) | `python streams/brainflow_to_lsl.py --profile brainbit` |
| 17 | `unicorn` | **g.tec Unicorn Hybrid Black** | `250 Hz`, 8 ch | `python streams/brainflow_to_lsl.py --profile unicorn` or Unicorn LSL |
| 18 | `octaflow` | **Neurogate OctaFlow (OctaEEG)** | `250 Hz`, 8 ch | Native LSL output or `timeflux_octaeeg` |
| — | *LSL Passthrough* | **EMOTIV EPOC X / Insight, Bitbrain, MindAffect, ANT eego** | Vendor-native | Enable LSL outlet in vendor software (e.g., EmotivPRO LSL) — `exercises/01` & `02` auto-discover any `type='EEG'` stream! |
| — | *Historical / DIY* | **icibici (Single-channel audio EEG)** | Audio ADC | Documented in NeuroTechX hardware archives; **never use while any connected device is plugged into wall power**. |

---

## 5. Tier 3 — Sister Biosignal & Imaging Modalities in the NeuroTechX Ecosystem

Clubs running multi-week series can follow `bci-workshop` with these companion open-source projects:

* **19. Surface EMG (Gesture / Roshambo / EMG-to-Pose):** [`timeflux/demos/roshambo`](https://github.com/timeflux/demos/tree/main/roshambo) & the EMG-to-Pose track of the [Neural Interface Foundation Challenge](https://neural-interfaces26.github.io/).
* **20. Cardiac ECG / HRV Biofeedback:** [`timeflux/demos/coherence`](https://github.com/timeflux/demos/tree/main/coherence).
* **21. Optical Brain Sensing (HEG & Open fNIRS):** **HEGduino V2** (Brains@Play), **[OpenfNIRS](https://openfnirs.org/hardware/)**, and **ninjaNIRS** (BU Neurophotonics Center).
* **22. Open Electrical Impedance Tomography & Ultrasound:** **[OpenEIT](https://github.com/OpenEIT/OpenEIT)** / Spectra and **[un0rick / pic0rick](https://un0rick.cc/)** open ultrasound hardware.
