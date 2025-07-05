from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest

from smugmug_photo_selector.models import (
    AlbumInfo,
    AlbumResponse,
    ImageSize,
    Photo,
)
from smugmug_photo_selector.smugmug_service import SmugMugService

EXPECTED_URLS_COUNT = 4
MIN_URLS_PER_PHOTO = 2
EXPECTED_TOTAL_PHOTOS = 3
IMAGE_COUNT = 15


@pytest.fixture
def service():
    with patch(
        'smugmug_photo_selector.smugmug_service.settings'
    ) as mock_settings:
        mock_settings.SMUGMUG_API_KEY = 'test_key'
        mock_settings.SMUGMUG_API_SECRET = 'test_secret'
        mock_settings.SMUGMUG_ACCESS_TOKEN = 'test_token'
        mock_settings.SMUGMUG_ACCESS_TOKEN_SECRET = 'test_token_secret'
        mock_settings.SMUGMUG_USER_AGENT = 'TestAgent'
        mock_settings.REQUEST_TIMEOUT = 30
        mock_settings.SMUGMUG_API_BASE_URL = 'https://api.smugmug.com/api/v2'
        mock_settings.SMUGMUG_WEB_URI_LOOKUP = (
            'https://api.smugmug.com/api/v2!weburilookup'
        )

        return SmugMugService()


def test_extract_album_key_success():
    test_cases = [
        ('https://user.smugmug.com/gallery/n-ABC123/', 'ABC123'),
        ('https://api.smugmug.com/api/v2/album/XYZ789', 'XYZ789'),
        ('https://example.com?albumkey=DEF456', 'DEF456'),
    ]

    for url, expected_key in test_cases:
        result = SmugMugService._extract_album_key(url)
        assert result == expected_key


def test_extract_album_key_failure():
    invalid_urls = [
        'https://example.com/no-album-key',
        'https://user.smugmug.com/just-a-gallery',
        'invalid-url',
    ]

    for url in invalid_urls:
        result = SmugMugService._extract_album_key(url)
        assert result is None


def test_extract_photo_urls_complete():
    image_data = {
        'ThumbnailUrl': 'https://photos.smugmug.com/img/Th/photo-Th.jpg',
        'SmallUrl': 'https://photos.smugmug.com/img/S/photo-S.jpg',
        'LargeUrl': 'https://photos.smugmug.com/img/L/photo-L.jpg',
        'OriginalUrl': 'https://photos.smugmug.com/img/O/photo-O.jpg',
    }

    urls = SmugMugService._extract_photo_urls(image_data)

    assert len(urls) == EXPECTED_URLS_COUNT
    sizes = [url.size for url in urls]
    assert ImageSize.THUMB in sizes
    assert ImageSize.LARGE in sizes
    assert ImageSize.ORIGINAL in sizes


def test_extract_photo_urls_thumb_only():
    image_data = {
        'ThumbnailUrl': 'https://photos.smugmug.com/img/Th/photo-Th.jpg'
    }

    urls = SmugMugService._extract_photo_urls(image_data)

    assert len(urls) > 1

    thumb_urls = [url for url in urls if url.size == ImageSize.THUMB]
    assert len(thumb_urls) == 1
    assert 'Th/photo-Th.jpg' in thumb_urls[0].url


def test_convert_image_to_photo(service):
    image_data = {
        'ImageKey': 'test123',
        'Title': 'Test Photo',
        'ThumbnailUrl': 'https://photos.smugmug.com/test/Th/test-Th.jpg',
        'LargeUrl': 'https://photos.smugmug.com/test/L/test-L.jpg',
    }

    photo = service._convert_image_to_photo(image_data)

    assert isinstance(photo, Photo)
    assert photo.id == 'test123'
    assert photo.title == 'Test Photo'
    assert photo.thumbnail_url is not None
    assert len(photo.urls) >= MIN_URLS_PER_PHOTO


@pytest.mark.asyncio
async def test_make_request_success(service):
    mock_response = Mock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.json.return_value = {'Response': {'test': 'data'}}

    with patch.object(service.session, 'get', return_value=mock_response):
        result = await service._make_request('https://test.com')
        assert result == {'Response': {'test': 'data'}}


@pytest.mark.asyncio
async def test_make_request_404(service):
    mock_response = Mock()
    mock_response.status_code = HTTPStatus.NOT_FOUND

    with patch.object(service.session, 'get', return_value=mock_response):
        with pytest.raises(ValueError, match='Álbum não encontrado'):
            await service._make_request('https://test.com')


@pytest.mark.asyncio
async def test_get_album_key_from_url(service):
    url = 'https://user.smugmug.com/gallery/n-ABC123/'

    result = await service._get_album_key(url)
    assert result == 'ABC123'


@pytest.mark.asyncio
async def test_get_all_photos_success(service):
    url = 'https://user.smugmug.com/test-album/n-ABC123'

    mock_album_data = {
        'Response': {
            'Album': {
                'AlbumKey': 'ABC123',
                'Title': 'Test Album',
                'ImageCount': 2,
            }
        }
    }

    mock_images_data = {
        'Response': {
            'AlbumImage': [
                {
                    'ImageKey': 'img1',
                    'Title': 'Photo 1',
                    'ThumbnailUrl': 'https://photos.smugmug.com/img1/Th/photo1-Th.jpg',
                    'LargeUrl': 'https://photos.smugmug.com/img1/L/photo1-L.jpg',
                },
                {
                    'ImageKey': 'img2',
                    'Title': 'Photo 2',
                    'ThumbnailUrl': 'https://photos.smugmug.com/img2/Th/photo2-Th.jpg',
                },
            ]
        }
    }

    def mock_make_request(url, params=None):
        if 'album/ABC123!images' in url:
            return mock_images_data
        return mock_album_data

    with patch.object(service, '_make_request', side_effect=mock_make_request):
        result = await service.get_all_photos(url)

        assert isinstance(result, AlbumResponse)
        assert result.album_title == 'Test Album'
        assert result.album_id == 'ABC123'
        assert result.total_photos == MIN_URLS_PER_PHOTO
        assert len(result.photos) == MIN_URLS_PER_PHOTO

        first_photo = result.photos[0]
        assert first_photo.id == 'img1'
        assert first_photo.title == 'Photo 1'


def test_service_initialization_without_credentials():
    """Teste de inicialização sem credenciais OAuth"""
    with patch(
        'smugmug_photo_selector.smugmug_service.settings'
    ) as mock_settings:
        mock_settings.SMUGMUG_API_KEY = None
        mock_settings.SMUGMUG_API_SECRET = 'test_secret'
        mock_settings.SMUGMUG_ACCESS_TOKEN = 'test_token'
        mock_settings.SMUGMUG_ACCESS_TOKEN_SECRET = 'test_token_secret'

        with pytest.raises(
            ValueError, match='Credenciais OAuth não configuradas'
        ):
            SmugMugService()


@pytest.mark.asyncio
async def test_get_all_photos_by_id_success(service):
    """Teste de sucesso para get_all_photos_by_id"""
    album_id = 'ABC123'

    mock_album_data = {
        'Response': {
            'Album': {
                'AlbumKey': 'ABC123',
                'Title': 'Test Album by ID',
                'ImageCount': 3,
            }
        }
    }

    mock_images_data = {
        'Response': {
            'AlbumImage': [
                {
                    'ImageKey': 'img1',
                    'Title': 'Photo 1',
                    'ThumbnailUrl': 'https://photos.smugmug.com/img1/Th/photo1-Th.jpg',
                    'LargeUrl': 'https://photos.smugmug.com/img1/L/photo1-L.jpg',
                },
                {
                    'ImageKey': 'img2',
                    'Title': 'Photo 2',
                    'ThumbnailUrl': 'https://photos.smugmug.com/img2/Th/photo2-Th.jpg',
                    'MediumUrl': 'https://photos.smugmug.com/img2/M/photo2-M.jpg',
                },
                {
                    'ImageKey': 'img3',
                    'Title': 'Photo 3',
                    'ThumbnailUrl': 'https://photos.smugmug.com/img3/Th/photo3-Th.jpg',
                },
            ]
        }
    }

    def mock_make_request(url, params=None):
        if 'album/ABC123!images' in url:
            return mock_images_data
        return mock_album_data

    with patch.object(service, '_make_request', side_effect=mock_make_request):
        result = await service.get_all_photos_by_id(album_id)

        assert isinstance(result, AlbumResponse)
        assert result.album_title == 'Test Album by ID'
        assert result.album_id == 'ABC123'
        assert result.total_photos == EXPECTED_TOTAL_PHOTOS
        assert len(result.photos) == EXPECTED_TOTAL_PHOTOS

        # Verificar primeira foto
        first_photo = result.photos[0]
        assert first_photo.id == 'img1'
        assert first_photo.title == 'Photo 1'
        assert len(first_photo.urls) >= MIN_URLS_PER_PHOTO

        # Verificar segunda foto
        second_photo = result.photos[1]
        assert second_photo.id == 'img2'
        assert second_photo.title == 'Photo 2'


@pytest.mark.asyncio
async def test_get_all_photos_by_id_with_n_prefix(service):
    """Teste para album_id com prefixo 'n-'"""
    album_id = 'n-ABC123'

    mock_album_data = {
        'Response': {
            'Album': {
                'AlbumKey': 'ABC123',
                'Title': 'Test Album with n- prefix',
                'ImageCount': 1,
            }
        }
    }

    mock_images_data = {
        'Response': {
            'AlbumImage': [
                {
                    'ImageKey': 'img1',
                    'Title': 'Single Photo',
                    'ThumbnailUrl': 'https://photos.smugmug.com/img1/Th/photo1-Th.jpg',
                },
            ]
        }
    }

    def mock_make_request(url, params=None):
        if 'album/ABC123!images' in url:
            return mock_images_data
        return mock_album_data

    with patch.object(service, '_make_request', side_effect=mock_make_request):
        result = await service.get_all_photos_by_id(album_id)

        assert isinstance(result, AlbumResponse)
        assert result.album_title == 'Test Album with n- prefix'
        assert result.album_id == 'ABC123'  # Deve remover o prefixo 'n-'
        assert result.total_photos == 1
        assert len(result.photos) == 1


@pytest.mark.asyncio
async def test_get_all_photos_by_id_empty_album_id(service):
    """Teste para album_id vazio"""
    with pytest.raises(ValueError, match='ID do álbum não pode estar vazio'):
        await service.get_all_photos_by_id('')

    with pytest.raises(ValueError, match='ID do álbum não pode estar vazio'):
        await service.get_all_photos_by_id('   ')


@pytest.mark.asyncio
async def test_get_all_photos_by_id_album_not_found(service):
    """Teste para álbum não encontrado"""
    album_id = 'INVALID123'

    mock_response = Mock()
    mock_response.status_code = HTTPStatus.NOT_FOUND

    with patch.object(service.session, 'get', return_value=mock_response):
        with pytest.raises(ValueError, match='Álbum não encontrado'):
            await service.get_all_photos_by_id(album_id)


@pytest.mark.asyncio
async def test_get_all_photos_by_id_empty_album(service):
    """Teste para álbum vazio (sem fotos)"""
    album_id = 'EMPTY123'

    mock_album_data = {
        'Response': {
            'Album': {
                'AlbumKey': 'EMPTY123',
                'Title': 'Empty Album',
                'ImageCount': 0,
            }
        }
    }

    mock_images_data = {
        'Response': {
            'AlbumImage': []  # Lista vazia
        }
    }

    def mock_make_request(url, params=None):
        if 'album/EMPTY123!images' in url:
            return mock_images_data
        return mock_album_data

    with patch.object(service, '_make_request', side_effect=mock_make_request):
        result = await service.get_all_photos_by_id(album_id)

        assert isinstance(result, AlbumResponse)
        assert result.album_title == 'Empty Album'
        assert result.album_id == 'EMPTY123'
        assert result.total_photos == 0
        assert len(result.photos) == 0


@pytest.mark.asyncio
async def test_get_album_info_success(service):
    """Teste de sucesso para get_album_info"""
    url = 'https://user.smugmug.com/test-album/n-ABC123'

    mock_album_data = {
        'Response': {
            'Album': {
                'AlbumKey': 'ABC123',
                'Title': 'Test Album Info',
                'ImageCount': IMAGE_COUNT,
                'Privacy': 'Public',
                'Description': 'Um álbum de teste para verificar informações',
                'DateCreated': '2024-01-15T10:30:00Z',
                'DateModified': '2024-01-20T14:45:00Z',
            }
        }
    }

    with patch.object(service, '_make_request', return_value=mock_album_data):
        result = await service.get_album_info(url)

        assert isinstance(result, AlbumInfo)
        assert result.album_id == 'ABC123'
        assert result.album_title == 'Test Album Info'
        assert result.album_url == 'https://www.smugmug.com/album/ABC123'
        assert result.total_photos == IMAGE_COUNT
        assert result.privacy == 'Public'
        assert (
            result.description
            == 'Um álbum de teste para verificar informações'
        )
        assert result.date_created == '2024-01-15T10:30:00Z'
        assert result.date_modified == '2024-01-20T14:45:00Z'


@pytest.mark.asyncio
async def test_get_album_info_minimal_data(service):
    """Teste para álbum com dados mínimos"""
    url = 'https://user.smugmug.com/minimal-album/n-MIN123'

    mock_album_data = {
        'Response': {
            'Album': {
                'AlbumKey': 'MIN123',
                'Title': 'Minimal Album',
                'ImageCount': 0,
                # Sem privacy, description, dates
            }
        }
    }

    with patch.object(service, '_make_request', return_value=mock_album_data):
        result = await service.get_album_info(url)

        assert isinstance(result, AlbumInfo)
        assert result.album_id == 'MIN123'
        assert result.album_title == 'Minimal Album'
        assert result.album_url == 'https://www.smugmug.com/album/MIN123'
        assert result.total_photos == 0
        assert result.privacy is None
        assert result.description is None
        assert result.date_created is None
        assert result.date_modified is None


@pytest.mark.asyncio
async def test_get_album_info_album_not_found(service):
    """Teste para álbum não encontrado na rota /info"""
    url = 'https://user.smugmug.com/invalid-album'

    mock_response = Mock()
    mock_response.status_code = HTTPStatus.NOT_FOUND

    with patch.object(service.session, 'get', return_value=mock_response):
        with pytest.raises(ValueError, match='Álbum não encontrado'):
            await service.get_album_info(url)
