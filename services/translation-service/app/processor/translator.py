# Translation logic
import asyncio

# replace later with real translation model / API
async def translate(text: str, source_lang: str) -> str:
    await asyncio.sleep(1)

    return f"[Translated from {source_lang}] {text}"