"""
A Máquina — inspirado em Georges Perec (1968)
Análise computacional de textos literários.
"""

import streamlit as st

st.set_page_config(
    page_title="A Máquina — Georges Perec",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import random
import re
import string
import json
import math
from collections import Counter

# ── Leitura de arquivos ──────────────────────────────────────────────────────

def ler_pdf(arquivo):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(arquivo)
        return "".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        return f"[erro ao ler PDF: {e}]"

def ler_docx(arquivo):
    try:
        from docx import Document
        return "\n".join(p.text for p in Document(arquivo).paragraphs)
    except Exception as e:
        return f"[erro ao ler DOCX: {e}]"

def ler_txt(arquivo):
    try:
        return arquivo.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"[erro ao ler TXT: {e}]"

def carregar_texto(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith(".pdf"):   return ler_pdf(arquivo)
    if nome.endswith((".docx",".doc")): return ler_docx(arquivo)
    return ler_txt(arquivo)

# ── Utilitários ───────────────────────────────────────────────────────────────

STOPWORDS = set([
    'the','a','an','of','in','is','are','was','were','be','been','being',
    'have','has','had','do','does','did','will','would','could','should',
    'may','might','must','shall','can','and','but','or','nor','for','yet',
    'so','as','at','by','if','on','to','up','it','its','he','she','we',
    'they','you','i','me','him','her','us','them','my','your','his','our',
    'their','this','that','these','those','what','which','who','when',
    'where','why','how','not','no','only','than','too','very','just','all',
    'both','each','few','more','most','other','some','such','into','with',
    'from','about','between','through','during','before','after','then',
    'once','here','there','any','also','even','still','back','way','well',
    'de','da','do','das','dos','em','na','no','nas','nos','um','uma',
    'uns','umas','que','se','com','por','para','mas','ou','ao','aos',
    'pelo','pela','pelos','pelas','seu','sua','seus','suas','ele','ela',
    'eles','elas','lhe','lhes','me','te','já','mais','como','quando',
    'bem','muito','também','só','ainda','onde','nem','entre','até','sem',
    'foi','ser','ter','está','são','isso','esse','essa','aqui','ali',
])

def tokenizar(texto):
    return re.findall(r'\b[a-záéíóúâêîôûãõàèìòùäëïöüçñ\w]+\b', texto.lower())

def linhas(texto):
    return [l.strip() for l in texto.split('\n') if l.strip()]

def classificar_palavras(palavras):
    try:
        import nltk
        tagged = nltk.pos_tag(palavras)
        cats = {"substantivos":[],"verbos":[],"adjetivos":[],"advérbios":[],"outros":[]}
        tag_map = {
            "NN":"substantivos","NNS":"substantivos","NNP":"substantivos","NNPS":"substantivos",
            "VB":"verbos","VBD":"verbos","VBG":"verbos","VBN":"verbos","VBP":"verbos","VBZ":"verbos",
            "JJ":"adjetivos","JJR":"adjetivos","JJS":"adjetivos",
            "RB":"advérbios","RBR":"advérbios","RBS":"advérbios",
        }
        for p, tag in tagged:
            cats[tag_map.get(tag,"outros")].append(p)
        return cats
    except Exception:
        return {"palavras": palavras}

def extrair_palavra_ancora(texto):
    palavras = re.findall(r'\b[a-záéíóúâêîôûãõàèìòùäëïöüç]+\b', texto.lower())
    filtradas = [p for p in palavras if p not in STOPWORDS and len(p) > 4]
    if not filtradas:
        return "essência"
    freq = Counter(filtradas)
    sufixos = ('ção','dade','ismo','eza','ura','ência','ância','tion','ness','ity','ism','ence','ment')
    for p, _ in freq.most_common(10):
        if any(p.endswith(s) for s in sufixos):
            return p
    return freq.most_common(1)[0][0]

def traducoes_palavra(palavra):
    dicionario = {
        "rest":     {"pt":"repouso","fr":"repos","de":"Ruhe","es":"reposo","it":"riposo","ja":"休み","la":"quies","ar":"راحة"},
        "silence":  {"pt":"silêncio","fr":"silence","de":"Schweigen","es":"silencio","it":"silenzio","ja":"沈黙","la":"silentium","ar":"صمت"},
        "peace":    {"pt":"paz","fr":"paix","de":"Friede","es":"paz","it":"pace","ja":"平和","la":"pax","ar":"سلام"},
        "death":    {"pt":"morte","fr":"mort","de":"Tod","es":"muerte","it":"morte","ja":"死","la":"mors","ar":"موت"},
        "life":     {"pt":"vida","fr":"vie","de":"Leben","es":"vida","it":"vita","ja":"生命","la":"vita","ar":"حياة"},
        "love":     {"pt":"amor","fr":"amour","de":"Liebe","es":"amor","it":"amore","ja":"愛","la":"amor","ar":"حب"},
        "time":     {"pt":"tempo","fr":"temps","de":"Zeit","es":"tiempo","it":"tempo","ja":"時間","la":"tempus","ar":"وقت"},
        "memory":   {"pt":"memória","fr":"mémoire","de":"Erinnerung","es":"memoria","it":"memoria","ja":"記憶","la":"memoria","ar":"ذاكرة"},
        "freedom":  {"pt":"liberdade","fr":"liberté","de":"Freiheit","es":"libertad","it":"libertà","ja":"自由","la":"libertas","ar":"حرية"},
        "truth":    {"pt":"verdade","fr":"vérité","de":"Wahrheit","es":"verdad","it":"verità","ja":"真実","la":"veritas","ar":"حقيقة"},
        "beauty":   {"pt":"beleza","fr":"beauté","de":"Schönheit","es":"belleza","it":"bellezza","ja":"美","la":"pulchritudo","ar":"جمال"},
        "dream":    {"pt":"sonho","fr":"rêve","de":"Traum","es":"sueño","it":"sogno","ja":"夢","la":"somnium","ar":"حلم"},
        "soul":     {"pt":"alma","fr":"âme","de":"Seele","es":"alma","it":"anima","ja":"魂","la":"anima","ar":"روح"},
        "word":     {"pt":"palavra","fr":"mot","de":"Wort","es":"palabra","it":"parola","ja":"言葉","la":"verbum","ar":"كلمة"},
        "light":    {"pt":"luz","fr":"lumière","de":"Licht","es":"luz","it":"luce","ja":"光","la":"lux","ar":"ضوء"},
        "darkness": {"pt":"trevas","fr":"obscurité","de":"Dunkel","es":"oscuridad","it":"oscurità","ja":"暗闇","la":"tenebrae","ar":"ظلام"},
        "breath":   {"pt":"sopro","fr":"souffle","de":"Hauch","es":"aliento","it":"respiro","ja":"息","la":"spiritus","ar":"نفس"},
        "waiting":  {"pt":"espera","fr":"attente","de":"Warten","es":"espera","it":"attesa","ja":"待機","la":"expectatio","ar":"انتظار"},
    }
    p = palavra.lower()
    if p in dicionario:
        return dicionario[p]
    for k, v in dicionario.items():
        if p in v.values():
            return v
    # fallback: variações fonéticas
    return {"pt": palavra, "fr": palavra+"e", "de": palavra.capitalize(),
            "es": palavra, "it": palavra+"o", "ja": "…", "la": palavra+"us", "ar": "…"}

# ── PROTOCOLO 0 ──────────────────────────────────────────────────────────────

def protocolo_zero(texto):
    palavras = tokenizar(texto)
    ls = linhas(texto)
    letras = [c for c in texto.lower() if c.isalpha()]
    pont = Counter(c for c in texto if c in '.,;:!?-—"\'()[]{}…')
    return {
        "01: número de linhas": len(ls),
        "02: número de palavras": len(palavras),
        "03: número de letras": len(letras),
        "04: distribuição de pontuação": dict(pont),
        "05: frequência de letras (top 10)": Counter(letras).most_common(10),
        "07: vocabulário único": len(set(palavras)),
        "022: média de palavras/linha": round(len(palavras)/len(ls), 2) if ls else 0,
        "08: índice de riqueza lexical (TTR)": round(len(set(palavras))/len(palavras), 3) if palavras else 0,
    }

# ── PROTOCOLO 1 ──────────────────────────────────────────────────────────────

def prot1_grupos(palavras, n):
    return [" ".join(palavras[i:i+n]) for i in range(0, len(palavras), n)]

def protocolo_um(texto):
    ls = linhas(texto)
    palavras = tokenizar(texto)
    p = palavras.copy(); random.shuffle(p)
    neg = ["não","jamais","nunca","nem"]
    neg_ls = []
    for l in ls:
        w = l.split()
        neg_ls.append(w[0]+" "+random.choice(neg)+" "+" ".join(w[1:]) if w else l)
    return {
        "111: recitação palavra a palavra": palavras,
        "112: recitação em grupos de 2": prot1_grupos(palavras, 2),
        "113: recitação em grupos de 3": prot1_grupos(palavras, 3),
        "114: recitação em grupos de 4": prot1_grupos(palavras, 4),
        "115: recitação em grupos de 6": prot1_grupos(palavras, 6),
        "116: recitação em grupos de 8": prot1_grupos(palavras, 8),
        "121: inversão": list(reversed(palavras)),
        "122: arranjo vertical": palavras,
        "123: permutação aleatória": p,
        "141: dobramento": " ".join(w+" "+w for w in palavras),
        "151: aférese": [" ".join(l.split()[1:]) if len(l.split())>1 else "" for l in ls],
        "152: apócope": [" ".join(l.split()[:-1]) if len(l.split())>1 else "" for l in ls],
        "161: negação": neg_ls,
    }

# ── PROTOCOLO 2 ──────────────────────────────────────────────────────────────

def protocolo_dois(texto):
    palavras = tokenizar(texto)
    def anagrama(pp):
        r = []
        for p in pp:
            l = list(p); random.shuffle(l); r.append("".join(l))
        return r
    def metathese(pp):
        r = []
        for p in pp:
            if len(p) >= 2:
                i = random.randint(0, len(p)-2); lp = list(p)
                lp[i], lp[i+1] = lp[i+1], lp[i]; r.append("".join(lp))
            else: r.append(p)
        return r
    pref = ["re","des","in","anti","sub","super","trans","contra","sobre","extra"]
    vogais = "aeiouáéíóú"
    def epentese(pp):
        r = []
        for p in pp:
            if len(p) > 2:
                i = random.randint(1, len(p)-1); r.append(p[:i]+random.choice(vogais)+p[i:])
            else: r.append(p)
        return r
    def isovocal(pp):
        mv = {'a':'e','e':'i','i':'o','o':'u','u':'a','á':'é','é':'í','í':'ó','ó':'ú','ú':'à'}
        return ["".join(mv.get(c,c) for c in p) for p in pp]
    chaves = [p for p in palavras if len(p) > 4]
    tpls = ["«{a}» não é «{b}»","quem tem «{a}» dispensa «{b}»",
            "mais vale «{a}» do que «{b}»","«{a}» com «{b}» faz «{c}»"]
    provs = []
    for t in tpls:
        try: provs.append(t.format(a=random.choice(chaves), b=random.choice(chaves),
                                    c=random.choice(chaves) if len(chaves)>2 else chaves[0]))
        except: pass
    sin = {
        "paz":["sossego","silêncio","calma"],"morte":["fim","extinção","repouso eterno"],
        "amor":["afeição","carinho","paixão"],"tempo":["duração","era","momento"],
        "rest":["repose","stillness","quiet"],"silence":["hush","stillness","quiet"],
    }
    trad = [random.choice(sin.get(p, [p+"†"])) for p in palavras[:30]]
    return {
        "211: anagrama": anagrama(palavras[:20]),
        "212: metátese": metathese(palavras[:20]),
        "221: próstese": [random.choice(pref)+p for p in palavras[:20]],
        "222: epêntese": epentese(palavras[:20]),
        "231: isovocalismo": isovocal(palavras[:20]),
        "242: proverbialização": provs,
        "251: tradução por sinônimos": trad,
    }

# ── PROTOCOLO 3 ──────────────────────────────────────────────────────────────

def protocolo_tres(texto):
    palavras = tokenizar(texto)
    freq = Counter(palavras).most_common(30)
    nomes = re.findall(r'\b[A-ZÁÉÍÓÚ][a-záéíóú]{2,}\b', texto)
    cooc = []
    for i in range(len(palavras)-1):
        if len(palavras[i]) > 3 and len(palavras[i+1]) > 3:
            cooc.append(f"{palavras[i]} + {palavras[i+1]}")
    return {
        "frequência das 30 palavras mais comuns": freq,
        "entidades (nomes próprios detectados)": Counter(nomes).most_common(10),
        "pares de co-ocorrência mais frequentes": Counter(cooc).most_common(10),
        "diversidade lexical": round(len(set(palavras))/len(palavras), 3) if palavras else 0,
        "hapax legomena": [p for p,c in Counter(palavras).items() if c == 1][:20],
    }

# ── PROTOCOLO 4 ──────────────────────────────────────────────────────────────

CITACOES = [
    ("Borges","A linguagem é um sistema de citações."),
    ("Wittgenstein","Os limites da minha linguagem são os limites do meu mundo."),
    ("Mallarmé","Um lance de dados jamais abolirá o acaso."),
    ("Derrida","Não há nada fora do texto."),
    ("Benjamin","A história é objeto de uma construção cujo lugar não é o tempo homogêneo."),
    ("Barthes","O autor está morto. O leitor nasce."),
    ("Foucault","O discurso não é simplesmente aquilo que traduz as lutas."),
    ("Perec","Escrever é tentar reter alguma coisa, fazer sobreviver alguma coisa."),
    ("Calvino","Um clássico é um livro que nunca terminou de dizer o que tem para dizer."),
    ("Kafka","Há esperança infinita — mas não para nós."),
    ("Beckett","Tente outra vez. Falhe outra vez. Falhe melhor."),
    ("Nietzsche","O homem ainda deve errar enquanto busca."),
    ("Hölderlin","Em breve seremos canção."),
    ("Baudelaire","O poeta é semelhante ao príncipe das nuvens."),
    ("Rilke","Ainda não sei se sou um falcão, uma tempestade ou um grande canto."),
    ("Goethe","Cinza é toda teoria; verde é a árvore dourada da vida."),
    ("Rimbaud","A verdadeira vida está ausente."),
    ("Bataille","Não sei quem fala e não sei quem ousa concluir o poema infinito."),
    ("Kierkegaard","Minha cabeça está vazia como um teatro onde acabei de me apresentar."),
    ("Novalis","Quando a palavra secreta é encontrada, toda a falsa existência se dissipa."),
    ("Neruda","Uma confusa trilha sem som nem pássaros."),
]

def protocolo_quatro(texto):
    palavras = tokenizar(texto)
    ancora = extrair_palavra_ancora(texto)
    trad = traducoes_palavra(ancora)
    chaves = [p for p in palavras if len(p) > 5 and p not in STOPWORDS]
    assoc = {}
    for chave in random.sample(chaves, min(8, len(chaves))):
        assoc[chave] = random.sample(CITACOES, min(2, len(CITACOES)))
    pals = random.sample(chaves, min(6, len(chaves)))
    perms = [f"{pals[i]} → {pals[j]}" for i in range(len(pals)) for j in range(len(pals)) if i != j]
    return {
        "ancora": ancora,
        "traducoes": trad,
        "associações livres": assoc,
        "permutações temáticas": random.sample(perms, min(12, len(perms))),
        "citações em livre alternância": random.sample(CITACOES, min(6, len(CITACOES))),
    }

# ── PROTOCOLO 5 — Grafo Ontológico ───────────────────────────────────────────

OLLAMA_PREFERENCIA = ["gemma2:2b","qwen2.5:3b","llama3.2:3b","llama3.1:8b",
                      "mistral:7b","qwen2.5:1.5b","phi3:mini"]

@st.cache_resource(show_spinner=False)
def _detectar_modelo_ollama():
    import urllib.request, urllib.error
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        data = json.loads(req.read().decode())
        instalados = {}
        for m in data.get("models", []):
            nome = m["name"]
            base = nome.split(":")[0]
            instalados[nome] = base
            instalados[base] = base
        for pref in OLLAMA_PREFERENCIA:
            base = pref.split(":")[0]
            if pref in instalados or base in instalados:
                return pref
        if instalados:
            return next(iter(data.get("models",[])))["name"]
        raise RuntimeError("Nenhum modelo encontrado no Ollama.")
    except urllib.error.URLError:
        raise RuntimeError("Ollama não está rodando. Execute: ollama serve")

def _ollama(modelo, prompt, system=None, temperatura=0.15):
    import urllib.request
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    payload = json.dumps({
        "model": modelo, "messages": msgs, "stream": False,
        "options": {"temperature": temperatura, "top_p": 0.9,
                    "repeat_penalty": 1.1, "num_predict": 2048, "num_ctx": 3000}
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=300)
    return json.loads(resp.read().decode())["message"]["content"].strip()

def _parse_json_flex(raw):
    """Tenta extrair JSON de uma string com texto extra ao redor."""
    raw = raw.strip().replace("```json","").replace("```","").strip()
    # tenta objeto completo
    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    # tenta lista
    m = re.search(r'\[[\s\S]*\]', raw)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    # objetos avulsos
    items = []
    for obj in re.findall(r'\{[^{}]+\}', raw):
        try: items.append(json.loads(obj))
        except: pass
    return items if items else None

def extrair_grafo_llm(texto, max_nos=40):
    import json as _json
    modelo = _detectar_modelo_ollama()

    # amostragem distribuída para textos longos
    MAX = 3000
    if len(texto) <= MAX:
        trecho = texto
    else:
        p = MAX // 3
        trecho = (texto[:p] + "\n[...]\n" +
                  texto[len(texto)//2-p//2:len(texto)//2+p//2] + "\n[...]\n" +
                  texto[-p:])

    SYSTEM = "Responda APENAS com JSON puro e valido. Sem markdown, sem texto extra."

    # PASSO 1 — nós
    p1 = (
        "Leia o texto literario e liste os " + str(min(max_nos, 20)) + " elementos mais importantes.\n\n"
        "Devolva APENAS este JSON (nada mais):\n"
        '[{"id":"Nome Exato","cat":"entidade","w":8},{"id":"Tema","cat":"conceito","w":6}]\n\n'
        "Categorias: entidade (personagem/lugar/obra), conceito (tema abstrato), "
        "qualidade (emocao/estado), acao (processo narrativo), relacao (vinculo estrutural)\n"
        "w = importancia 1-10\n\n"
        "TEXTO:\n" + trecho + "\n\nJSON:"
    )
    raw1 = _ollama(modelo, p1, system=SYSTEM)
    parsed1 = _parse_json_flex(raw1)

    nos_raw = []
    if isinstance(parsed1, list):
        nos_raw = parsed1
    elif isinstance(parsed1, dict):
        nos_raw = parsed1.get("nos", parsed1.get("nodes", [parsed1]))

    if not nos_raw:
        raise RuntimeError("Nenhum nó retornado. Resposta: " + raw1[:200])

    # normalizar nós
    CATS = {"entidade","conceito","qualidade","acao","ação","relacao","relação"}
    nos_dict = {}
    for n in nos_raw[:max_nos]:
        nid = str(n.get("id", n.get("nome", ""))).strip()
        if not nid: continue
        cat = str(n.get("cat", n.get("categoria", "conceito"))).strip()
        if cat not in CATS: cat = "conceito"
        cat = cat.replace("acao","ação").replace("relacao","relação")
        peso = max(1, min(10, int(n.get("w", n.get("peso", 3)))))
        desc = str(n.get("desc", n.get("descricao", ""))).strip()
        nos_dict[nid] = {"categoria": cat, "peso": peso, "descricao": desc}

    if not nos_dict:
        raise RuntimeError("Nós vazios após normalização.")

    ids_str = ", ".join('"' + k + '"' for k in list(nos_dict.keys())[:20])
    n_ar = min(40, len(nos_dict) * 2)

    # PASSO 2 — arestas
    p2 = (
        "Dados estes nos de um grafo literario:\n" + ids_str + "\n\n"
        "Crie " + str(n_ar) + " arestas. Devolva APENAS este JSON:\n"
        '[{"s":"No A","t":"No B","l":"verbo-especifico","w":5}]\n\n'
        "Regras: s e t = IDs exatos acima; l = verbo especifico (nao use: relaciona/esta/tem); w = 1-8\n"
        "Todo no deve ter ao menos uma aresta.\n\n"
        "TEXTO:\n" + trecho[:1500] + "\n\nJSON:"
    )
    raw2 = _ollama(modelo, p2, system=SYSTEM)
    parsed2 = _parse_json_flex(raw2)

    arestas_raw = []
    if isinstance(parsed2, list):
        arestas_raw = parsed2
    elif isinstance(parsed2, dict):
        arestas_raw = parsed2.get("arestas", parsed2.get("edges", []))

    # normalizar arestas
    nos_set = set(nos_dict.keys())
    nos_lower = {k.lower(): k for k in nos_set}

    def resolver(s):
        s = str(s).strip()
        if s in nos_set: return s
        sl = s.lower()
        if sl in nos_lower: return nos_lower[sl]
        for k, kc in nos_lower.items():
            if sl in k or k in sl: return kc
        return None

    arestas, vistos = [], set()
    for a in arestas_raw:
        src = resolver(a.get("s", a.get("source", "")))
        tgt = resolver(a.get("t", a.get("target", "")))
        lbl = str(a.get("l", a.get("label", "conecta"))).strip()[:35]
        w   = max(1, min(8, int(a.get("w", a.get("weight", 2)))))
        if src and tgt and src != tgt:
            ch = (min(src,tgt), max(src,tgt), lbl)
            if ch not in vistos:
                vistos.add(ch)
                arestas.append({"source":src,"target":tgt,"label":lbl,"weight":w})

    # conectar nós isolados
    conectados = {a["source"] for a in arestas} | {a["target"] for a in arestas}
    ancora = max(nos_dict, key=lambda k: nos_dict[k]["peso"])
    for nid in nos_set:
        if nid not in conectados and nid != ancora:
            candidatos = [k for k,v in nos_dict.items()
                          if k in conectados and v["categoria"]==nos_dict[nid]["categoria"] and k!=nid]
            alvo = max(candidatos, key=lambda k: nos_dict[k]["peso"]) if candidatos else ancora
            arestas.append({"source":nid,"target":alvo,"label":"integra","weight":1})

    return nos_dict, arestas

def extrair_grafo_fallback(texto, max_nos=40):
    palavras = tokenizar(texto)
    filtradas = [p for p in palavras if p not in STOPWORDS and len(p) > 4]
    freq_fil = Counter(filtradas)
    nomes = re.findall(r'\b[A-ZÁÉÍÓÚ][a-záéíóú]{3,}(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]{2,})?\b', texto)
    nomes_freq = Counter(nomes)
    nos_dict = {}
    for nome, cnt in nomes_freq.most_common(15):
        if len(nome) > 3:
            nos_dict[nome] = {"categoria":"entidade","peso":min(10,cnt*2),"descricao":""}
    sufixos = ('ção','dade','ismo','eza','ura','ência','ância','tion','ness','ity','ism','ence','ment')
    for p, cnt in freq_fil.most_common(100):
        if any(p.endswith(s) for s in sufixos) and p not in nos_dict:
            nos_dict[p] = {"categoria":"conceito","peso":min(10,cnt),"descricao":""}
        if len(nos_dict) >= max_nos: break
    genericas = {'anos','dias','vez','vezes','coisa','modo','forma','lado','lugar','parte','tipo','caso'}
    for p, cnt in freq_fil.most_common(60):
        if p not in nos_dict and p not in genericas and len(p) > 4:
            nos_dict[p] = {"categoria":"conceito","peso":min(10,cnt),"descricao":""}
        if len(nos_dict) >= max_nos: break
    nos_set = set(nos_dict.keys())
    arestas_raw = Counter()
    palavras_lower = texto.lower().split()
    for i, p in enumerate(palavras_lower):
        if p in nos_set:
            for v in palavras_lower[i+1:i+8]:
                if v in nos_set and v != p:
                    arestas_raw[tuple(sorted([p,v]))] += 1
    texto_lower = texto.lower()
    nos_list = list(nos_set)
    for i in range(len(nos_list)):
        for j in range(i+1, len(nos_list)):
            a, b = nos_list[i].lower(), nos_list[j].lower()
            pa, pb = texto_lower.find(a), texto_lower.find(b)
            if pa >= 0 and pb >= 0 and abs(pa-pb) < 400:
                arestas_raw[tuple(sorted([nos_list[i],nos_list[j]]))] += 1
    arestas = []
    for (src,tgt), peso in arestas_raw.most_common(50):
        cs, ct = nos_dict.get(src,{}).get("categoria",""), nos_dict.get(tgt,{}).get("categoria","")
        lbl = "implica" if "ação" in (cs,ct) else "associa-se" if "entidade" in (cs,ct) else "co-ocorre"
        arestas.append({"source":src,"target":tgt,"weight":peso,"label":lbl})
    return nos_dict, arestas

def extrair_grafo(texto, max_nos=40, usar_llm=True):
    if usar_llm:
        try:
            nos, ar = extrair_grafo_llm(texto, max_nos)
            return nos, ar, "ollama"
        except Exception as e:
            return *extrair_grafo_fallback(texto, max_nos), f"fallback ({e})"
    return *extrair_grafo_fallback(texto, max_nos), "fallback (manual)"

# ── Renderizador do grafo ─────────────────────────────────────────────────────

def gerar_html_grafo(nos_dict, arestas, titulo="grafo ontológico"):
    CORES = {
        "conceito":  {"fill":"#0d2d45","stroke":"#4aa8e8","glow":"#4aa8e8","text":"#7cc8f8"},
        "ação":      {"fill":"#0d2d1a","stroke":"#4ecb6e","glow":"#4ecb6e","text":"#7de89d"},
        "qualidade": {"fill":"#2d2200","stroke":"#f0c040","glow":"#f0c040","text":"#f8d870"},
        "entidade":  {"fill":"#2d1000","stroke":"#f07040","glow":"#f07040","text":"#f8a070"},
        "relação":   {"fill":"#1e0d35","stroke":"#b060f0","glow":"#b060f0","text":"#d090ff"},
    }
    nos_js = []
    for nome, dados in nos_dict.items():
        cat = dados.get("categoria","conceito")
        peso = dados.get("peso", 1)
        cor = CORES.get(cat, CORES["conceito"])
        raio = max(18, min(44, 14 + peso * 3.5))
        nos_js.append({
            "id": nome, "label": nome, "categoria": cat, "peso": peso,
            "descricao": dados.get("descricao",""),
            "raio": raio, "fill": cor["fill"], "stroke": cor["stroke"],
            "glow": cor["glow"], "textColor": cor["text"],
        })
    nos_json    = json.dumps(nos_js,  ensure_ascii=False)
    arestas_json = json.dumps(arestas, ensure_ascii=False)
    legenda = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px">'
        f'<span style="width:9px;height:9px;border-radius:50%;background:{v["fill"]};'
        f'border:1.5px solid {v["stroke"]};box-shadow:0 0 5px {v["glow"]};display:inline-block"></span>'
        f'<span style="color:#666;font-size:10px;letter-spacing:0.08em">{k}</span></span>'
        for k, v in CORES.items()
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a0a;font-family:'Courier New',monospace;overflow:hidden;user-select:none}}
#canvas{{display:block;cursor:grab}}#canvas:active{{cursor:grabbing}}
#header{{position:absolute;top:14px;left:50%;transform:translateX(-50%);text-align:center;pointer-events:none}}
#header-title{{color:#2a2a2a;font-size:10px;letter-spacing:0.25em;text-transform:uppercase}}
#header-sub{{color:#1a1a1a;font-size:9px;letter-spacing:0.15em;margin-top:2px}}
#legenda{{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);
  display:flex;flex-wrap:wrap;justify-content:center;gap:2px;
  background:rgba(8,8,8,0.92);padding:7px 16px;border:1px solid #1a1a1a;border-radius:2px}}
#controls{{position:absolute;top:14px;left:14px;display:flex;flex-direction:column;gap:6px}}
.btn{{background:rgba(10,10,10,0.9);border:1px solid #222;color:#555;
  font-family:'Courier New',monospace;font-size:9px;letter-spacing:0.1em;
  padding:5px 10px;cursor:pointer;transition:all 0.15s;text-transform:uppercase}}
.btn:hover{{border-color:#444;color:#aaa;background:#111}}.btn.active{{border-color:#666;color:#ccc}}
#stats{{position:absolute;top:14px;right:14px;color:#222;font-size:9px;
  letter-spacing:0.1em;text-align:right;line-height:1.8;pointer-events:none}}
#panel{{position:absolute;right:14px;top:50%;transform:translateY(-50%);
  width:210px;background:rgba(8,8,8,0.96);border:1px solid #1e1e1e;
  padding:14px;display:none;font-size:10px;line-height:1.9}}
#panel-name{{font-size:13px;letter-spacing:0.1em;margin-bottom:8px;
  border-bottom:1px solid #1e1e1e;padding-bottom:8px}}
#panel-close{{float:right;cursor:pointer;color:#444;font-size:11px}}
#panel-close:hover{{color:#888}}
.panel-label{{color:#333;font-size:9px;letter-spacing:0.12em}}.panel-val{{color:#888}}
#panel-connections{{margin-top:10px}}
.conn-item{{padding:3px 0;color:#444;font-size:9px;border-bottom:1px solid #111;letter-spacing:0.05em}}
.conn-item span{{color:#666}}
#tooltip{{position:fixed;background:#1a1a1a;border:1px solid #333;border-left:3px solid #4aa8e8;
  padding:8px 12px;font-family:monospace;font-size:0.75rem;color:#ccc;
  pointer-events:none;display:none;z-index:9999;max-width:220px;line-height:1.5}}
</style></head><body>
<div id="header"><div id="header-title">{titulo}</div><div id="header-sub">scroll · arraste · clique nos nós</div></div>
<div id="stats"><span id="stat-nos">nós: {len(nos_js)}</span><br><span id="stat-arestas">arestas: {len(arestas)}</span></div>
<div id="legenda">{legenda}</div>
<div id="controls">
  <button class="btn active" id="btn-labels" onclick="toggleLabels()">◎ labels</button>
  <button class="btn active" id="btn-edges"  onclick="toggleEdges()">⟷ relações</button>
  <button class="btn"        onclick="resetView()">⌂ reset</button>
  <button class="btn"  id="btn-freeze" onclick="toggleFreeze()">▶ física</button>
</div>
<div id="panel">
  <div id="panel-name"><span id="panel-close" onclick="closePanel()">✕</span><span id="panel-title"></span></div>
  <div class="panel-label">CATEGORIA</div><div class="panel-val" id="panel-cat"></div>
  <div class="panel-label" style="margin-top:6px">DESCRIÇÃO</div>
  <div class="panel-val" id="panel-desc" style="font-style:italic;color:#666;font-size:0.85em"></div>
  <div class="panel-label" style="margin-top:6px">PESO</div><div class="panel-val" id="panel-peso"></div>
  <div class="panel-label" style="margin-top:6px">CONEXÕES</div><div class="panel-val" id="panel-grau"></div>
  <div id="panel-connections"></div>
</div>
<div id="tooltip"></div>
<canvas id="canvas"></canvas>
<script>
const NOS_DATA={nos_json};
const ARESTAS_DATA={arestas_json};
const canvas=document.getElementById('canvas');
const ctx=canvas.getContext('2d');
let W,H;
function resize(){{W=canvas.width=window.innerWidth;H=canvas.height=window.innerHeight;}}
resize();window.addEventListener('resize',resize);
let offsetX=0,offsetY=0,scale=1;
let showLabels=true,showEdges=true,frozen=false;
let draggingNode=null,draggingCanvas=false;
let lastMX=0,lastMY=0,mouseDownX=0,mouseDownY=0;
let selectedNode=null,hoveredNode=null,frame=0;
const PARTICLES=Array.from({{length:60}},()=>({{
  x:Math.random()*2000-1000,y:Math.random()*2000-1000,
  r:Math.random()*1.2+0.3,a:Math.random()*0.3+0.05,
  vx:(Math.random()-0.5)*0.08,vy:(Math.random()-0.5)*0.08
}}));
const nos=NOS_DATA.map((n,i)=>{{
  const ang=(2*Math.PI*i)/NOS_DATA.length;
  const r=Math.min(280,NOS_DATA.length*7);
  return{{...n,x:Math.cos(ang)*r+(Math.random()-0.5)*50,y:Math.sin(ang)*r+(Math.random()-0.5)*50,vx:0,vy:0,fx:null,fy:null}};
}});
const nosIdx={{}};nos.forEach((n,i)=>nosIdx[n.id]=i);
const grau={{}},vizinhos={{}};
nos.forEach(n=>{{grau[n.id]=0;vizinhos[n.id]=[];}});
ARESTAS_DATA.forEach(a=>{{
  if(nosIdx[a.source]!==undefined&&nosIdx[a.target]!==undefined){{
    grau[a.source]=(grau[a.source]||0)+1;grau[a.target]=(grau[a.target]||0)+1;
    vizinhos[a.source]=vizinhos[a.source]||[];vizinhos[a.target]=vizinhos[a.target]||[];
    vizinhos[a.source].push({{id:a.target,label:a.label}});
    vizinhos[a.target].push({{id:a.source,label:a.label}});
  }}
}});
const K_REP=3500,K_ATR=0.06,K_CAT=0.005,DIST=100,DAMP=0.80,VMAX=6;
function simular(){{
  if(frozen)return;
  for(let i=0;i<nos.length;i++){{
    nos[i].vx*=DAMP;nos[i].vy*=DAMP;
    for(let j=i+1;j<nos.length;j++){{
      const dx=nos[i].x-nos[j].x,dy=nos[i].y-nos[j].y;
      const d2=dx*dx+dy*dy+1,d=Math.sqrt(d2),f=K_REP/d2;
      nos[i].vx+=f*dx/d;nos[i].vy+=f*dy/d;
      nos[j].vx-=f*dx/d;nos[j].vy-=f*dy/d;
    }}
    const grav=0.004*(1-nos[i].peso/12);
    nos[i].vx-=nos[i].x*grav;nos[i].vy-=nos[i].y*grav;
    nos[i].vx=Math.max(-VMAX,Math.min(VMAX,nos[i].vx));
    nos[i].vy=Math.max(-VMAX,Math.min(VMAX,nos[i].vy));
  }}
  ARESTAS_DATA.forEach(a=>{{
    const si=nosIdx[a.source],ti=nosIdx[a.target];
    if(si===undefined||ti===undefined)return;
    const s=nos[si],t=nos[ti];
    const dx=t.x-s.x,dy=t.y-s.y,d=Math.sqrt(dx*dx+dy*dy)+0.01;
    const f=K_ATR*(d-DIST);
    s.vx+=f*dx/d;s.vy+=f*dy/d;t.vx-=f*dx/d;t.vy-=f*dy/d;
  }});
  nos.forEach(n=>{{
    if(n.fx!==null){{n.x=n.fx;n.y=n.fy;return;}}
    n.x+=n.vx;n.y+=n.vy;
  }});
}}
function toScreen(wx,wy){{return[wx*scale+W/2+offsetX,wy*scale+H/2+offsetY];}}
function toWorld(sx,sy){{return[(sx-W/2-offsetX)/scale,(sy-H/2-offsetY)/scale];}}
function desenharAresta(a){{
  const si=nosIdx[a.source],ti=nosIdx[a.target];
  if(si===undefined||ti===undefined)return;
  const s=nos[si],t=nos[ti];
  const [sx,sy]=toScreen(s.x,s.y),[tx,ty]=toScreen(t.x,t.y);
  const sel=selectedNode&&(selectedNode.id===a.source||selectedNode.id===a.target);
  const hov=hoveredNode&&(hoveredNode.id===a.source||hoveredNode.id===a.target);
  const dim=selectedNode&&!sel;
  ctx.save();ctx.globalAlpha=dim?0.05:hov?0.9:sel?0.8:0.35;
  const nx=(tx-sx),ny=(ty-sy),nd=Math.sqrt(nx*nx+ny*ny)+0.01;
  const x0=sx+nx/nd*s.raio*scale,y0=sy+ny/nd*s.raio*scale;
  const x1=tx-nx/nd*t.raio*scale,y1=ty-ny/nd*t.raio*scale;
  ctx.strokeStyle=hov||sel?'#4aa8e8':'#1e3a5a';
  ctx.lineWidth=(hov||sel?1.5:0.8)*Math.max(0.5,scale);
  ctx.beginPath();ctx.moveTo(x0,y0);ctx.lineTo(x1,y1);ctx.stroke();
  // seta
  const aw=8*Math.max(0.5,scale),ah=5*Math.max(0.5,scale);
  const ax=nx/nd,ay=ny/nd,px=-ay,py=ax;
  ctx.fillStyle=hov||sel?'#4aa8e8':'#1e3a5a';
  ctx.beginPath();ctx.moveTo(x1,y1);
  ctx.lineTo(x1-ax*aw+px*ah,y1-ay*aw+py*ah);
  ctx.lineTo(x1-ax*aw-px*ah,y1-ay*aw-py*ah);
  ctx.closePath();ctx.fill();
  // label da aresta
  if(showEdges&&scale>0.55&&(hov||sel)){{
    const mx=(x0+x1)/2,my=(y0+y1)/2;
    ctx.font=`${{Math.max(8,9*scale)}}px 'Courier New'`;
    ctx.fillStyle='#2a4060';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(a.label,mx,my-8*scale);
  }}
  ctx.restore();
}}
function desenharNo(n){{
  const [x,y]=toScreen(n.x,n.y);
  const r=n.raio*scale;
  if(x+r<0||x-r>W||y+r<0||y-r>H)return;
  const isSelected=selectedNode&&selectedNode.id===n.id;
  const isHovered=hoveredNode&&hoveredNode.id===n.id;
  const dimmed=selectedNode&&!isSelected&&!(vizinhos[selectedNode.id]||[]).some(v=>v.id===n.id);
  ctx.save();ctx.globalAlpha=dimmed?0.15:1;
  ctx.shadowBlur=isHovered?20:12;ctx.shadowColor=n.glow;
  ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);
  ctx.fillStyle=n.fill;ctx.fill();
  ctx.strokeStyle=n.stroke;
  ctx.lineWidth=(isSelected?2.5:isHovered?2:1.5)*Math.max(0.5,scale);
  if(isSelected){{ctx.shadowBlur=20;ctx.shadowColor=n.glow;}}
  ctx.stroke();ctx.shadowBlur=0;
  if(showLabels&&scale>0.3){{
    const fsize=Math.max(9,Math.min(13,r*0.48));
    ctx.font=`bold ${{fsize}}px 'Courier New'`;
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillStyle=isSelected||isHovered?'#ffffff':n.textColor;
    ctx.shadowBlur=6;ctx.shadowColor='#000';
    const label=n.label.length>13?n.label.slice(0,12)+'…':n.label;
    ctx.fillText(label,x,y);ctx.shadowBlur=0;
    if(scale>0.65){{
      ctx.font=`${{Math.max(7,8*scale)}}px 'Courier New'`;
      ctx.fillStyle=n.stroke;ctx.globalAlpha=dimmed?0.15:0.6;
      ctx.fillText(n.categoria,x,y+r+Math.max(9,11*scale));ctx.globalAlpha=1;
    }}
  }}
  ctx.restore();
}}
function desenhar(){{
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#0a0a0a';ctx.fillRect(0,0,W,H);
  ctx.save();ctx.strokeStyle='#0f0f0f';ctx.lineWidth=0.5;
  const step=80*scale,ox=(offsetX+W/2)%step,oy=(offsetY+H/2)%step;
  for(let x=ox;x<W;x+=step){{ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}}
  for(let y=oy;y<H;y+=step){{ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}}
  ctx.restore();
  PARTICLES.forEach(p=>{{
    const[px,py]=toScreen(p.x,p.y);
    ctx.save();ctx.globalAlpha=p.a*(0.4+0.3*Math.sin(frame*0.02+p.x));
    ctx.fillStyle='#336688';ctx.beginPath();ctx.arc(px,py,p.r,0,Math.PI*2);ctx.fill();ctx.restore();
  }});
  ARESTAS_DATA.forEach(a=>desenharAresta(a));
  nos.forEach(n=>desenharNo(n));
}}
function loop(){{
  const steps=frame<200?3:frame<500?2:1;
  for(let i=0;i<steps;i++)simular();
  frame++;desenhar();requestAnimationFrame(loop);
}}
loop();
function openPanel(n){{
  selectedNode=n;
  document.getElementById('panel').style.display='block';
  document.getElementById('panel-title').textContent=n.label;
  document.getElementById('panel-title').style.color=n.stroke;
  document.getElementById('panel-cat').textContent=n.categoria;
  document.getElementById('panel-desc').textContent=n.descricao||'';
  document.getElementById('panel-peso').textContent=n.peso;
  document.getElementById('panel-grau').textContent=grau[n.id]||0;
  const viz=(vizinhos[n.id]||[]).slice(0,8);
  document.getElementById('panel-connections').innerHTML=viz.map(v=>
    `<div class="conn-item">&#x2192; <span>${{v.id}}</span> <span style="color:#2a4060">[${{v.label}}]</span></div>`
  ).join('');
}}
function closePanel(){{selectedNode=null;document.getElementById('panel').style.display='none';}}
// tooltip
const tt=document.getElementById('tooltip');
canvas.addEventListener('mousemove',e=>{{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left,my=e.clientY-rect.top;
  const[wx,wy]=toWorld(mx,my);
  if(draggingNode){{draggingNode.fx=wx;draggingNode.fy=wy;draggingNode.x=wx;draggingNode.y=wy;}}
  else if(draggingCanvas){{offsetX+=mx-lastMX;offsetY+=my-lastMY;}}
  else{{
    hoveredNode=null;tt.style.display='none';
    for(const n of nos){{
      const dx=n.x-wx,dy=n.y-wy;
      if(Math.sqrt(dx*dx+dy*dy)<n.raio+3/scale){{
        hoveredNode=n;canvas.style.cursor='pointer';
        tt.innerHTML='<strong style="color:#e8e8e8">'+n.label+'</strong><br>'
          +'<span style="color:#555;font-size:0.7rem">'+n.categoria.toUpperCase()+' · peso '+n.peso+'</span>'
          +(n.descricao?'<br><span style="color:#aaa;font-style:italic">'+n.descricao+'</span>':'');
        tt.style.display='block';tt.style.left=(e.clientX+14)+'px';tt.style.top=(e.clientY-10)+'px';
        break;
      }}
    }}
    if(!hoveredNode)canvas.style.cursor='grab';
  }}
  lastMX=mx;lastMY=my;
}});
canvas.addEventListener('mousedown',e=>{{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left,my=e.clientY-rect.top;
  const[wx,wy]=toWorld(mx,my);
  mouseDownX=wx;mouseDownY=wy;
  for(const n of nos){{
    const dx=n.x-wx,dy=n.y-wy;
    if(Math.sqrt(dx*dx+dy*dy)<n.raio+3/scale){{draggingNode=n;n.fx=n.x;n.fy=n.y;return;}}
  }}
  draggingCanvas=true;
}});
function releaseAll(){{
  if(draggingNode){{draggingNode.fx=null;draggingNode.fy=null;draggingNode=null;}}
  draggingCanvas=false;canvas.style.cursor='grab';
}}
canvas.addEventListener('mouseup',e=>{{
  const rect=canvas.getBoundingClientRect();
  const[wx,wy]=toWorld(e.clientX-rect.left,e.clientY-rect.top);
  if(draggingNode){{
    const d=Math.sqrt((draggingNode.x-mouseDownX)**2+(draggingNode.y-mouseDownY)**2);
    if(d<8/scale)openPanel(draggingNode);
  }} else {{
    let hit=false;
    for(const n of nos){{const dx=n.x-wx,dy=n.y-wy;if(Math.sqrt(dx*dx+dy*dy)<n.raio+3/scale){{hit=true;break;}}}}
    if(!hit&&selectedNode)closePanel();
  }}
  releaseAll();
}});
canvas.addEventListener('mouseleave',releaseAll);
window.addEventListener('mouseup',releaseAll);
canvas.addEventListener('wheel',e=>{{
  e.preventDefault();
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left,my=e.clientY-rect.top;
  const delta=e.deltaY>0?0.88:1.13;
  const ns=Math.max(0.12,Math.min(5,scale*delta));
  offsetX=mx-W/2-(mx-W/2-offsetX)*(ns/scale);
  offsetY=my-H/2-(my-H/2-offsetY)*(ns/scale);
  scale=ns;
}},{{passive:false}});
let lastPinchDist=null;
canvas.addEventListener('touchstart',e=>{{if(e.touches.length===1){{lastMX=e.touches[0].clientX;lastMY=e.touches[0].clientY;draggingCanvas=true;}}}},{{passive:true}});
canvas.addEventListener('touchmove',e=>{{
  if(e.touches.length===2){{
    const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
    if(lastPinchDist)scale=Math.max(0.12,Math.min(5,scale*(d/lastPinchDist)));
    lastPinchDist=d;
  }}else if(draggingCanvas&&e.touches.length===1){{
    offsetX+=e.touches[0].clientX-lastMX;offsetY+=e.touches[0].clientY-lastMY;
    lastMX=e.touches[0].clientX;lastMY=e.touches[0].clientY;
  }}
}},{{passive:true}});
canvas.addEventListener('touchend',()=>{{draggingCanvas=false;lastPinchDist=null;}},{{passive:true}});
function resetView(){{offsetX=0;offsetY=0;scale=1;frame=0;}}
function toggleLabels(){{showLabels=!showLabels;document.getElementById('btn-labels').classList.toggle('active',showLabels);}}
function toggleEdges(){{showEdges=!showEdges;document.getElementById('btn-edges').classList.toggle('active',showEdges);}}
function toggleFreeze(){{
  frozen=!frozen;
  const btn=document.getElementById('btn-freeze');
  btn.textContent=frozen?'⏸ física':'▶ física';
  btn.classList.toggle('active',!frozen);
}}
</script></body></html>"""

# ── CSS Global ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap');
html,body,[class*="css"]{font-family:'Courier Prime','Courier New',monospace;}
.stApp{background-color:#0a0a0a;color:#d4d4d4;}
h1,h2,h3{color:#e8e8e8!important;letter-spacing:0.05em;}
.stButton>button{background-color:#1a1a1a;color:#d4d4d4;border:1px solid #444;
  font-family:'Courier Prime',monospace;letter-spacing:0.1em;}
.stButton>button:hover{background-color:#2a2a2a;border-color:#888;color:#fff;}
.terminal-box{background-color:#111;border:1px solid #333;border-left:3px solid #666;
  padding:1rem 1.2rem;margin:0.5rem 0;font-size:0.82rem;line-height:1.6;
  color:#c8c8c8;white-space:pre-wrap;word-break:break-word;}
.protocol-header{background-color:#151515;border-top:1px solid #555;border-bottom:1px solid #333;
  padding:0.4rem 0.8rem;color:#aaaaaa;font-size:0.75rem;letter-spacing:0.15em;
  text-transform:uppercase;margin:1.2rem 0 0.4rem 0;}
.counter-label{color:#777;font-size:0.7rem;letter-spacing:0.12em;}
div[data-testid="stSidebarContent"]{background-color:#0d0d0d;}
.stTabs [data-baseweb="tab"]{background-color:#111;color:#888;
  font-family:'Courier Prime',monospace;font-size:0.8rem;letter-spacing:0.08em;}
.stTabs [aria-selected="true"]{color:#ddd!important;border-bottom-color:#666!important;}
.stTextArea textarea{background-color:#111;color:#ccc;font-family:'Courier Prime',monospace;
  font-size:0.82rem;border:1px solid #333;}
.ancora-word{font-size:2.2rem;letter-spacing:0.4em;color:#888;text-align:center;
  padding:1.5rem 0 0.5rem 0;text-transform:uppercase;}
.ancora-sub{font-size:0.65rem;color:#444;letter-spacing:0.2em;text-align:center;}
.blink{animation:blink 1s step-end infinite;}
@keyframes blink{50%{opacity:0;}}
header[data-testid="stHeader"]{display:none!important;}
#MainMenu{display:none!important;}
footer{display:none!important;}
.block-container{padding-top:1rem!important;}
[data-testid="stFileUploader"] section{background:#111;border:1px dashed #444;border-radius:4px;}
[data-testid="stFileUploader"] section:hover{border-color:#888;}
[data-testid="stFileUploaderDropzoneInstructions"] div span:first-child{display:none;}
[data-testid="stFileUploaderDropzoneInstructions"]::before{
  content:'Arraste e solte o arquivo aqui';color:#666;font-family:inherit;font-size:0.9rem;}
[data-testid="stFileUploaderDropzoneInstructions"] div small{display:none;}
[data-testid="stFileUploaderDropzoneInstructions"]::after{
  content:'Limite 200MB · PDF, DOCX, DOC, TXT';color:#444;font-size:0.75rem;display:block;margin-top:4px;}
[data-testid="stBaseButton-secondary"]{color:#888!important;border-color:#444!important;}
[data-testid="stBaseButton-secondary"] p{display:none;}
[data-testid="stBaseButton-secondary"]::after{content:'Procurar arquivo';}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ A MÁQUINA")
    st.markdown(
        "<span style='font-size:0.72rem;color:#666;letter-spacing:0.1em'>"
        "sistema de análise literária<br>baseado em Georges Perec, 1968"
        "</span>", unsafe_allow_html=True)
    st.markdown("---")
    fonte = st.radio("FONTE", ["📂 Upload de arquivo", "✏️ Entrada manual"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<span style='font-size:0.7rem;color:#555;letter-spacing:0.08em'>PROTOCOLOS ATIVOS</span>",
                unsafe_allow_html=True)
    prot0 = st.checkbox("00 — Análise estatística",  value=True)
    st.caption("Conta linhas, palavras, letras, pontuação e riqueza lexical.")
    prot1 = st.checkbox("01 — Operações internas",   value=True)
    st.caption("Recitações, inversões, permutações e deformações internas do texto.")
    prot2 = st.checkbox("02 — Operações externas",   value=True)
    st.caption("Anagramas, metáteses, traduções, provérbios e transformações linguísticas.")
    prot3 = st.checkbox("03 — Análise crítica",      value=True)
    st.caption("Frequências, entidades, coocorrências e diversidade lexical.")
    prot4 = st.checkbox("04 — Explosão de citações", value=True)
    st.caption("Associa palavras a citações, traduções e permutações temáticas.")
    prot5 = st.checkbox("05 — Grafo ontológico",     value=True)
    st.caption("Constrói uma rede visual de conceitos e relações extraídos do texto.")
    st.markdown("---")
    seed_val = st.number_input("SEMENTE ALEATÓRIA", value=42, min_value=0, max_value=9999)
    max_nos  = st.slider("NÓS NO GRAFO", 15, 60, 40) if prot5 else 40
    st.markdown("---")
    st.markdown(
        "<span style='font-size:0.65rem;color:#444'>"
        "«A peça busca simular o funcionamento<br>"
        "de um computador programado para<br>"
        "analisar e decompor um poema»<br><br>"
        "— G. Perec, La Machine, 1968"
        "</span>", unsafe_allow_html=True)

# ── Área principal ────────────────────────────────────────────────────────────

st.markdown(
    "<h1 style='font-size:1.6rem;letter-spacing:0.2em;margin-bottom:0'>A MÁQUINA</h1>"
    "<p style='color:#555;font-size:0.72rem;letter-spacing:0.15em;margin-top:0.2rem'>"
    "ANÁLISE COMPUTACIONAL DE TEXTO · INSPIRADO EM GEORGES PEREC · LA MACHINE (1968)"
    "</p>", unsafe_allow_html=True)
st.markdown("<div style='border-top:1px solid #2a2a2a;margin:0.5rem 0 1.5rem 0'></div>",
            unsafe_allow_html=True)

texto_bruto = None

if fonte == "📂 Upload de arquivo":
    arq = st.file_uploader("ARQUIVO", type=["pdf","docx","doc","txt"], label_visibility="collapsed")
    if arq:
        with st.spinner("lendo arquivo..."):
            texto_bruto = carregar_texto(arq)
        st.markdown(
            f"<div class='terminal-box'>"
            f"<span class='counter-label'>ARQUIVO: </span>{arq.name} "
            f"<span class='counter-label'>· CARACTERES: </span>{len(texto_bruto)}"
            f"</div>", unsafe_allow_html=True)
else:
    texto_bruto = st.text_area("TEXTO", height=180,
        placeholder="cole ou digite o texto aqui...", label_visibility="collapsed")

if not texto_bruto or len(texto_bruto.strip()) < 10:
    st.markdown(
        "<div class='terminal-box'>"
        "<span style='color:#444'>processadores prontos para gravar"
        "<span class='blink'>_</span></span></div>", unsafe_allow_html=True)
    st.stop()

with st.expander("TEXTO CARREGADO", expanded=False):
    st.markdown(
        f"<div class='terminal-box'>{texto_bruto[:2000]}{'...' if len(texto_bruto)>2000 else ''}</div>",
        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Execução ──────────────────────────────────────────────────────────────────

random.seed(int(seed_val))
palavras_globais = tokenizar(texto_bruto)

tabs = st.tabs(["00 · ESTATÍSTICA","01 · INTERNO","02 · EXTERNO",
                "03 · CRÍTICA","04 · CITAÇÕES","05 · GRAFO"])

# ── TAB 0 ─────────────────────────────────────────────────────────────────────
with tabs[0]:
    if not prot0:
        st.markdown("<div class='terminal-box'>protocolo 00 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 0 · análise estatística básica</div>",
                    unsafe_allow_html=True)
        dados = protocolo_zero(texto_bruto)
        c1,c2,c3,c4 = st.columns(4)
        for col,(lbl,val) in zip([c1,c2,c3,c4],[
            ("LINHAS",  dados["01: número de linhas"]),
            ("PALAVRAS",dados["02: número de palavras"]),
            ("LETRAS",  dados["03: número de letras"]),
            ("VOCAB",   dados["07: vocabulário único"]),
        ]):
            with col:
                st.markdown(f"<div class='terminal-box' style='text-align:center'>"
                            f"<div style='font-size:1.6rem;color:#ccc'>{val}</div>"
                            f"<div class='counter-label'>{lbl}</div></div>", unsafe_allow_html=True)
        ttr = dados["08: índice de riqueza lexical (TTR)"]
        av  = "texto rico" if ttr > 0.6 else "texto repetitivo" if ttr < 0.3 else "densidade média"
        st.markdown("<div class='protocol-header'>08: índice de riqueza lexical (TTR)</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{ttr} <span class='counter-label'>— {av}</span></div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>04: pontuação</div>", unsafe_allow_html=True)
        pont = dados["04: distribuição de pontuação"]
        st.markdown(f"<div class='terminal-box'>{'   '.join(f'{k}={v}' for k,v in pont.items() if v>0) or '(nenhuma)'}</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>05: frequência de letras (top 10)</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{'   '.join(f'{l}={n}' for l,n in dados['05: frequência de letras (top 10)'])}</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>07: distribuição sintática</div>", unsafe_allow_html=True)
        cats = classificar_palavras(palavras_globais[:200])
        for cat, pals in cats.items():
            if pals:
                st.markdown(f"<div class='terminal-box'><span class='counter-label'>{cat}:</span>"
                            f" {'   '.join(pals[:12])}</div>", unsafe_allow_html=True)

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tabs[1]:
    if not prot1:
        st.markdown("<div class='terminal-box'>protocolo 01 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 1 · operações internas · deformações rítmicas</div>",
                    unsafe_allow_html=True)
        p1 = protocolo_um(texto_bruto)
        for chave, valor in p1.items():
            st.markdown(f"<div class='protocol-header'>{chave}</div>", unsafe_allow_html=True)
            if isinstance(valor, list):
                if chave == "111: recitação palavra a palavra":
                    n = len(valor); chunk = max(1, n//4)
                    cols = st.columns(4)
                    for idx, col in enumerate(cols):
                        with col:
                            bloco = valor[idx*chunk:(idx+1)*chunk]
                            st.markdown("<div class='terminal-box'>"+"<br>".join(bloco[:30])+
                                        ("..." if len(bloco)>30 else "")+"</div>", unsafe_allow_html=True)
                elif chave == "122: arranjo vertical":
                    st.markdown("<div class='terminal-box'>"+"<br>".join(valor[:40])+"</div>",
                                unsafe_allow_html=True)
                else:
                    txt = "   ".join(str(v) for v in valor[:40])
                    if len(valor)>40: txt += " ···"
                    st.markdown(f"<div class='terminal-box'>{txt}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='terminal-box'>{valor}</div>", unsafe_allow_html=True)

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tabs[2]:
    if not prot2:
        st.markdown("<div class='terminal-box'>protocolo 02 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 2 · operações externas · substituições e transformações</div>",
                    unsafe_allow_html=True)
        p2 = protocolo_dois(texto_bruto)
        for chave, valor in p2.items():
            st.markdown(f"<div class='protocol-header'>{chave}</div>", unsafe_allow_html=True)
            if isinstance(valor, list):
                st.markdown(f"<div class='terminal-box'>{'   '.join(str(v) for v in valor)}</div>",
                            unsafe_allow_html=True)
            elif isinstance(valor, dict):
                for k,v in valor.items():
                    st.markdown(f"<div class='terminal-box'><span class='counter-label'>{k}:</span><br>"
                                f"{'   '.join(str(x) for x in v)}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='terminal-box'>{valor}</div>", unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>253: frequência como dados enciclopédicos</div>",
                    unsafe_allow_html=True)
        for palavra, contagem in Counter(palavras_globais).most_common(15):
            barra = "█" * min(40, contagem)
            st.markdown(f"<div class='terminal-box' style='padding:0.3rem 1rem'>"
                        f"<span style='display:inline-block;width:120px;color:#aaa'>{palavra}</span>"
                        f"<span style='color:#555'>{barra}</span>"
                        f"<span class='counter-label'> {contagem}</span></div>", unsafe_allow_html=True)

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tabs[3]:
    if not prot3:
        st.markdown("<div class='terminal-box'>protocolo 03 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 3 · elementos críticos · análise do corpus</div>",
                    unsafe_allow_html=True)
        p3 = protocolo_tres(texto_bruto)
        st.markdown("<div class='protocol-header'>frequência das 30 palavras mais comuns</div>",
                    unsafe_allow_html=True)
        for palavra, cont in p3["frequência das 30 palavras mais comuns"]:
            barra = "▓" * min(50, cont*2)
            st.markdown(f"<div class='terminal-box' style='padding:0.25rem 1rem'>"
                        f"<span style='display:inline-block;width:140px'>{palavra}</span>"
                        f"<span style='color:#444'>{barra}</span> "
                        f"<span class='counter-label'>{cont}</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>entidades detectadas (nomes próprios)</div>",
                    unsafe_allow_html=True)
        ents = p3["entidades (nomes próprios detectados)"]
        st.markdown(f"<div class='terminal-box'>{'   '.join(f'{n} ({c})' for n,c in ents) or '(nenhuma)'}</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>pares de co-ocorrência mais frequentes</div>",
                    unsafe_allow_html=True)
        for par, cont in p3["pares de co-ocorrência mais frequentes"]:
            st.markdown(f"<div class='terminal-box' style='padding:0.25rem 1rem'>"
                        f"{par} <span class='counter-label'>× {cont}</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>hapax legomena · palavras únicas</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{'   '.join(p3['hapax legomena'])} ···</div>",
                    unsafe_allow_html=True)
        div = p3["diversidade lexical"]
        av  = "MUITO RICA" if div>0.7 else "RICA" if div>0.5 else "MÉDIA" if div>0.3 else "REPETITIVA"
        st.markdown("<div class='protocol-header'>diversidade lexical (TTR)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{div} · {av}</div>", unsafe_allow_html=True)

# ── TAB 4 ─────────────────────────────────────────────────────────────────────
with tabs[4]:
    if not prot4:
        st.markdown("<div class='terminal-box'>protocolo 04 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 4 · explosão de citações · busca por associação livre</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='terminal-box'>PROCESSADORES 1, 2, 3 E CONTROLE DO SISTEMA FALAM EM LIVRE ALTERNÂNCIA</div>",
                    unsafe_allow_html=True)
        p4 = protocolo_quatro(texto_bruto)
        ancora, trad = p4["ancora"], p4["traducoes"]
        st.markdown("<div class='protocol-header'>associações livres · palavra-chave → citações</div>",
                    unsafe_allow_html=True)
        for chave, cits in p4["associações livres"].items():
            st.markdown(
                f"<div class='terminal-box'><span style='color:#888'>{chave}</span><br><br>"
                + "<br><br>".join(f"<em>{tc}</em><br><span class='counter-label'>— {au}</span>" for au,tc in cits)
                + "</div>", unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>permutações temáticas</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        perms = p4["permutações temáticas"]
        chunk = max(1, len(perms)//3)
        for i, col in enumerate(cols):
            with col:
                st.markdown("<div class='terminal-box'>"+"<br>".join(perms[i*chunk:(i+1)*chunk])+"</div>",
                            unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>citações em livre alternância</div>", unsafe_allow_html=True)
        for au, cit in p4["citações em livre alternância"]:
            st.markdown(f"<div class='terminal-box'>{cit}<br>"
                        f"<span class='counter-label'>— {au}</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='protocol-header'>palavra âncora do texto · multilinguismo</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='ancora-word'>{ancora}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='ancora-sub'>palavra mais semanticamente central do texto</div>",
                    unsafe_allow_html=True)
        bandeiras = {"pt":"🇧🇷","fr":"🇫🇷","de":"🇩🇪","es":"🇪🇸","it":"🇮🇹","ja":"🇯🇵","la":"🏛️","ar":"🌙"}
        trad_html = "".join(
            f"<span style='display:inline-block;margin:6px 12px;text-align:center'>"
            f"<span style='font-size:1.3rem'>{bandeiras.get(lang,'')}</span><br>"
            f"<span style='color:#aaa;font-size:0.9rem'>{palavra}</span><br>"
            f"<span class='counter-label'>{lang}</span></span>"
            for lang, palavra in trad.items())
        st.markdown(f"<div class='terminal-box' style='text-align:center;padding:1.2rem'>{trad_html}</div>",
                    unsafe_allow_html=True)
        ancora_up = ancora.upper()
        ruido = "   ".join(trad.values())
        variantes = "   ".join(ancora_up[:max(3,len(ancora_up)-1)+i%3] for i in range(8))
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='terminal-box' style='text-align:center;letter-spacing:0.3em;color:#444'>"
            f"{ancora_up}<br><br>{ruido}<br><br>{variantes}<br><br>"
            f"p{ancora[:2]}z   p{ancora[:2]}zz   p{ancora[:3]}sh   sh{ancora[:2]}sh   sh{ancora[:2]}shshsh"
            f"</div>", unsafe_allow_html=True)

# ── TAB 5 — GRAFO ONTOLÓGICO ──────────────────────────────────────────────────
with tabs[5]:
    if not prot5:
        st.markdown("<div class='terminal-box'>protocolo 05 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 5 · grafo ontológico · rede de conceitos e relações</div>",
                    unsafe_allow_html=True)
        col_llm, col_info = st.columns([1, 2])
        with col_llm:
            usar_llm = st.toggle("🧠 Extração semântica (Ollama)", value=True,
                help="Usa LLM local via Ollama. Requer: ollama serve + ollama pull qwen2.5:3b")
        with col_info:
            if usar_llm:
                try:
                    modelo_det = _detectar_modelo_ollama()
                    info = f"<span style='color:#4ecb6e'>{modelo_det}</span> · via Ollama"
                except Exception as e:
                    info = f"<span style='color:#f07040'>Ollama indisponível</span> · {str(e)[:60]}"
                st.markdown(
                    f"<div class='terminal-box' style='padding:0.4rem 0.8rem;font-size:0.75rem'>"
                    f"modo: <span style='color:#4aa8e8'>semântico local</span> · {info}"
                    f"</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div class='terminal-box' style='padding:0.4rem 0.8rem;font-size:0.75rem'>"
                    "modo: <span style='color:#f0c040'>estatístico</span> · heurísticas locais"
                    "</div>", unsafe_allow_html=True)

        cache_key = f"grafo_v7_{hash(texto_bruto[:500])}_{usar_llm}_{max_nos}"
        if st.button("⟳ Regenerar grafo", key="btn_regen"):
            if cache_key in st.session_state:
                del st.session_state[cache_key]

        if cache_key not in st.session_state:
            with st.spinner("extraindo ontologia" + (" via Ollama…" if usar_llm else " (estatístico)…")):
                nos_dict, arestas, metodo = extrair_grafo(texto_bruto, max_nos=max_nos, usar_llm=usar_llm)
            st.session_state[cache_key] = (nos_dict, arestas, metodo)
        else:
            nos_dict, arestas, metodo = st.session_state[cache_key]

        if metodo.startswith("fallback"):
            erro = metodo.replace("fallback (","").rstrip(")")
            st.markdown(
                f"<div class='terminal-box' style='border-left-color:#f07040;font-size:0.75rem'>"
                f"<span style='color:#f07040'>⚠ LLM indisponível</span> — extração estatística. "
                f"<span style='color:#555'>{erro[:120]}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(
                "<div class='terminal-box' style='border-left-color:#4ecb6e;font-size:0.75rem'>"
                "<span style='color:#4ecb6e'>✓ ontologia extraída via Ollama</span>"
                "</div>", unsafe_allow_html=True)

        cats_count = Counter(d["categoria"] for d in nos_dict.values())
        CORES_L = {"conceito":"#4aa8e8","ação":"#4ecb6e","qualidade":"#f0c040",
                   "entidade":"#f07040","relação":"#b060f0"}
        c1,c2,c3,c4,c5 = st.columns(5)
        for col,(cat,cor) in zip([c1,c2,c3,c4,c5],CORES_L.items()):
            with col:
                cnt = cats_count.get(cat, 0)
                st.markdown(f"<div class='terminal-box' style='text-align:center;border-left-color:{cor}'>"
                            f"<div style='font-size:1.4rem;color:{cor}'>{cnt}</div>"
                            f"<div class='counter-label'>{cat}</div></div>", unsafe_allow_html=True)

        n, a = len(nos_dict), len(arestas)
        dens = round(a/(n*(n-1)/2), 3) if n > 1 else 0
        st.markdown(f"<div class='terminal-box'>"
                    f"<span class='counter-label'>TOTAL NÓS:</span> {n}   "
                    f"<span class='counter-label'>TOTAL ARESTAS:</span> {a}   "
                    f"<span class='counter-label'>DENSIDADE:</span> {dens}</div>", unsafe_allow_html=True)

        html_grafo = gerar_html_grafo(nos_dict, arestas,
            titulo=f"grafo ontológico · {n} conceitos · {a} relações")
        st.components.v1.html(html_grafo, height=620, scrolling=False)

        st.markdown("<div class='protocol-header'>nós principais por categoria</div>", unsafe_allow_html=True)
        por_cat = {}
        for nome, dados in nos_dict.items():
            por_cat.setdefault(dados["categoria"], []).append((nome, dados["peso"]))
        for cat, itens in sorted(por_cat.items()):
            itens_ord = sorted(itens, key=lambda x: -x[1])[:10]
            cor = CORES_L.get(cat, "#888")
            partes = []
            for nm, p in itens_ord:
                desc = nos_dict[nm].get("descricao","")
                partes.append(f"{nm}({p})" + (f" <span style='color:#333'>— {desc}</span>" if desc else ""))
            st.markdown(
                f"<div class='terminal-box' style='border-left-color:{cor}'>"
                f"<span class='counter-label' style='color:{cor}'>{cat.upper()}:</span><br>"
                f"{'   '.join(partes)}</div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>relações mais fortes</div>", unsafe_allow_html=True)
        for ar in sorted(arestas, key=lambda x: -x["weight"])[:15]:
            barra = "─" * min(20, ar["weight"]*2)
            st.markdown(
                f"<div class='terminal-box' style='padding:0.3rem 1rem'>"
                f"{ar['source']} <span style='color:#446688'>{barra}[{ar['label']}]──</span> {ar['target']} "
                f"<span class='counter-label'>× {ar['weight']}</span></div>", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#333;font-size:0.68rem;letter-spacing:0.15em'>"
    "STOP · FIM DOS PROTOCOLOS · SALVO</div>", unsafe_allow_html=True)
