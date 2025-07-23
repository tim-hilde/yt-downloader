#!/bin/bash

# Deployment script for Raspberry Pi
# This script helps set up the YouTube downloader service

set -e

echo "🚀 Setting up YouTube Downloader Service on Raspberry Pi"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed. Please log out and back in for Docker permissions."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo pip3 install docker-compose
fi

# Create downloads directory
echo "📁 Creating downloads directory..."
mkdir -p downloads

# Build and start the service
echo "🔨 Building and starting the service..."
docker-compose up --build -d

# Wait for service to be healthy
echo "⏳ Waiting for service to be healthy..."
sleep 30

# Check service health
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Service is running and healthy!"
    echo "🌐 Access the service at: http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "📖 Usage example:"
    echo "curl -X POST http://localhost:5000/download \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"url\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}'"
else
    echo "❌ Service is not healthy. Check logs with: docker-compose logs"
    exit 1
fi