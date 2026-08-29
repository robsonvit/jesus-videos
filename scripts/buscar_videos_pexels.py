"""
buscar_videos_pexels.py — Projeto JESUS
Busca e baixa vídeos de natureza do Pexels via API.

Regras:
  - Palavras-chave FIXAS de natureza: florestas, cachoeiras, animais imponentes
  - Controla IDs já usados em pexels_usados.json (persiste entre rodadas no GitHub)
  - Nunca repete o mesmo vídeo enquanto houver novos disponíveis
  - Ao esgotar todos, reinicia e embaralha em ORDEM DIFERENTE
  - A câmera lenta e o hflip são aplicados em montar_video.py
"""

import json
import os
import random
import sys
from pathlib import Path
from typing import Optional

import requests

# ── Configurações ─────────────────────────────────────────────────────────────
PEXELS_API_BASE = "https://api.pexels.com/videos"
PROJETO_ROOT    = Path(__file__).parent.parent

# Arquivo que persiste entre rodadas (commitado via GitHub Actions)
PEXELS_USADOS_FILE = PROJETO_ROOT / "pexels_usados.json"

# ── Keywords FIXAS de natureza para o canal JESUS ────────────────────────────
# Grupos separados para busca rotativa e resultados variados
NATURE_KEYWORDS = [
    # Florestas e matas
    "forest sunlight rays",
    "misty forest morning",
    "ancient forest trees",
    "green jungle waterfall",
    "forest path fog",
    "tropical rainforest",
    "bamboo forest wind",
    "pine forest sunrise",
    # Cachoeiras e água
    "waterfall nature",
    "river waterfall slow",
    "epic waterfall landscape",
    "stream flowing water rocks",
    "mountain waterfall mist",
    "waterfall birds nature",
    # Animais imponentes
    "eagle flying majestic",
    "lion wild nature",
    "wolf nature wild",
    "whale ocean majestic",
    "deer forest peaceful",
    "bear river nature",
    "hawk soaring sky",
    "horse galloping nature",
    # Paisagens grandiosas
    "mountain sunrise clouds",
    "ocean waves powerful",
    "storm clouds lightning nature",
    "meadow flowers wind",
    "lake reflection mountains",
    "desert dunes sunset",
    "volcano eruption nature",
    "aurora borealis sky",
]


# ── Controle de IDs usados ────────────────────────────────────────────────────
def _carregar_usados() -> dict:
    """
    Carrega o JSON de controle de vídeos usados.
    Formato: { "usados": [id1, id2, ...], "ordem_base": 0 }
    """
    if PEXELS_USADOS_FILE.exists():
        try:
            with open(PEXELS_USADOS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Garante estrutura compatível
                if isinstance(data, list):
                    # Migração de formato antigo (lista simples)
                    return {"usados": data, "ordem_base": 0}
                return data
        except Exception:
            pass
    return {"usados": [], "ordem_base": 0}


def _salvar_usados(data: dict) -> None:
    """Salva o arquivo de controle (será commitado pelo GitHub Actions)."""
    with open(PEXELS_USADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _resetar_usados(ordem_base_atual: int) -> dict:
    """
    Reinicia a lista de usados quando todos os vídeos foram consumidos.
    Incrementa ordem_base para garantir embaralhamento diferente na próxima volta.
    """
    nova_ordem = ordem_base_atual + 1
    print(f"  ♻️  Todos os vídeos Pexels já foram usados! Reiniciando (volta #{nova_ordem})...")
    data = {"usados": [], "ordem_base": nova_ordem}
    _salvar_usados(data)
    return data


# ── Funções auxiliares Pexels ─────────────────────────────────────────────────
def _get_headers() -> dict:
    api_key = os.environ.get("PEXELS_API_KEY", "")
    if not api_key:
        raise ValueError("❌ PEXELS_API_KEY não configurada!")
    return {"Authorization": api_key}


def _escolher_melhor_arquivo(video_files: list) -> Optional[dict]:
    """
    Escolhe o melhor arquivo de vídeo (HD landscape prioritário).
    Prefere resolução HD, width > height (paisagem/horizontal).
    """
    landscape = [
        f for f in video_files
        if f.get("width", 0) > f.get("height", 0)
        and f.get("file_type", "") == "video/mp4"
        and f.get("width", 0) >= 1280
    ]
    if not landscape:
        landscape = [
            f for f in video_files
            if f.get("width", 0) > f.get("height", 0)
            and f.get("file_type", "") == "video/mp4"
        ]
    if not landscape:
        return None

    qualidade_ordem = {"hd": 0, "sd": 1, "uhd": 2}
    landscape.sort(key=lambda x: qualidade_ordem.get(x.get("quality", ""), 99))
    return landscape[0]


def _download_video(url: str, filepath: str) -> bool:
    """Baixa um vídeo do URL para o filepath indicado."""
    try:
        with requests.get(url, stream=True, timeout=90) as r:
            r.raise_for_status()
            baixado = 0
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    baixado += len(chunk)
            size_mb = baixado / (1024 * 1024)
            print(f"   📥 {Path(filepath).name} — {size_mb:.1f} MB")
            return True
    except Exception as e:
        print(f"   ❌ Erro ao baixar: {e}")
        if Path(filepath).exists():
            Path(filepath).unlink()
        return False


def _buscar_por_keyword(keyword: str, per_page: int = 20) -> list:
    """Busca vídeos no Pexels por palavra-chave. Retorna lista de vídeos."""
    params = {
        "query": keyword,
        "per_page": per_page,
        "orientation": "landscape",
        "size": "medium",
    }
    try:
        response = requests.get(
            f"{PEXELS_API_BASE}/search",
            headers=_get_headers(),
            params=params,
            timeout=30,
        )
        if response.status_code == 200:
            videos = response.json().get("videos", [])
            print(f"   🔍 '{keyword}': {len(videos)} vídeos encontrados")
            return videos
        else:
            print(f"   ⚠️ Pexels status {response.status_code} para '{keyword}'")
            return []
    except Exception as e:
        print(f"   ❌ Erro na busca '{keyword}': {e}")
        return []


# ── Função principal ──────────────────────────────────────────────────────────
def buscar_videos(keywords: list, duracao_audio: float, output_dir: str) -> list:
    """
    Busca e baixa vídeos de natureza do Pexels, evitando repetição entre rodadas.

    NOTA: O parâmetro `keywords` vindo do roteiro é IGNORADO neste projeto.
    Usamos exclusivamente as NATURE_KEYWORDS fixas para garantir estética
    consistente e majestosa no canal JESUS.

    Regras:
    - Nunca repete IDs já usados (rastreado em pexels_usados.json)
    - Ao esgotar todos os vídeos disponíveis, reinicia com ordem diferente
    - Keywords rotacionadas com seed baseada na ordem_base (embaralhamento único)

    Args:
        keywords: IGNORADO — mantido só para compatibilidade com pipeline.py
        duracao_audio: Duração da narração em segundos
        output_dir: Pasta onde salvar os vídeos baixados

    Returns:
        Lista de caminhos absolutos dos vídeos baixados
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Quantos clipes precisamos (considerando câmera lenta: lê menos segundos)
    # A câmera lenta 0.5x dobra a duração visual — baixamos menos material
    clips_necessarios = max(4, int(duracao_audio / 5) + 3)
    print(f"\n🌿 Buscando {clips_necessarios} clipes de natureza para {duracao_audio:.1f}s de áudio...")
    print(f"   (câmera lenta 0.5x ativa — clips renderizarão o dobro de tempo)")

    # ── Carrega controle de IDs usados ───────────────────────────────────────
    controle = _carregar_usados()
    ids_usados_historico = set(controle["usados"])
    ordem_base = controle["ordem_base"]
    print(f"   📋 IDs já usados em rodadas anteriores: {len(ids_usados_historico)}")

    # ── Embaralha keywords com seed baseada na ordem_base ────────────────────
    # Seed diferente a cada "volta" garante ordem de busca sempre diferente
    keywords_rotativa = NATURE_KEYWORDS[:]
    rng = random.Random(ordem_base * 7919 + len(ids_usados_historico))
    rng.shuffle(keywords_rotativa)

    ids_baixados_agora = set()
    caminhos_baixados  = []
    reiniciou          = False

    def _tentar_baixar(keyword: str) -> bool:
        """Tenta baixar clips de uma keyword. Retorna True se conseguiu algum."""
        nonlocal reiniciou
        if len(caminhos_baixados) >= clips_necessarios:
            return True

        videos = _buscar_por_keyword(keyword, per_page=25)
        # Embaralha com seed que muda a cada rodada para variar a seleção
        rng.shuffle(videos)

        encontrou = False
        for video in videos:
            if len(caminhos_baixados) >= clips_necessarios:
                break

            video_id = video.get("id")
            if not video_id:
                continue

            # Pula se já foi usado em rodadas anteriores
            if video_id in ids_usados_historico and not reiniciou:
                continue

            # Pula duplicatas na mesma rodada
            if video_id in ids_baixados_agora:
                continue

            # Filtra vídeos muito curtos
            if video.get("duration", 0) < 4:
                continue

            arquivo_video = _escolher_melhor_arquivo(video.get("video_files", []))
            if not arquivo_video:
                continue

            url = arquivo_video.get("link", "")
            if not url:
                continue

            filename = output_path / f"clip_{len(caminhos_baixados)+1:02d}_id{video_id}.mp4"
            if _download_video(url, str(filename)):
                ids_baixados_agora.add(video_id)
                caminhos_baixados.append(str(filename))
                encontrou = True

        return encontrou

    # ── Primeira passagem: apenas vídeos nunca usados ─────────────────────────
    for keyword in keywords_rotativa:
        if len(caminhos_baixados) >= clips_necessarios:
            break
        _tentar_baixar(keyword)

    # ── Se não conseguiu clips suficientes: reinicia histórico e tenta de novo ─
    if len(caminhos_baixados) < clips_necessarios:
        print(f"\n  ⚠️  Apenas {len(caminhos_baixados)} clips novos encontrados (precisamos de {clips_necessarios})")
        controle = _resetar_usados(ordem_base)
        ids_usados_historico = set()
        ordem_base = controle["ordem_base"]
        reiniciou = True

        # Nova ordem de busca após reset
        rng2 = random.Random(ordem_base * 7919)
        keywords_reset = NATURE_KEYWORDS[:]
        rng2.shuffle(keywords_reset)

        for keyword in keywords_reset:
            if len(caminhos_baixados) >= clips_necessarios:
                break
            _tentar_baixar(keyword)

    # ── Salva IDs usados nesta rodada no histórico ────────────────────────────
    controle_atualizado = _carregar_usados()  # Relê para não sobrescrever reset
    todos_usados = list(set(controle_atualizado["usados"]) | ids_baixados_agora)
    controle_atualizado["usados"] = todos_usados
    _salvar_usados(controle_atualizado)

    print(f"\n✅ {len(caminhos_baixados)} clipes de natureza baixados")
    print(f"   📝 Total de IDs no histórico agora: {len(todos_usados)}")
    return caminhos_baixados


# ── Execução standalone para teste ───────────────────────────────────────────
if __name__ == "__main__":
    if "--test" in sys.argv:
        print("🧪 Testando busca de vídeos de natureza (projeto JESUS)...")
        clips = buscar_videos(
            keywords=[],  # ignorado
            duracao_audio=40.0,
            output_dir="test_pexels_jesus/",
        )
        print(f"\n📁 Clipes baixados: {clips}")
