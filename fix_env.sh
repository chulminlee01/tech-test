#!/bin/bash

# Script to fix the OpenRouter authentication error
# This will comment out the invalid OPENROUTER_API_KEY

echo "========================================================================"
echo "🔧 Fixing OpenRouter Authentication Error"
echo "========================================================================"
echo ""

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

echo "📝 Backing up current .env file..."
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup created: ${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo ""

echo "🔧 Commenting out invalid OPENROUTER_API_KEY..."
sed -i.tmp 's/^OPENROUTER_API_KEY=/# OPENROUTER_API_KEY=/' "$ENV_FILE"
rm -f "${ENV_FILE}.tmp"
echo "✅ OPENROUTER_API_KEY has been commented out"
echo ""

echo "📋 Updated .env configuration:"
echo "  ✅ NVIDIA_API_KEY: Active (primary)"
echo "  ❌ OPENROUTER_API_KEY: Disabled (was invalid)"
echo "  ✅ GOOGLE_API_KEY: Active"
echo ""

echo "========================================================================"
echo "✅ Fix Complete!"
echo "========================================================================"
echo ""
echo "Your app will now use only NVIDIA API (no fallback)."
echo ""
echo "To re-enable OpenRouter fallback:"
echo "  1. Get a valid key from https://openrouter.ai"
echo "  2. Edit .env and uncomment the line"
echo "  3. Replace with your new valid key"
echo ""
echo "Restart your server:"
echo "  python3 app.py"
echo ""

