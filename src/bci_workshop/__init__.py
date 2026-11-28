"""NeuroTechX BCI Workshop v2.0 reusable toolkit."""

from .audio import generate_beep_wav, play_cue
from .classifier import (
    build_bci_pipeline,
    evaluate_bci_dataset,
)
from .dsp import (
    BANDS,
    OnlineFilterBank,
    compute_bandpowers,
    extract_epoch_features,
    slice_epochs,
)
from .lsl_buffer import EEGStreamBuffer
from .profiles import DEVICE_PROFILES, DeviceProfile, get_profile

__all__ = [
    "BANDS",
    "DEVICE_PROFILES",
    "DeviceProfile",
    "EEGStreamBuffer",
    "OnlineFilterBank",
    "build_bci_pipeline",
    "compute_bandpowers",
    "evaluate_bci_dataset",
    "extract_epoch_features",
    "generate_beep_wav",
    "get_profile",
    "play_cue",
    "slice_epochs",
]

__version__ = "2.0.0"
