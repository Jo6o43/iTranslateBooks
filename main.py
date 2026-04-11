import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import openai
from tqdm import tqdm
import os
import re

INPUT_FILE = "books_IN/Rakudai Kishi no Eiyuutan - 01.epub"
OUTPUT_FILE = "books_OUT/Rakudai Kishi no Eiyuutan - 01_try3.epub"
MODEL_NAME = "qwen3-v1-8b-instruct"
BASE_URL = "http://127.0.0.1:1234/v1"

client = openai.OpenAI(base_url=BASE_URL, api_key="lm-studio")

SYSTEM_PROMPT = """
You are an elite literary translator specializing in localizing Light Novels into Brazilian Portuguese (PT-BR).
Your mission is to provide a fluent, pleasant, and natural translation, respecting the stylistic norms of Brazil.

STYLISTIC GUIDELINES (PT-BR):
1. GERUND: Use the natural Brazilian gerund natively (e.g., 'estou fazendo' instead of 'estou a fazer').
2. PRONOUNS: Use natural Brazilian pronominal placement. It can sound more fluent to use proclisis (e.g., 'me deu' instead of 'deu-me').
3. VOCABULARY: Use Brazilian vocabulary (e.g., 'tela', 'celular', 'trem', 'banheiro', 'geladeira').
4. ADDRESS: Default to using 'você' for dialogues, preserving the classic informality of Light Novels.

TERMINOLOGY TO KEEP (DO NOT TRANSLATE):
- 'Blazer', 'Device', 'Noble Art', 'Mana', 'Magic Knight'.
- NAMES: Ikki, Stella, Shizuku, Alice, Kurogane.

TECHNICAL OUTPUT RULES:
- The text contains HTML tags (such as <a href="...">). KEEP these tags intact and in their correct original positions.
- Return ONLY the pure translation of the content. No comments, no explanations.
- Use the em dash (—) for dialogues.
"""

def translate_content(html_snippet):
    if not html_snippet.strip() or len(html_snippet) < 3:
        return html_snippet
    
    html_snippet = html_snippet.replace('\ufffd', '')
    html_snippet = re.sub(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u3000-\u303f\uff00-\uffef]', '', html_snippet)
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Translate while preserving HTML formatting: {html_snippet}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"\n[ERROR] Translation failed for snippet: {e}")
        return html_snippet

def process_epub():
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input file not found: {INPUT_FILE}")
        return

    book = epub.read_epub(INPUT_FILE)
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    
    print("Starting translation process...")
    
    for item in tqdm(items, desc="Chapters"):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3']):
            original_inner_html = tag.decode_contents()
            
            if original_inner_html.strip():
                translated_html = translate_content(original_inner_html)
                tag.clear()
                tag.append(BeautifulSoup(translated_html, 'html.parser'))
        
        item.set_content(str(soup).encode('utf-8'))

    book.set_language('pt-BR')
    epub.write_epub(OUTPUT_FILE, book)
    print(f"\n[SUCCESS] Translation completed successfully. Saved as: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_epub()