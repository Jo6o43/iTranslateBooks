import re
from typing import List

class DomBatcher:
    """Helper to group multiple BeautifulSoup tags into a single prompt input."""
    def __init__(self, max_chars=1500):
        self.max_chars = max_chars
        self.current_batch = []
        self.current_tags = []
        self.batches = [] # List of tuple (xml_string, list_of_tags)
        self.char_count = 0
        
    def add_tag(self, tag):
        content = tag.decode_contents().strip()
        if not content:
            return
            
        self.current_batch.append(content)
        self.current_tags.append(tag)
        self.char_count += len(content)
        
        if self.char_count >= self.max_chars:
            self._flush()
            
    def _flush(self):
        if not self.current_batch:
            return
        
        xml_parts = ["<batch>"]
        for i, text in enumerate(self.current_batch):
            xml_parts.append(f'<t id="{i}">{text}</t>')
        xml_parts.append("</batch>")
        
        self.batches.append(("\n".join(xml_parts), self.current_tags))
        self.current_batch = []
        self.current_tags = []
        self.char_count = 0
        
    def finish(self):
        self._flush()
        return self.batches

def parse_translated_batch(translated_xml: str) -> dict:
    """Parses the LLM output XML and returns a mapping of id -> translated text."""
    # LLMs might add markdown blocks like ```xml ... ```
    xml_str = re.sub(r'```[a-z]*\n(.*?)\n```', r'\1', translated_xml, flags=re.DOTALL)
    
    # We aggressively find <t id="x">...</t>
    results = {}
    pattern = re.compile(r'<t\s+id=["\']?(\d+)["\']?>(.*?)</t>', re.DOTALL)
    matches = pattern.findall(xml_str)
    for t_id, t_content in matches:
        results[int(t_id)] = t_content.strip()
    return results
