import asyncio
import logging
import re
from http import HTTPStatus
from typing import Any, Dict, List, Optional

import requests
from requests_oauthlib import OAuth1

from .config import settings
from .models import AlbumResponse, ImageSize, Photo, PhotoURL

logger = logging.getLogger(__name__)


class SmugMugService:
    def __init__(self):
        if not all([
            settings.SMUGMUG_API_KEY,
            settings.SMUGMUG_API_SECRET,
            settings.SMUGMUG_ACCESS_TOKEN,
            settings.SMUGMUG_ACCESS_TOKEN_SECRET,
        ]):
            raise ValueError('Credenciais OAuth não configuradas')

        self.oauth = OAuth1(
            client_key=settings.SMUGMUG_API_KEY,
            client_secret=settings.SMUGMUG_API_SECRET,
            resource_owner_key=settings.SMUGMUG_ACCESS_TOKEN,
            resource_owner_secret=settings.SMUGMUG_ACCESS_TOKEN_SECRET,
        )

        self.session = requests.Session()
        self.session.auth = self.oauth
        self.session.headers.update({
            'User-Agent': settings.SMUGMUG_USER_AGENT,
            'Accept': 'application/json',
        })

    async def _make_request(
        self, url: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Fazer requisição HTTP assíncrona"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.session.get(url, params=params)
        )

        if response.status_code == HTTPStatus.NOT_FOUND:
            raise ValueError('Álbum não encontrado')
        elif response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise ValueError('Rate limit excedido')
        elif response.status_code >= HTTPStatus.BAD_REQUEST:
            raise ValueError(f'Erro HTTP {response.status_code}')

        return response.json()

    @staticmethod
    def _extract_album_key(url: str) -> Optional[str]:
        """Extrair album key da URL"""
        patterns = [
            r'/n-([A-Za-z0-9]+)',
            r'/album/([A-Za-z0-9]+)',
            r'albumkey=([A-Za-z0-9]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    async def _get_album_key(self, url: str) -> str:
        """Obter album key via API ou URL"""
        # Validar URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        # Tentar extrair da URL primeiro
        album_key = self._extract_album_key(url)
        if album_key:
            return album_key

        # Usar API weburilookup
        params = {'WebUri': url, '_accept': 'application/json'}
        data = await self._make_request(
            settings.SMUGMUG_WEB_URI_LOOKUP, params
        )

        if 'Response' in data:
            response = data['Response']
            if response.get('Locator') == 'Album' and 'Album' in response:
                return response['Album']['AlbumKey']

        raise ValueError('Não foi possível encontrar álbum na URL')

    @staticmethod
    def _extract_photo_urls(image_data: Dict[str, Any]) -> List[PhotoURL]:
        """Extrair URLs de diferentes tamanhos"""
        urls = []

        # Mapeamento direto dos campos da API
        size_mappings = {
            'ThumbnailUrl': ImageSize.THUMB,
            'SmallUrl': ImageSize.SMALL,
            'MediumUrl': ImageSize.MEDIUM,
            'LargeUrl': ImageSize.LARGE,
            'XLargeUrl': ImageSize.XLARGE,
            'X2LargeUrl': ImageSize.X2LARGE,
            'X3LargeUrl': ImageSize.X3LARGE,
            'OriginalUrl': ImageSize.ORIGINAL,
        }

        for field, size in size_mappings.items():
            if field in image_data and image_data[field]:
                url_value = image_data[field]
                if isinstance(url_value, str) and url_value.startswith('http'):
                    urls.append(PhotoURL(size=size, url=url_value))

        # Se só temos thumbnail, construir outras URLs
        if len(urls) == 1 and urls[0].size == ImageSize.THUMB:
            thumb_url = urls[0].url
            size_suffixes = {
                ImageSize.SMALL: 'S',
                ImageSize.MEDIUM: 'M',
                ImageSize.LARGE: 'L',
                ImageSize.XLARGE: 'XL',
                ImageSize.X2LARGE: 'X2',
                ImageSize.X3LARGE: 'X3',
                ImageSize.ORIGINAL: 'O',
            }

            for size_enum, suffix in size_suffixes.items():
                new_url = thumb_url.replace('/Th/', f'/{suffix}/')
                new_url = new_url.replace('-Th.', f'-{suffix}.')
                if new_url != thumb_url:
                    urls.append(PhotoURL(size=size_enum, url=new_url))

        return urls

    def _convert_image_to_photo(self, image_data: Dict[str, Any]) -> Photo:
        """Converter dados da API para Photo"""
        urls = self._extract_photo_urls(image_data)

        # Thumbnail URL
        thumbnail_url = None
        if urls:
            thumb_url = next(
                (url.url for url in urls if url.size == ImageSize.THUMB), None
            )
            thumbnail_url = thumb_url or urls[0].url

        return Photo(
            id=image_data.get('ImageKey', ''),
            title=image_data.get('Title'),
            urls=urls,
            thumbnail_url=thumbnail_url,
        )

    async def get_all_photos(self, url: str) -> AlbumResponse:
        """Obter todas as fotos de um álbum - FUNÇÃO PRINCIPAL"""
        album_key = await self._get_album_key(url)

        # Obter info do álbum
        album_url = f'{settings.SMUGMUG_API_BASE_URL}/album/{album_key}'
        album_data = await self._make_request(album_url, {'_verbosity': '1'})

        album_info = album_data['Response']['Album']
        album_title = album_info.get('Title', 'Álbum sem título')
        total_photos = album_info.get('ImageCount', 0)

        # Obter todas as imagens
        images_url = (
            f'{settings.SMUGMUG_API_BASE_URL}/album/{album_key}!images'
        )
        params = {
            '_verbosity': '2',
            'count': total_photos or 5000,  # Pegar todas de uma vez
        }

        images_data = await self._make_request(images_url, params)
        images = images_data.get('Response', {}).get('AlbumImage', [])

        # Converter para Photo objects
        photos = [self._convert_image_to_photo(img) for img in images]

        return AlbumResponse(
            album_title=album_title,
            album_id=album_key,
            total_photos=len(photos),
            photos=photos,
        )

    async def get_all_photos_by_id(self, album_id: str) -> AlbumResponse:
        """Obter todas as fotos de um álbum pelo ID"""
        # Validar se o album_id tem formato válido
        if not album_id or not album_id.strip():
            raise ValueError('ID do álbum não pode estar vazio')

        # Remover prefixo 'n-' se presente para normalizar
        album_key = (
            album_id.replace('n-', '')
            if album_id.startswith('n-')
            else album_id
        )

        # Obter info do álbum
        album_url = f'{settings.SMUGMUG_API_BASE_URL}/album/{album_key}'
        album_data = await self._make_request(album_url, {'_verbosity': '1'})

        album_info = album_data['Response']['Album']
        album_title = album_info.get('Title', 'Álbum sem título')
        total_photos = album_info.get('ImageCount', 0)

        # Obter todas as imagens
        images_url = (
            f'{settings.SMUGMUG_API_BASE_URL}/album/{album_key}!images'
        )
        params = {
            '_verbosity': '2',
            'count': total_photos or 5000,  # Pegar todas de uma vez
        }

        images_data = await self._make_request(images_url, params)
        images = images_data.get('Response', {}).get('AlbumImage', [])

        # Converter para Photo objects
        photos = [self._convert_image_to_photo(img) for img in images]

        return AlbumResponse(
            album_title=album_title,
            album_id=album_key,
            total_photos=len(photos),
            photos=photos,
        )
