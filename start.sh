#!/bin/bash

# Digiskills IT Helpdesk - Quick Start Script

set -e

echo "========================================="
echo "Digiskills IT Helpdesk - Setup & Start"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file to set your SECRET_KEY and passwords!"
    echo "   For production, generate a secure SECRET_KEY:"
    echo "   python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    echo ""
    read -p "Press Enter to continue with default settings (NOT recommended for production)..."
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Starting Digiskills IT Helpdesk..."
echo ""

# Stop any existing containers
docker-compose down 2>/dev/null || true

# Build and start containers
docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo "Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "========================================="
    echo "✓ Digiskills is now running!"
    echo "========================================="
    echo ""
    echo "Access the application:"
    echo "  Frontend: http://localhost"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "Default login credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""
    echo "⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker-compose logs -f"
    echo "  Stop app:     docker-compose down"
    echo "  Restart:      docker-compose restart"
    echo ""
else
    echo ""
    echo "ERROR: Services failed to start"
    echo "Check logs with: docker-compose logs"
    exit 1
fi
