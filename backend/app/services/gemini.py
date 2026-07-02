import httpx
import logging
import json
import asyncio
import time
from app.config import settings
from fastapi import HTTPException, status

logger = logging.getLogger("mindspace.gemini")

# Crisis safety keyword phrases
CRISIS_KEYWORDS = [
    "suicide", "self-harm", "self harm", "kill myself", "end my life", 
    "ending my life", "overdose", "cutting myself", "want to die", 
    "wish I was dead", "harm myself", "hurt myself"
]

CRISIS_RESPONSE = {
    "summary": "It sounds like you are going through an incredibly challenging time, and we want to make sure you are safe.",
    "detected_patterns": ["Crisis safety indicator triggered"],
    "reflection_question": "Please reach out to a trusted professional, contact a local support helpline, or text HOME to 741741 to connect with a crisis counselor immediately. You don't have to navigate this alone.",
    "model_used": "safety_filter"
}

def check_crisis_language(content: str) -> bool:
    """Pre-scan content for self-harm or crisis-related keywords."""
    cleaned = content.lower()
    return any(keyword in cleaned for keyword in CRISIS_KEYWORDS)

def generate_local_fallback(content: str) -> dict:
    """Generate a deterministic fallback reflection in Python when Gemini is down."""
    # Summarize: take the first 120 characters or 2 sentences
    sentences = [s.strip() for s in content.split(".") if s.strip()]
    summary_text = ""
    if sentences:
        first_few = sentences[:2]
        summary_text = " ".join(first_few) + "."
    else:
        summary_text = "Empty journal entry."
        
    summary = f"AI service is temporarily busy. A fallback reflection has been generated. Entry summary: {summary_text}"
    
    # Identify simple keywords
    common_feelings = ["happy", "sad", "anxious", "stress", "tired", "energy", "sleep", "productive", "work", "focus", "rest", "family", "friend", "creative"]
    detected = []
    content_lower = content.lower()
    for word in common_feelings:
        if word in content_lower:
            detected.append(word.capitalize())
    if not detected:
        detected = ["Reflection"]
        
    # Take at most 3 patterns
    detected = detected[:3]
    
    # Generate one reflective question
    question = "You reflected on your thoughts today. What is one small insight you can carry forward from this experience?"
    
    return {
        "summary": summary,
        "detected_patterns": detected,
        "reflection_question": question,
        "model_used": "Local Fallback"
    }

async def generate_reflection_from_gemini(journal_content: str) -> dict:
    """Scan journal content for safety, and call Gemini API to generate structured reflection."""
    if check_crisis_language(journal_content):
        logger.warning("Crisis safety trigger activated! Bypassing Google Gemini API.")
        return CRISIS_RESPONSE

    # Determine if mock fallback should activate
    is_key_missing = (
        not settings.GEMINI_API_KEY 
        or settings.GEMINI_API_KEY.strip() == "" 
        or settings.GEMINI_API_KEY == "mock-key-for-local-testing"
    )
    should_mock = settings.MOCK_AI or is_key_missing

    if should_mock:
        if settings.MOCK_AI:
            logger.info("Using mock reflection because MOCK_AI=true.")
        else:
            logger.info("Using mock reflection because GEMINI_API_KEY is missing.")
            
        return {
            "summary": "You are taking time to examine your daily thoughts. Setting targets and logging events shows excellent self-awareness.",
            "detected_patterns": ["Self-awareness", "Goal tracking"],
            "reflection_question": "What is one small step you can take tomorrow to build on today's progress?",
            "model_used": f"mock-{settings.GEMINI_MODEL}"
        }

    logger.info(f"Using Gemini model: {settings.GEMINI_MODEL}")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    
    prompt = f"""
    Analyze the following user's private journal entry.
    
    Journal Entry:
    \"\"\"{journal_content}\"\"\"
    
    You must produce a JSON response matching the following schema structure:
    {{
      "summary": "A concise 2-sentence summary of the reflection. Highlight any positive observations of their choices or progress.",
      "detected_patterns": ["Pattern 1", "Pattern 2", "Pattern 3"], // List emotional patterns, triggers, or feelings identified (maximum 3)
      "reflection_question": "One thoughtful, open-ended question to encourage further writing."
    }}
    
    CRITICAL ETHICAL CONSTRAINT: You must never diagnose medical or mental health conditions, provide therapy, or act as a medical professional. Speak with humility, act as a reflective companion, and make observations rather than claiming clinical certainty.
    """

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Executing API request to Google Gemini {settings.GEMINI_MODEL} service...")
            response = await client.post(url, json=payload, timeout=20.0)
            
            if response.status_code != 200:
                logger.error(f"Gemini API returned HTTP error {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI service is temporarily busy."
                )
                
            res_data = response.json()
            text_content = res_data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text_content)
            
            # Ensure required JSON keys are present in parsed response
            if "summary" not in parsed or "detected_patterns" not in parsed or "reflection_question" not in parsed:
                raise ValueError("Parsed Gemini JSON output is missing required fields.")
                
            parsed["model_used"] = settings.GEMINI_MODEL
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to communicate or parse Gemini response: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI service is temporarily busy."
            )

async def generate_reflection_with_retry(content: str) -> dict:
    """Invoke Gemini reflection generation with exponential backoff retries."""
    delays = [0, 2, 4]
    last_error = None
    
    start_time = time.perf_counter()
    
    for attempt, delay in enumerate(delays, start=1):
        if delay > 0:
            logger.warning(f"Gemini API request failed. Retrying (attempt {attempt}/3) after {delay}s delay...")
            await asyncio.sleep(delay)
        else:
            logger.info(f"Attempting Gemini API call (attempt {attempt}/3) immediately...")
            
        try:
            res = await generate_reflection_from_gemini(content)
            duration = time.perf_counter() - start_time
            logger.info(f"Gemini API request succeeded on attempt {attempt}/3. Total duration: {duration:.3f} seconds.")
            return res
        except Exception as e:
            logger.warning(f"Attempt {attempt}/3 failed with error: {e}")
            last_error = e
            
    duration = time.perf_counter() - start_time
    logger.error(f"All 3 Gemini API attempts failed. Total duration: {duration:.3f} seconds. Error: {last_error}")
    raise last_error
