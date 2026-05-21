import asyncio

from app.processor.category import classify_grievance
from app.processor.sentiment import analyze_emotion, analyze_sentiment, derive_urgency


async def analyze(text: str, category: list[str]) -> dict:
    category_result = await asyncio.to_thread(classify_grievance, text, category)
    sentiment_result = await asyncio.to_thread(analyze_sentiment, text)
    emotion_result = await asyncio.to_thread(analyze_emotion, text)

    urgency = derive_urgency(emotion_result["label"])

    return {
        "category": category_result["category"],
        "category_confidence": category_result["confidence"],
        "sentiment": sentiment_result["label"],
        "sentiment_score": sentiment_result["score"],
        "emotion": emotion_result["label"],
        "emotion_score": emotion_result["score"],
        "urgency": urgency,
    }
