# iTranslateBooks

Uma aplicação para traduzir ficheiros EPUB localmente utilizando o LLM da sua preferência através do LM Studio ou outras APIs compatíveis (como o Ollama). Esta aplicação foca-se em preservar a estrutura original do e-book (HTML, tags, imagens) e possui lógicas avançadas para tradução de Light Novels.

## Características Principais

- **Tradução Local**: Utiliza modelos LLM locais via API (ex: LM Studio), poupando custos e garantindo privacidade.
- **Resiliência e Retoma**: As traduções em curso são guardadas em disco numa base de dados SQLite. Se a aplicação for fechada a meio de um livro, ao retomar, recomeça de onde ficou.
- **Processamento Paralelo**: Traduz múltiplos "chunks" em simultâneo com concorrência ajustável, otimizando o tempo.
- **Sistema de Prompts Dinâmicos**: Regras separadas para estilo literário (Language Prompt) e estrutura técnica (Advanced Prompt).
- **Interface Gráfica (UI)**: Uma interface moderna ao estilo "IDE" para arrastar, soltar, e acompanhar traduções.
- **Suporte CLI**: Interface de linha de comando opcional para execução automatizada.

## Requisitos

- Python 3.10+
- [LM Studio](https://lmstudio.ai/) ou outra API compatível com os standards da OpenAI.
- Modelo LLM (Recomendado: Qwen, Llama 3, etc.) com capacidade de contexto razoável (pelo menos 8k-16k, dependendo do livro).

## Instalação

1. Clone o repositório ou faça download.
2. Instale as dependências com o `pip`:
```bash
pip install -r requirements.txt
```

## Como Usar

### Usando a Interface Gráfica (UI)

1. Execute o script principal da interface gráfica:
```bash
python gui.py
```
2. Abra o **LM Studio**, carregue o seu modelo, e inicie o **Local Server** (geralmente `http://127.0.0.1:1234/v1`).
3. No iTranslateBooks, na aba **Explorer**, certifique-se de que coloca os seus EPUBs na pasta `books_IN/` (pode alterar as pastas nas **Definições**).
4. Selecione os livros, clique em **Adicionar à Fila**.
5. Em **Definições**, defina os parâmetros:
   - *Workers*: Quantas tarefas paralelas. Recomendado: 3 a 5 (depende da sua VRAM e CPU).
   - *Temperature*: `0.4` é o ideal para traduções fiéis mas não robóticas.
6. Clique em **INICIAR TRADUÇÃO** no painel da fila.

### Usando a Linha de Comando (CLI)

Pode usar o script `main.py` diretamente para executar traduções em lote ou em ficheiros individuais:

**Traduzir um ficheiro específico:**
```bash
python main.py --input "meu_livro.epub" --workers 4
```

**Traduzir todos os ficheiros na pasta `books_IN/` (default):**
```bash
python main.py --workers 3
```

> Nota: O CLI carrega por defeito as configurações avançadas (prompts, etc.) guardadas através da Interface Gráfica.

## Funcionalidades Avançadas

- **Glossário**: Nas Definições, pode escrever dicionários em tempo real (ex: `Magus: Mago`) que serão rigorosamente respeitados pelo LLM.
- **Logs e Relatórios**: Por defeito, a aplicação emite um relatório TXT contendo tempos, memória consumida e erros encontrados.
- **Drop Caps / Formatação Especial**: A aplicação reconstitui letras capitulares perdidas nas traduções e preserva negritos e itálicos isolados.
