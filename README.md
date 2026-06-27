# ⚙️ A Máquina
### Sistema de análise literária computacional
*inspirado em Georges Perec · La Machine, 1968*

---

**A Máquina** é uma aplicação de análise textual, que submete obras literárias a seis protocolos de escrutínio computacional — da estatística bruta ao grafo ontológico - gerada por inteligência artificial local. O projeto parte da peça radiofônica *La Machine* (1968), em que Perec alimenta um computador com *A Princesa de Clèves* e debate ao vivo com os resultados. Aqui, o leitor pode fazer o mesmo com qualquer texto.

---

## Protocolos

| Nº | Nome | Descrição |
|----|------|-----------|
| 00 | **Estatística** | Linhas, palavras, letras, pontuação, riqueza lexical e distribuição de frequências |
| 01 | **Operações internas** | Recitações, inversões, permutações e deformações do texto |
| 02 | **Operações externas** | Anagramas, metáteses, traduções, provérbios e transformações linguísticas |
| 03 | **Análise crítica** | Frequências, entidades, coocorrências e diversidade lexical |
| 04 | **Explosão de citações** | Associação de palavras a citações, traduções e permutações temáticas |
| 05 | **Grafo ontológico** | Rede interativa de conceitos e relações extraída por LLM local via Ollama |

---

## Requisitos

### Python
- Python 3.9 ou superior
- Dependências listadas em `requirements.txt`

```bash
pip install -r requirements.txt
```

### Ollama (para o Protocolo 05 — Grafo Ontológico)

O grafo ontológico requer um modelo de linguagem rodando localmente via [Ollama](https://ollama.com).  
Os demais protocolos funcionam sem ele.

**Instalação:**

1. Baixe e instale o Ollama em [ollama.com/download](https://ollama.com/download)
2. Inicie o servidor:
```bash
ollama serve
```
3. Baixe um modelo (escolha conforme sua RAM/VRAM disponível):

| Modelo | Tamanho | RAM mínima | Qualidade |
|--------|---------|------------|-----------|
| `ollama pull qwen2.5:3b` | ~2 GB | 4 GB | boa |
| `ollama pull llama3.2:3b` | ~2 GB | 4 GB | boa |
| `ollama pull llama3.1:8b` | ~5 GB | 8 GB | muito boa |
| `ollama pull mistral:7b` | ~4 GB | 8 GB | muito boa |

A aplicação detecta automaticamente o melhor modelo disponível.

---

## Como usar

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/a-maquina-perec.git
cd a-maquina-perec

# Instale as dependências
pip install -r requirements.txt

# (Opcional) Inicie o Ollama para o grafo ontológico
ollama serve

# Execute a aplicação
streamlit run maquina_perec.py
```

Acesse em: **http://localhost:8501**

---

## Formatos aceitos

- `.pdf` — PDFs com texto selecionável
- `.docx` / `.doc` — documentos Word
- `.txt` — texto puro (UTF-8)

Ou insira o texto diretamente pela entrada manual.

---

## Funcionamento do Grafo Ontológico

O Protocolo 05 envia amostras do texto ao modelo Ollama em duas chamadas sequenciais:

1. **Extração de nós** — o modelo identifica personagens, lugares, temas, emoções e ações narrativas
2. **Extração de arestas** — o modelo mapeia as relações entre os elementos identificados

O resultado é um grafo interativo com física de partículas: nós arrastáveis, zoom, painel de detalhes ao clique e tooltip ao hover.

A qualidade do grafo depende diretamente do modelo escolhido. Modelos maiores (7B+) produzem ontologias significativamente mais ricas.

---

## Hardware testado

| Configuração | Protocolo 05 | Tempo estimado |
|---|---|---|
| CPU apenas | ✓ (lento) | 2–4 min |
| GPU NVIDIA (CUDA) | ✓ (rápido) | 15–45 seg |
| GPU AMD (ROCm) | ✓ | variável |
| Apple Silicon | ✓ (rápido) | 20–60 seg |

> **Nota sobre CUDA:** algumas combinações de driver NVIDIA + versão do Ollama podem apresentar incompatibilidade de PTX. Nesse caso, o Ollama cai automaticamente para CPU. Atualize o driver NVIDIA para a versão mais recente para resolver.

---

## Estrutura

```
a-maquina-perec/
├── maquina_perec.py   # aplicação principal (único arquivo)
├── requirements.txt   # dependências Python
└── README.md
```

---

## Referência

> PEREC, Georges. *La Machine à analyser les romans*.  
> Émission radiophonique, ORTF, 1968.  
> Republicado em: *L'Arc*, nº 76, 1979.

---

## Licença

MIT — uso livre para fins acadêmicos e não comerciais.

