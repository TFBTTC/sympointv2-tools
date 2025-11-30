#!/bin/bash
# =============================================================================
# sync_to_github.sh - Sauvegarde les scripts modifiés vers GitHub
# =============================================================================
# Usage: ./sync_to_github.sh "message de commit"
# À EXÉCUTER AVANT DE FERMER LE POD
# =============================================================================

set -e

REPO_DIR="/workspace/sympointv2-tools"
SCRIPTS_DIR="$REPO_DIR/scripts"

COMMIT_MSG="${1:-Auto-save $(date +%Y-%m-%d_%H:%M)}"

echo "=============================================="
echo "  📤 Synchronisation vers GitHub"
echo "=============================================="

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "❌ Repo git non trouvé dans $REPO_DIR"
    exit 1
fi

cd "$REPO_DIR"

echo ""
echo "📋 Vérification des scripts modifiés..."

for script in smart_pdf_parser_v2.py run_inference.py analyze_pdf_ocg.py; do
    if [ -f "/workspace/$script" ] && [ ! -L "/workspace/$script" ]; then
        echo "   📝 $script modifié - copie..."
        cp "/workspace/$script" "$SCRIPTS_DIR/$script"
    fi
done

if git diff --quiet && git diff --staged --quiet; then
    echo ""
    echo "✅ Aucune modification à sauvegarder"
    exit 0
fi

echo ""
echo "📊 Modifications détectées:"
git status --short

echo ""
echo "💾 Commit et push..."
git add -A
git commit -m "$COMMIT_MSG"
git push

echo ""
echo "=============================================="
echo "  ✅ Synchronisation terminée!"
echo "=============================================="
