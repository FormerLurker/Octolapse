#!/bin/bash
# Example: send render progress updates to Octolapse from a before/after render script.
#
# Usage:
#   OCTOPRINT_API_KEY=your_key ./send_render_progress.sh 42
#
# Set OCTOPRINT_HOST to override the default (http://localhost:5000).
#
# This is useful for before/after render scripts that do their own processing
# (e.g. re-encoding, watermarking) and want to drive the Octolapse progress
# bar in the OctoPrint UI.

OCTOPRINT_HOST="${OCTOPRINT_HOST:-http://localhost:5000}"
OCTOPRINT_API_KEY="${OCTOPRINT_API_KEY:-}"
PERCENT="${1:-}"

if [ -z "$OCTOPRINT_API_KEY" ]; then
    echo "Error: OCTOPRINT_API_KEY is not set" >&2
    exit 1
fi

if [ -z "$PERCENT" ]; then
    echo "Usage: $0 <percent>" >&2
    echo "  percent: 0-100" >&2
    exit 1
fi

response=$(curl -sf -X POST \
    -H "Content-Type: application/json" \
    -H "X-Api-Key: $OCTOPRINT_API_KEY" \
    -d "{\"percent\": $PERCENT}" \
    "$OCTOPRINT_HOST/plugin/octolapse/renderProgress")

if [ $? -ne 0 ]; then
    echo "Error: failed to connect to OctoPrint at $OCTOPRINT_HOST" >&2
    exit 1
fi

success=$(echo "$response" | grep -o '"success": *true')
if [ -z "$success" ]; then
    echo "Error: $response" >&2
    exit 1
fi

echo "Progress updated: ${PERCENT}%"
