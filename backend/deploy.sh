#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env

# Variables
PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="visbets-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Build the Docker image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Push the image to Google Container Registry
echo "Pushing image to GCR..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars="ENVIRONMENT=production" \
  --set-secrets="NBA_API_KEY=nba-api-key:latest"

echo "Deployment completed successfully!" 