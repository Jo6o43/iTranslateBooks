import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import openai
from tqdm import tqdm
import os

# --- CONFIGURAÇÕES ---
INPUT_FILE = "books_IN/Chivalry_of_a_Failed_Knight_Vol1.epub"
OUTPUT_FILE = "books_OUT/Chivalry_V1_Final_Pro_try2.epub"
MODEL_NAME = "qwen3-v1-8b-instruct"
BASE_URL = "http://127.0.0.1:1234/v1"

client = openai.OpenAI(base_url=BASE_URL, api_key="lm-studio")

# --- O TEU PROMPT DE ELITE (RESTAURADO E MELHORADO) ---
SYSTEM_PROMPT = """
Você é um tradutor literário de elite, especializado na localização de Light Novels para o Português de Portugal (PT-PT). 
Sua missão é realizar uma tradução fluida, respeitando as normas gramaticais e o vocabulário de Portugal.

DIRETRIZES ESTILÍSTICAS (PT-PT):
1. GERÚNDIO: Proibido o uso do gerúndio brasileiro. Utilize a construção 'estou a fazer' em vez de 'estou fazendo'.
2. PRONOMES: Utilize a colocação pronominal de Portugal (ênclise). Ex: 'deu-me' em vez de 'me deu'.
3. VOCABULÁRIO: Utilize termos de Portugal (ex: 'ecrã', 'telemóvel', 'comboio', 'casa de banho').
4. TRATAMENTO: Utilize o 'tu' para diálogos informais entre personagens. Use 'você' apenas para formalidade estrita.

TERMINOLOGIA A MANTER (NÃO TRADUZIR):
- 'Blazer', 'Device', 'Noble Art', 'Mana', 'Magic Knight'.
- NOMES: Ikki, Stella, Shizuku, Alice, Kurogane.

REGRAS TÉCNICAS DE SAÍDA:
- O texto contém etiquetas HTML (como <a href="...">). MANTÉM estas etiquetas intactas e na posição correta.
- Retorne APENAS a tradução pura do conteúdo. Sem comentários.
- Use o travessão (—) para diálogos.
"""

def translate_content(html_snippet):
    if not html_snippet.strip() or len(html_snippet) < 3:
        return html_snippet
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Traduza preservando o HTML: {html_snippet}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"\n[ERRO] Falha no parágrafo: {e}")
        return html_snippet

def process_epub():
    if not os.path.exists(INPUT_FILE):
        print(f"Erro: '{INPUT_FILE}' não encontrado!")
        return

    book = epub.read_epub(INPUT_FILE)
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    
    print(f"🚀 Tradução de Elite iniciada (PT-PT + Links + 4060 Ti)...")
    
    for item in tqdm(items, desc="Capítulos"):
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        
        # Traduzimos o conteúdo preservando a estrutura interna (links, negritos, etc)
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3']):
            original_inner_html = tag.decode_contents()
            
            if original_inner_html.strip():
                translated_html = translate_content(original_inner_html)
                tag.clear()
                # Reinsere o HTML traduzido de volta na tag
                tag.append(BeautifulSoup(translated_html, 'html.parser'))
        
        item.set_content(str(soup).encode('utf-8'))

    book.set_language('pt-PT')
    epub.write_epub(OUTPUT_FILE, book)
    print(f"\n✅ SUCESSO! Livro com links e estilo PT-PT guardado como: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_epub()