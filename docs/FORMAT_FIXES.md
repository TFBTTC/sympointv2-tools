# Corrections de Format pour SymPointV2

## Résumé des Problèmes Identifiés (Session Debugging 2024-12)

### Comparaison FloorPlanCAD vs Notre Parser

| Aspect | FloorPlanCAD (fonctionne) | Notre fichier (avant fix) | Impact |
|--------|---------------------------|---------------------------|--------|
| **Dimensions** | 140 x 140 | 1190 x 841 | Échelle incompatible |
| **Primitives** | ~916 | ~42993 | Trop de micro-primitives |
| **args format** | `[x1,y1,x2,y2,...]` (flat) | `[[x1,y1],...]` (nested) | ❌ Format incorrect |
| **widths** | Uniforme 0.1 | Variable 0.03-1.0 | Features différentes |
| **instanceIds** | -1 | 0 | Valeur incorrecte |
| **lengths mean** | 5.44 | 0.25 | Primitives trop courtes |
| **lengths distribution** | 55% dans [1-5] | 78% < 0.1 | Micro-primitives |

### Distribution des Lengths

```
FloorPlanCAD:
  [0-0.1):   0.3%  ← Presque rien
  [0.1-1):  21.4%
  [1-5):   55.0%  ← Majorité
  [5-10):  12.6%
  [10+):   10.7%

Notre fichier (avant fix):
  [0-0.1):  78.1%  ← Problème! (textes, micro-détails)
  [0.1-1):  19.1%
  [1-5):    1.8%
  [5+):     1.0%
```

## Corrections Appliquées

### 1. Format args (CRITIQUE)

**Avant (incorrect):**
```json
"args": [
  [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
  ...
]
```

**Après (correct):**
```json
"args": [
  [x1, y1, x2, y2, x3, y3, x4, y4],
  ...
]
```

### 2. Rescaling vers ~140x140

```python
scale = 140 / max(width, height)
new_args = [[p * scale for p in arg] for arg in args]
```

### 3. Filtrage des Micro-Primitives

```python
MIN_LENGTH = 0.5  # Après rescaling
filtered = [p for p in primitives if calculate_length(p) >= MIN_LENGTH]
```

### 4. Valeurs Uniformes

```python
"widths": [0.1] * n,        # Pas de variation
"instanceIds": [-1] * n,    # -1 = pas d'instance assignée
"rgb": [[0, 0, 0]] * n      # Champ requis
```

## Nettoyage du Plan (Très Important)

Les plans ArchiCAD contiennent beaucoup d'éléments parasites:

### À EXCLURE:
- ❌ Textes et annotations
- ❌ Côtes et dimensions (283, 366, etc.)
- ❌ Légendes (CUI, F, PL, AV, VR, ETEL, CLIM)
- ❌ Cartouche complet
- ❌ Rose des vents
- ❌ Plan de situation miniature
- ❌ Hachures décoratives

### À GARDER:
- ✅ Murs et cloisons
- ✅ Portes (symboles d'ouverture arc)
- ✅ Fenêtres (traits)
- ✅ Éléments sanitaires
- ✅ Escaliers

## Résultats Après Corrections

### Test sur FloorPlanCAD (fichier officiel):
```
Classes détectées:
  Background: 69.7%
  Bed: 16.6%
  Curtain Wall: 8.6%
  Stairs: 2.0%
  Rolling Door: 1.4%
Instances: 40 ✅
```

### Test sur notre plan (après fix):
```
Instances détectées: 13 (vs 0 avant)
Scores sémantiques:
  Wall: 0.0628 ✅
  Window: 0.0109 ✅
  Single Door: 0.0049 ✅
```

Le modèle détecte maintenant des éléments mais avec confiance faible due au style graphique différent. Fine-tuning recommandé pour plans français/européens.
