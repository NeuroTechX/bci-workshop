# Step-by-Step Participant Instructions

Welcome to the **NeuroTechX Hands-On BCI Workshop**! Please complete **Section 1 (Installation & Self-Test)** before arriving so we can spend our time together exploring real brain signals and building live BCIs.

---

## 1. Installation & 30-Second Self-Test

### Option A — Recommended (`uv`, macOS / Linux / Windows)

1. Install `uv` if you don't have it yet: <https://docs.astral.sh/uv/getting-started/installation/>
2. Clone this repository and install dependencies:
   ```bash
   git clone https://github.com/NeuroTechX/bci-workshop.git
   cd bci-workshop
   uv venv
   uv pip install -e ".[riemann,dev]"
   ```
3. Run the self-test:
   ```bash
   uv run python exercises/00_check_setup.py --self-test
   ```
   You should see `[OK]` next to `numpy`, `scipy`, `sklearn`, `matplotlib`, `pylsl`, `pyriemann`, WAV cue generation, and the live LSL stream check!

### Option B — Standard `venv` + `pip` (Python 3.10+)

```bash
git clone https://github.com/NeuroTechX/bci-workshop.git
cd bci-workshop
python3 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[riemann,dev]"
python exercises/00_check_setup.py --self-test
```

---

## 2. Starting an EEG Stream (Terminal 1)

Keep **Terminal 1** running throughout the workshop to stream EEG onto **Lab Streaming Layer (LSL)**. Pick the option matching your setup (see [`docs/TARGETS.md`](docs/TARGETS.md) for all 22 targets):

* **No headset (every laptop works!):**
  ```bash
  python streams/mock_eeg_stream.py
  ```
* **Replay a recorded `.fif`, `.edf`, or `.csv` EEG file:**
  ```bash
  python streams/replay_eeg_stream.py path/to/recording.fif
  ```
* **Muse 2 / Muse S (native Bluetooth LE via `muselsl` or `BrainFlow`):**
  ```bash
  uv pip install muselsl bleak
  muselsl stream
  ```
  *(Or for Muse S "Athena" / OpenBCI / Crown / BrainBit / Unicorn / FreeEEG32 via BrainFlow:)*
  ```bash
  uv pip install brainflow pyserial
  python streams/brainflow_to_lsl.py --profile muse2
  ```
  > **Safety check:** If using any wired/DIY board (OpenBCI USB, PiEEG, BioAmp EXG Pill, FreeEEG32), **unplug your laptop's AC wall charger** and run on battery power!

---

## 3. Exercise 01 — Real-Time Neurofeedback & Artifacts (Terminal 2)

```bash
python exercises/01_neurofeedback.py          # add --mains 50 outside 60 Hz regions
```

### Things to try:
1. **Artifacts vs. brainwaves:** Blink twice (`AF7`/`AF8` frontal deflection) and gently clench your jaw (broadband `20–45 Hz` muscle EMG across channels). Notice how 100 µV muscle artifacts are 5–10× larger than cortical EEG!
2. **The Berger Effect (1929):** Sit completely still with relaxed facial muscles and **close your eyes for 10–15 seconds**. Watch the **8–12 Hz Alpha** bar and the rolling Relative Alpha curve climb on posterior/temporal sensors (`TP9`/`TP10` or `O1`/`O2`), then drop as soon as you open your eyes.

---

## 4. Exercise 02 — Train & Audit Your Own Live Binary BCI

```bash
python exercises/02_basic_bci.py --clf lda
```

1. **Record Class 0 (`16s`):** Keep your eyes open and facial muscles relaxed (try **not** to cheat with jaw clenches!).
2. **Record Class 1 (`16s`):** Close your eyes and relax to boost posterior `8–12 Hz` alpha.
3. **Inspect the Leakage Audit printout:**
   * Notice the gap between **Training resubstitution** / **Naive random CV on overlapping windows** (which leaks correlated neighbors across train and test) and **Contiguous temporal block CV** (your honest generalization score!).
4. **Compare Riemannian Geometry (`pyRiemann`):**
   Re-run with spatial covariance classification (Barachant, Chevallier et al.):
   ```bash
   python exercises/02_basic_bci.py --clf riemann-mdm
   ```

---

## 5. Exercise 03 — Hook Your BCI Up to Anything (Hackathon Bridge)

While `02_basic_bci.py` is running in Terminal 2, open **Terminal 3**:

```bash
python exercises/03_udp_output_demo.py
```

`02_basic_bci.py` streams JSON packets (`{"class": 1, "prob_class1": 0.84, ...}`) to `udp://127.0.0.1:5005` *and* onto an LSL stream named `BCI_Decisions`. Modify `03_udp_output_demo.py`—or switch to **Path B (`timeflux/`)**—to drive audio, visuals, games, or robotics!
