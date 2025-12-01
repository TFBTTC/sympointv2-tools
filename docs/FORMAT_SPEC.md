# Spécification du Format JSON SymPointV2

## Vue d'ensemble

SymPointV2 attend des fichiers JSON avec le suffixe `_s2.json` contenant des primitives vectorielles.

## Structure du Fichier

```json
{
  "width": 140,
  "height": 99,
  "commands": [0, 0, 1, 0, ...],
  "args": [
    [x0, y0, x1, y1, x2, y2, x3, y3],
    ...
  ],
  "lengths": [5.2, 3.1, ...],
  "layerIds": [0, 0, 1, 2, ...],
  "widths": [0.1, 0.1, ...],
  "semanticIds": [35, 35, ...],
  "instanceIds": [-1, -1, ...],
  "rgb": [[0,0,0], [0,0,0], ...]
}
```

## Champs Obligatoires

| Champ | Type | Description |
|-------|------|-------------|
| `width` | int | Largeur du plan (typiquement 140) |
| `height` | int | Hauteur du plan (typiquement 99) |
| `commands` | list[int] | Type de primitive: 0=ligne, 1=courbe |
| `args` | list[list[float]] | 8 coordonnées (4 points × 2 coords) par primitive |
| `lengths` | list[float] | Longueur de chaque primitive |
| `layerIds` | list[int] | ID du layer (0=murs, 1=moyens, 2=détails) |
| `widths` | list[float] | Épaisseur (uniforme: 0.1) |
| `semanticIds` | list[int] | Classe sémantique (35=background pour inférence) |
| `instanceIds` | list[int] | ID d'instance (-1 pour inférence) |
| `rgb` | list[list[int]] | Couleur RGB (ignoré) |

## Format des Coordonnées (args)

Chaque primitive est définie par **4 points de contrôle** :

```
[x0, y0, x1, y1, x2, y2, x3, y3]
  │      │      │      │
  ▼      ▼      ▼      ▼
Point0 Point1 Point2 Point3
(start) (1/3)  (2/3)  (end)
```

Pour une **ligne** (command=0), les points intermédiaires sont interpolés :
- Point1 = Point0 + 0.33 × (Point3 - Point0)
- Point2 = Point0 + 0.66 × (Point3 - Point0)

Pour une **courbe** (command=1), les 4 points sont les points de contrôle Bézier.

## Layers

| Layer ID | Signification | Critère de sélection |
|----------|---------------|---------------------|
| 0 | Murs | Traits épais (top 10% des widths) |
| 1 | Éléments moyens | Traits moyens (50-90% des widths) |
| 2 | Détails | Traits fins (bottom 50% des widths) |

## Dimensions Recommandées

- **Target**: 140 × 140 (ou ratio préservé, ex: 140 × 99)
- **FloorPlanCAD reference**: ~900-2000 primitives
- **Lengths**: mean ~5-10, max ~100

## Exemple Minimal

```json
{
  "width": 140,
  "height": 99,
  "commands": [0, 0],
  "args": [
    [10, 10, 30, 30, 50, 50, 70, 70],
    [10, 70, 30, 70, 50, 70, 70, 70]
  ],
  "lengths": [84.85, 60.0],
  "layerIds": [0, 0],
  "widths": [0.1, 0.1],
  "semanticIds": [35, 35],
  "instanceIds": [-1, -1],
  "rgb": [[0,0,0], [0,0,0]]
}
```

## Différences avec FloorPlanCAD

| Aspect | FloorPlanCAD | Nos plans français |
|--------|--------------|--------------------|
| Format args | nested [[x,y], [x,y], ...] | flat [x, y, x, y, ...] |
| Dimensions source | ~1000×1000 | ~1191×842 |
| instanceIds | 0, 1, 2, ... | -1 (inférence) |
| Murs | Lignes doubles | Lignes simples épaisses |

## Validation

Vérifier que :
1. `len(commands) == len(args) == len(lengths) == ...`
2. Chaque élément de `args` a exactement 8 floats
3. `width` et `height` sont ≤ 140
4. `lengths` > 0
