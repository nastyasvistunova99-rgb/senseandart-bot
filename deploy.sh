#!/bin/bash

# Deploy script for Google Cloud Run
# This script deploys the Telegram bot to Google Cloud Run

set -e

PROJECT_ID="senseandart-bot-new"
SERVICE_NAME="senseandart-bot"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting deployment to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"

# 1. Create Dockerfile if it doesn't exist
if [ ! -f "Dockerfile" ]; then
    echo "📝 Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY config.py .
COPY credentials.json .

# Run the bot
CMD ["python", "main.py"]
EOF
fi

# 2. Build Docker image
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

# 3. Push to Google Container Registry
echo "📤 Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# 4. Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --memory 256Mi \
  --timeout 3600 \
  --no-allow-unauthenticated \
  --set-env-vars="TELEGRAM_BOT_TOKEN=7904726862:AAGicriNr_ElKmz6jGaW5pBCWNudiw3LvR0,CHANNEL_ID=-1003027665711,GOOGLE_SHEETS_ID=1mUQ8PflOvHUD2q1V7zegkgGUmvRQUG9k6P6tyZJbM44,SHEET_NAME=Sheet1,PROMO_POST_ID=42"

echo "✅ Deployment complete!"
echo "Your bot is now running on Google Cloud Run."
echo ""
echo "To view logs:"
echo "  gcloud run logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "To stop the service:"
echo "  gcloud run services delete ${SERVICE_NAME} --region ${REGION}"
