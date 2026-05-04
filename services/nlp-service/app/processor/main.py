import asyncio

async def analyze(text: str) -> dict:
    await asyncio.sleep(1)

    text_lower = text.lower()

    # 🧠 fake sentiment logic
    if any(w in text_lower for w in ["angry", "hate", "bad", "terrible"]):
        sentiment = "negative"
        emotion = "anger"
        category = "complaint"
    elif any(w in text_lower for w in ["happy", "good", "great", "love"]):
        sentiment = "positive"
        emotion = "joy"
        category = "feedback"
    else:
        sentiment = "neutral"
        emotion = "calm"
        category = "general"

    return {
        "sentiment": sentiment,
        "emotion": emotion,
        "category": category
    }