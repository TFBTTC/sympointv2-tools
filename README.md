# SymPointV2 Tools

Outils pour l'inférence SymPointV2 sur des plans d'architecture français (PDF/SVG).

## 🎯 Objectif

Convertir des plans d'architecture (PDF exportés depuis ArchiCAD, AutoCAD, etc.) en format compatible avec SymPointV2 pour la segmentation sémantique des éléments architecturaux.

## 📦 Installation

### Prérequis
- GPU NVIDIA avec CUDA 11.3+
- Python 3.7-3.8
- PyTorch 1.10.x

### Sur RunPod
```bash
# Utiliser l'image: pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel
# GPU recommandé: RTX 4000 Ada (20GB)

# Cloner ce repo
git clone https://github.com/TFBTTC/sympointv2-tools.git
cd sympointv2-tools

# Installer SymPointV2
git clone https://github.com/nicehuster/SymPointV2.git /workspace/SymPointV2
cd /workspace/SymPointV2/modules/pointops
python setup.py install

# Télécharger le checkpoint
mkdir -p /workspace/SymPointV2/checkpoints/sympointv2
gdown --id 1ZeWtgZJKD_yWmFNWwBOMN9_4-x-ZXUuS -O /workspace/SymPointV2/checkpoints/sympointv2/best.pth
```

## 🚀 Utilisation

### Workflow Complet

```bash
# 1. Parser le PDF (universel - fonctionne avec ou sans OCG)
python scripts/universal_pdf_parser.py mon_plan.pdf

# 2. Lancer l'inférence (avec post-traitement pour les murs)
python scripts/run_inference_v2.py mon_plan_s2.json

# 3. Voir les résultats
cat mon_plan_pred.json
```

### Parsers Disponibles

| Script | Description | Usage |
|--------|-------------|-------|
| `universal_pdf_parser.py` | **RECOMMANDÉ** - Parser universel auto-adaptatif | PDFs avec ou sans OCG |
| `smart_pdf_parser_v5.py` | Parser avec seuils fixes | PDFs ArchiCAD standards |

## 📊 Classes Détectées

SymPointV2 détecte 35 catégories d'éléments architecturaux :

### Portes (1-6)
- Single Door, Double Door, Sliding Door, Folding Door, Revolving Door, Rolling Door

### Fenêtres (7-10)
- Window, Bay Window, Blind Window, Opening Symbol

### Mobilier (11-15)
- Sofa, Bed, Chair, Table, TV Cabinet

### Cuisine (16-19)
- Gas Stove, Sink, Refrigerator, AirCon

### Sanitaires (20-25)
- Bath, Bathtub, Washing Machine, Squat Toilet, Urinal, Toilet

### Circulation (26-28)
- Stairs, Elevator, Escalator

### Éléments Linéaires (31-34)
- **Wall**, Curtain Wall, Railing, Fence

### Background (35)
- Éléments non classifiés

## 🔧 Architecture du Parser Universel

```
PDF Input
    │
    ▼
┌─────────────────────────────┐
│  Phase 1: ANALYSE           │
│  - Détection OCG            │
│  - Distribution épaisseurs  │
│  - Calcul seuils auto       │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Phase 2: EXTRACTION        │
│  - Zones texte (exclusion)  │
│  - Cartouche (exclusion)    │
│  - Classification par width │
│    • >= p90 → Murs (L0)     │
│    • >= p50 → Moyens (L1)   │
│    • < p50  → Détails (L2)  │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Phase 3: NORMALISATION     │
│  - Rescale → 140x140        │
│  - Filtrage par longueur    │
│  - Format SymPointV2        │
└─────────────────────────────┘
    │
    ▼
JSON Output (_s2.json)
```

## 🎯 Post-Traitement (Inférence v2)

Le modèle SymPointV2 est entraîné sur FloorPlanCAD (plans chinois) et confond parfois les murs français avec "Railing".

**Solution** : Le script `run_inference_v2.py` applique un post-traitement :
- Les primitives du **Layer 0** (traits épais) prédites comme "Railing" ou "Fence" sont remappées en "Wall"

## 📈 Résultats Typiques

| PDF Type | Wall | Window | Door | Instances |
|----------|------|--------|------|----------|
| Avec OCG | 78-91% | 0.5-2.5% | 1-2% | 6-8 |
| Sans OCG | 2-10% | - | - | 2-3 |

## ⚠️ Limitations

1. **Style graphique** : Le modèle est entraîné sur FloorPlanCAD (Chine), les plans français ont un style différent
2. **Scores faibles** : Les confidences sont souvent < 0.1 (mais les prédictions restent correctes)
3. **Murs** : Nécessite le post-traitement pour remapper Railing → Wall

## 🐛 Bug Connu : pointops knnquery

Le code original SymPointV2 a un bug CUDA dans `knnquery` qui cause des crashs.

**Solution** : Le patch est automatiquement appliqué dans `run_inference_v2.py` :
```python
valid_idx = torch.clamp(idx[:, i].long(), 0, feat.shape[0] - 1)
```

## 📁 Structure du Projet

```
sympointv2-tools/
├── scripts/
│   ├── universal_pdf_parser.py   # Parser universel (recommandé)
│   ├── smart_pdf_parser_v5.py    # Parser avec protection murs
│   ├── run_inference.py          # Inférence basique
│   └── run_inference_v2.py       # Inférence avec post-traitement
├── docs/
│   └── FORMAT_SPEC.md            # Spécification format JSON
└── README.md
```

## 🔗 Liens

- [SymPointV2 Original](https://github.com/nicehuster/SymPointV2)
- [FloorPlanCAD Dataset](https://floorplancad.github.io/)
- [Documentation Project](./docs/)

## 📄 License

MIT License - voir LICENSE
