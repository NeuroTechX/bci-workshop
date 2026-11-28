# Path B — Declarative Real-Time & Browser UI Track (`Timeflux`)

Alongside the pure-Python scripts in `exercises/` (**Path A**), `bci-workshop` v2.0 ships ready-to-run declarative graphs for **[Timeflux](https://timeflux.io)** — the open-source Python biosignal engine co-developed in the NeuroTechX Paris / CORTICO ecosystem by **Pierre Clisson**, **Sylvain Chevallier**, and **Raphaëlle Bertrand-Lalo** ([`timeflux/hackathon`](https://github.com/timeflux/hackathon), [`timeflux/demos`](https://github.com/timeflux/demos)).

## When to pick Path B (`Timeflux`) vs. Path A (`exercises/`)

| Goal | Best Path |
| :--- | :--- |
| Understand every line of LSL buffering, Welch PSD, Shrinkage LDA, and leakage auditing in pure Python | **Path A (`exercises/01_neurofeedback.py` & `02_basic_bci.py`)** |
| Launch a live **browser dashboard (`http://localhost:8000`)**, swap hardware via YAML, or run **P300 / Oddball / c-VEP spellers** at a hackathon | **Path B (`timeflux/`)** |

## Quickstart (Zero Hardware or Any LSL Headset)

1. Install Timeflux extras in a Python environment:
   ```bash
   uv pip install timeflux timeflux-dsp timeflux-ui pyriemann
   ```
2. Start any LSL EEG stream in Terminal 1 (mock, replay, `muselsl`, `brainflow_to_lsl.py`, PiEEG, or OpenBCI):
   ```bash
   python streams/mock_eeg_stream.py
   ```
3. Launch the Timeflux real-time bandpower & browser UI graph in Terminal 2:
   ```bash
   timeflux -d timeflux/neurofeedback_lsl.yaml
   ```
4. Open **`http://localhost:8000/monitor/`** in your browser to inspect live filtered EEG and alpha/beta/theta bandpowers in real time!

## Complete Turnkey Applications in `timeflux/demos`

Once `neurofeedback_lsl.yaml` is running, explore the full open-source application suite maintained at [`github.com/timeflux/demos`](https://github.com/timeflux/demos):

* **Bandpower Neurofeedback UI:** `neurofeedback/bands` (`synthetic.yaml`, `replay.yaml`, `cyton.yaml`, `bitalino.yaml`)
* **Auditory/Visual Oddball (ERP):** `oddball` (`lsl.yaml`, `cyton.yaml`, `random.yaml` + Tone.js browser stimulus)
* **EMG Rock–Paper–Scissors:** `roshambo` (`bitalino.yaml`, `replay.yaml`)
* **P300 Speller:** `speller/P300` (`lsl.yaml`, `cyton.yaml`, `hackeeg.yaml`)
* **Fast-Calibration Dry-EEG Burst / Code-VEP Speller (`c-VEP`):** `speller/CVEP` (`lsl_pieeg.yaml`, `hackeeg.yaml`, `random.yaml` — featured at Graz BCI 2024 & Neuroergonomics 2024)
* **Online rASR Artifact Cleaning:** [`timeflux/timeflux_rasr`](https://github.com/timeflux/timeflux_rasr)
