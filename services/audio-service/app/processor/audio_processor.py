import subprocess
import os

def convert_to_wav(input_path: str) -> str:
    output_path = input_path.rsplit(".", 1)[0] + ".wav"

    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        output_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_path