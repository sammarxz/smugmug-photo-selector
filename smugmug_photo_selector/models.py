from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ImageSize(str, Enum):
    THUMB = 'Thumb'
    SMALL = 'Small'
    MEDIUM = 'Medium'
    LARGE = 'Large'
    XLARGE = 'XLarge'
    X2LARGE = 'X2Large'
    X3LARGE = 'X3Large'
    ORIGINAL = 'Original'


class PhotoURL(BaseModel):
    size: ImageSize
    url: str


class Photo(BaseModel):
    id: str
    title: Optional[str] = None
    urls: List[PhotoURL]
    thumbnail_url: Optional[str] = None


class AlbumResponse(BaseModel):
    album_title: str
    album_id: str
    total_photos: int
    photos: List[Photo]


class AlbumInfo(BaseModel):
    album_id: str
    album_title: str
    album_url: str
    total_photos: int
    privacy: Optional[str] = None
    description: Optional[str] = None
    date_created: Optional[str] = None
    date_modified: Optional[str] = None
