"""Device and simulation profiles for NeuroTechX chapters and student clubs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    key: str
    name: str
    tier: str
    sfreq: float
    channels: tuple[str, ...]
    alpha_channels: tuple[str, ...]
    backend: str
    brainflow_board: str | None = None
    notes: str = ""


DEVICE_PROFILES: dict[str, DeviceProfile] = {
    "mock": DeviceProfile(
        key="mock",
        name="Interactive Synthetic LSL Stream (Zero Hardware)",
        tier="Tier 0: Simulation",
        sfreq=256.0,
        channels=("TP9", "AF7", "AF8", "TP10"),
        alpha_channels=("TP9", "TP10"),
        backend="streams/mock_eeg_stream.py",
        notes="1/f pink background + posterior 10 Hz Berger alpha + frontal blinks/EMG.",
    ),
    "replay": DeviceProfile(
        key="replay",
        name="Recorded EEG File Replay (MNE / PlayerLSL)",
        tier="Tier 0: Simulation",
        sfreq=256.0,
        channels=("TP9", "AF7", "AF8", "TP10"),
        alpha_channels=("TP9", "TP10"),
        backend="streams/replay_eeg_stream.py",
        notes="Loops a real or bundled multi-channel EEG recording over LSL.",
    ),
    "brainflow-synthetic": DeviceProfile(
        key="brainflow-synthetic",
        name="BrainFlow SYNTHETIC_BOARD",
        tier="Tier 0: Simulation",
        sfreq=250.0,
        channels=("Fz", "C3", "Cz", "C4", "Pz", "PO7", "Oz", "PO8", "F5", "F7", "F3", "F1", "F2", "F4", "F6", "F8"),
        alpha_channels=("PO7", "Oz", "PO8"),
        backend="streams/brainflow_to_lsl.py",
        brainflow_board="SYNTHETIC_BOARD",
        notes="Exercises the full BrainFlow -> LSL pipeline without physical hardware.",
    ),
    "muse2": DeviceProfile(
        key="muse2",
        name="InteraXon Muse 2 / Muse 2016",
        tier="Tier 1: Chapter Headsets",
        sfreq=256.0,
        channels=("TP9", "AF7", "AF8", "TP10"),
        alpha_channels=("TP9", "TP10"),
        backend="muselsl or brainflow",
        brainflow_board="MUSE_2_BOARD",
        notes="Native OS BLE via `muselsl stream` (Bleak) or `brainflow_to_lsl.py --profile muse2`.",
    ),
    "museS": DeviceProfile(
        key="museS",
        name="InteraXon Muse S (Gen 1 / Gen 2)",
        tier="Tier 1: Chapter Headsets",
        sfreq=256.0,
        channels=("TP9", "AF7", "AF8", "TP10"),
        alpha_channels=("TP9", "TP10"),
        backend="muselsl or brainflow",
        brainflow_board="MUSE_S_BOARD",
        notes="Soft headband; stream with `muselsl stream` or `brainflow_to_lsl.py --profile museS`.",
    ),
    "museS-athena": DeviceProfile(
        key="museS-athena",
        name="InteraXon Muse S Athena (Gen 3)",
        tier="Tier 1: Chapter Headsets",
        sfreq=256.0,
        channels=("TP9", "AF7", "AF8", "TP10"),
        alpha_channels=("TP9", "TP10"),
        backend="brainflow",
        brainflow_board="MUSE_S_ATHENA_BOARD",
        notes="Uses updated BLE GATT handles supported in BrainFlow 5.22+ / OpenMuse.",
    ),
    "ganglion": DeviceProfile(
        key="ganglion",
        name="OpenBCI Ganglion (4-ch)",
        tier="Tier 1: Chapter Headsets",
        sfreq=200.0,
        channels=("Fp1", "Fp2", "TP7", "TP8"),
        alpha_channels=("TP7", "TP8"),
        backend="brainflow",
        brainflow_board="GANGLION_BOARD",
        notes="4-channel EEG/EMG/ECG @ 200 Hz via native BLE or BLED112.",
    ),
    "cyton": DeviceProfile(
        key="cyton",
        name="OpenBCI Cyton (8-ch)",
        tier="Tier 1: Chapter Headsets",
        sfreq=250.0,
        channels=("Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2"),
        alpha_channels=("O1", "O2", "P7", "P8"),
        backend="brainflow or timeflux",
        brainflow_board="CYTON_BOARD",
        notes="8-channel ADS1299 @ 250 Hz via USB dongle; requires `--serial-port`.",
    ),
    "cyton-daisy": DeviceProfile(
        key="cyton-daisy",
        name="OpenBCI Cyton + Daisy (16-ch)",
        tier="Tier 1: Chapter Headsets",
        sfreq=125.0,
        channels=("Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8", "C3", "Cz", "C4", "P7", "P3", "Pz", "P4", "O1", "O2"),
        alpha_channels=("O1", "O2", "P3", "Pz", "P4"),
        backend="brainflow",
        brainflow_board="CYTON_DAISY_BOARD",
        notes="16-channel ADS1299 @ 125 Hz; great for multi-channel pyRiemann Motor Imagery.",
    ),
    "pieeg": DeviceProfile(
        key="pieeg",
        name="PiEEG (Raspberry Pi 4/5 ADS1299 Shield)",
        tier="Tier 1: Open Hardware",
        sfreq=250.0,
        channels=("Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"),
        alpha_channels=("Ch7", "Ch8"),
        backend="lsl / timeflux",
        notes="Run PiEEG LSL publisher on battery-isolated Pi (`lsl_pieeg.yaml` in Timeflux). NEVER connect Pi to mains wall power while electrodes touch skin.",
    ),
    "freeeeg32": DeviceProfile(
        key="freeeeg32",
        name="FreeEEG32 (32-ch Open Hardware)",
        tier="Tier 1: Open Hardware",
        sfreq=512.0,
        channels=tuple(f"EEG{i}" for i in range(1, 33)),
        alpha_channels=("EEG29", "EEG30", "EEG31", "EEG32"),
        backend="brainflow",
        brainflow_board="FREEEEG32_BOARD",
        notes="32-channel open-hardware ADS1299 acquisition board via USB isolator.",
    ),
    "hackeeg": DeviceProfile(
        key="hackeeg",
        name="Starcat HackEEG (Arduino Due ADS1299)",
        tier="Tier 1: Open Hardware",
        sfreq=250.0,
        channels=("Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"),
        alpha_channels=("Ch7", "Ch8"),
        backend="timeflux_hackeeg / lsl",
        notes="Supported natively in Timeflux (`hackeeg.yaml` P300 & c-VEP demos).",
    ),
    "bitalino": DeviceProfile(
        key="bitalino",
        name="BITalino / PLUX Biosignals (EEG / EMG / ECG)",
        tier="Tier 1: Open Hardware",
        sfreq=1000.0,
        channels=("EEG", "EMG", "ECG"),
        alpha_channels=("EEG",),
        backend="timeflux_bitalino / lsl",
        notes="Ideal for hybrid EEG + EMG (`roshambo`) + ECG (`coherence`) student labs.",
    ),
    "bioamp": DeviceProfile(
        key="bioamp",
        name="Upside Down Labs BioAmp EXG Pill (Arduino / ESP32)",
        tier="Tier 1: Open Hardware",
        sfreq=250.0,
        channels=("ExG1", "ExG2"),
        alpha_channels=("ExG1",),
        backend="timeflux_upsidedownlabs / serial-lsl",
        notes="Ultra-low-cost ($20-$35) student-club sensor. Unplug laptop charger (battery power only!).",
    ),
    "crown": DeviceProfile(
        key="crown",
        name="Neurosity Crown / Notion",
        tier="Tier 2: Commercial LSL / BrainFlow",
        sfreq=256.0,
        channels=("CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"),
        alpha_channels=("PO3", "PO4", "CP3", "CP4"),
        backend="brainflow or native LSL",
        brainflow_board="CROWN_BOARD",
        notes="8-channel dry headset covering central/parietal-occipital sites.",
    ),
    "brainbit": DeviceProfile(
        key="brainbit",
        name="BrainBit Headband",
        tier="Tier 2: Commercial LSL / BrainFlow",
        sfreq=250.0,
        channels=("T3", "T4", "O1", "O2"),
        alpha_channels=("O1", "O2"),
        backend="brainflow",
        brainflow_board="BRAINBIT_BOARD",
        notes="4-channel temporal/occipital dry headband; strong posterior alpha.",
    ),
    "unicorn": DeviceProfile(
        key="unicorn",
        name="g.tec Unicorn Hybrid Black",
        tier="Tier 2: Commercial LSL / BrainFlow",
        sfreq=250.0,
        channels=("Fz", "C3", "Cz", "C4", "Pz", "PO7", "Oz", "PO8"),
        alpha_channels=("PO7", "Oz", "PO8"),
        backend="brainflow or Unicorn LSL",
        brainflow_board="UNICORN_BOARD",
        notes="8-channel hybrid dry/wet cap optimized for P300, c-VEP, and Motor Imagery.",
    ),
    "octaflow": DeviceProfile(
        key="octaflow",
        name="Neurogate OctaFlow (OctaEEG)",
        tier="Tier 2: Commercial LSL / Timeflux",
        sfreq=250.0,
        channels=("Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"),
        alpha_channels=("Ch7", "Ch8"),
        backend="native LSL or timeflux_octaeeg",
        notes="8-channel wireless EEG/EMG/ECG with native LSL & Timeflux support.",
    ),
}


def get_profile(key: str) -> DeviceProfile:
    if key not in DEVICE_PROFILES:
        valid = ", ".join(sorted(DEVICE_PROFILES))
        raise KeyError(f"Unknown device profile '{key}'. Choose one of: {valid}")
    return DEVICE_PROFILES[key]
