# SymPointV2 Tools

Outils pour utiliser SymPointV2 (segmentation de plans d'architecture) sur RunPod.

## 🚀 Quick Start

```bash
# Sur RunPod avec template pytorch:1.10.0-cuda11.3
cd /workspace
git clone https://github.com/TFBTTC/sympointv2-tools.git
cd sympointv2-tools
chmod +x setup.sh && ./setup.sh
```

## 📋 Workflow

```bash
# 1. Parser un PDF
python scripts/smart_pdf_parser_v3.py mon_plan.pdf

# 2. Lancer l'inférence
python scripts/run_inference.py mon_plan_s2.json
```

## ⚠️ Points Critiques

### Format JSON Correct

Le format doit correspondre exactement à FloorPlanCAD:

```json
{
  "width": 140,
  "height": 140,
  "commands": [0, 0, 1, 0],
  "args": [
    [x1, y1, x2, y2, x3, y3, x4, y4],
    ...
  ],
  "lengths": [2.5, 3.1, ...],
  "widths": [0.1, 0.1, ...],
  "instanceIds": [-1, -1, ...],
  "semanticIds": [35, 35, ...],
  "layerIds": [0, 1, 1, ...],
  "rgb": [[0,0,0], ...]
}
```

### Nettoyage Requis

Supprimer avant parsing:
- ❌ Textes, annotations, côtes
- ❌ Cartouche, légendes
- ❌ Rose des vents, plan situation

Garder:
- ✅ Murs, cloisons
- ✅ Portes, fenêtres
- ✅ Sanitaires, escaliers

## 📁 Structure

```
├── scripts/
│   ├── smart_pdf_parser_v3.py  # Parser PDF optimisé
│   ├── run_inference.py        # Inférence avec patch
│   └── analyze_pdf_ocg.py      # Analyse calques OCG
├── docs/
│   ├── FORMAT_FIXES.md         # Détail des corrections
│   └── CLEANING_GUIDE.md       # Guide nettoyage
├── configs/
│   └── runpod_template.json    # Config RunPod
└── setup.sh                    # Installation
```

## 🔧 Corrections Appliquées (v3)

1. **Format args**: Liste plate `[x1,y1,x2,y2,...]`
2. **Rescaling**: Vers ~140x140 (standard FloorPlanCAD)
3. **Filtrage**: Micro-primitives < 0.5 unité
4. **Widths**: Uniformes (0.1)
5. **instanceIds**: -1 (pas 0)

## 📊 Résultats Attendus

Avec un plan correctement préparé:
- Wall, Door, Window détectés
- ~10-50 instances
- Scores 0.05-0.20 (style différent de FloorPlanCAD)

Pour de meilleurs résultats: fine-tuning sur vos plans.

## 📚 Documentation

- [Guide Corrections Format](docs/FORMAT_FIXES.md)
- [Guide Nettoyage Plans](docs/CLEANING_GUIDE.md)
- [Guide Claude](GUIDE_CLAUDE.md)
