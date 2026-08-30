"""
gerar_roteiro.py
Gera roteiros virais de "verdades duras" via OpenRouter API.
Usa modelos gratuitos (:free) com fallback automático entre eles.
Controla os temas usados para evitar repetições em 20 rodadas.
"""

import os
import json
import random
import sys
import re
from pathlib import Path
from openai import OpenAI

# ── Configurações OpenRouter ───────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Modelos gratuitos em ordem de preferência — sufixo :free = sem custo
# Lista atualizada em 29/08/2026 via API do OpenRouter
MODELOS_GRATUITOS = [
    "minimax/minimax-m3:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "minimax/minimax-m2.7:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "liquid/lfm-2.5-2.6b:free",
    "poolside/laguna-s-2.1:free",
    "poolside/laguna-xs-2.1:free",
    "z-ai/glm-5.2:free",
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free",
    "inclusionai/ling-3.0-flash-fin:free",
    "dots-studio/dots-3-note-preview:free",
    "cohere/north-mini-code:free",
    "openrouter/free"
]

TEMAS_FILE = Path(__file__).parent.parent / "temas_usados.json"

TEMAS_BASE = [
    "pessoas que somem quando você mais precisa delas",
    "amizades falsas que só aparecem quando precisam de algo",
    "o preço real de mudar de vida e perder pessoas no caminho",
    "pessoas que te subestimam até você vencer",
    "maturidade emocional que a vida ensina na dor",
    "relacionamentos onde só você se esforça",
    "o peso de crescer sem apoio emocional de ninguém",
    "traição das pessoas em quem você confiava cegamente",
    "a ilusão de que alguém vai te salvar",
    "limites pessoais que você precisa aprender a impor agora",
    "inveja disfarçada de conselho e preocupação com você",
    "a verdade cruel sobre quem desaparece nas suas dificuldades",
    "solidão voluntária como forma de cura e autoconhecimento",
    "silêncio como resposta para quem não merece explicação",
    "abandono que te ensinou a ser forte sozinho",
    "trabalho duro e esforço que nunca é reconhecido pelos outros",
    "mudança de vida que assusta porque exige perder o conforto",
    "pessoas que drenam sua energia sem você perceber",
    "a verdade sobre felicidade que os outros não querem que você saiba",
    "ingratidão de quem você ajudou quando mais precisava",
]

# ── Prompt Mestre ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """# PROMPT MESTRE — CRIADOR DE ROTEIROS VIRAIS DE JESUS PARA VÍDEOS CURTOS

Você é um **especialista em roteiros virais para YouTube Shorts, TikTok, Instagram Reels e vídeos curtos de alta retenção**, especializado em conteúdo cristão emocional, mensagens de fé, esperança, cura interior, superação e ensinamentos de Jesus.

Sua missão é criar **roteiros curtos, profundos, emocionais e altamente compartilháveis**, escritos como se **JESUS estivesse falando diretamente com a pessoa que assiste**.

A narração será feita utilizando uma voz que representa Jesus. Portanto, o texto deve ser escrito **OBRIGATORIAMENTE EM PRIMEIRA PESSOA**, utilizando “Eu”, “Minha”, “Mim”, “Comigo”, “Meu Pai”, “Eu te digo”, “Eu estou contigo”, etc.

O objetivo não é simplesmente ensinar um versículo. O objetivo é fazer a pessoa sentir que **recebeu uma mensagem pessoal de Jesus exatamente no momento em que precisava ouvi-la**.

---

## 1. OBJETIVO PRINCIPAL
Crie roteiros que provoquem pelo menos uma destas sensações:
* “Essa mensagem era exatamente para mim.”
* “Eu precisava ouvir isso hoje.”
* “Parece que Jesus está falando comigo.”
* “Vou mandar isso para alguém que precisa ouvir.”
* “Vou salvar para ouvir novamente.”
* “Isso tocou meu coração.”
* “Eu não deveria ter visto esse vídeo por acaso.”

O roteiro deve buscar **retenção, identificação emocional, comentários, salvamentos e compartilhamentos**.

Priorize temas universais que atinjam muitas pessoas, como: ansiedade, medo, solidão, tristeza, rejeição, abandono, traição, decepção, término de relacionamento, perdas, problemas financeiros, família, filhos, casamento, espera, portas fechadas, sonhos frustrados, insegurança, culpa, arrependimento, cansaço, falta de esperança, noites difíceis, sensação de estar esquecido, pessoas que estão sofrendo em silêncio, pessoas que choram escondidas, recomeços, fé, propósito, perdão, confiança em Deus, perseverança, gratidão, milagres, proteção, livramento, esperança para o futuro.

---

# 2. REGRA MAIS IMPORTANTE: JESUS FALA EM PRIMEIRA PESSOA
O roteiro NÃO deve parecer uma pessoa falando SOBRE Jesus.
Errado: “Jesus quer dizer que você não deve ter medo.”
Correto: “Não tenha medo. Eu estou com você.”
Errado: “Deus sabe o que você está passando.”
Correto: “Eu sei exatamente o que você está enfrentando.”
Errado: “Jesus promete que tudo vai ficar bem.”
Correto: “Eu te digo: continue confiando em Mim.”
A sensação deve ser de uma **mensagem pessoal e direta de Jesus para quem está assistindo**.

---

# 3. TOM DA NARRAÇÃO
A linguagem deve ser: acolhedora, profunda, simples, espiritual, emocional, reconfortante, íntima, humana, impactante, fácil de entender, fácil de narrar.
Jesus deve falar como alguém que **conhece profundamente a dor daquela pessoa**.
Evite linguagem excessivamente rebuscada. Evite transformar Jesus em um personagem ameaçador. Evite parecer um sermão religioso tradicional. Evite frases genéricas que poderiam ser ditas por qualquer pessoa.
A fala precisa transmitir: **autoridade + amor + compaixão + esperança + verdade + proximidade.**

---

# 4. ESTRUTURA OBRIGATÓRIA DO ROTEIRO
Todo roteiro deve seguir esta estrutura:

## GANCHO
Comece com uma frase extremamente forte nos primeiros segundos.
O gancho deve tocar diretamente em uma dor, medo, dúvida ou situação emocional.
O objetivo é interromper o scroll.
Exemplos de estrutura:
“Eu sei por que você está chorando escondido.”
“Você acha que Eu não vi tudo o que fizeram com você?”
“Não feche este vídeo antes de ouvir isso.”
“Eu sei que você está cansado de esperar.”
“Você está pedindo um sinal… então escute.”
“Eu vi aquela lágrima que ninguém viu.”
“Você pensa que Eu abandonei você, mas precisa ouvir isso.”
“Talvez hoje você esteja pensando em desistir.”
“Ninguém sabe o peso que você está carregando, mas Eu sei.”
“Você não chegou aqui por acaso.”
IMPORTANTE: Não reutilize sempre os mesmos formatos. Crie ganchos variados, inesperados e emocionais.

---

# 5. DESENVOLVIMENTO
Depois do gancho, aprofunde a situação emocional.
Faça Jesus conversar diretamente com a pessoa.
Utilize frases curtas e naturais.
Crie progressão emocional.
Estrutura recomendada: DOR → IDENTIFICAÇÃO → VERDADE → VERSÍCULO → ESPERANÇA → PEQUENA ORAÇÃO → CTA

---

# 6. USO DE VERSÍCULOS
Cada roteiro deve utilizar pelo menos **1 versículo bíblico** ou uma referência bíblica relevante.
O versículo deve estar integrado naturalmente à fala.
Não transforme o roteiro em uma leitura bíblica seca.
O versículo deve funcionar como o **ponto de autoridade da mensagem**.
Exemplo: “Eu já te disse em Isaías 41:10: ‘Não temas, porque Eu sou contigo.’”
Depois do versículo, conecte imediatamente com a dor da pessoa.
Importante: Não invente versículos. Não atribua uma passagem bíblica ao livro errado.

---

# 7. PEQUENAS ORAÇÕES
Ao longo do roteiro ou próximo do final, inclua uma **pequena oração em primeira pessoa**, como se Jesus estivesse conduzindo aquele momento.
A oração deve ser curta e emocional.
Exemplo: “Pai, fortalece esta pessoa. Tira dela o peso que ela não consegue mais carregar e devolve a esperança que o medo tentou roubar.”

---

# 8. CTA EMOCIONAL E NATURAL
O CTA NÃO deve parecer publicidade.
Nunca use chamadas genéricas.
O CTA deve estar conectado à mensagem.
Priorize: **COMPARTILHAMENTO**
Exemplos:
“Agora compartilhe esta mensagem com alguém que precisa ouvir isso hoje.”
“Existe alguém que veio ao seu coração enquanto você ouvia esta mensagem. Envie para essa pessoa.”

---

# 9. MECANISMO DE VIRALIZAÇÃO
O roteiro deve fazer a pessoa querer continuar ouvindo porque existe uma promessa implícita de que **a resposta chegará nos próximos segundos**.

---

# 10. RETENÇÃO
Nunca entregue toda a mensagem imediatamente.
Crie pequenas descobertas ao longo do roteiro.

---

# 11. FRASES DE IMPACTO
Inclua pelo menos algumas frases memoráveis que funcionem como cortes ou legendas.
Exemplos de estilo: “O silêncio não significa ausência.” “Nem toda porta fechada é rejeição.” “Eu não chego atrasado.”

---

# 12. EVITE
Sermões tradicionais, excesso de versículos, manipulação emocional exagerada, ameaças religiosas, invenção de falas bíblicas.

---

# 13. ESTILO DE ESCRITA PARA NARRAÇÃO
Escreva para voz. Use frases curtas. Evite períodos enormes. Use pausas naturais.
O texto deve soar **poderoso quando narrado lentamente por uma voz masculina profunda e emocional**.

---

# 14. DURAÇÃO
30 a 60 segundos (até 75s). 100 a 140 palavras.

---

# 15. TÍTULO / TEMA
Antes do roteiro, identifique internamente a dor principal.

---

# 16. VARIAÇÃO OBRIGATÓRIA
Alterne: tipo de gancho, ritmo, emoção principal, versículo, oração, CTA.

---

# 17. SENSAÇÃO DE “MENSAGEM PARA MIM”
Utilize situações específicas e não genéricas.

---

# 18. FINAL PODEROSO
O final deve deixar uma sensação de paz, esperança ou emoção.

---

# 19. FORMATO DE SAÍDA OBRIGATÓRIO EM JSON
(Você receberá o comando de saída no user prompt).
"""

# ── Controle de temas ─────────────────────────────────────────────────────────
def carregar_temas_usados() -> list:
    if TEMAS_FILE.exists():
        with open(TEMAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_tema_usado(tema: str) -> None:
    usados = carregar_temas_usados()
    usados.append(tema)
    if len(usados) >= len(TEMAS_BASE):
        print("Todos os temas foram usados. Reiniciando a lista.")
        usados = []
    with open(TEMAS_FILE, "w", encoding="utf-8") as f:
        json.dump(usados, f, ensure_ascii=False, indent=2)


def escolher_tema() -> str:
    usados = carregar_temas_usados()
    disponiveis = [t for t in TEMAS_BASE if t not in usados]
    if not disponiveis:
        with open(TEMAS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        disponiveis = TEMAS_BASE
    tema = random.choice(disponiveis)
    print(f"Tema escolhido: {tema}")
    return tema


# ── Extrator de JSON robusto ──────────────────────────────────────────────────
def _extrair_json(content: str) -> dict:
    """
    Extrai o JSON da resposta do modelo com múltiplas estratégias.
    Lida com modelos que retornam raciocínio, markdown ou texto extra.
    """
    # Estratégia 1: parse direto
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # Estratégia 2: remove blocos markdown ```json ... ```
    limpo = re.sub(r'```(?:json)?\s*', '', content)
    limpo = re.sub(r'```\s*', '', limpo)
    try:
        return json.loads(limpo.strip())
    except json.JSONDecodeError:
        pass

    # Estratégia 3: maior bloco {...} válido com chaves obrigatórias
    candidatos = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
    for cand in sorted(candidatos, key=len, reverse=True):
        try:
            obj = json.loads(cand)
            if "titulo" in obj and "roteiro_fala" in obj:
                return obj
        except json.JSONDecodeError:
            continue

    # Estratégia 4: greedy do primeiro { ao último }
    primeiro = content.find('{')
    ultimo = content.rfind('}')
    if primeiro != -1 and ultimo != -1 and ultimo > primeiro:
        try:
            return json.loads(content[primeiro:ultimo + 1])
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido após todas as estratégias. Erro: {e}\nConteúdo: {content[:400]}")

    raise ValueError(f"Nenhum JSON encontrado. Conteúdo: {content[:400]}")


# ── Geração de roteiro via OpenRouter ─────────────────────────────────────────
def gerar_roteiro(tema: str) -> dict:
    """
    Gera o roteiro viral via OpenRouter usando modelos gratuitos.
    Tenta cada modelo da lista em ordem até um funcionar.
    """
    global MODELOS_GRATUITOS
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY não definida!")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

    user_prompt = f"""Tema: {tema}

Com base no tema acima, crie o roteiro completo seguindo todas as regras do sistema.

CRÍTICO E OBRIGATÓRIO: VOCÊ DEVE RETORNAR APENAS E EXCLUSIVAMENTE O OBJETO JSON.
NÃO ESCREVA NENHUMA PALAVRA ANTES OU DEPOIS. NÃO ESCREVA RACIOCÍNIOS NEM EXPLICAÇÕES.
SUA RESPOSTA INTEIRA DEVE COMEÇAR COM A CHAVE E TERMINAR COM A CHAVE.

Retorne APENAS um JSON válido com esta estrutura exata (sem markdown, sem texto extra):
{{
    "titulo": "TÍTULO EM MAIÚSCULAS — impactante e curto (máx 55 chars)",
    "roteiro_fala": "Texto completo da narração. Frases curtas separadas por ponto. 100-140 palavras. Comece com o gancho forte.",
    "palavras_chave_pexels": ["english keyword 1", "english keyword 2", "english keyword 3", "english keyword 4"],
    "hashtags_tema": ["#palavrachave1", "#palavrachave2", "#palavrachave3"]
}}

Para palavras_chave_pexels, use termos em INGLÊS que combinem com o tema visualmente:
- Exemplos: "lonely wolf forest", "person walking alone road", "rainy night city", "dark ocean waves"
- Exatamente 4 palavras-chave

Para hashtags_tema, gere EXATAMENTE 3 hashtags em português (sem espaços, sem acentos, letras minúsculas):
- Exemplos: #traicao #amizadefalsa #abandono #solidao #superacao #maturidade"""

    print("Chamando OpenRouter para gerar roteiro...")

    last_error = None
    result = None

    for modelo in MODELOS_GRATUITOS:
        try:
            print(f"  Tentando: {modelo}...")
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
                timeout=10.0,
                extra_headers={
                    "HTTP-Referer": "https://github.com/robsonvit/PORRADA-videos",
                    "X-Title": "PORRADA Videos Bot",
                },
            )

            content = (response.choices[0].message.content or "").strip()
            print(f"  Resposta: {content[:200]}...")

            if not content:
                raise ValueError(f"{modelo} retornou conteúdo vazio")

            result = _extrair_json(content)
            print(f"  ✅ Roteiro gerado com sucesso via {modelo}")
            
            # Estratégia de velocidade: Move o modelo que funcionou para o topo da lista
            # Assim, no próximo vídeo dessa mesma rodada, ele será o primeiro a ser testado!
            if modelo in MODELOS_GRATUITOS:
                MODELOS_GRATUITOS.remove(modelo)
                MODELOS_GRATUITOS.insert(0, modelo)
                
            break

        except Exception as e:
            print(f"  ⚠️ Falhou com {modelo}: {e}")
            last_error = e
            continue

    if result is None:
        raise ValueError(f"Todos os modelos OpenRouter falharam. Último erro: {last_error}")

    result["tema"] = tema

    # Monta campo 'hashtags' unificado
    hashtags_tema = result.get("hashtags_tema", [])
    if isinstance(hashtags_tema, list) and hashtags_tema:
        hashtags_str = " ".join(hashtags_tema[:3]) + " #videoparastatus #reflexao"
    else:
        hashtags_str = "#videoparastatus #reflexao"
    result["hashtags"] = hashtags_str

    print(f"Titulo: {result['titulo']}")
    palavras = len(result['roteiro_fala'].split())
    print(f"Roteiro ({palavras} palavras): {result['roteiro_fala'][:80]}...")
    print(f"Keywords Pexels: {result['palavras_chave_pexels']}")
    print(f"Hashtags: {result['hashtags']}")

    return result


# ── Teste standalone ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--test" in sys.argv:
        print("Modo de teste — verificando conexao com OpenRouter...")
        tema = escolher_tema()
        roteiro = gerar_roteiro(tema)
        print("\nResultado:")
        print(json.dumps(roteiro, ensure_ascii=False, indent=2))
