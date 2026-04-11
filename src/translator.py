import openai
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import BASE_URL, MODEL_NAME, SYSTEM_PROMPT
from src.db_cache import get_cached_translation, save_translation

client = openai.OpenAI(base_url=BASE_URL, api_key="lm-studio")

class TranslationError(Exception):
    pass

def sanitize_text(text: str) -> str:
    text = text.replace('\ufffd', '')
    text = re.sub(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3000-\u303f\uff00-\uffef]', '', text)
    return text

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def _call_llm(xml_payload: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate while preserving HTML formatting:\n{xml_payload}"}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

def translate_batch_cached(xml_payload: str) -> str:
    xml_payload = sanitize_text(xml_payload)
    
    cached = get_cached_translation(xml_payload)
    if cached:
        return cached
        
    try:
        translated = _call_llm(xml_payload)
        save_translation(xml_payload, translated)
        return translated
    except Exception as e:
        print(f"\n[ERROR] Translation failed after 4 retries. Skipping chunk. Reason: {e}")
        return xml_payload # Fallback: return original if it completely fails
