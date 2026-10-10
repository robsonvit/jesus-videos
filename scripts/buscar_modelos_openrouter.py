"""
buscar_modelos_openrouter.py
Busca dinamicamente os modelos gratuitos disponíveis na API do OpenRouter.
Usa a API oficial (/api/v1/models) que é rápida, leve e não precisa de browser.
Faz cache local por 6 horas para evitar chamadas excessivas.
"""

import json
import os
import time
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

# Configuracoes
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
CACHE_FILE = Path(__file__).parent.parent / "modelos_cache.json"
CACHE_TTL_SEGUNDOS = 6 * 3600  # 6 horas

# Modelos CONHECIDOS como problematicos (so disponiveis em agentic harnesses)
MODELOS_BLOQUEADOS = {
    "thinkingmachines/inkling-small:free",
    "thinkingmachines/inkling:free",
}

# Modelos fallback caso a API falhe completamente
MODELOS_FALLBACK = [
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
]


def _carregar_cache():
    """Carrega o cache de modelos se ainda for valido."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        timestamp = data.get("timestamp", 0)
        if time.time() - timestamp < CACHE_TTL_SEGUNDOS:
            modelos = data.get("modelos", [])
            if modelos:
                print(f"  Cache valido com {len(modelos)} modelos gratuitos.")
                return modelos
    except Exception:
        pass
    return None


def _salvar_cache(modelos):
    """Salva a lista de modelos no cache local."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "modelos": modelos}, f, indent=2)
    except Exception as e:
        print(f"  Nao foi possivel salvar cache: {e}")


def _fetch_com_requests(url, headers):
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def _fetch_com_urllib(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def buscar_modelos_gratuitos(openrouter_api_key=""):
    """
    Busca os modelos gratuitos disponiveis na API do OpenRouter.
    Retorna lista de IDs de modelos gratuitos.
    """
    # 1. Tentar cache
    cache = _carregar_cache()
    if cache:
        return cache

    print("  Buscando modelos gratuitos na API do OpenRouter...")

    headers = {
        "Accept": "application/json",
        "User-Agent": "jesus-videos-bot/1.0",
    }
    if openrouter_api_key:
        headers["Authorization"] = f"Bearer {openrouter_api_key}"

    try:
        if HAS_REQUESTS:
            data = _fetch_com_requests(OPENROUTER_API_URL, headers)
        elif HAS_URLLIB:
            data = _fetch_com_urllib(OPENROUTER_API_URL, headers)
        else:
            raise RuntimeError("Nenhuma biblioteca HTTP disponivel.")

        todos_modelos = data.get("data", [])
        print(f"  Total de modelos na API: {len(todos_modelos)}")

        modelos_free = []
        for m in todos_modelos:
            mid = m.get("id", "")
            if not mid.endswith(":free"):
                continue
            if mid in MODELOS_BLOQUEADOS:
                continue

            arch = m.get("architecture", {})
            input_mod = arch.get("input_modalities") or arch.get("modality", "")
            if isinstance(input_mod, list):
                if "text" not in input_mod:
                    continue

            modelos_free.append({
                "id": mid,
                "context": m.get("context_length", 0),
                "name": m.get("name", mid),
            })

        modelos_free.sort(key=lambda x: x["context"], reverse=True)
        lista_ids = [m["id"] for m in modelos_free]

        if not lista_ids:
            raise ValueError("Nenhum modelo gratuito encontrado na resposta da API.")

        print(f"  {len(lista_ids)} modelos gratuitos encontrados:")
        for m in modelos_free[:10]:
            print(f"     - {m['id']} (ctx: {m['context']:,})")
        if len(modelos_free) > 10:
            print(f"     ... e mais {len(modelos_free) - 10} modelos.")

        _salvar_cache(lista_ids)
        return lista_ids

    except Exception as e:
        print(f"  Falha ao buscar modelos da API: {e}")
        print(f"  Usando lista de fallback com {len(MODELOS_FALLBACK)} modelos.")
        return MODELOS_FALLBACK.copy()


def invalidar_cache():
    """Remove o cache para forcar nova busca na proxima execucao."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        print("  Cache de modelos invalidado.")


if __name__ == "__main__":
    import sys
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    if "--invalidar" in sys.argv:
        invalidar_cache()

    modelos = buscar_modelos_gratuitos(api_key)
    print(f"\nLista final ({len(modelos)} modelos):")
    for i, m in enumerate(modelos, 1):
        print(f"  {i:2}. {m}")
