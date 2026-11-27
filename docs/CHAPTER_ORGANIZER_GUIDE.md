# Chapter & Student Club Organizer Guide (Running a 2.5-Hour Workshop)

This guide distills ten years of NeuroTechX HackNight and university club lessons into a repeatable run-of-show—especially for the common scenario where **30 people bring laptops, Wi-Fi is congested, and you only have 0 to 4 EEG headsets in the room**.

---

## 1. One Week Before the Event

1. **Send the 2-line pre-install instructions** from [`README.md`](../README.md) so attendees run `uv sync` (or `pip install -e .`) and `python exercises/00_check_setup.py --self-test` at home.
2. **Prepare a USB stick fallback** containing wheel files (`pip download -d wheels .`) in case venue Wi-Fi drops.
3. **Charge headsets & bring consumables:**
   * Alcohol wipes / skin prep pads (crucial for forehead/mastoid impedance on dry Muse/BrainBit sensors).
   * Spare AAA/LiPo batteries (OpenBCI) or USB battery banks (PiEEG / BioAmp).
   * Remind participants with wired DIY boards to **charge their laptops beforehand** so they can unplug AC wall chargers during live recording.

---

## 2. Solving the "30 Laptops, 2 Headsets" Bottleneck

Do **not** spend 45 minutes trying to pair Bluetooth headsets on 30 laptops! Instead:

1. **Every attendee runs on `streams/mock_eeg_stream.py` (or `replay_eeg_stream.py`) first.** Everyone gets live filtered traces, Welch PSD bandpower bars, and a working binary classifier on their own laptop within 5 minutes.
2. **Set up 1–3 dedicated "Hardware Stations"** (facilitator laptops already paired to a Muse, OpenBCI, Crown, or PiEEG):
   * Note that **Lab Streaming Layer (LSL) broadcasts over the local LAN** (if multicast is permitted on a dedicated router) *or* volunteers can rotate in 5-minute turns at the Hardware Stations to test blinks, jaw clenches, and the Eyes-Closed Berger alpha effect on real brain signals!

---

## 3. Recommended 150-Minute Run-of-Show

| Time | Segment | Material |
| :--- | :--- | :--- |
| **0:00 – 0:25** | **1. Intro to BCIs, Signals & Safety** | `workshop_slides.pdf` (Slides 1–10): Closed-loop BCI diagram, oscillatory rhythms vs. ERPs, why artifacts (`100 µV` blinks/EMG) dwarf cortical EEG (`10 µV`), and battery isolation / consent. |
| **0:25 – 0:40** | **2. Stream Verification (`Exercise 00`)** | Everyone starts `python streams/mock_eeg_stream.py` in Terminal 1 and runs `python exercises/00_check_setup.py` in Terminal 2. |
| **0:40 – 1:15** | **3. Neurofeedback & Berger Effect (`Exercise 01`)** | Run `python exercises/01_neurofeedback.py` (adjust `--mains 50` in 50 Hz regions). Compare simulated state switches, then rotate volunteers onto Hardware Stations to observe real blinks, jaw clenches, and Eyes-Closed 8–12 Hz alpha rise! |
| **1:15 – 1:25** | *Short Break & Headset Rotation* | Wipe dry sensors with alcohol pads between participants. |
| **1:25 – 2:05** | **4. Build & Audit a Live Binary BCI (`Exercise 02`)** | Slides 13–18 + `python exercises/02_basic_bci.py --clf lda` (and `--clf riemann-mdm` if `pyriemann` is installed). Discuss **why naive random CV on overlapping windows cheats** vs. honest contiguous-block CV! |
| **2:05 – 2:30** | **5. Mini-Hack: Hook Up an Output (`Exercise 03` & `Timeflux`)** | Pipe UDP JSON (`exercises/03_udp_output_demo.py`) into sound, p5.js/Three.js, or launch `timeflux -d timeflux/neurofeedback_lsl.yaml` (`http://localhost:8000`). Point interested students to `EEG-ExPy`, `MOABB`, and `dl-eeg-playground`. |

---

## 4. Customizing the Slides for Your Chapter or Club

* **Zero-LaTeX option:** Edit [`slides/workshop_slides.md`](../slides/workshop_slides.md) in any text editor and present with [Marp](https://marp.app/) (VS Code extension or CLI) or Reveal.js.
* **LaTeX Beamer option:** Edit [`slides/workshop_slides.tex`](../slides/workshop_slides.tex) (which uses the shared 2026–27 `beamerthemeNeuroTechX.sty`) and compile in 2 seconds with [Tectonic](https://tectonic-typesetting.github.io/):
  ```bash
  cd slides && tectonic -X compile --outdir .. workshop_slides.tex
  ```
