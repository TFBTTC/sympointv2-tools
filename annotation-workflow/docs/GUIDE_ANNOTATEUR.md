# 📖 Guide de l'Annotateur - SymPointV2

## Bienvenue !

Ce guide vous explique comment annoter des plans d'architecture pour améliorer notre modèle d'IA.

---

## 🎯 Votre Mission

Identifier et dessiner des polygones autour des éléments architecturaux dans les plans :
- **Murs** (Wall)
- **Portes** (Door)  
- **Fenêtres** (Window)
- **Fond/Légende** (Background)

---

## 💻 Installation de Label Studio

### Option 1 : Avec Docker (Recommandé)
```bash
docker run -it -p 8080:8080 -v $(pwd)/mydata:/label-studio/data heartexlabs/label-studio:latest
```

### Option 2 : Avec pip
```bash
pip install label-studio
label-studio start
```

### Option 3 : Google Colab (Gratuit, pas d'installation)
Voir le notebook fourni : `annotation_colab.ipynb`

---

## 🚀 Démarrage Rapide

### 1. Ouvrir Label Studio
- Aller sur http://localhost:8080
- Créer un compte (email + mot de passe simple)

### 2. Créer un Projet
- Cliquer "Create Project"
- Nom : "Plans Architecture"
- Importer le fichier de configuration XML fourni

### 3. Importer les Images
- Cliquer "Import"
- Glisser-déposer les fichiers PNG des plans

### 4. Commencer l'Annotation
- Cliquer sur une image
- Sélectionner un label (Wall, Door, Window, Background)
- Dessiner un polygone autour de l'élément
- Répéter pour tous les éléments visibles
- Cliquer "Submit" quand terminé

---

## 🏷️ Les Classes à Annoter

### 🧱 WALL (Murs) - PRIORITÉ 1
**Quoi :** Tous les murs et cloisons du plan
**Comment les reconnaître :**
- Traits épais
- Forment la structure du bâtiment
- Délimitent les pièces

### 🚪 DOOR (Portes) - PRIORITÉ 1
**Quoi :** Toutes les portes (simples, doubles, coulissantes)
**Comment les reconnaître :**
- Arc de cercle (symbole d'ouverture)
- Interruption dans le mur
- Parfois avec symbole de poignée

**Types de portes :**
- `Single Door` (ID 1) : Porte simple avec 1 arc
- `Double Door` (ID 2) : Porte double avec 2 arcs
- `Sliding Door` (ID 3) : Porte coulissante (trait droit)

### 🪟 WINDOW (Fenêtres) - PRIORITÉ 1
**Quoi :** Toutes les fenêtres
**Comment les reconnaître :**
- Deux traits parallèles dans le mur
- Plus fin que les murs
- Pas d'arc d'ouverture (contrairement aux portes)

### ⬛ BACKGROUND (Fond) - PRIORITÉ 2
**Quoi :** Tout ce qui N'EST PAS un élément architectural
**Exemples :**
- Texte et annotations ("Séjour", "12.5 m²")
- Légendes
- Cartouche (cadre avec infos projet)
- Hachures décoratives
- Rose des vents
- Cotes et dimensions

**Règle d'or : En cas de doute → BACKGROUND**

---

## ✏️ Comment Dessiner les Polygones

### Technique de base
1. Sélectionner le label (ex: Wall)
2. Cliquer sur le premier point du contour
3. Cliquer sur les points suivants pour former le polygone
4. Double-cliquer pour fermer le polygone

### Conseils
- **Précision raisonnable** : Pas besoin d'être au pixel près
- **Englober l'élément** : Le polygone doit contenir tout l'élément
- **Un polygone par élément** : Séparer chaque mur, chaque porte
- **Suivre les contours** : Longer les bords de l'élément

---

## ⚠️ Erreurs Courantes à Éviter

### ❌ Confondre fenêtres et portes
- Fenêtre = 2 traits parallèles, PAS d'arc
- Porte = Arc d'ouverture visible

### ❌ Oublier le Background
- Les légendes doivent être marquées Background
- Les hachures décoratives = Background
- Le texte = Background

### ❌ Polygones trop petits
- Englober TOUT l'élément
- Inclure les détails (poignées de porte, etc.)

---

## ⏱️ Temps Estimé par Plan

| Complexité | Temps |
|------------|-------|
| Plan simple (studio) | 10-15 min |
| Plan moyen (T3) | 15-25 min |
| Plan complexe (villa) | 25-40 min |

---

## 💾 Sauvegarder et Exporter

### Sauvegarder en cours de route
- Cliquer "Update" régulièrement
- Label Studio sauvegarde automatiquement

### Exporter quand terminé
1. Aller dans Project → Export
2. Choisir format "JSON"
3. Télécharger le fichier
4. Envoyer à Pierre-Antoine

---

## 🆘 En Cas de Problème

### "Je ne sais pas quelle classe choisir"
→ Utiliser **Background** et noter l'élément problématique

### "L'image est floue/illisible"
→ Passer au plan suivant et signaler

### "Label Studio plante"
→ Rafraîchir la page, les annotations sont sauvegardées

### "Je ne comprends pas un symbole"
→ Prendre une capture d'écran et demander

---

**Merci pour votre travail ! Chaque annotation compte ! 🙏**
