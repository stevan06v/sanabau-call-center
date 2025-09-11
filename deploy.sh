#!/bin/bash

set -e

echo "Starting deployment..."

if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

echo "Stopping existing containers..."
docker-compose down --remove-orphans

echo "Building and starting containers..."
docker-compose up -d --build

echo "Waiting for service..."
sleep 10

if docker-compose ps | grep -q "Up"; then
    echo "Deployment successful"
    echo "Available at: https://aicaller.websters.at"
else
    echo "Deployment failed - check logs"
    exit 1
fi
