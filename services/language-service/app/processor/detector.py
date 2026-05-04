# Language detection logic
# super simple placeholder — replace later with langdetect / fasttext

def detect_language(text: str) -> str:
    text = text.lower()

    # dumb heuristic (good enough for now)
    if all(ord(c) < 128 for c in text):
        return "en"
    return "non-en"