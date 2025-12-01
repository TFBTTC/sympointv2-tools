# 🛠️ Installation de Label Studio

Ce guide explique comment installer et configurer Label Studio pour l'annotation des plans.

---

## Option 1: Docker (Recommandé) 🐳

### Installation
```bash
# Télécharger l'image
docker pull heartexlabs/label-studio:latest

# Créer un dossier pour les données
mkdir -p ~/annotation_data/images
mkdir -p ~/annotation_data/exports

# Lancer Label Studio
docker run -it -p 8080:8080 \
  -v ~/annotation_data:/label-studio/data \
  heartexlabs/label-studio:latest
```

### Accès
- Ouvrir http://localhost:8080 dans le navigateur
- Créer un compte (email + mot de passe simple)

---

## Option 2: pip (Python) 🐍

### Prérequis
- Python 3.8+
- pip

### Installation
```bash
# Créer un environnement virtuel (optionnel mais recommandé)
python -m venv labelstudio-env
source labelstudio-env/bin/activate  # Linux/Mac
# ou: labelstudio-env\Scripts\activate  # Windows

# Installer Label Studio
pip install label-studio

# Lancer
label-studio start
```

---

## Option 3: Google Colab (Gratuit, en ligne) ☁️

Pour les annotateurs sans installation locale, utiliser ce notebook Colab :

```python
# Cellule 1: Installation
!pip install label-studio

# Cellule 2: Lancement avec ngrok (tunnel)
!pip install pyngrok
from pyngrok import ngrok

# Créer un tunnel
public_url = ngrok.connect(8080)
print(f"Label Studio accessible sur: {public_url}")

# Lancer Label Studio
!label-studio start --no-browser --port 8080
```

---

## Configuration du Projet

### 1. Créer un nouveau projet
- Cliquer "Create Project"
- Nom: "Plans Architecture"
- Description: "Annotation des plans pour SymPointV2"

### 2. Importer la configuration de labels
- Aller dans "Settings" → "Labeling Interface"
- Cliquer sur "Code"
- Coller le contenu du fichier `label-studio-config.xml`
- Sauvegarder

### 3. Importer les images
- Aller dans "Import"
- Glisser-déposer les fichiers PNG
- Ou utiliser "Upload Files"

---

## Configuration Recommandée

### Raccourcis clavier
Les raccourcis sont définis dans la config XML:
- `W` = Wall (Murs)
- `D` = Single Door (Porte)
- `F` = Window (Fenêtre)
- `B` = Background (Fond)
- `T` = Toilet
- `S` = Stairs

### Tips de productivité
1. **Utiliser le zoom**: Molette souris ou boutons +/-
2. **Déplacer l'image**: Clic droit + drag
3. **Annuler**: Ctrl+Z
4. **Supprimer région**: Sélectionner + Suppr
5. **Dupliquer région**: Ctrl+D (utile pour fenêtres identiques)

---

## Export des Annotations

### Pour exporter
1. Aller dans le projet
2. Cliquer "Export"
3. Sélectionner "JSON"
4. Télécharger

---

## Troubleshooting

### "Port 8080 déjà utilisé"
```bash
# Utiliser un autre port
docker run -p 8081:8080 heartexlabs/label-studio:latest
# Accéder via http://localhost:8081
```

### "Images ne s'affichent pas"
Vérifier que les chemins sont corrects. Si les images sont dans un dossier local:
```bash
docker run -p 8080:8080 \
  -v /chemin/vers/images:/label-studio/data/local-files \
  heartexlabs/label-studio:latest
```

---

## Ressources

- Documentation officielle: https://labelstud.io/guide/
- GitHub: https://github.com/HumanSignal/label-studio
- Playground (démo): https://labelstud.io/playground/
