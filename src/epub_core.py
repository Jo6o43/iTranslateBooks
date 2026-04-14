import os
import time
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import AppConfig
from src.chunker import DomBatcher, parse_translated_batch
from src.translator import translate_batch_cached
from src.db_cache import clear_cache_for_epub

import asyncio

async def process_document(batches, config: AppConfig, sem: asyncio.Semaphore, shared_state: dict, log_callback, progress_callback, total_batches: int):
    context_str = ""
    for batch_tuple in batches:
        if config.cancel_event.is_set():
            return
            
        xml_payload, original_tags = batch_tuple
        
        async with sem:
            translated_xml_or_fallback = await translate_batch_cached(xml_payload, config, context_str, log_callback)
            
        if config.use_context:
            context_str = translated_xml_or_fallback
            
        try:
            translated_map = parse_translated_batch(translated_xml_or_fallback)
            for i, tag in enumerate(original_tags):
                if i in translated_map and translated_map[i]:
                    if tag.name == 'img':
                        tag['alt'] = translated_map[i]
                    else:
                        tag.clear()
                        tag.append(BeautifulSoup(translated_map[i], 'html.parser'))
        except Exception as e:
            msg = f"\n[ERROR] Failed to map back translation batch: {e}"
            if log_callback: log_callback(msg)
            else: print(msg)
            
        shared_state['completed'] += 1
        if progress_callback:
            elapsed = time.time() - shared_state['start_time']
            avg_time_per_batch = elapsed / shared_state['completed']
            remaining_batches = total_batches - shared_state['completed']
            eta = avg_time_per_batch * remaining_batches
            progress_callback(shared_state['completed'], total_batches, elapsed, eta)

def process_epub(config: AppConfig, log_callback=None, progress_callback=None):
    if not os.path.exists(config.input_file):
        msg = f"[ERROR] Input file not found: {config.input_file}"
        if log_callback: log_callback(msg)
        else: print(msg)
        return False

    if log_callback: log_callback(f"[*] A carregar EPUB: {os.path.basename(config.input_file)}")
    
    book = epub.read_epub(config.input_file)
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    
    documents_batches = []
    total_batches = 0
    
    for item in items:
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        batcher = DomBatcher(max_chars=1500)
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'img']):
            batcher.add_tag(tag)
        batches = batcher.finish()
        if batches:
            documents_batches.append(batches)
            total_batches += len(batches)
        
        item._parsed_soup = soup
        
    if total_batches == 0:
        if log_callback: log_callback("[INFO] Documento sem texto detetado para traduzir.")
        return True
        
    if log_callback: log_callback(f"[*] Tradução em andamento. Total de Envios (Chunks): {total_batches}")
    
    shared_state = {'completed': 0, 'start_time': time.time()}
    sem = asyncio.Semaphore(config.max_workers)
    
    async def run_all():
        tasks = [asyncio.create_task(process_document(batches, config, sem, shared_state, log_callback, progress_callback, total_batches)) for batches in documents_batches]
        await asyncio.gather(*tasks)
        
    asyncio.run(run_all())
    
    if config.cancel_event.is_set():
        if log_callback: log_callback("[WARNING] Tradução abortada pelo utilizador.")
        return False
        
    if log_callback: log_callback("[*] Tradução das tags concluída. Reconstruindo EPUB...")
    for item in items:
        if hasattr(item, '_parsed_soup'):
            item.set_content(str(item._parsed_soup).encode('utf-8'))

    book.set_language('pt-BR')
    
    # Atualizar Metadados
    titles = book.get_metadata('DC', 'title')
    if titles:
        # Pega no primeiro título e acrescenta "[PT-BR]"
        original_title = titles[0][0]
        # Limpar titles anteriores
        book.metadata['http://purl.org/dc/elements/1.1/']['title'] = []
        book.set_title(f"{original_title} [PT-BR]")
        if log_callback: log_callback(f"[INFO] Título do livro atualizado para: {original_title} [PT-BR]")

    os.makedirs(os.path.dirname(config.output_file) or '.', exist_ok=True)
    epub.write_epub(config.output_file, book)
    
    success_msg = f"[SUCCESS] Livro traduzido e renderizado. Concluído em: {config.output_file}"
    if log_callback: log_callback(success_msg)
    else: print(success_msg)
    
    epub_filename = os.path.basename(config.input_file)
    clear_cache_for_epub(epub_filename)
    if log_callback: log_callback(f"[INFO] Cache da database deletada para o arquivo processado: {epub_filename}.")
    return True
