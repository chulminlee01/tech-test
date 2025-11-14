#!/bin/bash

# Complete fix for OpenRouter configuration
echo "🔧 Disabling all OpenRouter configuration..."

cd /Users/chulmin.lee/Desktop/github/tech_test2

# Comment out all OpenRouter related lines
sed -i.bak2 \
    -e 's/^OPENROUTER_/# OPENROUTER_/g' \
    -e 's/^FALLBACK_MODEL/# FALLBACK_MODEL/g' \
    -e 's/^FALLBACK_BASE_URL/# FALLBACK_BASE_URL/g' \
    -e 's/^DEEPSEEK_THINKING/# DEEPSEEK_THINKING/g' \
    .env

rm -f .env.bak2

echo "✅ All OpenRouter configuration disabled"
echo ""
echo "Now using:"
echo "  ✅ NVIDIA API only (no fallback)"
echo ""

