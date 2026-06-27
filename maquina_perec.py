"""
A Máquina — inspirado em Georges Perec (1968)
Análise computacional de textos literários.
"""

import streamlit as st
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
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
        return texto
    except Exception as e:
        return f"[erro ao ler PDF: {e}]"

def ler_docx(arquivo):
    try:
        from docx import Document
        doc = Document(arquivo)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"[erro ao ler DOCX: {e}]"

def ler_txt(arquivo):
    try:
        return arquivo.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"[erro ao ler TXT: {e}]"

def carregar_texto(arquivo):
    nome = arquivo.name.lower()
    if nome.endswith(".pdf"):
        return ler_pdf(arquivo)
    elif nome.endswith(".docx") or nome.endswith(".doc"):
        return ler_docx(arquivo)
    else:
        return ler_txt(arquivo)

# ── Utilitários linguísticos ─────────────────────────────────────────────────

STOPWORDS = set([
    'the','a','an','of','in','is','are','was','were','be','been','being',
    'have','has','had','do','does','did','will','would','could','should',
    'may','might','must','shall','can','and','but','or','nor','for','yet',
    'so','as','at','by','if','on','to','up','it','its','he','she','we',
    'they','you','i','me','him','her','us','them','my','your','his','our',
    'their','this','that','these','those','what','which','who','whom',
    'when','where','why','how','not','no','only','own','than','too','very',
    'just','over','all','both','each','few','more','most','other','some',
    'such','into','with','from','about','between','through','during',
    'before','after','above','below','then','once','here','there','any',
    'also','even','still','back','way','well','long','down','day','get',
    'come','go','know','think','see','look','want','give','use','find',
    # PT
    'de','da','do','das','dos','em','na','no','nas','nos','um','uma',
    'uns','umas','que','se','com','por','para','mas','ou','ao','aos',
    'pelo','pela','pelos','pelas','seu','sua','seus','suas','ele','ela',
    'eles','elas','lhe','lhes','me','te','já','mais','como','quando',
    'bem','muito','também','só','ainda','onde','nem','entre','até','sem',
    'foi','ser','ter','está','são','são','isso','esse','essa','isso',
    'isso','aqui','ali','then','whose','nor','need','dare','ought',
])

def tokenizar(texto):
    palavras = re.findall(r'\b[a-záéíóúâêîôûãõàèìòùäëïöüçñ\w]+\b', texto.lower())
    return [p for p in palavras if len(p) > 0]

def linhas(texto):
    return [l.strip() for l in texto.split('\n') if l.strip()]

def classificar_palavras(palavras):
    try:
        import nltk
        tagged = nltk.pos_tag(palavras)
        cats = {
            "substantivos": [], "verbos": [], "adjetivos": [],
            "advérbios": [], "preposições": [], "pronomes": [],
            "artigos": [], "outros": [],
        }
        tag_map = {
            "NN": "substantivos", "NNS": "substantivos",
            "NNP": "substantivos", "NNPS": "substantivos",
            "VB": "verbos", "VBD": "verbos", "VBG": "verbos",
            "VBN": "verbos", "VBP": "verbos", "VBZ": "verbos",
            "JJ": "adjetivos", "JJR": "adjetivos", "JJS": "adjetivos",
            "RB": "advérbios", "RBR": "advérbios", "RBS": "advérbios",
            "IN": "preposições",
            "PRP": "pronomes", "PRP$": "pronomes",
            "WP": "pronomes", "WP$": "pronomes",
            "DT": "artigos",
        }
        for palavra, tag in tagged:
            cats[tag_map.get(tag, "outros")].append(palavra)
        return cats
    except Exception:
        return {"palavras": palavras}

# ── Palavra âncora (substitui SILÊNCIO/PAZ no prot4) ────────────────────────

def extrair_palavra_ancora(texto):
    """Encontra a palavra mais semanticamente central do texto."""
    palavras = re.findall(r'\b[a-záéíóúâêîôûãõàèìòùäëïöüç]+\b', texto.lower())
    filtradas = [p for p in palavras if p not in STOPWORDS and len(p) > 4]
    if not filtradas:
        return "essência"
    freq = Counter(filtradas)
    candidatos = freq.most_common(10)
    # prefere substantivos abstratos (heurística: terminações comuns)
    sufixos_abstratos = ('ção','dade','ismo','eza','ura','ência','ância',
                          'tion','ness','ity','ism','ence','ance','ment',
                          'heit','keit','ung','schaft')
    for palavra, _ in candidatos:
        if any(palavra.endswith(s) for s in sufixos_abstratos):
            return palavra
    return candidatos[0][0]

def traducoes_palavra(palavra):
    """Retorna traduções aproximadas em 8 línguas via dicionário temático."""
    dicionario = {
        # conceitos abstratos comuns
        "rest":      {"pt":"repouso","fr":"repos","de":"Ruhe","es":"reposo","it":"riposo","ja":"休み","la":"quies","ar":"راحة"},
        "silence":   {"pt":"silêncio","fr":"silence","de":"Schweigen","es":"silencio","it":"silenzio","ja":"沈黙","la":"silentium","ar":"صمت"},
        "peace":     {"pt":"paz","fr":"paix","de":"Friede","es":"paz","it":"pace","ja":"平和","la":"pax","ar":"سلام"},
        "death":     {"pt":"morte","fr":"mort","de":"Tod","es":"muerte","it":"morte","ja":"死","la":"mors","ar":"موت"},
        "life":      {"pt":"vida","fr":"vie","de":"Leben","es":"vida","it":"vita","ja":"生命","la":"vita","ar":"حياة"},
        "love":      {"pt":"amor","fr":"amour","de":"Liebe","es":"amor","it":"amore","ja":"愛","la":"amor","ar":"حب"},
        "time":      {"pt":"tempo","fr":"temps","de":"Zeit","es":"tiempo","it":"tempo","ja":"時間","la":"tempus","ar":"وقت"},
        "nature":    {"pt":"natureza","fr":"nature","de":"Natur","es":"naturaleza","it":"natura","ja":"自然","la":"natura","ar":"طبيعة"},
        "light":     {"pt":"luz","fr":"lumière","de":"Licht","es":"luz","it":"luce","ja":"光","la":"lux","ar":"ضوء"},
        "darkness":  {"pt":"trevas","fr":"obscurité","de":"Dunkel","es":"oscuridad","it":"oscurità","ja":"暗闇","la":"tenebrae","ar":"ظلام"},
        "freedom":   {"pt":"liberdade","fr":"liberté","de":"Freiheit","es":"libertad","it":"libertà","ja":"自由","la":"libertas","ar":"حرية"},
        "truth":     {"pt":"verdade","fr":"vérité","de":"Wahrheit","es":"verdad","it":"verità","ja":"真実","la":"veritas","ar":"حقيقة"},
        "beauty":    {"pt":"beleza","fr":"beauté","de":"Schönheit","es":"belleza","it":"bellezza","ja":"美","la":"pulchritudo","ar":"جمال"},
        "memory":    {"pt":"memória","fr":"mémoire","de":"Erinnerung","es":"memoria","it":"memoria","ja":"記憶","la":"memoria","ar":"ذاكرة"},
        "dream":     {"pt":"sonho","fr":"rêve","de":"Traum","es":"sueño","it":"sogno","ja":"夢","la":"somnium","ar":"حلم"},
        "soul":      {"pt":"alma","fr":"âme","de":"Seele","es":"alma","it":"anima","ja":"魂","la":"anima","ar":"روح"},
        "body":      {"pt":"corpo","fr":"corps","de":"Körper","es":"cuerpo","it":"corpo","ja":"体","la":"corpus","ar":"جسد"},
        "word":      {"pt":"palavra","fr":"mot","de":"Wort","es":"palabra","it":"parola","ja":"言葉","la":"verbum","ar":"كلمة"},
        "forest":    {"pt":"floresta","fr":"forêt","de":"Wald","es":"bosque","it":"foresta","ja":"森","la":"silva","ar":"غابة"},
        "mountain":  {"pt":"montanha","fr":"montagne","de":"Berg","es":"montaña","it":"montagna","ja":"山","la":"mons","ar":"جبل"},
        "birds":     {"pt":"pássaros","fr":"oiseaux","de":"Vögel","es":"pájaros","it":"uccelli","ja":"鳥","la":"aves","ar":"طيور"},
        "breath":    {"pt":"sopro","fr":"souffle","de":"Hauch","es":"aliento","it":"respiro","ja":"息","la":"spiritus","ar":"نفس"},
        "silence":   {"pt":"silêncio","fr":"silence","de":"Schweigen","es":"silencio","it":"silenzio","ja":"沈黙","la":"silentium","ar":"صمت"},
        "waiting":   {"pt":"espera","fr":"attente","de":"Warten","es":"espera","it":"attesa","ja":"待機","la":"expectatio","ar":"انتظار"},
        "machine":   {"pt":"máquina","fr":"machine","de":"Maschine","es":"máquina","it":"macchina","ja":"機械","la":"machina","ar":"آلة"},
        "language":  {"pt":"linguagem","fr":"langage","de":"Sprache","es":"lenguaje","it":"linguaggio","ja":"言語","la":"lingua","ar":"لغة"},
        "poem":      {"pt":"poema","fr":"poème","de":"Gedicht","es":"poema","it":"poesia","ja":"詩","la":"poema","ar":"قصيدة"},
        "poetry":    {"pt":"poesia","fr":"poésie","de":"Dichtung","es":"poesía","it":"poesia","ja":"詩","la":"poesis","ar":"شعر"},
        "knowledge": {"pt":"conhecimento","fr":"connaissance","de":"Wissen","es":"conocimiento","it":"conoscenza","ja":"知識","la":"scientia","ar":"معرفة"},
        "power":     {"pt":"poder","fr":"pouvoir","de":"Macht","es":"poder","it":"potere","ja":"力","la":"potentia","ar":"قوة"},
        "history":   {"pt":"história","fr":"histoire","de":"Geschichte","es":"historia","it":"storia","ja":"歴史","la":"historia","ar":"تاريخ"},
        "god":       {"pt":"deus","fr":"dieu","de":"Gott","es":"dios","it":"dio","ja":"神","la":"deus","ar":"الله"},
        "man":       {"pt":"homem","fr":"homme","de":"Mensch","es":"hombre","it":"uomo","ja":"人","la":"homo","ar":"إنسان"},
        "woman":     {"pt":"mulher","fr":"femme","de":"Frau","es":"mujer","it":"donna","ja":"女","la":"femina","ar":"امرأة"},
        "child":     {"pt":"criança","fr":"enfant","de":"Kind","es":"niño","it":"bambino","ja":"子供","la":"puer","ar":"طفل"},
        "city":      {"pt":"cidade","fr":"ville","de":"Stadt","es":"ciudad","it":"città","ja":"都市","la":"urbs","ar":"مدينة"},
        "water":     {"pt":"água","fr":"eau","de":"Wasser","es":"agua","it":"acqua","ja":"水","la":"aqua","ar":"ماء"},
        "fire":      {"pt":"fogo","fr":"feu","de":"Feuer","es":"fuego","it":"fuoco","ja":"火","la":"ignis","ar":"نار"},
        "earth":     {"pt":"terra","fr":"terre","de":"Erde","es":"tierra","it":"terra","ja":"大地","la":"terra","ar":"أرض"},
        "sky":       {"pt":"céu","fr":"ciel","de":"Himmel","es":"cielo","it":"cielo","ja":"空","la":"caelum","ar":"سماء"},
    }
    p = palavra.lower()
    if p in dicionario:
        return dicionario[p]
    # fallback: gera variações fonéticas simuladas
    return {
        "pt": p + "o" if not p.endswith('o') else p,
        "fr": p + "e" if not p.endswith('e') else p,
        "de": p[0].upper() + p[1:],
        "es": p,
        "it": p + "a" if not p.endswith('a') else p,
        "ja": "【" + p[:3] + "】",
        "la": p + "um",
        "ar": "◌" + p[:4],
    }

# ── PROTOCOLO 0 ──────────────────────────────────────────────────────────────

def protocolo_zero(texto):
    ls = linhas(texto)
    palavras = tokenizar(texto)
    letras = [c for c in texto.lower() if c.isalpha()]
    ppl = [len(tokenizar(l)) for l in ls] if ls else [0]
    pontuacao = {
        "vírgulas": texto.count(','), "pontos": texto.count('.'),
        "ponto-e-vírgulas": texto.count(';'), "exclamações": texto.count('!'),
        "interrogações": texto.count('?'), "reticências": texto.count('...'),
    }
    return {
        "01: número de linhas": len(ls),
        "02: número de palavras": len(palavras),
        "021: palavras por linha": ppl,
        "022: média de palavras/linha": round(sum(ppl)/len(ppl), 2) if ppl else 0,
        "03: número de letras": len(letras),
        "04: distribuição de pontuação": pontuacao,
        "05: frequência de letras (top 10)": Counter(letras).most_common(10),
        "06: distribuição de palavras por linha": dict(sorted(Counter(ppl).items())),
        "07: vocabulário único": len(set(palavras)),
        "08: índice de riqueza lexical (TTR)": round(len(set(palavras))/len(palavras), 3) if palavras else 0,
    }

# ── PROTOCOLO 1 ──────────────────────────────────────────────────────────────

def prot1_recitacao_grupos(palavras, n):
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
        "112: recitação em grupos de 2": prot1_recitacao_grupos(palavras, 2),
        "113: recitação em grupos de 3": prot1_recitacao_grupos(palavras, 3),
        "114: recitação em grupos de 4": prot1_recitacao_grupos(palavras, 4),
        "115: recitação em grupos de 6": prot1_recitacao_grupos(palavras, 6),
        "116: recitação em grupos de 8": prot1_recitacao_grupos(palavras, 8),
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
    ls = linhas(texto)

    def anagrama(pp):
        r=[]
        for p in pp:
            l=list(p); random.shuffle(l); r.append("".join(l))
        return r

    def metathese(pp):
        r=[]
        for p in pp:
            if len(p)>=2:
                i=random.randint(0,len(p)-2); lp=list(p); lp[i],lp[i+1]=lp[i+1],lp[i]; r.append("".join(lp))
            else: r.append(p)
        return r

    pref=["re","des","in","anti","sub","super","trans","contra","sobre","extra"]
    vogais="aeiouáéíóú"

    def epentese(pp):
        r=[]
        for p in pp:
            if len(p)>2:
                i=random.randint(1,len(p)-1); r.append(p[:i]+random.choice(vogais)+p[i:])
            else: r.append(p)
        return r

    def paragram(pp):
        r=[]
        for p in pp:
            if len(p)>1:
                i=random.randint(0,len(p)-1); n=list(p); n[i]=random.choice(string.ascii_lowercase); r.append("".join(n))
            else: r.append(p)
        return r

    def isovocal(pp):
        mv={'a':'e','e':'i','i':'o','o':'u','u':'a','á':'é','é':'í','í':'ó','ó':'ú','ú':'à'}
        return ["".join(mv.get(c,c) for c in p) for p in pp]

    chaves=[p for p in palavras if len(p)>4]
    tpls=["«{a}» não é «{b}»","quem tem «{a}» dispensa «{b}»",
          "mais vale «{a}» do que «{b}»","«{a}» com «{b}» faz «{c}»",
          "o «{a}» do outro sempre parece maior","entre «{a}» e «{b}», escolha «{c}»"]
    provs=[]
    for t in tpls:
        try: provs.append(t.format(a=random.choice(chaves),b=random.choice(chaves),c=random.choice(chaves) if len(chaves)>2 else chaves[0]))
        except: pass

    sin={
        "paz":["sossego","silêncio","calma","tranquilidade"],
        "morte":["fim","extinção","repouso eterno","término"],
        "amor":["afeição","carinho","paixão","devoção"],
        "tempo":["duração","era","época","momento"],
        "rest":["repose","stillness","quiet","sleep"],
        "forest":["woodland","grove","thicket","wood"],
        "birds":["fowl","avians","winged creatures","flock"],
        "breath":["sigh","exhalation","wind","air"],
        "silence":["hush","stillness","muteness","quiet"],
        "hilltops":["peaks","summits","crests","heights"],
    }
    trad=[random.choice(sin.get(p,[p+"†"])) for p in palavras[:30]]

    return {
        "211: anagrama": anagrama(palavras[:20]),
        "212: metátese": metathese(palavras[:20]),
        "221: próstese": [random.choice(pref)+p for p in palavras[:20]],
        "222: epêntese": epentese(palavras[:20]),
        "223: parograma": paragram(palavras[:20]),
        "224: tmese (w)": ["w".join(p) for p in palavras[:10]],
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
        if len(palavras[i])>3 and len(palavras[i+1])>3:
            cooc.append(f"{palavras[i]} + {palavras[i+1]}")
    return {
        "frequência das 30 palavras mais comuns": freq,
        "entidades (nomes próprios detectados)": Counter(nomes).most_common(10),
        "pares de co-ocorrência mais frequentes": Counter(cooc).most_common(10),
        "diversidade lexical": round(len(set(palavras))/len(palavras), 3) if palavras else 0,
        "hapax legomena": [p for p,c in Counter(palavras).items() if c==1][:20],
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
    ("Heine","E um tolo espera a resposta."),
    ("Bataille","Não sei quem fala e não sei quem ousa concluir o poema infinito."),
    ("Kierkegaard","Minha cabeça está vazia como um teatro onde acabei de me apresentar."),
    ("Novalis","Quando a palavra secreta é encontrada, toda a falsa existência se dissipa."),
    ("Schiller","Não porque pensemos, queremos ou sentimos, existimos."),
    ("Neruda","Uma confusa trilha sem som nem pássaros."),
]

def protocolo_quatro(texto):
    palavras = tokenizar(texto)
    ancora = extrair_palavra_ancora(texto)
    trad = traducoes_palavra(ancora)
    chaves = [p for p in palavras if len(p)>5 and p not in STOPWORDS]

    assoc = {}
    for chave in random.sample(chaves, min(8, len(chaves))):
        assoc[chave] = random.sample(CITACOES, min(2, len(CITACOES)))

    pals_tem = random.sample(chaves, min(6, len(chaves)))
    perms = [f"{pals_tem[i]} → {pals_tem[j]}"
             for i in range(len(pals_tem)) for j in range(len(pals_tem)) if i!=j]

    return {
        "ancora": ancora,
        "traducoes": trad,
        "associações livres": assoc,
        "permutações temáticas": random.sample(perms, min(12, len(perms))),
        "citações em livre alternância": random.sample(CITACOES, min(6, len(CITACOES))),
    }

# ── PROTOCOLO 5 — Grafo Ontológico ───────────────────────────────────────────

# ── modelos Ollama disponíveis (ordem de preferência) ────────────────────────
OLLAMA_MODELOS_PREFERENCIA = [
    "qwen2.5:3b",
    "qwen2.5:1.5b",
    "llama3.2:3b",
    "llama3.1:8b",
    "mistral:7b",
    "phi3:mini",
]

@st.cache_resource(show_spinner=False)
def _detectar_modelo_ollama():
    """
    Detecta modelos Ollama disponíveis localmente e retorna o melhor disponível.
    Usa a API REST do Ollama (http://localhost:11434).
    Resultado fica em cache na sessão — não re-detecta a cada run.
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        data = json.loads(req.read().decode())
        instalados = {m["name"].split(":")[0] + ":" + m["name"].split(":")[1]
                      if ":" in m["name"] else m["name"] + ":latest"
                      for m in data.get("models", [])}
        # também aceita nomes sem tag
        instalados_base = {m.split(":")[0] for m in instalados}

        for pref in OLLAMA_MODELOS_PREFERENCIA:
            base = pref.split(":")[0]
            if pref in instalados or base in instalados_base:
                # retorna o nome exato instalado
                for ins in instalados:
                    if ins.startswith(base + ":"):
                        return ins
                return pref
        # nenhum preferido encontrado — retorna o primeiro disponível
        if instalados:
            return next(iter(instalados))
        raise RuntimeError("Nenhum modelo encontrado no Ollama.")
    except urllib.error.URLError:
        raise RuntimeError("Ollama não está rodando. Inicie com: ollama serve")


def _inferir_ollama(modelo, prompt, system=None, temperatura=0.3):
    """
    Chama a API REST do Ollama e retorna o texto gerado.
    Usa /api/chat com formato de mensagens.
    """
    import urllib.request

    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": modelo,
        "messages": msgs,
        "stream": False,
        "options": {
            "temperature": temperatura,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_predict": 1024,
            "num_ctx": 2048,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=300)
    data = json.loads(resp.read().decode())
    return data["message"]["content"].strip()


def extrair_grafo_ontologico_llm(texto, max_nos=40):
    """
    Extrai ontologia via Ollama (LLM local quantizado — rápido em CPU e GPU).
    Estratégia em 2 passos:
      1) Análise literária livre em prosa — o modelo raciocina sem schema
      2) Conversão da análise em JSON estruturado
    Requer: ollama serve  +  ollama pull qwen2.5:3b  (ou outro modelo suportado)
    """
    import json as _json

    modelo = _detectar_modelo_ollama()

    trecho = texto[:2000] if len(texto) > 2000 else texto

    # blacklist dinâmica: palavras mais frequentes sem valor estrutural
    tokens_bl = re.findall(r'\b[a-záéíóúâêîôûãõàèìòùç]{3,}\b', texto.lower())
    sw_bl = {
        'que','com','uma','por','não','ele','ela','seu','sua','mas','como',
        'mais','para','dos','das','nos','nas','era','ser','ter','foi','são',
        'está','isso','esse','essa','este','esta','quando','porque','nunca',
        'sempre','depois','antes','ainda','sobre','muito','mesmo','outro',
        'todos','cada','entre','aqui','onde','quem','qual','pela','pelo',
        'desde','além','junto','contra','dentro','fora','nada','tudo','modo',
        'forma','tipo','caso','lado','parte','tempo','vezes','então','assim',
        'logo','tanto','agora','hoje','havia','podia','fazer','quase','algum',
        'alguns','algumas','houve','tinha','foram','estar','sendo','feito',
        'disse','dizia','fazia','ficou','ficam','ficava','seria','teriam',
    }
    freq_bl = Counter(p for p in tokens_bl if p not in sw_bl and len(p) > 3)
    blacklist_str = ", ".join(f'"{p}"' for p, _ in freq_bl.most_common(20))

    SYSTEM = "Você é um analista literário especializado em ontologias narrativas. Responda APENAS com JSON válido, sem markdown, sem texto adicional."

    # ── PASSO 1: análise literária livre ─────────────────────────────────────
    PROMPT_ANALISE = f"""Liste em poucas frases os principais elementos do texto:
- Entidades (personagens, lugares, objetos)
- Temas centrais (abstratos, não palavras comuns)
- Emoções/qualidades dominantes
- Ações narrativas importantes
- Como eles se relacionam

EVITE estas palavras: {blacklist_str}
Liste 10 a 20 elementos. Seja conciso.

TEXTO:
{trecho}"""

    analise = _inferir_ollama(modelo, PROMPT_ANALISE, temperatura=0.3)

    if not analise.strip():
        raise RuntimeError("Modelo não retornou análise.")

    # ── PASSO 2: converte análise em JSON ─────────────────────────────────────
    PROMPT_JSON = f"""Com base na análise literária abaixo, produza um JSON para um grafo ontológico.

ANÁLISE:
{analise[:1200]}

CATEGORIAS PERMITIDAS:
- "entidade": personagem nomeado, lugar, obra, objeto simbólico
- "conceito": tema abstrato (Memória, Profecia, Metalinguagem, Resistência)
- "qualidade": emoção ou atributo dominante (Solidão, Angústia, Êxtase)
- "ação": processo narrativo como substantivo (Fuga, Criação, Ruptura, Busca)
- "relação": vínculo estrutural (Traição, Herança, Eco, Espelhamento)

REGRAS OBRIGATÓRIAS:
- IDs em Title Case: "Memória e Repetição", "Teatro", "Hans Magnus"
- peso 1–10 (10=núcleo protagonista, 1=periférico)
- label das arestas: verbos específicos ao texto (PROIBIDO: "relaciona", "está", "co-ocorre")
- todo nó deve aparecer em pelo menos uma aresta
- entre 15 e {max_nos} nós; entre 20 e 45 arestas

Responda SOMENTE com JSON válido, sem markdown, sem texto antes ou depois:
{{"nos":[{{"id":"Nome","categoria":"conceito","peso":7,"descricao":"papel no texto"}}],"arestas":[{{"source":"Nome A","target":"Nome B","label":"verbo","weight":4}}]}}"""

    raw = _inferir_ollama(modelo, PROMPT_JSON, system=SYSTEM, temperatura=0.1)

    # ── limpeza e parsing multi-estratégia ──────────────────────────────────
    raw = raw.strip()
    # remove markdown fences
    if "```" in raw:
        raw = re.sub(r"```[a-z]*\n?", "", raw).strip().rstrip("`").strip()

    dados = None
    nos_raw = []
    arestas_raw = []

    # estratégia 1: objeto {"nos":[], "arestas":[]}
    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        try:
            dados = _json.loads(m.group(0))
            nos_raw     = dados.get("nos", dados.get("nós", dados.get("nodes", [])))
            arestas_raw = dados.get("arestas", dados.get("edges", dados.get("links", [])))
        except Exception:
            dados = None

    # estratégia 2: o modelo devolveu lista plana de objetos (nós e arestas misturados)
    if not nos_raw:
        m2 = re.search(r'\[[\s\S]*\]', raw)
        if m2:
            try:
                lista = _json.loads(m2.group(0))
                for item in lista:
                    if isinstance(item, dict):
                        if "source" in item or "target" in item:
                            arestas_raw.append(item)
                        elif "id" in item:
                            nos_raw.append(item)
            except Exception:
                pass

    # estratégia 3: múltiplos objetos JSON separados (NDJSON-like)
    if not nos_raw:
        objetos = re.findall(r'\{[^{}]+\}', raw)
        for obj_str in objetos:
            try:
                item = _json.loads(obj_str)
                if "source" in item or "target" in item:
                    arestas_raw.append(item)
                elif "id" in item:
                    nos_raw.append(item)
            except Exception:
                pass

    if not nos_raw:
        raise RuntimeError(f"Nenhum nó parseável. Resposta do modelo:\n{raw[:500]}")

    # ── normaliza nós ─────────────────────────────────────────────────────────
    nos_dict = {}
    for n in nos_raw[:max_nos]:
        nid = str(n.get("id", "")).strip()
        if not nid:
            continue
        cat = n.get("categoria", "conceito")
        if cat not in ("entidade","conceito","qualidade","ação","relação"):
            cat = "conceito"
        nos_dict[nid] = {
            "categoria": cat,
            "peso": max(1, min(10, int(n.get("peso", 3)))),
            "descricao": n.get("descricao", ""),
        }

    nos_set   = set(nos_dict.keys())
    nos_lower = {k.lower(): k for k in nos_set}

    def resolver(s):
        s = str(s).strip()
        if s in nos_set: return s
        sl = s.lower()
        if sl in nos_lower: return nos_lower[sl]
        for k, kc in nos_lower.items():
            if sl in k or k in sl: return kc
        return None

    # ── normaliza arestas ─────────────────────────────────────────────────────
    arestas, vistos = [], set()
    for a in arestas_raw:
        src = resolver(a.get("source",""))
        tgt = resolver(a.get("target",""))
        lbl = str(a.get("label","relaciona")).strip()[:35]
        w   = max(1, min(8, int(a.get("weight", 2))))
        if src and tgt and src != tgt:
            ch = (min(src,tgt), max(src,tgt), lbl)
            if ch not in vistos:
                vistos.add(ch)
                arestas.append({"source":src,"target":tgt,"label":lbl,"weight":w})

    # ── conecta nós isolados ──────────────────────────────────────────────────
    conectados = {a["source"] for a in arestas} | {a["target"] for a in arestas}
    ancora = max(nos_dict, key=lambda k: nos_dict[k]["peso"])
    for nid in nos_set:
        if nid not in conectados and nid != ancora:
            mesmo_tipo = [k for k, v in nos_dict.items()
                          if k in conectados and v["categoria"] == nos_dict[nid]["categoria"] and k != nid]
            alvo = max(mesmo_tipo, key=lambda k: nos_dict[k]["peso"]) if mesmo_tipo else ancora
            arestas.append({"source":nid,"target":alvo,"label":"integra","weight":1})

    return nos_dict, arestas



def extrair_grafo_ontologico_fallback(texto, max_nos=40):
    """
    Fallback estatístico melhorado: usa heurísticas mais inteligentes
    para encontrar termos significativos quando a API não está disponível.
    """
    palavras = tokenizar(texto)
    freq = Counter(palavras)

    # extrai candidatos: palavras longas fora de stopwords
    filtradas = [p for p in palavras if p not in STOPWORDS and len(p) > 4]
    freq_fil = Counter(filtradas)

    # nomes próprios (alta relevância semântica)
    nomes = re.findall(r'\b[A-ZÁÉÍÓÚ][a-záéíóú]{3,}(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]{2,})?\b', texto)
    nomes_freq = Counter(nomes)

    nos_dict = {}

    # 1. nomes próprios → entidade
    for nome, cnt in nomes_freq.most_common(15):
        if len(nome) > 3:
            nos_dict[nome] = {"categoria": "entidade", "peso": min(10, cnt * 2), "descricao": ""}

    # 2. substantivos abstratos (sufixos) → conceito
    sufixos_conceito = ('ção','dade','ismo','eza','ura','ência','ância','agem',
                        'tion','ness','ity','ism','ence','ance','ment','heit','ung')
    for p, cnt in freq_fil.most_common(100):
        if any(p.endswith(s) for s in sufixos_conceito) and p not in nos_dict:
            nos_dict[p] = {"categoria": "conceito", "peso": min(10, cnt), "descricao": ""}
        if len(nos_dict) >= max_nos:
            break

    # 3. complementa com palavras mais frequentes (excluindo genéricas óbvias)
    genericas = {'anos','dias','vez','vezes','coisa','coisas','modo','forma',
                 'lado','lugar','parte','tipo','caso','mesmo','outra','outro'}
    for p, cnt in freq_fil.most_common(60):
        if p not in nos_dict and p not in genericas and len(p) > 4:
            nos_dict[p] = {"categoria": "conceito", "peso": min(10, cnt), "descricao": ""}
        if len(nos_dict) >= max_nos:
            break

    # arestas por co-ocorrência em janela de 8 palavras
    nos_set = set(nos_dict.keys())
    arestas_raw = Counter()
    janela = 8
    palavras_orig = texto.split()
    palavras_lower = [p.lower() for p in palavras_orig]
    for i, p in enumerate(palavras_lower):
        if p in nos_set:
            vizs = palavras_lower[i+1:i+janela]
            for v in vizs:
                if v in nos_set and v != p:
                    arestas_raw[tuple(sorted([p, v]))] += 1
    # também testa nomes próprios (multi-palavra)
    texto_lower = texto.lower()
    nos_list = list(nos_set)
    for i in range(len(nos_list)):
        for j in range(i+1, len(nos_list)):
            a, b = nos_list[i].lower(), nos_list[j].lower()
            # verifica proximidade no texto
            pa, pb = texto_lower.find(a), texto_lower.find(b)
            if pa >= 0 and pb >= 0 and abs(pa-pb) < 400:
                arestas_raw[tuple(sorted([nos_list[i], nos_list[j]]))] += 1

    arestas = []
    labels_fallback = ["relaciona", "co-ocorre", "associa-se", "implica", "qualifica"]
    for (src, tgt), peso in arestas_raw.most_common(50):
        cat_src = nos_dict.get(src, {}).get("categoria", "conceito")
        cat_tgt = nos_dict.get(tgt, {}).get("categoria", "conceito")
        if "ação" in (cat_src, cat_tgt):
            lbl = "implica"
        elif "entidade" in (cat_src, cat_tgt):
            lbl = "associa-se"
        elif "qualidade" in (cat_src, cat_tgt):
            lbl = "qualifica"
        else:
            lbl = "co-ocorre"
        arestas.append({"source": src, "target": tgt, "weight": peso, "label": lbl})

    return nos_dict, arestas


def extrair_grafo_ontologico(texto, max_nos=40, usar_llm=True):
    """
    Wrapper: tenta extração via LLM local; cai no fallback estatístico se falhar.
    Retorna (nos_dict, arestas, metodo_usado).
    """
    if usar_llm:
        try:
            nos, arestas = extrair_grafo_ontologico_llm(texto, max_nos)
            return nos, arestas, "local"
        except Exception as e:
            return *extrair_grafo_ontologico_fallback(texto, max_nos), f"fallback ({e})"
    else:
        return *extrair_grafo_ontologico_fallback(texto, max_nos), "fallback (manual)"


def gerar_html_grafo(nos_dict, arestas, titulo="grafo ontológico"):
    """
    Gera HTML com canvas force-directed no estilo grafoOllama:
    fundo #0a0a0a, nós com glow intenso e borda colorida, arestas curvas com seta,
    painel lateral ao clicar no nó, partículas de fundo, física suave,
    drag interativo, zoom com trackpad, controles flutuantes.
    """

    CORES = {
        "conceito":  {"fill": "#0d2d45", "stroke": "#4aa8e8", "glow": "#4aa8e8", "text": "#7cc8f8"},
        "ação":      {"fill": "#0d2d1a", "stroke": "#4ecb6e", "glow": "#4ecb6e", "text": "#7de89d"},
        "qualidade": {"fill": "#2d2200", "stroke": "#f0c040", "glow": "#f0c040", "text": "#f8d870"},
        "entidade":  {"fill": "#2d1000", "stroke": "#f07040", "glow": "#f07040", "text": "#f8a070"},
        "relação":   {"fill": "#1e0d35", "stroke": "#b060f0", "glow": "#b060f0", "text": "#d090ff"},
    }

    # serializa nós com raio proporcional ao peso
    nos_js = []
    for nome, dados in nos_dict.items():
        cat = dados.get("categoria", "conceito")
        peso = dados.get("peso", 1)
        cor = CORES.get(cat, CORES["conceito"])
        raio = max(18, min(44, 14 + peso * 3.5))
        nos_js.append({
            "id": nome,
            "label": nome,
            "categoria": cat,
            "peso": peso,
            "raio": raio,
            "fill": cor["fill"],
            "stroke": cor["stroke"],
            "glow": cor["glow"],
            "textColor": cor["text"],
        })

    nos_json = json.dumps(nos_js, ensure_ascii=False)
    arestas_json = json.dumps(arestas, ensure_ascii=False)

    legenda_items = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px">'
        f'<span style="width:9px;height:9px;border-radius:50%;background:{v["fill"]};'
        f'border:1.5px solid {v["stroke"]};box-shadow:0 0 5px {v["glow"]};display:inline-block"></span>'
        f'<span style="color:#666;font-size:10px;letter-spacing:0.08em">{k}</span></span>'
        for k, v in CORES.items()
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0a0a0a; font-family:'Courier New',monospace; overflow:hidden; user-select:none; }}
  #canvas {{ display:block; cursor:grab; }}
  #canvas:active {{ cursor:grabbing; }}

  #header {{
    position:absolute; top:14px; left:50%; transform:translateX(-50%);
    text-align:center; pointer-events:none;
  }}
  #header-title {{
    color:#2a2a2a; font-size:10px; letter-spacing:0.25em; text-transform:uppercase;
  }}
  #header-sub {{
    color:#1a1a1a; font-size:9px; letter-spacing:0.15em; margin-top:2px;
  }}

  #legenda {{
    position:absolute; bottom:14px; left:50%; transform:translateX(-50%);
    display:flex; flex-wrap:wrap; justify-content:center; gap:2px;
    background:rgba(8,8,8,0.92); padding:7px 16px; border:1px solid #1a1a1a;
    border-radius:2px;
  }}

  #controls {{
    position:absolute; top:14px; left:14px; display:flex; flex-direction:column; gap:6px;
  }}
  .btn {{
    background:rgba(10,10,10,0.9); border:1px solid #222; color:#555;
    font-family:'Courier New',monospace; font-size:9px; letter-spacing:0.1em;
    padding:5px 10px; cursor:pointer; transition:all 0.15s;
    text-transform:uppercase;
  }}
  .btn:hover {{ border-color:#444; color:#aaa; background:#111; }}
  .btn.active {{ border-color:#666; color:#ccc; }}

  #stats {{
    position:absolute; top:14px; right:14px;
    color:#222; font-size:9px; letter-spacing:0.1em; text-align:right;
    line-height:1.8; pointer-events:none;
  }}

  /* painel lateral de detalhes do nó */
  #panel {{
    position:absolute; right:14px; top:50%; transform:translateY(-50%);
    width:200px; background:rgba(8,8,8,0.95); border:1px solid #1e1e1e;
    padding:14px; display:none; font-size:10px; line-height:1.9;
  }}
  #panel-name {{
    font-size:13px; letter-spacing:0.1em; margin-bottom:8px;
    border-bottom:1px solid #1e1e1e; padding-bottom:8px;
  }}
  #panel-close {{
    float:right; cursor:pointer; color:#444; font-size:11px;
  }}
  #panel-close:hover {{ color:#888; }}
  .panel-label {{ color:#333; font-size:9px; letter-spacing:0.12em; }}
  .panel-val {{ color:#888; }}

  #panel-connections {{ margin-top:10px; }}
  .conn-item {{
    padding:3px 0; color:#444; font-size:9px;
    border-bottom:1px solid #111; letter-spacing:0.05em;
  }}
  .conn-item span {{ color:#666; }}
</style>
</head>
<body>
<div id="header">
  <div id="header-title">{titulo}</div>
  <div id="header-sub">scroll · arraste · clique</div>
</div>
<div id="stats">
  <span id="stat-nos">nós: {len(nos_js)}</span><br>
  <span id="stat-arestas">arestas: {len(arestas)}</span>
</div>
<div id="legenda">{legenda_items}</div>
<div id="controls">
  <button class="btn active" id="btn-labels" onclick="toggleLabels()">◎ labels</button>
  <button class="btn active" id="btn-edges" onclick="toggleEdgeLabels()">⟷ relações</button>
  <button class="btn" onclick="resetView()">⌂ reset</button>
  <button class="btn" id="btn-freeze" onclick="toggleFreeze()">▶ física</button>
</div>
<div id="panel">
  <div id="panel-name">
    <span id="panel-close" onclick="closePanel()">✕</span>
    <span id="panel-title"></span>
  </div>
  <div class="panel-label">CATEGORIA</div>
  <div class="panel-val" id="panel-cat"></div>
  <div class="panel-label" style="margin-top:6px">FREQUÊNCIA</div>
  <div class="panel-val" id="panel-peso"></div>
  <div class="panel-label" style="margin-top:6px">CONEXÕES</div>
  <div class="panel-val" id="panel-grau"></div>
  <div id="panel-connections"></div>
</div>
<canvas id="canvas"></canvas>

<script>
const NOS_DATA = {nos_json};
const ARESTAS_DATA = {arestas_json};

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

let W, H;
function resize() {{
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
}}
resize();
window.addEventListener('resize', resize);

// estado
let offsetX = 0, offsetY = 0, scale = 1;
let showLabels = true, showEdgeLabels = true;
let frozen = false;
let draggingNode = null, draggingCanvas = false;
let lastMX = 0, lastMY = 0;
let selectedNode = null;
let hoveredNode = null;
let frame = 0;

// partículas de fundo
const PARTICLES = Array.from({{length: 60}}, () => ({{
  x: Math.random() * 2000 - 1000,
  y: Math.random() * 2000 - 1000,
  r: Math.random() * 1.2 + 0.3,
  a: Math.random() * 0.3 + 0.05,
  vx: (Math.random()-0.5) * 0.08,
  vy: (Math.random()-0.5) * 0.08,
}}));

// inicializa nós em círculo com jitter
const nos = NOS_DATA.map((n, i) => {{
  const ang = (2 * Math.PI * i) / NOS_DATA.length;
  const r = Math.min(280, NOS_DATA.length * 7);
  return {{
    ...n,
    x: Math.cos(ang) * r + (Math.random()-0.5)*50,
    y: Math.sin(ang) * r + (Math.random()-0.5)*50,
    vx: 0, vy: 0,
    fx: null, fy: null,
  }};
}});

const nosIdx = {{}};
nos.forEach((n,i) => nosIdx[n.id] = i);

// pré-calcula grau e vizinhos
const grau = {{}};
const vizinhos = {{}};
nos.forEach(n => {{ grau[n.id] = 0; vizinhos[n.id] = []; }});
ARESTAS_DATA.forEach(a => {{
  if (nosIdx[a.source] !== undefined && nosIdx[a.target] !== undefined) {{
    grau[a.source] = (grau[a.source]||0) + 1;
    grau[a.target] = (grau[a.target]||0) + 1;
    vizinhos[a.source] = vizinhos[a.source] || [];
    vizinhos[a.target] = vizinhos[a.target] || [];
    vizinhos[a.source].push({{id: a.target, label: a.label}});
    vizinhos[a.target].push({{id: a.source, label: a.label}});
  }}
}});

// física — repulsão moderada, atração forte, clustering por categoria
const K_REP  = 3500;   // repulsão (era 10000 — expulsava entidades para fora)
const K_ATR  = 0.06;   // atração por aresta (era 0.010 — fraca demais)
const K_CAT  = 0.005;  // atração suave entre nós da mesma categoria
const DIST   = 100;    // distância-alvo das arestas
const DAMP   = 0.80;
const VMAX   = 6;

function simular() {{
  if (frozen) return;

  // repulsão par-a-par
  for (let i = 0; i < nos.length; i++) {{
    nos[i].vx *= DAMP;
    nos[i].vy *= DAMP;
    for (let j = i+1; j < nos.length; j++) {{
      const dx = nos[i].x - nos[j].x, dy = nos[i].y - nos[j].y;
      const d2 = dx*dx + dy*dy + 1;
      const d  = Math.sqrt(d2);
      const f  = K_REP / d2;
      nos[i].vx += f*dx/d; nos[i].vy += f*dy/d;
      nos[j].vx -= f*dx/d; nos[j].vy -= f*dy/d;
    }}
    // gravidade central — mais forte para nós leves/periféricos
    const gf = 0.0008 + 0.004 / (nos[i].peso || 1);
    nos[i].vx -= nos[i].x * gf;
    nos[i].vy -= nos[i].y * gf;
  }}

  // atração por arestas — escala com weight
  ARESTAS_DATA.forEach(a => {{
    const si = nosIdx[a.source], ti = nosIdx[a.target];
    if (si===undefined||ti===undefined) return;
    const s=nos[si], t=nos[ti];
    const dx=t.x-s.x, dy=t.y-s.y;
    const d=Math.sqrt(dx*dx+dy*dy)+0.01;
    const f=K_ATR*(d-DIST)*(0.6 + a.weight*0.08);
    s.vx+=f*dx/d; s.vy+=f*dy/d;
    t.vx-=f*dx/d; t.vy-=f*dy/d;
  }});

  // clustering suave por categoria
  for (let i = 0; i < nos.length; i++) {{
    for (let j = i+1; j < nos.length; j++) {{
      if (nos[i].categoria !== nos[j].categoria) continue;
      const dx=nos[j].x-nos[i].x, dy=nos[j].y-nos[i].y;
      const d=Math.sqrt(dx*dx+dy*dy)+0.01;
      if (d > 300) continue;
      const f=K_CAT*(1 - 200/d);
      nos[i].vx+=f*dx/d; nos[i].vy+=f*dy/d;
      nos[j].vx-=f*dx/d; nos[j].vy-=f*dy/d;
    }}
  }}

  // integração
  nos.forEach(n => {{
    if (n.fx!==null) {{ n.x=n.fx; n.y=n.fy; return; }}
    const sp=Math.sqrt(n.vx*n.vx+n.vy*n.vy);
    if (sp>VMAX) {{ n.vx=n.vx/sp*VMAX; n.vy=n.vy/sp*VMAX; }}
    n.x+=n.vx; n.y+=n.vy;
  }});
  PARTICLES.forEach(p => {{
    p.x+=p.vx; p.y+=p.vy;
    if (Math.abs(p.x)>1200) p.vx*=-1;
    if (Math.abs(p.y)>1200) p.vy*=-1;
  }});
}}

function toScreen(wx, wy) {{
  return [wx*scale + W/2 + offsetX, wy*scale + H/2 + offsetY];
}}
function toWorld(sx, sy) {{
  return [(sx-W/2-offsetX)/scale, (sy-H/2-offsetY)/scale];
}}

function drawArrow(sx, sy, tx, ty, strokeColor, alpha, w) {{
  const dx=tx-sx, dy=ty-sy, d=Math.sqrt(dx*dx+dy*dy);
  if (d<1) return;
  // ponta da seta recuada do nó destino
  const nx=dx/d, ny=dy/d;
  const ex=tx-nx*8, ey=ty-ny*8;
  // ponto de controle para curva
  const mx=(sx+ex)/2, my=(sy+ey)/2;
  const cx=mx-ny*18, cy=my+nx*18;

  ctx.save();
  ctx.globalAlpha=alpha;
  ctx.strokeStyle=strokeColor;
  ctx.lineWidth=w;
  ctx.beginPath();
  ctx.moveTo(sx,sy);
  ctx.quadraticCurveTo(cx,cy,ex,ey);
  ctx.stroke();
  // seta
  const t2=0.95;
  const ax=2*(1-t2)*(cx-sx)+2*t2*(ex-cx);
  const ay=2*(1-t2)*(cy-sy)+2*t2*(ey-cy);
  const an=Math.atan2(ay,ax);
  ctx.beginPath();
  ctx.moveTo(ex,ey);
  ctx.lineTo(ex-8*Math.cos(an-0.4),ey-8*Math.sin(an-0.4));
  ctx.lineTo(ex-8*Math.cos(an+0.4),ey-8*Math.sin(an+0.4));
  ctx.closePath();
  ctx.fillStyle=strokeColor;
  ctx.fill();
  ctx.restore();
}}

function desenharAresta(a) {{
  const si=nosIdx[a.source], ti=nosIdx[a.target];
  if (si===undefined||ti===undefined) return;
  const s=nos[si], t=nos[ti];
  const [sx,sy]=toScreen(s.x,s.y);
  const [tx,ty]=toScreen(t.x,t.y);
  const dx=tx-sx, dy=ty-sy, d=Math.sqrt(dx*dx+dy*dy);
  if (d<1) return;
  // recua das bordas dos nós
  const nx=dx/d, ny=dy/d;
  const x0=sx+nx*s.raio*scale, y0=sy+ny*s.raio*scale;
  const x1=tx-nx*t.raio*scale, y1=ty-ny*t.raio*scale;

  const isHighlighted = selectedNode && (a.source===selectedNode.id||a.target===selectedNode.id);
  const alpha = selectedNode
    ? (isHighlighted ? 0.75 : 0.06)
    : Math.min(0.45, 0.08 + a.weight*0.07);
  const w = Math.min(2.5, 0.6 + a.weight*0.3) * (isHighlighted?1.8:1);
  const color = isHighlighted ? '#88aacc' : '#2a4060';
  drawArrow(x0,y0,x1,y1,color,alpha,w);

  // label da aresta
  if (showEdgeLabels && scale>0.7 && (isHighlighted || (!selectedNode && scale>1.0))) {{
    const mx2=(x0+x1)/2, my2=(y0+y1)/2;
    const ny2=-nx; // perpendicular
    const lx=mx2+ny2*(-18), ly=my2+(nx)*(-18);
    ctx.save();
    ctx.globalAlpha=alpha*1.1;
    ctx.font=`${{Math.max(8,9*scale)}}px 'Courier New'`;
    ctx.fillStyle='#446688';
    ctx.textAlign='center';
    ctx.textBaseline='middle';
    ctx.fillText(a.label, lx, ly);
    ctx.restore();
  }}
}}

function desenharNo(n) {{
  const [x,y]=toScreen(n.x,n.y);
  const r=n.raio*scale;
  if (r<3) return;
  const isSelected = selectedNode && selectedNode.id===n.id;
  const isHovered  = hoveredNode  && hoveredNode.id===n.id;
  const dimmed = selectedNode && !isSelected &&
    !ARESTAS_DATA.some(a=>(a.source===selectedNode.id&&a.target===n.id)||(a.target===selectedNode.id&&a.source===n.id));

  ctx.save();
  ctx.globalAlpha = dimmed ? 0.2 : 1;

  // glow externo
  const glowR = isSelected||isHovered ? 28 : 14;
  const glowA = isSelected ? 0.9 : isHovered ? 0.7 : 0.45;
  const grad = ctx.createRadialGradient(x,y,r*0.4,x,y,r+glowR*scale);
  grad.addColorStop(0, n.glow+'44');
  grad.addColorStop(1, n.glow+'00');
  ctx.beginPath();
  ctx.arc(x,y,r+glowR*scale,0,Math.PI*2);
  ctx.fillStyle=grad;
  ctx.globalAlpha=(dimmed?0.1:glowA);
  ctx.fill();

  ctx.globalAlpha = dimmed ? 0.18 : 1;

  // fill do nó
  const nodeGrad = ctx.createRadialGradient(x-r*0.25,y-r*0.25,r*0.1,x,y,r);
  nodeGrad.addColorStop(0, lighten(n.fill, 0.4));
  nodeGrad.addColorStop(1, n.fill);
  ctx.beginPath();
  ctx.arc(x,y,r,0,Math.PI*2);
  ctx.fillStyle=nodeGrad;
  ctx.fill();

  // borda
  ctx.strokeStyle = isSelected||isHovered ? n.glow : n.stroke;
  ctx.lineWidth = (isSelected ? 2.5 : isHovered ? 2 : 1.5) * Math.max(0.5,scale);
  if (isSelected) {{
    ctx.shadowBlur=20; ctx.shadowColor=n.glow;
  }}
  ctx.stroke();
  ctx.shadowBlur=0;

  // label dentro do nó
  if (showLabels && scale>0.3) {{
    const fsize = Math.max(9, Math.min(13, r*0.48));
    ctx.font=`bold ${{fsize}}px 'Courier New'`;
    ctx.textAlign='center';
    ctx.textBaseline='middle';
    ctx.fillStyle = isSelected||isHovered ? '#ffffff' : n.textColor;
    ctx.shadowBlur=6; ctx.shadowColor='#000';
    const label = n.label.length>13 ? n.label.slice(0,12)+'…' : n.label;
    ctx.fillText(label,x,y);
    ctx.shadowBlur=0;
    // categoria abaixo, fora do nó
    if (scale>0.65) {{
      ctx.font=`${{Math.max(7,8*scale)}}px 'Courier New'`;
      ctx.fillStyle=n.stroke;
      ctx.globalAlpha = dimmed ? 0.15 : 0.6;
      ctx.fillText(n.categoria, x, y+r+Math.max(9,11*scale));
      ctx.globalAlpha=1;
    }}
  }}
  ctx.restore();
}}

function lighten(hex, f) {{
  const n=parseInt(hex.replace('#',''),16);
  const r=Math.min(255,((n>>16)&0xff)+Math.round(f*80));
  const g=Math.min(255,((n>>8)&0xff)+Math.round(f*80));
  const b=Math.min(255,(n&0xff)+Math.round(f*80));
  return `rgb(${{r}},${{g}},${{b}})`;
}}

function desenhar() {{
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle='#0a0a0a';
  ctx.fillRect(0,0,W,H);

  // grade
  ctx.save();
  ctx.strokeStyle='#0f0f0f';
  ctx.lineWidth=0.5;
  const step=80*scale;
  const ox=(offsetX+W/2)%step, oy=(offsetY+H/2)%step;
  for (let x=ox;x<W;x+=step) {{ ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke(); }}
  for (let y=oy;y<H;y+=step) {{ ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke(); }}
  ctx.restore();

  // partículas
  PARTICLES.forEach(p => {{
    const [px,py]=toScreen(p.x,p.y);
    ctx.save();
    ctx.globalAlpha=p.a*(0.4+0.3*Math.sin(frame*0.02+p.x));
    ctx.fillStyle='#336688';
    ctx.beginPath();
    ctx.arc(px,py,p.r,0,Math.PI*2);
    ctx.fill();
    ctx.restore();
  }});

  // arestas
  ARESTAS_DATA.forEach(a => desenharAresta(a));
  // nós
  nos.forEach(n => desenharNo(n));
}}

function loop() {{
  const steps = frame < 200 ? 3 : frame < 500 ? 2 : 1;
  for (let i=0;i<steps;i++) simular();
  frame++;
  desenhar();
  requestAnimationFrame(loop);
}}
loop();

// PAINEL DE DETALHES
function openPanel(n) {{
  selectedNode = n;
  document.getElementById('panel').style.display='block';
  document.getElementById('panel-title').textContent = n.label;
  document.getElementById('panel-title').style.color = n.stroke;
  document.getElementById('panel-cat').textContent = n.categoria;
  document.getElementById('panel-peso').textContent = n.peso;
  const g = grau[n.id]||0;
  document.getElementById('panel-grau').textContent = g;
  const viz = (vizinhos[n.id]||[]).slice(0,8);
  const conn = document.getElementById('panel-connections');
  conn.innerHTML = viz.map(v=>
    `<div class="conn-item">&#x2192; <span>${{v.id}}</span> <span style="color:#2a4060">[` + v.label + `]</span></div>`
  ).join('');
}}
function closePanel() {{
  selectedNode = null;
  document.getElementById('panel').style.display='none';
}}

// INTERAÇÕES
// TOOLTIP no hover
const tooltip = document.createElement('div');
tooltip.id = 'graph-tooltip';
tooltip.style.cssText = 'position:fixed;background:#1a1a1a;border:1px solid #444;border-left:3px solid #4aa8e8;padding:8px 12px;font-family:monospace;font-size:0.75rem;color:#ccc;pointer-events:none;display:none;z-index:9999;max-width:220px;line-height:1.5';
document.body.appendChild(tooltip);

canvas.addEventListener('mousemove', e => {{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const [wx,wy]=toWorld(mx,my);
  if (draggingNode) {{
    draggingNode.fx=wx; draggingNode.fy=wy;
    draggingNode.x=wx; draggingNode.y=wy;
  }} else if (draggingCanvas) {{
    offsetX+=mx-lastMX; offsetY+=my-lastMY;
  }} else {{
    hoveredNode=null;
    for (const n of nos) {{
      const dx=n.x-wx, dy=n.y-wy;
      if (Math.sqrt(dx*dx+dy*dy) < n.raio+3/scale) {{
        hoveredNode=n; canvas.style.cursor='pointer';
        // mostrar tooltip
        const tt=document.getElementById('graph-tooltip');
        tt.innerHTML = '<strong style="color:#e8e8e8">' + n.label + '</strong><br>'
          + '<span style="color:#666;font-size:0.7rem">' + n.categoria.toUpperCase() + ' · peso ' + n.peso + '</span>'
          + (n.descricao ? '<br><span style="color:#aaa;font-style:italic">' + n.descricao + '</span>' : '');
        tt.style.display='block';
        tt.style.left=(e.clientX+14)+'px';
        tt.style.top=(e.clientY-10)+'px';
        break;
      }}
    }}
    if (!hoveredNode) {{
      canvas.style.cursor='grab';
      document.getElementById('graph-tooltip').style.display='none';
    }}
  }}
  lastMX=mx; lastMY=my;
}});

canvas.addEventListener('mousedown', e => {{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const [wx,wy]=toWorld(mx,my);
  for (const n of nos) {{
    const dx=n.x-wx, dy=n.y-wy;
    if (Math.sqrt(dx*dx+dy*dy) < n.raio+3/scale) {{
      draggingNode=n; n.fx=n.x; n.fy=n.y; return;
    }}
  }}
  draggingCanvas=true;
}});

canvas.addEventListener('mouseup', e => {{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const [wx,wy]=toWorld(mx,my);
  if (draggingNode) {{
    // click sem drag → abre painel
    const dx=draggingNode.x-wx, dy=draggingNode.y-wy;
    if (Math.sqrt(dx*dx+dy*dy)<2/scale) openPanel(draggingNode);
    draggingNode.fx=null; draggingNode.fy=null; draggingNode=null;
  }} else {{
    // clique no vazio fecha painel
    let hitNode=false;
    for (const n of nos) {{
      const dx2=n.x-wx, dy2=n.y-wy;
      if (Math.sqrt(dx2*dx2+dy2*dy2)<n.raio+3/scale) {{ hitNode=true; break; }}
    }}
    if (!hitNode && selectedNode) closePanel();
  }}
  draggingCanvas=false;
  canvas.style.cursor='grab';
}});

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const delta=e.deltaY>0?0.88:1.13;
  const ns=Math.max(0.12,Math.min(5,scale*delta));
  offsetX=mx-W/2-(mx-W/2-offsetX)*(ns/scale);
  offsetY=my-H/2-(my-H/2-offsetY)*(ns/scale);
  scale=ns;
}},{{passive:false}});

// touch
let lastPinchDist=null;
canvas.addEventListener('touchstart', e => {{
  if (e.touches.length===1) {{
    lastMX=e.touches[0].clientX; lastMY=e.touches[0].clientY; draggingCanvas=true;
  }}
}},{{passive:true}});
canvas.addEventListener('touchmove', e => {{
  if (e.touches.length===2) {{
    const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,
                       e.touches[0].clientY-e.touches[1].clientY);
    if (lastPinchDist) {{ scale=Math.max(0.12,Math.min(5,scale*(d/lastPinchDist))); }}
    lastPinchDist=d;
  }} else if (draggingCanvas&&e.touches.length===1) {{
    offsetX+=e.touches[0].clientX-lastMX; offsetY+=e.touches[0].clientY-lastMY;
    lastMX=e.touches[0].clientX; lastMY=e.touches[0].clientY;
  }}
}},{{passive:true}});
canvas.addEventListener('touchend', () => {{ draggingCanvas=false; lastPinchDist=null; }},{{passive:true}});

function resetView() {{ offsetX=0; offsetY=0; scale=1; frame=0; }}
function toggleLabels() {{
  showLabels=!showLabels;
  document.getElementById('btn-labels').classList.toggle('active',showLabels);
}}
function toggleEdgeLabels() {{
  showEdgeLabels=!showEdgeLabels;
  document.getElementById('btn-edges').classList.toggle('active',showEdgeLabels);
}}
function toggleFreeze() {{
  frozen=!frozen;
  const btn=document.getElementById('btn-freeze');
  btn.textContent=frozen?'⏸ física':'▶ física';
  btn.classList.toggle('active',!frozen);
}}
</script>
</body>
</html>"""
    return html

# ── Interface Streamlit ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="A Máquina — Georges Perec",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap');
html, body, [class*="css"] { font-family: 'Courier Prime', 'Courier New', monospace; }
.stApp { background-color: #0a0a0a; color: #d4d4d4; }
h1, h2, h3 { color: #e8e8e8 !important; letter-spacing: 0.05em; }
.stButton > button {
  background-color: #1a1a1a; color: #d4d4d4;
  border: 1px solid #444; font-family: 'Courier Prime', monospace;
  letter-spacing: 0.1em;
}
.stButton > button:hover { background-color: #2a2a2a; border-color: #888; color: #fff; }
.terminal-box {
  background-color: #111111; border: 1px solid #333;
  border-left: 3px solid #666; padding: 1rem 1.2rem;
  margin: 0.5rem 0; font-size: 0.82rem; line-height: 1.6;
  color: #c8c8c8; white-space: pre-wrap; word-break: break-word;
}
.protocol-header {
  background-color: #151515; border-top: 1px solid #555;
  border-bottom: 1px solid #333; padding: 0.4rem 0.8rem;
  color: #aaaaaa; font-size: 0.75rem; letter-spacing: 0.15em;
  text-transform: uppercase; margin: 1.2rem 0 0.4rem 0;
}
.counter-label { color: #777; font-size: 0.7rem; letter-spacing: 0.12em; }
div[data-testid="stSidebarContent"] { background-color: #0d0d0d; }
.stTabs [data-baseweb="tab"] {
  background-color: #111; color: #888;
  font-family: 'Courier Prime', monospace;
  font-size: 0.8rem; letter-spacing: 0.08em;
}
.stTabs [aria-selected="true"] { color: #ddd !important; border-bottom-color: #666 !important; }
.stTextArea textarea {
  background-color: #111; color: #ccc;
  font-family: 'Courier Prime', monospace;
  font-size: 0.82rem; border: 1px solid #333;
}
.ancora-word {
  font-size: 2.2rem; letter-spacing: 0.4em; color: #888;
  text-align: center; padding: 1.5rem 0 0.5rem 0;
  text-transform: uppercase;
}
.ancora-sub { font-size: 0.65rem; color: #444; letter-spacing: 0.2em; text-align: center; }
.blink { animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }
/* esconder header branco do Streamlit */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
.block-container { padding-top: 1rem !important; }
/* estilizar uploader */
[data-testid="stFileUploader"] section { background: #111; border: 1px dashed #444; border-radius: 4px; }
[data-testid="stFileUploader"] section:hover { border-color: #888; }
[data-testid="stFileUploader"] section p { color: #666 !important; }
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
    st.markdown("<span style='font-size:0.7rem;color:#555;letter-spacing:0.08em'>PROTOCOLOS ATIVOS</span>", unsafe_allow_html=True)
    prot0 = st.checkbox("00 — Análise estatística", value=True)
    st.caption("Conta linhas, palavras, letras, pontuação e riqueza lexical.")
    prot1 = st.checkbox("01 — Operações internas", value=True)
    st.caption("Recitações, inversões, permutações e deformações internas do texto.")
    prot2 = st.checkbox("02 — Operações externas", value=True)
    st.caption("Anagramas, metáteses, traduções, provérbios e transformações linguísticas.")
    prot3 = st.checkbox("03 — Análise crítica", value=True)
    st.caption("Frequências, entidades, coocorrências e diversidade lexical.")
    prot4 = st.checkbox("04 — Explosão de citações", value=True)
    st.caption("Associa palavras a citações, traduções e permutações temáticas.")
    prot5 = st.checkbox("05 — Grafo ontológico", value=True)
    st.caption("Constrói uma rede visual de conceitos e relações extraídos do texto.")
    st.markdown("---")
    seed_val = st.number_input("SEMENTE ALEATÓRIA", value=42, min_value=0, max_value=9999)
    if prot5:
        max_nos = st.slider("NÓS NO GRAFO", 15, 60, 40)
    else:
        max_nos = 40
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
st.markdown("<div style='border-top:1px solid #2a2a2a;margin:0.5rem 0 1.5rem 0'></div>", unsafe_allow_html=True)

texto_bruto = None

if fonte == "📂 Upload de arquivo":
    st.markdown(
        "<style>"
        "[data-testid='stFileUploaderDropzoneInstructions'] div span:first-child"
        " { display:none; }"
        "[data-testid='stFileUploaderDropzoneInstructions']::before"
        " { content:'Arraste e solte o arquivo aqui'; color:#666; font-family:inherit; font-size:0.9rem; }"
        "[data-testid='stFileUploaderDropzoneInstructions'] div small"
        " { display:none; }"
        "[data-testid='stFileUploaderDropzoneInstructions']::after"
        " { content:'Limite 200MB · PDF, DOCX, DOC, TXT'; color:#444; font-size:0.75rem; display:block; margin-top:4px; }"
        "[data-testid='stBaseButton-secondary'] { color:#888 !important; border-color:#444 !important; }"
        "[data-testid='stBaseButton-secondary']::after { content:'Procurar arquivo'; }"
        "[data-testid='stBaseButton-secondary'] p { display:none; }"
        "</style>", unsafe_allow_html=True)
    arq = st.file_uploader("INSERIR ARQUIVO", type=["pdf","docx","doc","txt"], label_visibility="collapsed")
    if arq:
        with st.spinner("lendo arquivo..."):
            texto_bruto = carregar_texto(arq)
        st.markdown(
            f"<div class='terminal-box'>"
            f"<span class='counter-label'>ARQUIVO: </span>{arq.name} "
            f"<span class='counter-label'>· CARACTERES: </span>{len(texto_bruto)}"
            f"</div>", unsafe_allow_html=True)
else:
    texto_bruto = st.text_area("INSERIR TEXTO", height=180,
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
# processamento automático após carga do arquivo

# ── Execução ──────────────────────────────────────────────────────────────────

random.seed(int(seed_val))
palavras_globais = tokenizar(texto_bruto)
ls_globais = linhas(texto_bruto)

tabs = st.tabs([
    "00 · ESTATÍSTICA",
    "01 · INTERNO",
    "02 · EXTERNO",
    "03 · CRÍTICA",
    "04 · CITAÇÕES",
    "05 · GRAFO",
])

# ── TAB 0 ─────────────────────────────────────────────────────────────────────

with tabs[0]:
    if not prot0:
        st.markdown("<div class='terminal-box'>protocolo 00 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 0 · análise estatística básica</div>", unsafe_allow_html=True)
        dados = protocolo_zero(texto_bruto)
        col1,col2,col3,col4 = st.columns(4)
        for col,(lbl,val) in zip([col1,col2,col3,col4],[
            ("LINHAS", dados["01: número de linhas"]),
            ("PALAVRAS", dados["02: número de palavras"]),
            ("LETRAS", dados["03: número de letras"]),
            ("VOCAB ÚNICO", dados["07: vocabulário único"]),
        ]):
            with col:
                st.markdown(
                    f"<div class='terminal-box' style='text-align:center'>"
                    f"<div style='font-size:1.6rem;color:#ccc'>{val}</div>"
                    f"<div class='counter-label'>{lbl}</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>022: média de palavras por linha</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{dados['022: média de palavras/linha']}</div>", unsafe_allow_html=True)

        ttr = dados["08: índice de riqueza lexical (TTR)"]
        st.markdown("<div class='protocol-header'>08: índice de riqueza lexical (TTR)</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='terminal-box'>{ttr} "
            f"<span class='counter-label'>— {'texto rico' if ttr>0.6 else 'texto repetitivo' if ttr<0.3 else 'densidade média'}</span></div>",
            unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>04: pontuação</div>", unsafe_allow_html=True)
        pont = dados["04: distribuição de pontuação"]
        st.markdown(f"<div class='terminal-box'>{'   '.join(f'{k}={v}' for k,v in pont.items() if v>0) or '(nenhuma)'}</div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>05: frequência de letras (top 10)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{'   '.join(f'{l}={n}' for l,n in dados['05: frequência de letras (top 10)'])}</div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>07: distribuição sintática</div>", unsafe_allow_html=True)
        cats = classificar_palavras(palavras_globais[:200])
        for cat, pals in cats.items():
            if pals:
                st.markdown(
                    f"<div class='terminal-box'>"
                    f"<span class='counter-label'>{cat}:</span> {'   '.join(pals[:12])}</div>",
                    unsafe_allow_html=True)

# ── TAB 1 ─────────────────────────────────────────────────────────────────────

with tabs[1]:
    if not prot1:
        st.markdown("<div class='terminal-box'>protocolo 01 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 1 · operações internas · deformações rítmicas</div>", unsafe_allow_html=True)
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
                            st.markdown(
                                "<div class='terminal-box'>"+"<br>".join(bloco[:30])+
                                ("..." if len(bloco)>30 else "")+"</div>", unsafe_allow_html=True)
                elif chave == "122: arranjo vertical":
                    st.markdown("<div class='terminal-box'>"+"<br>".join(valor[:40])+"</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='protocol-header'>protocolo nº 2 · operações externas · substituições e transformações</div>", unsafe_allow_html=True)
        p2 = protocolo_dois(texto_bruto)
        for chave, valor in p2.items():
            st.markdown(f"<div class='protocol-header'>{chave}</div>", unsafe_allow_html=True)
            if isinstance(valor, list):
                txt = "   ".join(str(v) for v in valor)
                st.markdown(f"<div class='terminal-box'>{txt}</div>", unsafe_allow_html=True)
            elif isinstance(valor, dict):
                for k,v in valor.items():
                    st.markdown(
                        f"<div class='terminal-box'><span class='counter-label'>{k}:</span><br>"
                        f"{'   '.join(str(x) for x in v)}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='terminal-box'>{valor}</div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>253: frequência como dados enciclopédicos</div>", unsafe_allow_html=True)
        for palavra, contagem in Counter(palavras_globais).most_common(15):
            barra = "█" * min(40, contagem)
            st.markdown(
                f"<div class='terminal-box' style='padding:0.3rem 1rem'>"
                f"<span style='display:inline-block;width:120px;color:#aaa'>{palavra}</span>"
                f"<span style='color:#555'>{barra}</span>"
                f"<span class='counter-label'> {contagem}</span></div>", unsafe_allow_html=True)

# ── TAB 3 ─────────────────────────────────────────────────────────────────────

with tabs[3]:
    if not prot3:
        st.markdown("<div class='terminal-box'>protocolo 03 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 3 · elementos críticos · análise do corpus</div>", unsafe_allow_html=True)
        p3 = protocolo_tres(texto_bruto)

        st.markdown("<div class='protocol-header'>frequência das 30 palavras mais comuns</div>", unsafe_allow_html=True)
        for palavra, cont in p3["frequência das 30 palavras mais comuns"]:
            barra = "▓" * min(50, cont*2)
            st.markdown(
                f"<div class='terminal-box' style='padding:0.25rem 1rem'>"
                f"<span style='display:inline-block;width:140px'>{palavra}</span>"
                f"<span style='color:#444'>{barra}</span> "
                f"<span class='counter-label'>{cont}</span></div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>entidades detectadas (nomes próprios)</div>", unsafe_allow_html=True)
        ents = p3["entidades (nomes próprios detectados)"]
        st.markdown(
            f"<div class='terminal-box'>{'   '.join(f'{n} ({c})' for n,c in ents) or '(nenhuma detectada)'}</div>",
            unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>pares de co-ocorrência mais frequentes</div>", unsafe_allow_html=True)
        for par, cont in p3["pares de co-ocorrência mais frequentes"]:
            st.markdown(
                f"<div class='terminal-box' style='padding:0.25rem 1rem'>"
                f"{par} <span class='counter-label'>× {cont}</span></div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>hapax legomena · palavras únicas</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{'   '.join(p3['hapax legomena'])} ···</div>", unsafe_allow_html=True)

        div = p3["diversidade lexical"]
        av = "MUITO RICA" if div>0.7 else "RICA" if div>0.5 else "MÉDIA" if div>0.3 else "REPETITIVA"
        st.markdown("<div class='protocol-header'>diversidade lexical (TTR)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='terminal-box'>{div} · {av}</div>", unsafe_allow_html=True)

# ── TAB 4 ─────────────────────────────────────────────────────────────────────

with tabs[4]:
    if not prot4:
        st.markdown("<div class='terminal-box'>protocolo 04 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='protocol-header'>protocolo nº 4 · explosão de citações · busca por associação livre</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='terminal-box'>"
            "PROCESSADORES 1, 2, 3 E CONTROLE DO SISTEMA FALAM EM LIVRE ALTERNÂNCIA"
            "</div>", unsafe_allow_html=True)

        p4 = protocolo_quatro(texto_bruto)
        ancora = p4["ancora"]
        trad = p4["traducoes"]

        st.markdown("<div class='protocol-header'>associações livres · palavra-chave → citações</div>", unsafe_allow_html=True)
        for chave, cits in p4["associações livres"].items():
            st.markdown(
                f"<div class='terminal-box'>"
                f"<span style='color:#888'>{chave}</span><br><br>"
                + "<br><br>".join(
                    f"<em>{tc}</em><br><span class='counter-label'>— {au}</span>"
                    for au, tc in cits)
                + "</div>", unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>permutações temáticas</div>", unsafe_allow_html=True)
        cols = st.columns(3)
        perms = p4["permutações temáticas"]
        chunk = max(1, len(perms)//3)
        for i, col in enumerate(cols):
            with col:
                st.markdown(
                    "<div class='terminal-box'>"+"<br>".join(perms[i*chunk:(i+1)*chunk])+"</div>",
                    unsafe_allow_html=True)

        st.markdown("<div class='protocol-header'>citações em livre alternância</div>", unsafe_allow_html=True)
        for au, cit in p4["citações em livre alternância"]:
            st.markdown(
                f"<div class='terminal-box'>{cit}<br>"
                f"<span class='counter-label'>— {au}</span></div>", unsafe_allow_html=True)

        # ── PALAVRA ÂNCORA + MULTILINGUISMO ──────────────────────────────────
        st.markdown("<div class='protocol-header'>palavra âncora do texto · multilinguismo</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='ancora-word'>{ancora}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='ancora-sub'>palavra mais semanticamente central do texto</div>", unsafe_allow_html=True)

        # tabela de traduções
        bandeiras = {"pt":"🇧🇷","fr":"🇫🇷","de":"🇩🇪","es":"🇪🇸","it":"🇮🇹","ja":"🇯🇵","la":"🏛️","ar":"🌙"}
        trad_html = "".join(
            f"<span style='display:inline-block;margin:6px 12px;text-align:center'>"
            f"<span style='font-size:1.3rem'>{bandeiras.get(lang,'')}</span><br>"
            f"<span style='color:#aaa;font-size:0.9rem'>{palavra}</span><br>"
            f"<span class='counter-label'>{lang}</span>"
            f"</span>"
            for lang, palavra in trad.items()
        )
        st.markdown(
            f"<div class='terminal-box' style='text-align:center;padding:1.2rem'>{trad_html}</div>",
            unsafe_allow_html=True)

        # coda multilíngue (com a palavra âncora)
        ancora_up = ancora.upper()
        sufixos = ["o","e","","um","os","es","ão","ung","eit","ion","ità","ité","α","a","i"]
        variantes = "   ".join(ancora_up[:max(3,len(ancora_up)-1)+i%3] for i in range(8))
        ruido = "   ".join(trad.values())
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='terminal-box' style='text-align:center;letter-spacing:0.3em;color:#444'>"
            f"{ancora_up}<br><br>"
            f"{ruido}<br><br>"
            f"{variantes}<br><br>"
            f"p{ancora[:2]}z   p{ancora[:2]}zz   p{ancora[:3]}sh   sh{ancora[:2]}sh   sh{ancora[:2]}shshsh"
            f"</div>", unsafe_allow_html=True)

# ── TAB 5 — GRAFO ONTOLÓGICO ──────────────────────────────────────────────────

with tabs[5]:
    if not prot5:
        st.markdown("<div class='terminal-box'>protocolo 05 desativado</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='protocol-header'>"
            "protocolo nº 5 · grafo ontológico · rede de conceitos e relações"
            "</div>", unsafe_allow_html=True)

        # ── controles de extração ─────────────────────────────────────────────
        col_llm, col_info = st.columns([1, 2])
        with col_llm:
            usar_llm = st.toggle("🧠 Extração semântica (Ollama)", value=True,
                help="Usa modelo LLM local via Ollama para identificar personagens, temas e conceitos "
                     "narrativos reais. Requer: ollama serve + ollama pull qwen2.5:3b. "
                     "Desative para usar extração estatística (rápida, sem modelo).")
        with col_info:
            if usar_llm:
                try:
                    modelo_det = _detectar_modelo_ollama()
                    info_modelo = f"<span style='color:#4ecb6e'>{modelo_det}</span> · via Ollama"
                except Exception as e:
                    info_modelo = f"<span style='color:#f07040'>Ollama indisponível</span> · {str(e)[:60]}"
                st.markdown(
                    f"<div class='terminal-box' style='padding:0.4rem 0.8rem;font-size:0.75rem'>"
                    f"modo: <span style='color:#4aa8e8'>semântico local</span> · "
                    f"{info_modelo}"
                    f"</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div class='terminal-box' style='padding:0.4rem 0.8rem;font-size:0.75rem'>"
                    "modo: <span style='color:#f0c040'>estatístico</span> · "
                    "frequência e heurísticas locais (qualidade reduzida, sem modelo)"
                    "</div>", unsafe_allow_html=True)

        # chave de cache: muda se o texto ou o modo mudar
        cache_key = f"grafo_v6_{hash(texto_bruto[:500])}_{usar_llm}_{max_nos}"

        if st.button("⟳ Regenerar grafo", key="btn_regen"):
            if cache_key in st.session_state:
                del st.session_state[cache_key]

        if cache_key not in st.session_state:
            with st.spinner("extraindo ontologia" + (" via LLM local…" if usar_llm else " (modo estatístico)…")):
                nos_dict, arestas, metodo = extrair_grafo_ontologico(
                    texto_bruto, max_nos=max_nos, usar_llm=usar_llm)
            st.session_state[cache_key] = (nos_dict, arestas, metodo)
        else:
            nos_dict, arestas, metodo = st.session_state[cache_key]

        # aviso se caiu no fallback
        if metodo.startswith("fallback"):
            erro_msg = metodo.replace("fallback (", "").rstrip(")")
            st.markdown(
                f"<div class='terminal-box' style='border-left-color:#f07040;font-size:0.75rem'>"
                f"<span style='color:#f07040'>⚠ LLM local indisponível</span> — usando extração estatística. "
                f"<span style='color:#444'>({erro_msg})</span>"
                f"</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                "<div class='terminal-box' style='border-left-color:#4ecb6e;font-size:0.75rem'>"
                "<span style='color:#4ecb6e'>✓ ontologia extraída via Ollama</span>"
                "</div>", unsafe_allow_html=True)

        # estatísticas do grafo
        cats_count = Counter(d["categoria"] for d in nos_dict.values())
        c1,c2,c3,c4,c5 = st.columns(5)
        CORES_LABEL = {
            "conceito":"#4aa8e8","ação":"#4ecb6e",
            "qualidade":"#f0c040","entidade":"#f07040","relação":"#b060f0"
        }
        for col,(cat,cnt) in zip([c1,c2,c3,c4,c5],
            [("conceito",cats_count.get("conceito",0)),
             ("ação",cats_count.get("ação",0)),
             ("qualidade",cats_count.get("qualidade",0)),
             ("entidade",cats_count.get("entidade",0)),
             ("relação",cats_count.get("relação",0))]):
            with col:
                cor = CORES_LABEL[cat]
                st.markdown(
                    f"<div class='terminal-box' style='text-align:center;border-left-color:{cor}'>"
                    f"<div style='font-size:1.4rem;color:{cor}'>{cnt}</div>"
                    f"<div class='counter-label'>{cat}</div></div>", unsafe_allow_html=True)

        st.markdown(
            f"<div class='terminal-box'>"
            f"<span class='counter-label'>TOTAL NÓS:</span> {len(nos_dict)}   "
            f"<span class='counter-label'>TOTAL ARESTAS:</span> {len(arestas)}   "
            f"<span class='counter-label'>DENSIDADE:</span> "
            f"{round(len(arestas)/(len(nos_dict)*(len(nos_dict)-1)/2),3) if len(nos_dict)>1 else 0}"
            f"</div>", unsafe_allow_html=True)

        # grafo interativo
        html_grafo = gerar_html_grafo(nos_dict, arestas,
            titulo=f"grafo ontológico · {len(nos_dict)} conceitos · {len(arestas)} relações")
        st.components.v1.html(html_grafo, height=620, scrolling=False)

        # tabela de nós principais
        st.markdown("<div class='protocol-header'>nós principais por categoria</div>", unsafe_allow_html=True)
        por_cat = {}
        for nome, dados in nos_dict.items():
            por_cat.setdefault(dados["categoria"], []).append((nome, dados["peso"]))
        for cat, itens in sorted(por_cat.items()):
            itens_ord = sorted(itens, key=lambda x: -x[1])[:10]
            cor = CORES_LABEL.get(cat,"#888")
            # mostra descrição LLM se disponível
            partes = []
            for n, p in itens_ord:
                desc = nos_dict[n].get("descricao", "")
                partes.append(f"{n}({p})" + (f" <span style='color:#333'>— {desc}</span>" if desc else ""))
            lista = "   ".join(partes)
            st.markdown(
                f"<div class='terminal-box' style='border-left-color:{cor}'>"
                f"<span class='counter-label' style='color:{cor}'>{cat.upper()}:</span><br>{lista}"
                f"</div>", unsafe_allow_html=True)

        # arestas mais fortes
        st.markdown("<div class='protocol-header'>relações mais fortes</div>", unsafe_allow_html=True)
        for a in sorted(arestas, key=lambda x: -x["weight"])[:15]:
            barra = "─" * min(20, a["weight"]*2)
            st.markdown(
                f"<div class='terminal-box' style='padding:0.3rem 1rem'>"
                f"{a['source']} <span style='color:#446688'>{barra}[{a['label']}]──</span> {a['target']} "
                f"<span class='counter-label'>× {a['weight']}</span></div>", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#333;font-size:0.68rem;letter-spacing:0.15em'>"
    "STOP · FIM DOS PROTOCOLOS · SALVO"
    "</div>", unsafe_allow_html=True)
