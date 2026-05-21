


import logging
import os

import subprocess



import torch


logger = logging.getLogger(__name__)

# Performance tuning
torch.backends.cudnn.benchmark = True
torch.set_num_threads(1)

# Native formats
NATIVE_AUDIO_FORMATS = {
    ".wav", ".flac", ".ogg", ".oga", ".opus",
    ".aiff", ".aif", ".aifc",
    ".au", ".snd",
    ".caf",
    ".w64", ".rf64",
    ".mp3",
    ".nist", ".sph",
    ".voc", ".svx",
}

# Requires ffmpeg
CONVERTIBLE_AUDIO_FORMATS = {
    ".mp4", ".m4a", ".aac", ".wma", ".webm",
    ".amr", ".3gp", ".mka", ".ac3", ".ape",
    ".wv", ".tta", ".spx",
}

SUPPORTED_AUDIO_FORMATS = (
    NATIVE_AUDIO_FORMATS
    | CONVERTIBLE_AUDIO_FORMATS
)


def get_file_extension(audio_filename: str) -> str:
    return os.path.splitext(
        audio_filename
    )[1].lower()




from pathlib import Path
import subprocess

def convert_to_wav(input_path) -> str:
    input_path = Path(input_path)

    output_path = input_path.with_suffix(
        input_path.suffix + ".converted.wav"
    )

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-ar",
                "16000",
                "-ac",
                "1",
                "-f",
                "wav",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )

        return str(output_path)

    except FileNotFoundError:
        raise RuntimeError("ffmpeg is not installed.")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "ffmpeg conversion failed: "
            f"{e.stderr.decode(errors='replace')}"
        )