"""
Script simples para obter tokens OAuth do SmugMug via console
Baseado no exemplo oficial do SmugMug, mas simplificado

Requisitos:
    pip install requests requests-oauthlib

Uso:
    python simple_oauth.py <API_KEY> <API_SECRET>
"""

import sys
import webbrowser
from http import HTTPStatus

from requests_oauthlib import OAuth1Session

# URLs OAuth do SmugMug
REQUEST_TOKEN_URL = (
    'https://secure.smugmug.com/services/oauth/1.0a/getRequestToken'
)
ACCESS_TOKEN_URL = (
    'https://secure.smugmug.com/services/oauth/1.0a/getAccessToken'
)
AUTHORIZE_URL = 'https://secure.smugmug.com/services/oauth/1.0a/authorize'
API_BASE_URL = 'https://api.smugmug.com/api/v2'
CODE_LENGTH = 6


def get_request_token(api_key, api_secret):
    print('\n1️⃣ Obtendo request token...')
    oauth = OAuth1Session(
        api_key, client_secret=api_secret, callback_uri='oob'
    )
    try:
        response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
        print(f'✅ Request token: {response["oauth_token"][:20]}...')
        return response['oauth_token'], response['oauth_token_secret']
    except Exception as e:
        print(f'❌ Erro ao obter request token: {e}')
        return None, None


def authorize_user(request_token):
    print('\n2️⃣ Redirecionando para autorização...')
    auth_url = (
        f'{AUTHORIZE_URL}?oauth_token={request_token}'
        f'&Access=Full&Permissions=Modify'
    )
    print('\n🌐 Abra esta URL no navegador:')
    print(f'{auth_url}')
    print('\n📱 Ou pressione ENTER para tentar abrir automaticamente...')
    input_resp = input()
    if not input_resp.strip():
        try:
            webbrowser.open(auth_url)
            print('✅ Navegador aberto!')
        except Exception as e:
            print(f'⚠️  Não foi possível abrir automaticamente: {e}')
    print('\n📋 Após autorizar no SmugMug:')
    print(f'   - Você verá uma página com um código de {CODE_LENGTH} dígitos')
    print('   - Digite esse código abaixo')
    while True:
        verifier = input(f'\n🔢 Código de {CODE_LENGTH} dígitos: ').strip()
        if len(verifier) == CODE_LENGTH and verifier.isdigit():
            return verifier
        print(
            f'❌ Código deve ter exatamente {CODE_LENGTH} dígitos numéricos!'
        )


def get_access_token(
    api_key, api_secret, request_token, request_token_secret, verifier
):
    print('\n3️⃣ Obtendo access token...')
    oauth = OAuth1Session(
        api_key,
        client_secret=api_secret,
        resource_owner_key=request_token,
        resource_owner_secret=request_token_secret,
        verifier=verifier,
    )
    try:
        response = oauth.fetch_access_token(ACCESS_TOKEN_URL)
        print(f'✅ Access token: {response["oauth_token"][:20]}...')
        return response['oauth_token'], response['oauth_token_secret']
    except Exception as e:
        print(f'❌ Erro ao obter access token: {e}')
        return None, None


def test_tokens(api_key, api_secret, access_token, access_token_secret):
    print('\n4️⃣ Testando tokens...')
    test_oauth = OAuth1Session(
        api_key,
        client_secret=api_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )
    try:
        response = test_oauth.get(
            f'{API_BASE_URL}!authuser', headers={'Accept': 'application/json'}
        )
        if response.status_code == HTTPStatus.OK:
            user_data = response.json()
            user_name = (
                user_data.get('Response', {})
                .get('User', {})
                .get('Name', 'Usuário')
            )
            print(f'✅ Conectado como: {user_name}')
            return True
        else:
            print(f'❌ Teste falhou. Status: {response.status_code}')
            print(f'❌ Resposta: {response.text}')
            return False
    except Exception as e:
        print(f'❌ Erro no teste: {e}')
        return False


def get_oauth_tokens(api_key: str, api_secret: str):
    """
    Obter tokens OAuth do SmugMug via console

    Args:
        api_key: Sua API Key do SmugMug
        api_secret: Seu API Secret do SmugMug

    Returns:
        tuple: (access_token, access_token_secret) ou (None, None) se falhar
    """
    print('🔄 Iniciando processo OAuth...')
    request_token, request_token_secret = get_request_token(
        api_key, api_secret
    )
    if not request_token:
        return None, None
    verifier = authorize_user(request_token)
    access_token, access_token_secret = get_access_token(
        api_key, api_secret, request_token, request_token_secret, verifier
    )
    if not access_token:
        return None, None
    if test_tokens(api_key, api_secret, access_token, access_token_secret):
        return access_token, access_token_secret
    return None, None


def main():
    """Função principal"""

    print('🚀 Gerador de Tokens OAuth - SmugMug')
    print('=' * 40)

    # Verificar argumentos
    ARGUMENT_COUNT = 3
    if len(sys.argv) != ARGUMENT_COUNT:
        print('❌ Uso incorreto!')
        print(f'   {sys.argv[0]} <API_KEY> <API_SECRET>')
        print('\n📋 Exemplo:')
        print(f'   {sys.argv[0]} abc123key def456secret')
        print('\n🔑 Obtenha suas credenciais em:')
        print('   https://api.smugmug.com/api/v2/doc')
        sys.exit(1)

    api_key = sys.argv[1]
    api_secret = sys.argv[2]

    print(f'🔑 API Key: {api_key[:10]}...')
    print(f'🔐 API Secret: {api_secret[:10]}...')

    # Obter tokens
    access_token, access_token_secret = get_oauth_tokens(api_key, api_secret)

    if access_token and access_token_secret:
        print('\n' + '=' * 50)
        print('🎉 SUCESSO! Tokens OAuth obtidos:')
        print('=' * 50)
        print()
        print('# Adicione ao seu .env:')
        print(f'SMUGMUG_API_KEY={api_key}')
        print(f'SMUGMUG_API_SECRET={api_secret}')
        print(f'SMUGMUG_ACCESS_TOKEN={access_token}')
        print(f'SMUGMUG_ACCESS_TOKEN_SECRET={access_token_secret}')
        print()
        print('=' * 50)
        print('✅ Agora você pode usar a API v2 do SmugMug!')

        # Salvar em arquivo
        try:
            with open('smugmug_tokens.txt', 'w', encoding='utf-8') as f:
                f.write(f'SMUGMUG_API_KEY={api_key}\n')
                f.write(f'SMUGMUG_API_SECRET={api_secret}\n')
                f.write(f'SMUGMUG_ACCESS_TOKEN={access_token}\n')
                f.write(f'SMUGMUG_ACCESS_TOKEN_SECRET={access_token_secret}\n')
            print('💾 Tokens salvos em: smugmug_tokens.txt')
        except Exception as e:
            print(f'⚠️  Não foi possível salvar arquivo: {e}')

    else:
        print('\n❌ Falha ao obter tokens!')
        print('🔄 Tente executar novamente')
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n👋 Cancelado pelo usuário')
        sys.exit(0)
    except Exception as e:
        print(f'\n❌ Erro: {e}')
        sys.exit(1)
