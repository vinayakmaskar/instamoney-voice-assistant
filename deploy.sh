#!/bin/bash
set -euo pipefail

PROJECT_ID="voice-chatbot-482909"
REGION="asia-south1"
SERVICE_NAME="voice-chatbot-backend"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=== InstaMoney Voice Chatbot — Cloud Run Deployment ==="
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Service:  $SERVICE_NAME"
echo ""

# 1. Set active project
gcloud config set project "$PROJECT_ID"

# 2. Enable required APIs (idempotent)
echo "→ Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --quiet

# 3. Create secrets in Secret Manager (skip if they already exist)
echo "→ Setting up secrets..."
SECRETS_FILE="secrets.json"

if [ ! -f "$SECRETS_FILE" ]; then
  echo "ERROR: $SECRETS_FILE not found. Create it first."
  exit 1
fi

# Upload the entire secrets.json as a single secret
if gcloud secrets describe app-secrets --project="$PROJECT_ID" >/dev/null 2>&1; then
  echo "  Secret 'app-secrets' exists, creating new version..."
  gcloud secrets versions add app-secrets --data-file="$SECRETS_FILE" --quiet
else
  echo "  Creating secret 'app-secrets'..."
  gcloud secrets create app-secrets --data-file="$SECRETS_FILE" --replication-policy="automatic" --quiet
fi

# 4. Build and push container
echo "→ Building container with Cloud Build..."
gcloud builds submit --tag "$IMAGE" --timeout=600 --quiet

# 5. Deploy to Cloud Run
echo "→ Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --timeout 300 \
  --allow-unauthenticated \
  --set-secrets="/app/secrets.json=app-secrets:latest" \
  --set-env-vars="DJANGO_SETTINGS_MODULE=voice_chatbot.settings" \
  --quiet

# 6. Print the service URL
echo ""
echo "=== Deployment Complete ==="
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')
echo "Backend URL: $SERVICE_URL"
echo "WebSocket:   ${SERVICE_URL/https/wss}/ws/voice-chat/?stage=basic_details"
echo ""
echo "Update your frontend WS_URL to point to the WebSocket URL above."
