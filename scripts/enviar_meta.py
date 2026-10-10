import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Configurações do Meta (Enfermagem Curiosa)
USER_ACCESS_TOKEN = "EAAdxhP3IqDABSirjI6y40XZCED3kVz6GzNAlxWzKGq5wzA66ALKAE6qr2Y1HoGN5ccLo8ZAu9Cv0r3rGakRD0W9KtCcH9O4JQYtolZCZCpx3tyhwZBqtRyvr0obZAZBVpZCiWcbszZCZBLnyY4p2mBpQ8YQJgQAfu1RqK2t5ZB9ZBOjPOOUqAsHPS4m0ZC6OZB77c4"
PAGE_ACCESS_TOKEN = "EAAdxhP3IqDABSlpygZAG2LJaLKjmGUbgyLlJeAAbFZBUNirBbMqoV9MVNFpKeHxsfBeZB0iNEji2sCOuPLHntrZCA4yp4raQY5xkuw92i0rw76CTsZAStZCwpTeoUVn6dawnMvNCrlgWunTURSiByG79CNwhyZAxtxOs0PJ9Qf0eqbNiH2sBK35a49sszOEpJ6xZBgsIDAsZD"
FB_PAGE_ID = "101746485343968"
IG_ACCOUNT_ID = "17841446226605429"
GRAPH_API_VERSION = "v18.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

def _get_public_url(file_path):
    """
    Faz upload para servidor temporário para obter uma URL pública (necessário para IG Reels).
    """
    print(f"   Tentando upload temporário em tmpfiles.org para o Instagram...")
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': f}, timeout=120)
        d = r.json()
        if d.get('status') == 'success':
            public_url = d['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
            print(f"   ✅ tmpfiles.org: OK -> {public_url}")
            return public_url
    except Exception as e:
        print(f"   ⚠️  tmpfiles.org erro: {e}")

    print(f"   Tentando file.io...")
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://file.io', files={'file': f}, data={'expires': '1d'}, timeout=120)
        d = r.json()
        if d.get('success'):
            public_url = d['link']
            print(f"   ✅ file.io: OK -> {public_url}")
            return public_url
    except Exception as e:
        print(f"   ⚠️  file.io erro: {e}")
        
    return None

def _check_status(container_id, platform="ig"):
    """Verifica se o video terminou de ser processado pela Meta"""
    if platform == "ig":
        url = f"{BASE_URL}/{container_id}?fields=status_code&access_token={USER_ACCESS_TOKEN}"
    else:
        url = f"{BASE_URL}/{container_id}?fields=status&access_token={PAGE_ACCESS_TOKEN}"
        
    for _ in range(12):  # Espera até 2 minutos (12 * 10s)
        response = requests.get(url).json()
        if platform == "ig":
            status = response.get('status_code')
            if status == 'FINISHED':
                return True
            elif status == 'ERROR':
                print(f"Erro no processamento do IG: {response}")
                return False
        else:
            v_status = response.get('status', {})
            if isinstance(v_status, dict):
                st = v_status.get('video_status')
                if st == 'ready': return True
                if st == 'error': 
                    print(f"Erro no processamento do Facebook: {response}")
                    return False
            elif v_status == 'ready':
                return True
            print(f"Aguardando processamento Facebook... ({v_status})")
            
        time.sleep(10)
    return False

def enviar_facebook_reels(video_path: str, caption: str):
    print(f"Iniciando envio para Facebook Page Reels: {video_path}")
    file_size = os.path.getsize(video_path)
    
    # 1. Initialize session
    init_url = f"{BASE_URL}/{FB_PAGE_ID}/video_reels"
    init_payload = {
        'upload_phase': 'start',
        'access_token': PAGE_ACCESS_TOKEN,
        'file_size': file_size
    }
    init_res = requests.post(init_url, data=init_payload).json()
    
    if 'video_id' not in init_res:
        print(f"❌ Erro ao iniciar sessão FB: {init_res}")
        return False
        
    video_id = init_res['video_id']
    upload_url = init_res['upload_url']
    
    # 2. Enviar arquivo
    headers = {
        'Authorization': f'OAuth {PAGE_ACCESS_TOKEN}',
        'offset': '0',
        'file_size': str(file_size)
    }
    
    with open(video_path, 'rb') as f:
        video_data = f.read()
        
    requests.post(upload_url, headers=headers, data=video_data)
    
    # 3. Check status
    print("Arquivo enviado (FB). Aguardando processamento da Meta...")
    if not _check_status(video_id, "fb"):
         print("Aviso: O vídeo ainda não está 'ready' no Facebook, mas tentaremos publicar assim mesmo.")
         
    # 4. Concluir e Publicar
    finish_url = f"{BASE_URL}/{FB_PAGE_ID}/video_reels"
    finish_payload = {
        'access_token': PAGE_ACCESS_TOKEN,
        'video_id': video_id,
        'upload_phase': 'finish',
        'video_state': 'PUBLISHED',
        'description': caption,
        'share_to_feed': True
    }
        
    finish_res = requests.post(finish_url, data=finish_payload).json()
    
    if finish_res.get('success'):
        print(f"✅ Reel publicado com sucesso na Página do FB!")
        return True
    else:
        print(f"❌ Erro ao publicar no FB (Step 4): {finish_res}")
        return False

def enviar_instagram_reels(video_path: str, caption: str):
    print(f"Iniciando envio para Instagram Reels: {video_path}")
    
    video_url = _get_public_url(video_path)
    if not video_url:
        print(f"❌ Todos os serviços de upload temporário falharam")
        return False
        
    # Criar container COM video_url e caption
    print(f"Criando container no Instagram...")
    url_media = f"{BASE_URL}/{IG_ACCOUNT_ID}/media"
    payload = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption,
        'access_token': USER_ACCESS_TOKEN
    }
    
    res = requests.post(url_media, params=payload).json()
    
    if 'id' not in res:
        print(f"❌ Erro ao criar container: {res}")
        return False
    
    container_id = res['id']
    print(f"✅ Container criado: {container_id}")
    
    print(f"Aguardando processamento do Instagram...")
    if not _check_status(container_id, "ig"):
        print(f"❌ Falha no processamento")
        return False
    
    # Pequeno aguardo antes de publicar
    time.sleep(5)
    
    pub_res = requests.post(
        f"{BASE_URL}/{IG_ACCOUNT_ID}/media_publish",
        params={'creation_id': container_id, 'access_token': USER_ACCESS_TOKEN}
    ).json()
    
    if 'id' not in pub_res:
        print(f"❌ Erro ao publicar IG: {pub_res}")
        return False
    
    media_id = pub_res['id']
    print(f"✅ REEL PUBLICADO NO INSTAGRAM! Media ID: {media_id}")
    return True

def enviar_meta_completo(video_path: str, caption: str):
    """Faz o envio para o Facebook"""
    print("\n🌐 Iniciando postagem no Meta (Facebook) para 'Enfermagem Curiosa'...")
    # Add @seguidores as requested
    caption_com_todos = f"@seguidores\n\n{caption}"
    
    # Facebook
    enviar_facebook_reels(video_path, caption_com_todos)
    
    print("✅ Processo Meta finalizado.")
