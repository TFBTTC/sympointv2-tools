# 🏗️ SymPointV2 Tools

Outils pour la segmentation de plans d'architecture avec SymPointV2 sur RunPod.

## 🚀 Quick Start

```bash
cd /workspace
git clone https://github.com/TFBTTC/sympointv2-tools.git
cd sympointv2-tools
chmod +x setup.sh && ./setup.sh
```

## 📁 Structure

```
sympointv2-tools/
├── setup.sh                    # Installation automatique
├── sync_to_github.sh           # Sauvegarde vers GitHub
├── GUIDE_COMPLET.md           # Documentation détaillée
└── scripts/
    ├── smart_pdf_parser_v2.py # Parser PDF → JSON
    ├── run_inference.py       # Inférence SymPointV2
    └── analyze_pdf_ocg.py     # Analyse structure PDF
```

## 🔗 Ressources Google Drive

| Fichier | Lien |
|---------|------|
| **best.pth** (135MB) | [Télécharger](https://drive.google.com/file/d/1LczVNXapght3S65gx0ZOhQ3UqkBg4hJ7/view) |
| **svg_pointT.yaml** | [Télécharger](https://drive.google.com/file/d/1c0_al7p72D7eTOHgBP_kxU1H1Ia-ZakV/view) |
| **plan_test_ocg.pdf** | [Télécharger](https://drive.google.com/file/d/1zr0khQ34Utjznvxv3HbI4yoJUe-IU5JU/view) |

## ⚙️ Configuration RunPod

| Paramètre | Valeur |
|-----------|--------|
| Image | `pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel` |
| GPU | RTX 4000 Ada (20GB) |
| Volume | 50 GB sur `/workspace` |

## 🔄 Workflow

```bash
# Parser un PDF
python smart_pdf_parser_v2.py mon_plan.pdf

# Lancer l'inférence
python run_inference.py mon_plan_s2.json

# Avant de fermer le pod - sauvegarder les modifs
./sync_to_github.sh "description"
```

## 🐛 Problèmes résolus

- ✅ Bug pointops knnquery (patch intégré)
- ✅ Incompatibilité checkpoint PyTorch
- ✅ Détection automatique OCG

## 📊 Classes (35)

Portes (1-6), Fenêtres (7-10), Mobilier (11-15), Cuisine (16-19), Sanitaires (20-25), Circulation (26-28), Murs (31-34), Background (35)
