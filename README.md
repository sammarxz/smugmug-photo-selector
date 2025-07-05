# SmugMug Photo Selector

A FastAPI application that extracts all photos from a SmugMug album in all available sizes.

## Features

- 🖼️ Extract all photos from any SmugMug album
- 📏 Get photos in multiple sizes (Thumbnail, Small, Medium, Large, XLarge, X2Large, X3Large, Original)
- 🔐 OAuth 1.0a authentication with SmugMug API
- 🚀 FastAPI with automatic API documentation
- 🧪 Comprehensive test suite
- 📦 Poetry for dependency management

## Quick Start

### Prerequisites

- Python 3.13+
- SmugMug API credentials

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd smugmug-photo-selector
```

2. Install dependencies:
```bash
poetry install
```

3. Set up your SmugMug API credentials:
```bash
# Copy the OAuth script
cp scripts/simple_oauth.py .

# Run the OAuth script to get your tokens
python simple_oauth.py <YOUR_API_KEY> <YOUR_API_SECRET>
```

4. Create a `.env` file with your credentials:
```env
SMUGMUG_API_KEY=your_api_key
SMUGMUG_API_SECRET=your_api_secret
SMUGMUG_ACCESS_TOKEN=your_access_token
SMUGMUG_ACCESS_TOKEN_SECRET=your_access_token_secret
```

5. Run the application:
```bash
poetry run fastapi dev smugmug_photo_selector/app.py
```

The API will be available at `http://localhost:8000`

## Docker Deployment

### Using Docker Compose (Recommended)

1. Create a `.env` file with your SmugMug credentials:
```env
SMUGMUG_API_KEY=your_api_key
SMUGMUG_API_SECRET=your_api_secret
SMUGMUG_ACCESS_TOKEN=your_access_token
SMUGMUG_ACCESS_TOKEN_SECRET=your_access_token_secret
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

### Using Docker directly

1. Build the image:
```bash
docker build -t smugmug-photo-selector .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e SMUGMUG_API_KEY=your_api_key \
  -e SMUGMUG_API_SECRET=your_api_secret \
  -e SMUGMUG_ACCESS_TOKEN=your_access_token \
  -e SMUGMUG_ACCESS_TOKEN_SECRET=your_access_token_secret \
  smugmug-photo-selector
```

## API Usage

### Get Album Photos

**Endpoint:** `GET /photos`

**Query Parameters:**
- `url` (required): SmugMug album URL

**Example:**
```bash
curl "http://localhost:8000/photos?url=https://user.smugmug.com/album-name"
```

**Response:**
```json
{
  "album_title": "My Album",
  "album_id": "ABC123",
  "total_photos": 10,
  "photos": [
    {
      "id": "img1",
      "title": "Photo 1",
      "thumbnail_url": "https://photos.smugmug.com/img1/Th/photo1-Th.jpg",
      "urls": [
        {
          "size": "Thumb",
          "url": "https://photos.smugmug.com/img1/Th/photo1-Th.jpg"
        },
        {
          "size": "Large",
          "url": "https://photos.smugmug.com/img1/L/photo1-L.jpg"
        },
        {
          "size": "Original",
          "url": "https://photos.smugmug.com/img1/O/photo1-O.jpg"
        }
      ]
    }
  ]
}
```

### API Documentation

Once the server is running, you can access:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Configuration

The application uses environment variables for configuration. Create a `.env` file with:

```env
# Server settings
HOST=0.0.0.0
PORT=8000
RELOAD=true

# SmugMug API settings
SMUGMUG_API_KEY=your_api_key
SMUGMUG_API_SECRET=your_api_secret
SMUGMUG_ACCESS_TOKEN=your_access_token
SMUGMUG_ACCESS_TOKEN_SECRET=your_access_token_secret

# Optional settings
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

## Getting SmugMug API Credentials

1. Go to [SmugMug API Documentation](https://api.smugmug.com/api/v2/doc)
2. Create a new application
3. Get your API Key and API Secret
4. Use the provided OAuth script to get access tokens:

```bash
python scripts/simple_oauth.py <API_KEY> <API_SECRET>
```

Follow the interactive prompts to complete the OAuth flow.

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=smugmug_photo_selector

# Run specific test file
poetry run pytest tests/test_smugmug_service.py
```

### Code Quality

```bash
# Lint code
poetry run ruff check

# Format code
poetry run ruff format

# Fix linting issues
poetry run ruff check --fix
```

### Available Tasks

```bash
# Lint code
poetry run task lint

# Format code
poetry run task format

# Run tests
poetry run task test

# Start development server
poetry run task run
```

## Project Structure

```
smugmug-photo-selector/
├── smugmug_photo_selector/
│   ├── app.py              # FastAPI application
│   ├── config.py           # Configuration settings
│   ├── models.py           # Pydantic models
│   └── smugmug_service.py  # SmugMug API service
├── scripts/
│   └── simple_oauth.py     # OAuth token generator
├── tests/
│   └── test_smugmug_service.py
├── pyproject.toml          # Poetry configuration
└── README.md
```

## API Models

### AlbumResponse
- `album_title`: Album title
- `album_id`: SmugMug album ID
- `total_photos`: Number of photos in album
- `photos`: List of Photo objects

### Photo
- `id`: Photo ID
- `title`: Photo title (optional)
- `urls`: List of PhotoURL objects
- `thumbnail_url`: Thumbnail URL (optional)

### PhotoURL
- `size`: Image size (Thumb, Small, Medium, Large, XLarge, X2Large, X3Large, Original)
- `url`: Direct URL to the image

## Error Handling

The API returns appropriate HTTP status codes:
- `400`: Bad request (invalid URL, album not found)
- `500`: Internal server error

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions:
1. Check the [SmugMug API Documentation](https://api.smugmug.com/api/v2/doc)
2. Review the test files for usage examples
3. Open an issue on GitHub
