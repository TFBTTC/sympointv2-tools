# Guide de Nettoyage des Plans PDF pour SymPointV2

## Pourquoi Nettoyer?

Les plans architecturaux contiennent de nombreux éléments que SymPointV2 ne reconnaît pas:
- Le modèle a été entraîné sur FloorPlanCAD (plans chinois simplifiés)
- Les éléments non-architecturaux génèrent du bruit (milliers de micro-primitives)
- Les textes se convertissent en centaines de petits segments

## Éléments à Supprimer

### 1. Textes et Annotations
```
- Noms de pièces: "Pièce à vivre", "SdE/WC", "Séjour"
- Dimensions: "283", "366", "16,47 m²"
- Labels: "A 1004", "BÂTIMENT A"
- Légendes: CUI, F, PF, AV, GC, VR, ETEL, CLIM, PL
```

### 2. Cartouche
```
- Logo entreprise (COGEDIM, Semewal)
- Informations projet (FAMILLE PASSION IV)
- Tableau surfaces
- Adresse, date, indice
- Mentions légales
```

### 3. Éléments Graphiques Annexes
```
- Rose des vents (orientation N/S/E/O)
- Plan de situation miniature
- Échelle graphique
- Cadre du plan
```

### 4. Hachures et Remplissages
```
- Hachures de coupe
- Remplissages décoratifs
- Ombrages
```

## Méthodes de Nettoyage

### Option 1: Via Calques OCG (Recommandé)

Si le PDF a des calques OCG:
```python
# Exclure les calques par nom
exclude_patterns = [
    'text', 'texte', 'annotation',
    'cote', 'dimension', 'dim',
    'legende', 'legend',
    'cartouche', 'title',
    'hatch', 'hachure'
]
```

### Option 2: Export Sélectif depuis ArchiCAD/Revit

Exporter uniquement les calques:
- Murs
- Cloisons
- Portes
- Fenêtres
- Sanitaires (optionnel)

### Option 3: Filtrage par Longueur

Les textes génèrent des primitives très courtes:
```python
MIN_LENGTH = 0.5  # Filtre la plupart des textes
MIN_LENGTH = 1.0  # Filtrage plus agressif
```

### Option 4: Crop de Zone

Découper uniquement la zone du plan:
```python
# Exclure cartouche et légendes
crop_rect = fitz.Rect(x0, y0, x1, y1)
```

## Workflow Recommandé

1. **Analyser le PDF**
   ```bash
   python analyze_pdf_ocg.py plan.pdf
   ```

2. **Parser avec filtrage**
   ```bash
   python smart_pdf_parser_v3.py plan.pdf --min-length 1.0
   ```

3. **Vérifier les statistiques**
   - Primitives: devrait être ~1000-3000
   - Lengths mean: devrait être ~3-6
   - Lengths median: devrait être ~1-3

4. **Lancer l'inférence**
   ```bash
   python run_inference.py plan_s2.json
   ```

## Cas Particuliers

### Plans Multi-Pages
Traiter chaque page séparément ou découper en zones.

### Plans Très Grands (>50m)
Découper en blocs de ~10-15m comme recommandé par FloorPlanCAD.

### Plans avec Mobilier Détaillé
Le modèle reconnaît certains meubles (lit, canapé, table) mais pas les détails.
