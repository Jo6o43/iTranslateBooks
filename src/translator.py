import openai
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from src.db_cache import get_cached_translation, save_translation
from src.config import AppConfig

def sanitize_text(text: str) -> str:
    text = text.replace('\ufffd', '')
    text = re.sub(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3000-\u303f\uff00-\uffef]', '', text)
    return text

def check_xml_integrity(original_xml: str, translated_xml: str) -> bool:
    orig_matches = re.findall(r'<t\s+id=["\']?(\d+)["\']?>', original_xml)
    trans_matches = re.findall(r'<t\s+id=["\']?(\d+)["\']?>', translated_xml)
    missing = set(orig_matches) - set(trans_matches)
    if missing:
        raise ValueError(f"LLM format error. Missing chunk IDs: {missing}")
    return True

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def _call_llm(xml_payload: str, config: AppConfig, context_str: str) -> str:
    client = openai.AsyncOpenAI(base_url=config.base_url, api_key="lm-studio")
    
    messages = [{"role": "system", "content": config.system_prompt}]
    if context_str and config.use_context:
        messages.append({"role": "user", "content": f"Previous context for reference (Do not translate this block again):\n{context_str}"})
        messages.append({"role": "assistant", "content": "Understood. I will use the previous context to ensure consistent terminology and character representation."})
        
    messages.append({"role": "user", "content": f"Translate while preserving HTML formatting:\n{xml_payload}"})
        
    response = await client.chat.completions.create(
        model=config.model_name,
        messages=messages,
        temperature=getattr(config, 'temperature', 0.4)
    )
    content = response.choices[0].message.content
    check_xml_integrity(xml_payload, content)
    usage = getattr(response, 'usage', None)
    tokens = getattr(usage, 'completion_tokens', 0) if usage else 0
    return content, tokens

async def translate_batch_cached(xml_payload: str, config: AppConfig, context_str: str = '', log_callback=None, error_log: list = None) -> tuple[str, int]:
    xml_payload = sanitize_text(xml_payload)
    
    import os
    import traceback
    epub_filename = os.path.basename(config.input_file)
    
    cached = get_cached_translation(xml_payload, epub_filename)
    if cached:
        return cached, 0
        
    try:
        translated, tokens = await _call_llm(xml_payload, config, context_str)
        save_translation(xml_payload, translated, epub_filename)
        return translated, tokens
    except Exception as e:
        error_str = str(e)
        if "Context size has been exceeded" in error_str and context_str:
            warn_msg = f"Fallback ativado: Limite de Contexto (Context Size) ultrapassado. Bloco salvo ignorando o histórico (contexto).\nConteúdo Inicial do Bloco (HTML/Parágrafo): {xml_payload[:150]}..."
            if error_log is not None:
                error_log.append(warn_msg)
            if log_callback:
                log_callback(f"\n[WARNING] Limite de Contexto ultrapassado! A tentar traduzir o bloco isoladamente sem o contexto anterior para não interromper...")
            try:
                translated, tokens = await _call_llm(xml_payload, config, "")
                save_translation(xml_payload, translated, epub_filename)
                return translated, tokens
            except Exception as e2:
                e = e2

        tb = traceback.format_exc()
        msg = f"\n[ERROR] Translation failed after 4 retries. Skipping chunk. Reason: {e}\nStacktrace: {tb}\nPayload: {xml_payload[:200]}..."
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
        if error_log is not None:
            error_log.append(f"LLM Error: {e}\nPayload snippet: {xml_payload[:100]}...\n{tb}")
        return xml_payload, 0
