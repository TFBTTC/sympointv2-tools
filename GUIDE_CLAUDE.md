# Guide Claude - SymPointV2 Tools

## Connexion Pod RunPod

```bash
# Vérifier les pods actifs
runpod:list-pods

# Connexion SSH
ssh root@<IP> -p <PORT>
```

## Setup Rapide (Nouveau Pod)

```bash
# 1. Cloner les outils
cd /workspace
git clone https://github.com/TFBTTC/sympointv2-tools.git
cd sympointv2-tools && chmod +x setup.sh && ./setup.sh

# 2. Ou setup manuel
cd /workspace/SymPointV2/modules/pointops
python setup.py install
export LD_LIBRARY_PATH=/opt/conda/lib/python3.7/site-packages/torch/lib:$LD_LIBRARY_PATH
```

## Workflow Inférence

```bash
# 1. Parser le PDF (v3 avec corrections)
python scripts/smart_pdf_parser_v3.py input.pdf --min-length 0.5

# 2. Lancer inférence
python scripts/run_inference.py input_s2.json
```

## Corrections Format Critiques

| Champ | Valeur Correcte | Erreur Fréquente |
|-------|-----------------|------------------|
| args | `[x1,y1,x2,y2,...]` flat | `[[x1,y1],...]` nested |
| dimensions | ~140x140 | dimensions PDF originales |
| widths | `[0.1, 0.1, ...]` uniforme | valeurs variables |
| instanceIds | `[-1, -1, ...]` | `[0, 0, ...]` |
| lengths | filtrer < 0.5 | garder tout |

## Statistiques Cibles (FloorPlanCAD)

- Dimensions: ~140x140
- Primitives: ~900-2000
- Lengths mean: ~5.4
- Lengths median: ~2.1

## Problèmes Connus

### 100% Background
1. Vérifier format args (liste plate!)
2. Vérifier rescaling (~140x140)
3. Filtrer micro-primitives (textes)
4. Style graphique différent → fine-tuning requis

### CUDA Error knnquery
Le patch est dans run_inference.py (torch.clamp sur indices)

## Liens Utiles

- Repo outils: https://github.com/TFBTTC/sympointv2-tools
- SymPointV2 original: https://github.com/nicehuster/SymPointV2
- FloorPlanCAD dataset: https://floorplancad.github.io/
