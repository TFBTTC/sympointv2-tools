# 🎯 Workflow d'Annotation pour Fine-tuning SymPointV2

## Objectif
Créer un dataset d'entraînement pour fine-tuner SymPointV2 sur des plans architecturaux français.

## Budget
- **Outils d'annotation : GRATUIT** (Label Studio open source)
- **Hébergement : GRATUIT** (local ou Google Colab)
- **Stockage : GRATUIT** (Google Drive < 15GB)
- **Total : 0€** (hors RunPod pour le training)

---

## 📋 Vue d'Ensemble du Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE D'ANNOTATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PRÉPARATION (Pierre-Antoine)                                │
│     PDF → SVG → PNG + JSON de base                              │
│                                                                 │
│  2. ANNOTATION (Collaborateur)                                  │
│     Label Studio : dessiner polygones sur PNG                   │
│     Classes : Wall, Door, Window, Background, Furniture...      │
│                                                                 │
│  3. CONVERSION (Automatique)                                    │
│     Annotations Label Studio → Format SymPointV2                │
│     Mapping polygones → primitives SVG                          │
│                                                                 │
│  4. TRAINING (Pierre-Antoine)                                   │
│     Fine-tuning sur RunPod avec le nouveau dataset              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Technique

| Composant | Outil | Coût |
|-----------|-------|------|
| Annotation | Label Studio (Docker) | Gratuit |
| Hébergement | Local / Google Colab | Gratuit |
| Stockage | Google Drive | Gratuit |
| Conversion | Scripts Python custom | Gratuit |
| Communication | WhatsApp/Telegram | Gratuit |

---

## 📊 Classes à Annoter

### Priorité HAUTE (erreurs fréquentes)
| ID | Classe | Description | Couleur suggérée |
|----|--------|-------------|------------------|
| 33 | **Wall** | Murs, cloisons | Rouge #A66B20 |
| 7 | **Window** | Fenêtres | Bleu #604EF5 |
| 1 | **Single Door** | Portes simples | Rose #E03E9B |
| 35 | **Background** | Légendes, hachures, texte | Noir #000000 |

### Priorité MOYENNE
| ID | Classe | Description |
|----|--------|-------------|
| 2 | Double Door | Portes doubles |
| 3 | Sliding Door | Portes coulissantes |
| 27 | Toilet | WC |
| 22-23 | Bath/Bathtub | Sanitaires |
| 28 | Stairs | Escaliers |

---

## 🚀 Quick Start

### 1. Préparer les plans (Pierre-Antoine)
```bash
cd /workspace/annotation-workflow
python tools/prepare_for_annotation.py /path/to/plans/*.pdf --output ./data/
```

### 2. Lancer Label Studio (Collaborateur)
```bash
docker run -it -p 8080:8080 -v $(pwd)/data:/label-studio/data heartexlabs/label-studio:latest
```

### 3. Annoter les plans
- Ouvrir http://localhost:8080
- Importer les PNG
- Dessiner les polygones par classe

### 4. Convertir les annotations
```bash
python tools/convert_annotations.py ./exports/annotations.json --output ./dataset/
```

### 5. Fine-tuner le modèle
```bash
# Sur RunPod
python train_finetune.py --data ./dataset/ --epochs 20
```

---

## ⏱️ Estimation du Temps

| Tâche | Temps estimé |
|-------|--------------|
| Setup Label Studio | 30 min |
| Annotation par plan | 15-30 min |
| 50 plans annotés | ~15-25 heures |
| Conversion + validation | 1 heure |
| Fine-tuning | 2-4 heures |

**Recommandation :** Commencer avec 20-30 plans pour un premier fine-tuning, puis itérer.
