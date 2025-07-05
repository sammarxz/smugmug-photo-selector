import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import AlbumResponse
from .smugmug_service import SmugMugService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='SmugMug Photo Extractor',
    description='Extrai todas as fotos de um álbum SmugMug',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET'],
    allow_headers=['*'],
)

smugmug_service = SmugMugService()


@app.get('/', tags=['Info'])
async def root():
    return {
        'service': 'SmugMug Photo Extractor',
        'version': '1.0.0',
        'endpoint': '/photos',
    }


@app.get('/photos', response_model=AlbumResponse, tags=['Photos'])
async def get_album_photos(
    url: str = Query(..., description='URL do álbum SmugMug'),
):
    """
    Extrair TODAS as fotos de um álbum SmugMug em todos os
    tamanhos disponíveis.

    Exemplo: /photos?url=https://user.smugmug.com/album-name
    """
    try:
        logger.info(f'Extracting photos from: {url}')
        return await smugmug_service.get_all_photos(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f'Error: {e}')
        raise HTTPException(status_code=500, detail='Erro interno')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'app:app',
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
