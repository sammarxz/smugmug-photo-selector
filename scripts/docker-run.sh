#!/bin/bash

# SmugMug Photo Selector - Docker Runner
# This script helps you run the application with Docker

set -e

echo "🐳 SmugMug Photo Selector - Docker Runner"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with your SmugMug credentials:"
    echo ""
    echo "SMUGMUG_API_KEY=your_api_key"
    echo "SMUGMUG_API_SECRET=your_api_secret"
    echo "SMUGMUG_ACCESS_TOKEN=your_access_token"
    echo "SMUGMUG_ACCESS_TOKEN_SECRET=your_access_token_secret"
    echo ""
    echo "You can use the OAuth script to get your tokens:"
    echo "python scripts/simple_oauth.py <API_KEY> <API_SECRET>"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found!"
    echo "Please install docker-compose and try again."
    exit 1
fi

echo "✅ Environment check passed"
echo ""

# Build and run
echo "🚀 Building and starting the application..."
docker-compose up --build

echo ""
echo "✅ Application stopped" 