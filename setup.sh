#!/bin/bash
# =============================================================================
# setup.sh - Installation complète SymPointV2 Tools
# =============================================================================
# Usage: ./setup.sh
# =============================================================================

set -e

WORKSPACE="/workspace"

echo "=============================================="
echo "  🚀 SymPointV2 Tools - Installation"
echo "=============================================="

# Étape 1: Vérifier/Installer SymPointV2
echo ""
echo "[1/5] Vérification de SymPointV2..."

if [ ! -d "$WORKSPACE/SymPointV2" ]; then
    echo "   Clonage de SymPointV2..."
    cd $WORKSPACE
    git clone https://github.com/nicehuster/SymPointV2.git
fi

# Étape 2: Installer les dépendances Python
echo ""
echo "[2/5] Installation des dépendances Python..."

pip install -q gdown pymupdf munch pyyaml scipy scikit-learn svgpathtools 2>/dev/null || true

if ! python -c "import detectron2" 2>/dev/null; then
    echo "   Installation de detectron2..."
    pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html
fi

# Étape 3: Télécharger le checkpoint
echo ""
echo "[3/5] Vérification du checkpoint..."

CKPT_DIR="$WORKSPACE/SymPointV2/checkpoints/sympointv2"
mkdir -p "$CKPT_DIR"

if [ ! -f "$CKPT_DIR/best.pth" ]; then
    echo "   Téléchargement de best.pth (~135 MB)..."
    gdown 1LczVNXapght3S65gx0ZOhQ3UqkBg4hJ7 -O "$CKPT_DIR/best.pth"
fi

if [ ! -f "$CKPT_DIR/svg_pointT.yaml" ]; then
    echo "   Téléchargement de svg_pointT.yaml..."
    gdown 1c0_al7p72D7eTOHgBP_kxU1H1Ia-ZakV -O "$CKPT_DIR/svg_pointT.yaml"
fi

# Étape 4: Compiler pointops si nécessaire
echo ""
echo "[4/5] Vérification de pointops..."

cd $WORKSPACE/SymPointV2
if ! python -c "from modules.pointops.functions import pointops" 2>/dev/null; then
    echo "   Compilation de pointops..."
    cd "$WORKSPACE/SymPointV2/modules/pointops"
    python setup.py install 2>&1 | tail -3
fi

# Étape 5: Créer les liens symboliques
echo ""
echo "[5/5] Configuration des scripts..."

cd $WORKSPACE
ln -sf sympointv2-tools/scripts/smart_pdf_parser_v2.py . 2>/dev/null || true
ln -sf sympointv2-tools/scripts/run_inference.py . 2>/dev/null || true
ln -sf sympointv2-tools/scripts/analyze_pdf_ocg.py . 2>/dev/null || true
ln -sf sympointv2-tools/sync_to_github.sh . 2>/dev/null || true

mkdir -p test_pdfs

export LD_LIBRARY_PATH=/opt/conda/lib/python3.7/site-packages/torch/lib:$LD_LIBRARY_PATH
echo 'export LD_LIBRARY_PATH=/opt/conda/lib/python3.7/site-packages/torch/lib:$LD_LIBRARY_PATH' >> ~/.bashrc 2>/dev/null || true

# Validation
echo ""
echo "=============================================="
echo "  🔍 Validation"
echo "=============================================="

python << 'EOF'
import sys
try:
    import torch
    print(f"✅ PyTorch {torch.__version__}" + (" + CUDA" if torch.cuda.is_available() else ""))
    sys.path.insert(0, '/workspace/SymPointV2')
    from modules.pointops.functions import pointops
    print("✅ pointops")
    import detectron2
    print("✅ detectron2")
    import fitz
    print("✅ PyMuPDF")
    import os
    if os.path.exists('/workspace/SymPointV2/checkpoints/sympointv2/best.pth'):
        print("✅ Checkpoint")
    print("\n🎉 Installation complète!")
except Exception as e:
    print(f"❌ Erreur: {e}")
EOF

echo ""
echo "=============================================="
echo "  ✅ PRÊT À UTILISER"
echo "=============================================="
echo ""
echo "Commandes:"
echo "  python smart_pdf_parser_v2.py <plan.pdf>"
echo "  python run_inference.py <plan_s2.json>"
echo ""
