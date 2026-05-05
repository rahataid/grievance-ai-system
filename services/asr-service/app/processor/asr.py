import asyncio

# Replace this later with Whisper / actual ASR
async def transcribe(audio_path: str) -> str:
    await asyncio.sleep(1)
    return f"Transcription of {audio_path}"