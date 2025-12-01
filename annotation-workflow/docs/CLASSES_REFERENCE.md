# 📚 Référence des Classes SymPointV2

Ce document liste les 35 classes utilisées par SymPointV2.

---

## Classes "Things" (Instances comptables)

### 🚪 Portes (ID 1-6)

| ID | Nom | Description | Symbole typique |
|----|-----|-------------|----------------|
| 1 | Single Door | Porte simple à un vantail | Arc 90° |
| 2 | Double Door | Porte double à deux vantaux | Deux arcs |
| 3 | Sliding Door | Porte coulissante | Trait avec flèche |
| 4 | Folding Door | Porte pliante | Zigzag |
| 5 | Revolving Door | Porte tambour | Croix dans cercle |
| 6 | Rolling Door | Rideau métallique | Ligne ondulée |

### 🪟 Fenêtres (ID 7-10)

| ID | Nom | Description | Symbole typique |
|----|-----|-------------|----------------|
| 7 | Window | Fenêtre standard | Deux traits parallèles |
| 8 | Bay Window | Baie vitrée | Large ouverture |
| 9 | Blind Window | Fenêtre aveugle | Trait simple |
| 10 | Opening Symbol | Symbole d'ouverture | Arc court |

### 🛋️ Mobilier (ID 11-17)

| ID | Nom | Description |
|----|-----|-------------|
| 11 | Sofa | Canapé |
| 12 | Bed | Lit |
| 13 | Chair | Chaise |
| 14 | Table | Table |
| 15 | TV Cabinet | Meuble TV |
| 16 | Wardrobe | Armoire |
| 17 | Cabinet | Placard |

### 🍳 Cuisine (ID 18-21)

| ID | Nom | Description |
|----|-----|-------------|
| 18 | Gas Stove | Plaque de cuisson |
| 19 | Sink | Évier |
| 20 | Refrigerator | Réfrigérateur |
| 21 | Airconditioner | Climatisation |

### 🚿 Sanitaires (ID 22-27)

| ID | Nom | Description |
|----|-----|-------------|
| 22 | Bath | Douche |
| 23 | Bathtub | Baignoire |
| 24 | Washing Machine | Lave-linge |
| 25 | Squat Toilet | WC à la turque |
| 26 | Urinal | Urinoir |
| 27 | Toilet | WC |

### 🔄 Circulation (ID 28-30)

| ID | Nom | Description |
|----|-----|-------------|
| 28 | Stairs | Escaliers |
| 29 | Elevator | Ascenseur |
| 30 | Escalator | Escalator |

---

## Classes "Stuff" (Non comptables)

### 🧱 Structure (ID 33-35)

| ID | Nom | Description | Note |
|----|-----|-------------|------|
| 33 | **Wall** | Murs et cloisons | ⭐ Le plus important |
| 34 | Curtain Wall | Mur-rideau (verre) | Rare |
| 35 | Railing | Garde-corps, rampe | Parfois confondu avec murs |

### ⬛ Background (ID 36 → traité comme 35)

| ID | Nom | Description |
|----|-----|-------------|
| 36 | Background | Tout le reste |

**Inclut :**
- Texte et annotations
- Légendes
- Cartouche
- Hachures décoratives
- Cotes et dimensions
- Rose des vents
- Plans de situation

---

## Priorités pour l'Annotation

### 🔴 HAUTE PRIORITÉ (erreurs fréquentes du modèle)
1. **Wall (33)** - Les murs sont souvent confondus avec Railing
2. **Window (7)** - Confondues avec les portes
3. **Single Door (1)** - Confondues avec les fenêtres
4. **Background (35)** - Les légendes sont classées comme murs

### 🟡 PRIORITÉ MOYENNE
- Double Door (2)
- Sliding Door (3)
- Toilet (27)
- Stairs (28)

### 🟢 PRIORITÉ BASSE (optionnel)
- Mobilier (11-17)
- Cuisine (18-21)
- Autres sanitaires (22-26)

---

## Conseils pour les Cas Ambigus

| Situation | Recommandation |
|-----------|----------------|
| Pas sûr si mur ou railing | Si épais → Wall |
| Pas sûr si porte ou fenêtre | Si arc visible → Door |
| Élément décoratif | → Background |
| Symbole inconnu | → Background |
| Texte/cote | → Background |
| Hachure | → Background |
