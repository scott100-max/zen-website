#!/bin/bash
# R2 Upload + CDN Cache Purge
# Usage: tools/r2-upload.sh <local-file> <r2-key> [content-type]
# Example: tools/r2-upload.sh content/audio-free/narrator-welcome.mp3 content/audio-free/narrator-welcome.mp3 audio/mpeg

set -euo pipefail

LOCAL_FILE="$1"
R2_KEY="$2"
CONTENT_TYPE="${3:-audio/mpeg}"
BUCKET="salus-mind"
CDN_BASE="https://media.salus-mind.com"

# Load env vars
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  export $(grep -E '^(CF_CACHE_PURGE_TOKEN|CF_ZONE_ID)=' "$SCRIPT_DIR/.env" | xargs)
fi

if [ -z "${CF_CACHE_PURGE_TOKEN:-}" ] || [ -z "${CF_ZONE_ID:-}" ]; then
  echo "ERROR: CF_CACHE_PURGE_TOKEN and CF_ZONE_ID must be set in .env"
  exit 1
fi

if [ ! -f "$LOCAL_FILE" ]; then
  echo "ERROR: File not found: $LOCAL_FILE"
  exit 1
fi

echo "Uploading: $LOCAL_FILE → $BUCKET/$R2_KEY"
npx wrangler r2 object put "$BUCKET/$R2_KEY" --file="$LOCAL_FILE" --remote --content-type="$CONTENT_TYPE"

# Purge base URL + find any ?v= query string variants referenced in HTML
CDN_URL="${CDN_BASE}/${R2_KEY}"
PURGE_URLS="\"${CDN_URL}\""

# Scan HTML files for ?v= variants of this URL
for vurl in $(grep -roh "${R2_KEY}?v=[^\"']*" *.html sessions/*.html articles/*.html newsletters/*.html 2>/dev/null | sort -u); do
  PURGE_URLS="${PURGE_URLS},\"${CDN_BASE}/${vurl}\""
done

echo "Purging CDN cache: ${CDN_URL} (+ query string variants)"
PURGE_RESULT=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer ${CF_CACHE_PURGE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"files\":[${PURGE_URLS}]}")

if echo "$PURGE_RESULT" | grep -q '"success":true'; then
  echo "CDN purge: OK"
else
  echo "CDN purge: FAILED — $PURGE_RESULT"
  exit 1
fi

# Verify served file matches local
sleep 2
LOCAL_MD5=$(md5 -q "$LOCAL_FILE")
SERVED_MD5=$(curl -s "$CDN_BASE/$R2_KEY?v=$(date +%s)" -o /tmp/_r2_verify.tmp && md5 -q /tmp/_r2_verify.tmp)
rm -f /tmp/_r2_verify.tmp

if [ "$LOCAL_MD5" = "$SERVED_MD5" ]; then
  echo "Verified: CDN serving correct file (md5: $LOCAL_MD5)"
else
  echo "WARNING: CDN md5 ($SERVED_MD5) != local md5 ($LOCAL_MD5) — may need time to propagate"
fi
